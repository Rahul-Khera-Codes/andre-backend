import asyncio

from ..models import (
    Message,
    Session
)
from ..utils.azure_ai import TalkToYourDocument


def async_to_sync_stream_response_consumer(agen, question: str, ttyd: TalkToYourDocument):
    """
    Wrap an async generator so it can be used as a sync iterator
    for StreamingHttpResponse.
    """
    # save user role -> question
    # ttyd.add_to_history("user", question)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def consume():
        async for item in agen:
            yield item

    ait = consume().__aiter__()
    output = ""
    try:
        while True:
            value = loop.run_until_complete(ait.__anext__())
            output += value
            print(value)
            yield value
    except StopAsyncIteration:
        # ttyd.add_to_history("assistant", output)
        pass
    finally:
        loop.close()
        