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
