import argparse
import os
import json
from pathlib import Path
from urllib.parse import urlsplit


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--uri', default='tcp://127.0.0.1:10300')
    p.add_argument('--halogen-url', default=os.getenv('HALOGEN_URL', 'http://localhost:8731/v1'))
    p.add_argument('--api-key-file', type=Path)
    p.add_argument('--overrides', type=Path, help='JSON mapping exact model IDs to profile fields')
    p.add_argument('--default-asr')
    p.add_argument('--default-tts')
    p.add_argument('--default-voice')
    p.add_argument('--health', action='store_true')
    for name, default, kind in [('refresh',30,float), ('stale-grace',120,float), ('timeout',120,float), ('concurrency',2,int), ('max-connections',16,int), ('max-bytes',25000000,int), ('max-seconds',1200,float), ('max-text',4096,int)]:
        p.add_argument('--'+name, default=default, type=kind)
    a = p.parse_args()
    if urlsplit(a.halogen_url).scheme not in ('http','https'):
        p.error('Halogen URL must use HTTP or HTTPS')
    for k in ('refresh','stale_grace','timeout','concurrency','max_connections','max_bytes','max_seconds','max_text'):
        if getattr(a,k) <= 0: p.error(k+' must be positive')
    a.key = a.api_key_file.read_text().strip() if a.api_key_file else os.getenv('HALOGEN_API_KEY')
    a.profiles = json.loads(a.overrides.read_text()) if a.overrides else {}
    return a
