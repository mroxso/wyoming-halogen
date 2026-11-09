import asyncio
import logging
import httpx
from wyoming.server import AsyncEventHandler
from wyoming.error import Error
from .audio import validate
from .stt import transcribe
from .tts import synthesize

class Handler(AsyncEventHandler):
    def __init__(self, reader, writer, registry, slots):
        super().__init__(reader,writer)
        self.registry = registry
        self.client = registry.client
        self.config = registry.config
        self.slots = slots
        self.program = None
        self.reset()

    def reset(self):
        self.model = None
        self.fmt = None
        self.buffer = bytearray()
        self.language = None

    async def handle_event(self,event):
        try:
            if event.type == 'describe':
                await self.write_event(self.registry.info().event())
            elif event.type == 'select-program': self.program = event.data['name']
            elif event.type == 'transcribe':
                if self.model: raise ValueError('A transcription is already active')
                self.model = self.registry.select('asr',event.data.get('name') or self.program)
                self.language = event.data.get('language')
                if self.language and self.language not in self.model.languages: raise ValueError('Unsupported language')
            elif event.type == 'audio-start':
                if not self.model or self.fmt: raise ValueError('Expected transcribe before audio-start')
                self.fmt = tuple(event.data[k] for k in ('rate','width','channels'))
                validate(*self.fmt)
            elif event.type == 'audio-chunk':
                if not self.fmt: raise ValueError('Expected audio-start')
                if tuple(event.data[k] for k in ('rate','width','channels')) != self.fmt: raise ValueError('PCM format changed')
                payload = event.payload or b''
                if len(payload) % (self.fmt[1]*self.fmt[2]): raise ValueError('Unaligned PCM')
                limit = min(self.config.max_bytes,int(self.config.max_seconds*self.fmt[0]*self.fmt[1]*self.fmt[2]))
                if len(self.buffer)+len(payload)>limit: raise ValueError('Recording exceeds configured limit')
                self.buffer.extend(payload)
            elif event.type in ('audio-stop','synthesize'):
                if event.type == 'audio-stop' and not self.fmt: raise ValueError('Expected audio-start')
                if event.type == 'synthesize' and self.model: raise ValueError('Transcription is active')
                if self.slots.locked():
                    await self.write_event(Error('Server is busy; try again later','busy').event())
                else:
                    async with self.slots:
                        async with asyncio.timeout(self.config.timeout):
                            if event.type == 'audio-stop': await transcribe(self)
                            else: await synthesize(self,event)
                self.reset()
            elif event.type.startswith('synthesize-'): raise ValueError('Streaming text input is unsupported')
        except (ValueError,KeyError,TypeError,IndexError) as exc:
            self.reset()
            await self.write_event(Error(str(exc),'invalid-input').event())
        except (httpx.HTTPError,TimeoutError):
            self.reset()
            logging.warning('Speech request failed')
            await self.write_event(Error('Upstream speech request failed','upstream-error').event())
        return True

    async def run(self):
        # Read independently so EOF cancels active HTTP work immediately.
        task = None
        try:
            from wyoming.event import async_read_event
            while True:
                read = asyncio.create_task(async_read_event(self.reader))
                if task:
                    done,_ = await asyncio.wait((read,task),return_when=asyncio.FIRST_COMPLETED)
                    if task in done:
                        await task
                        task = None
                event = await read
                if event is None: break
                if task:
                    await self.write_event(Error('Request already active','busy').event())
                    continue
                task = asyncio.create_task(self.handle_event(event))
                if event.type not in ('audio-stop','synthesize'):
                    await task
                    task = None
        finally:
            if task:
                task.cancel()
                await asyncio.gather(task,return_exceptions=True)
            self.reset()
            self.writer.close()
