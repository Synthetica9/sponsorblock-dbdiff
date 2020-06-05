import asyncio
from datetime import timedelta
import itertools


async def every(dt, coro, *args, **kwargs):
    if isinstance(dt, timedelta):
        dt = dt.total_seconds()

    while True:
        await coro(*args, **kwargs)
        await asyncio.sleep(dt)
