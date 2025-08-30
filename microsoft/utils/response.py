import asyncio

def async_to_sync_stream_response_consumer(agen):
    """
    Wrap an async generator so it can be used as a sync iterator
    for StreamingHttpResponse.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def consume():
        async for item in agen:
            yield item

    ait = consume().__aiter__()
    try:
        while True:
            value = loop.run_until_complete(ait.__anext__())
            print(value)
            yield value
    except StopAsyncIteration:
        pass
    finally:
        loop.close()
        