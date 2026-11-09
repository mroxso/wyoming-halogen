from wyoming.audio import AudioStart, AudioChunk, AudioStop

async def synthesize(h, event):
    d = event.data
    voice = d.get('voice') or {}
    model = h.registry.select('tts',voice.get('name') or h.program)
    language = voice.get('language')
    if language and language not in model.languages: raise ValueError('Unsupported language')
    speaker = voice.get('speaker') or h.config.default_voice or model.voices[0]
    if speaker not in model.voices: raise ValueError('Unsupported speaker')
    text = d['text']
    if not isinstance(text,str) or not 0 < len(text) <= h.config.max_text: raise ValueError('Text exceeds configured limit or is empty')
    if d.get('text_format','text') != 'text': raise ValueError('Only plain text is supported')
    body = dict(model=model.id,input=text,voice=speaker,response_format='pcm',stream=True)
    if language:
        body['language'] = language
    async with h.client.http.stream('POST',h.client.base+'/v1/audio/speech',json=body) as r:
        r.raise_for_status()
        await h.write_event(AudioStart(model.rate,2,1).event())
        pending = b''
        total = 0
        async for chunk in r.aiter_bytes():
            total += len(chunk)
            if total > h.config.max_bytes: raise ValueError('Generated audio exceeds configured limit')
            pending += chunk
            aligned = len(pending)//2*2
            for offset in range(0,aligned,4096):
                await h.write_event(AudioChunk(model.rate,2,1,pending[offset:min(offset+4096,aligned)]).event())
            pending = pending[aligned:]
        if pending: raise ValueError('Truncated PCM sample')
    await h.write_event(AudioStop().event())
