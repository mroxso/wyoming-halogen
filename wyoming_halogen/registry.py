import asyncio
import logging
import time
from .profiles import PROFILES, Profile

class Registry:
    def __init__(self, client, config):
        self.client, self.config = client, config
        self.models = ()
        self.last_success = 0
        self.healthy = False

    async def refresh(self):
        try:
            health, inventory = await self.client.inventory()
            profiles = dict(PROFILES)
            for name, fields in self.config.profiles.items():
                profiles[name] = Profile(id=name, **fields)
            ready = health.get('npu',{}).get('status') == 'ok'
            self.models = tuple(profiles[m['id']] for m in sorted(inventory,key=lambda m:m['id']) if m['id'] in profiles and ready and m.get('ready',True))
            self.last_success = time.monotonic()
            self.healthy = True
        except Exception:
            self.healthy = False
            logging.warning('Discovery failed')
            if time.monotonic()-self.last_success >= self.config.stale_grace: self.models = ()

    async def run(self):
        while True:
            await asyncio.sleep(self.config.refresh)
            await self.refresh()

    def select(self, capability, name=None):
        name = name or getattr(self.config,'default_'+capability)
        models = [m for m in self.models if getattr(m,capability) and (not name or m.id == name)]
        if len(models)!=1: raise ValueError('Select one available model with a configured default or explicit name')
        return models[0]

    def resolve_voice(self, name=None, program=None):
        # Voice IDs include the model so selection remains unambiguous.
        for model in self.models:
            if model.tts:
                for speaker in model.voices:
                    if name == f'{model.id}/{speaker}':
                        return model, speaker
        # Preserve the previous model-name + speaker protocol for existing clients.
        return self.select('tts', name or program), None

    def info(self):
        from wyoming.info import Info, Attribution, AsrProgram, AsrModel, TtsProgram, TtsVoice
        info = Info()
        for m in self.models:
            common = dict(name=m.id, attribution=Attribution('Halogen','https://github.com/peonist-ai/halogen-flash-server'), installed=True, description=m.provenance, version=None)
            if m.asr: info.asr.append(AsrProgram(**common,models=[AsrModel(**common,languages=list(m.languages))]))
            if m.tts:
                voices = [TtsVoice(**{**common, 'name': f'{m.id}/{speaker}',
                                      'description': speaker.replace('_', ' ').title()},
                                   languages=list(m.languages)) for speaker in m.voices]
                info.tts.append(TtsProgram(**common, voices=voices))
        return info
