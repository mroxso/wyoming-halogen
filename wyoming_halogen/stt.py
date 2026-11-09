from wyoming.asr import Transcript
from .audio import wav_bytes

async def transcribe(handler):
    text = await handler.client.transcribe(handler.model, wav_bytes(handler.buffer,handler.fmt),handler.language)
    await handler.write_event(Transcript(text,language=handler.language).event())
