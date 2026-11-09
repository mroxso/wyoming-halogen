import asyncio
import logging
from wyoming.server import AsyncServer
from .config import parse_args
from .halogen import Halogen
from .registry import Registry
from .server import Handler

async def run(config):
    client = Halogen(config)
    registry = Registry(client,config)
    await registry.refresh()
    if config.health:
        print('healthy' if registry.healthy else 'degraded')
        await client.http.aclose()
        return 0 if registry.healthy else 1
    refresh = asyncio.create_task(registry.run())
    slots = asyncio.Semaphore(config.concurrency)
    server = AsyncServer.from_uri(config.uri)
    def factory(reader,writer):
        handler = Handler(reader,writer,registry,slots)
        if len(server._handlers) >= config.max_connections:
            writer.close()
        return handler
    try:
        await server.run(factory)
    finally:
        refresh.cancel()
        await asyncio.gather(refresh,return_exceptions=True)
        tasks = list(server._handlers)
        for task in tasks: task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        await server.stop()
        await client.http.aclose()
    return 0

def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    try: raise SystemExit(asyncio.run(run(parse_args())))
    except KeyboardInterrupt: pass

if __name__ == '__main__': main()
