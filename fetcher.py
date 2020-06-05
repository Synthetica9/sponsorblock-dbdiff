import asyncio
import aiohttp
import aiofiles
import aiosqlite

from time import time
from pathlib import Path
from math import log2, copysign


async def prune_db(in_path, out_path):
    # TODO: also copy category when this becomes relevant
    # isolation_level is needed to avoid the issue also specified in
    # https://github.com/ghaering/pysqlite/issues/109
    async with aiosqlite.connect(in_path) as db:
        await db.execute('''
            ATTACH DATABASE ':memory:' AS out_db
        ''')

        await db.execute('''
            CREATE TABLE out_db.compactSponsorTimes (
                videoID STRING NOT NULL,
                startTime REAL NOT NULL,
                endTime REAL NOT NULL,
                category STRING NOT NULL
            )
        ''')

        segments = []
        block = float('-inf')
        lastVideoID = None

        Q = '''
            SELECT videoID, startTime, endTime, category, votes
            FROM sponsorTimes
            ORDER BY videoID, startTime
        '''
        async with db.execute(Q) as cur:
            async for (videoID, startTime, endTime, category, votes) in cur:
                shouldAppend = False
                if startTime > block or lastVideoID != videoID:
                    block = endTime
                    lastVideoID = videoID
                    shouldAppend = True
                elif segments and 0 <= votes > segments[-1][1]:
                    segments.pop()
                    shouldAppend = True

                if shouldAppend:
                    segments.append(
                        (
                            (videoID, startTime, endTime, category),
                            votes
                        )
                    )

        await db.executemany('''
            INSERT INTO out_db.compactSponsorTimes
            VALUES (?, ?, ?, ?)
        ''', (x[0] for x in segments))

        await db.commit()

        # Dump to file:
        await db.execute('''
            VACUUM out_db INTO ?
        ''', [str(out_path)])


async def dump_db(app, content):
    staging_file_path = Path(app['config']['db_staging_location'])
    staging_file_path.parent.mkdir(parents=True, exist_ok=True)
    m = app['hash_algo']()
    try:
        async with aiofiles.open(staging_file_path, "xb") as f:
            async for data in content.iter_chunked(1024):
                m.update(data)
                await f.write(data)

        out_path = app['utils'].digestPath(m)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if not out_path.exists():
            await prune_db(staging_file_path, out_path)
    finally:
        staging_file_path.unlink()
    return m.hexdigest()


async def fetcher(app):
    endpoint = app['config']['master_endpoint']

    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint) as response:
            app.logger.info('Starting fetch of database')

            app['persistent']['latest'] = latest = await dump_db(app, response.content)
            app['utils'].logAccess(latest)

            app.logger.info('Finished fetch of database')
            app.logger.debug(f'Latest hash is now {latest}')
