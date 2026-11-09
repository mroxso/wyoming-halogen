import asyncio
import io
import wave
from types import SimpleNamespace
import pytest
from wyoming_halogen.audio import wav_bytes, validate
from wyoming_halogen.registry import Registry
from wyoming_halogen.profiles import PROFILES

class Client:
    fail = False
    models = []
    async def inventory(self):
        if self.fail: raise RuntimeError()
        return {'npu':{'status':'ok'}},self.models

@pytest.mark.asyncio
async def test_inventory_recovery_and_selection():
    c = Client()
    config = SimpleNamespace(profiles={},stale_grace=0,default_asr=None,default_tts=None)
    r = Registry(c,config)
    c.models = [{'id':'LFM3-Audio-2B-fast'},{'id':'unrelated'}]
    await r.refresh()
    assert len(r.info().asr)==len(r.info().tts)==1
    assert r.select('asr').id == 'LFM3-Audio-2B-fast'
    c.fail=True
    await r.refresh()
    assert not r.models and not r.healthy
    c.fail=False
    await r.refresh()
    assert r.models
    c.models=[]
    await r.refresh()
    assert not r.models
    with pytest.raises(ValueError): r.select('tts')

def test_wav():
    data = b'\0\0'*160
    with wave.open(io.BytesIO(wav_bytes(data,(16000,2,1)))) as w:
        assert w.getframerate()==16000
        assert w.readframes(160)==data
    with pytest.raises(ValueError): validate(0,2,1)

@pytest.mark.asyncio
async def test_german_advertised_for_both_services():
    c = Client()
    c.models = [{'id':'LFM3-Audio-2B-fast'}]
    r = Registry(c,SimpleNamespace(profiles={},stale_grace=0))
    await r.refresh()
    info = r.info()
    assert 'de' in info.asr[0].models[0].languages
    assert 'de' in info.tts[0].voices[0].languages
    assert 'en-GB' in info.tts[0].voices[0].languages

@pytest.mark.asyncio
async def test_tts_forwards_language_and_speaker():
    import httpx
    from wyoming.event import Event
    from wyoming_halogen.tts import synthesize
    requests = []
    def respond(request):
        import json
        requests.append(json.loads(request.content))
        return httpx.Response(200,content=b'\x00\x00'*12)
    events = []
    async def write(event): events.append(event)
    model = PROFILES['LFM3-Audio-2B-fast']
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
        h = SimpleNamespace(registry=SimpleNamespace(resolve_voice=lambda *args:(model,None)),
            program=None, config=SimpleNamespace(default_voice=None,max_text=4096,max_bytes=1000),
            client=SimpleNamespace(http=http,base='http://halogen'),write_event=write)
        await synthesize(h,Event('synthesize',data={'text':'Guten Morgen.',
            'voice':{'name':model.id,'language':'de','speaker':'male'}}))
        assert requests[0]['language']=='de'
        assert requests[0]['voice']=='male'
        assert [e.type for e in events]==['audio-start','audio-chunk','audio-stop']
        with pytest.raises(ValueError,match='Unsupported language'):
            await synthesize(h,Event('synthesize',data={'text':'Hello','voice':{'language':'xx'}}))
        assert len(requests)==1

@pytest.mark.asyncio
async def test_home_assistant_voice_selection():
    import httpx
    import json
    from wyoming.event import Event
    from wyoming_halogen.tts import synthesize
    c = Client()
    c.models = [{'id': 'LFM3-Audio-2B-fast'}]
    config = SimpleNamespace(profiles={}, stale_grace=0, default_tts=None,
                             default_voice=None, max_text=4096, max_bytes=1000)
    r = Registry(c, config)
    await r.refresh()
    voices = r.info().tts[0].voices
    assert [v.description for v in voices] == ['Female', 'Male']
    assert all(v.speakers is None for v in voices)
    requests = []
    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, content=b'\0\0')
    async def write(event): pass
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
        h = SimpleNamespace(registry=r, program=None, config=config,
                            client=SimpleNamespace(http=http, base='http://halogen'),
                            write_event=write)
        for voice in voices:
            await synthesize(h, Event('synthesize', data={'text':'Hallo',
                'voice':{'name':voice.name, 'language':'de'}}))
    assert [req['voice'] for req in requests] == ['female', 'male']
    assert all(req['model'] == 'LFM3-Audio-2B-fast' for req in requests)
    assert r.resolve_voice('LFM3-Audio-2B-fast')[1] is None
    with pytest.raises(ValueError): r.resolve_voice('unknown/voice')
