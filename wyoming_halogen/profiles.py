from dataclasses import dataclass

@dataclass(frozen=True)
class Profile:
    id: str
    asr: bool
    tts: bool
    languages: tuple[str, ...]
    voices: tuple[str, ...] = ()
    rate: int = 24000
    provenance: str = 'Halogen NPU documentation'

LANGUAGES = ('zh', 'en', 'fr', 'de', 'it', 'ja', 'ko', 'pt', 'ru', 'es')
VOICES = ('aiden', 'dylan', 'eric', 'ono_anna', 'ryan', 'serena', 'sohee', 'uncle_fu', 'vivian')
PROFILES = {}
for size in ('0.6b', '1.7b'):
    name = f'qwen3-asr-{size}'
    PROFILES[name] = Profile(name, True, False, LANGUAGES)
    name = f'qwen3-tts-{size}-customvoice'
    PROFILES[name] = Profile(name, False, True, LANGUAGES, VOICES)
# Halogen documents 19 LFM3 speech locales; en is its US-English alias.
LFM_LANGUAGES = ('en', 'en-US', 'en-GB', 'ar', 'da', 'de', 'el', 'fi', 'fr',
                 'he', 'it', 'ja', 'ko', 'nl', 'pl', 'pt', 'es', 'sv', 'tr', 'zh')

for name in ('LFM3-Audio-2B', 'LFM3-Audio-2B-fast'):
    PROFILES[name] = Profile(name, True, True, LFM_LANGUAGES, ('female', 'male'))
