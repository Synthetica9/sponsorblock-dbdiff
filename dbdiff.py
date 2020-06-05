import aiosqlite
import binascii


async def dbdiff(app, old, new):
    try:
        out_digest = app['utils'].hash_combine(old, new)
    except binascii.Error:
        raise FileNotFoundError()

    old_path, new_path, out_path = (
        app['utils'].digestPath(x) for x in [old, new, out_digest]
    )

    if not all([x.exists() for x in [old_path, new_path]]):
        raise FileNotFoundError()

    if not out_path.exists():
        app.logger.info(f'Diffing {old} and {new}')
        async with aiosqlite.connect(':memory:') as db:
            await db.execute('ATTACH ? AS old', [str(old_path)])
            await db.execute('ATTACH ? AS new', [str(new_path)])

            try:
                await db.execute('''
                    CREATE TABLE added AS
                        SELECT * FROM new.compactSponsorTimes
                        EXCEPT SELECT * from old.compactSponsorTimes
                ''')
                await db.execute('''
                    CREATE TABLE removed AS
                        SELECT * FROM old.compactSponsorTimes
                        EXCEPT SELECT * from new.compactSponsorTimes
                ''')
            except aiosqlite.OperationalError:
                raise RuntimeError('Could not unify databases')

            await db.commit()

            await db.execute('VACUUM INTO ?', [str(out_path)])

    return out_digest
