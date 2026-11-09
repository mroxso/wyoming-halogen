import httpx

class Halogen:
    def __init__(self, config):
        self.config = config
        self.base = config.halogen_url.rstrip('/').removesuffix('/v1')
        self.http = httpx.AsyncClient(timeout=config.timeout, headers={'Authorization': f'Bearer {config.key}'} if config.key else {}, limits=httpx.Limits(max_connections=config.concurrency+2))

    async def inventory(self):
        health = await self.http.get(self.base+'/health')
        health.raise_for_status()
        models = await self.http.get(self.base+'/v1/models')
        models.raise_for_status()
        return health.json(), models.json()['data']

    async def transcribe(self, model, wav, language):
        data = {'model':model.id, 'response_format':'json'}
        if language: data['language'] = language
        r = await self.http.post(self.base+'/v1/audio/transcriptions', data=data, files={'file':('audio.wav',wav,'audio/wav')})
        r.raise_for_status()
        text = r.json()['text']
        if not isinstance(text,str): raise ValueError('Malformed transcript')
        return text
