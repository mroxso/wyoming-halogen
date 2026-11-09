# Wyoming–Halogen

Async Python proxy exposing Halogen speech models to Wyoming clients. Requires Python 3.11+; no accelerator access is needed in this process.

```sh
pip install .
wyoming-halogen --halogen-url http://halogen:8731/v1
```

Use `HALOGEN_URL` and optional `HALOGEN_API_KEY`, or `--api-key-file` for a mounted secret. Run `wyoming-halogen --help` for limits, concurrency, refresh, timeouts and defaults. `--health` checks discovery and exits nonzero on failure. The listener remains available during upstream outages; descriptions expire after `--stale-grace` seconds and recover on refresh. A successful empty inventory removes services immediately.

## Home Assistant

Start Halogen with a supported speech model. Bind the proxy explicitly to the LAN:

```sh
wyoming-halogen --uri tcp://0.0.0.0:10300 --halogen-url http://halogen:8731/v1
```

In Settings → Devices & services → Add integration, select Wyoming Protocol and enter the proxy host and port. See the [official instructions](https://www.home-assistant.io/integrations/wyoming/). Both STT and TTS should be created when both are advertised. In Settings → Voice assistants, edit an Assist pipeline, select these providers, choose a compatible language and voice/speaker, and retain your conversation agent. Speak a command and verify the transcript, resulting action and audible response.

Client model selection varies. Run separate proxy instances with `--default-asr MODEL --default-tts MODEL` on distinct `--uri` ports to make model selection deterministic, and add each port as its own integration entry. Reload the Wyoming integration after model changes or proxy restart; if new capabilities are missing, remove and re-add the entry. Check descriptions and provider availability after each change. External VAD is required for STT recording boundaries.

Wyoming has no native authentication or encryption. Expose the listener only to trusted networks; see the [upstream security model](https://github.com/OHF-Voice/wyoming/blob/main/SECURITY.md).

## Models and protocol

Pinned client contracts: Wyoming 1.11.0 and HTTPX 0.28.1. Exact profiles cover Qwen3-ASR 0.6B/1.7B, Qwen3-TTS CustomVoice 0.6B/1.7B, and LFM3-Audio-2B with its fast variant. Unknown IDs are omitted. Discovery requires healthy NPU status and presence in `/v1/models`; loaded-only status is not required because Halogen loads on demand. Profiles derive from the [Halogen NPU reference](https://github.com/peonist-ai/halogen-flash-server/blob/main/docs/NPU.md). LFM advertises the 19 speech locales documented by Halogen, including German; the selected language is forwarded for STT and TTS. After updating the container, reload the Wyoming integration so Home Assistant refreshes its supported languages. Qwen language coverage is currently limited to the shared ten-language subset.

ASR accepts integer PCM WAV-compatible input, 8–192 kHz, 1–4 bytes per sample, mono/stereo. WAV is passed at the original rate: Halogen handles decoding/resampling, so no local resampler is necessary. Defaults limit recordings to 25 MB / 20 minutes and text to 4096 characters. TTS requests streamed 24 kHz 16-bit mono PCM. Explicit `transcribe.name`, `select-program`, and `synthesize.voice.name` select models; `voice.speaker` selects the upstream voice. Ambiguous defaults fail. Unsupported languages and speakers fail before inference.

Custom profiles use `--overrides profiles.json`, mapping exact IDs to `asr`, `tts`, `languages`, `voices`, `rate`, and optional `provenance`. Only enable dedicated endpoint capabilities verified for your build. Example:

```json
{"my-speech-model":{"asr":true,"tts":true,"languages":["en"],"voices":["female","male"],"rate":24000,"provenance":"Operator verified endpoint contract"}}
```

## Container and development

Start with Docker Compose (copy `.env.example` to `.env` and edit as needed):

```sh
cp .env.example .env
HALOGEN_URL=http://halogen:8731/v1 docker compose up -d --build
```

By default, `compose.yaml` connects to Halogen on the Docker host using `host.docker.internal:8731` and publishes Wyoming on port 10300. Set `HALOGEN_URL` to your Halogen server URL, `WYOMING_PORT` to change the published port, and optionally `HALOGEN_API_KEY` for authentication. These variables can also be set in a local `.env` file. Use the Docker host's hostname and published port when adding the Home Assistant integration.

```sh
docker build -t wyoming-halogen .
docker run --rm -p 10300:10300 -e HALOGEN_URL=http://halogen:8731/v1 wyoming-halogen
pip install '.[test]'
pytest
```

Live validation confirmed LFM3-Audio-2B-fast WAV output at 24 kHz, 16-bit mono, and retranscription of generated speech. Unit tests cover inventory filtering, outage expiry/recovery, selection and WAV conversion.

Release validation still required: a real Home Assistant Assist pipeline, Qwen live coverage, inventory combinations on separate Halogen builds, disconnect/load stress tests, and WAV-response fallback. Current TTS requires the documented PCM response contract. No Home Assistant end-to-end validation is claimed.
