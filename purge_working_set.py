from pathlib import Path


async def purge_working_set(app):
    app.logger.info('Purging working set')

    max_working_set_size = app['config']['max_working_set_size']
    access_log = app['persistent']['access_log']
    digest_to_path = app['utils'].digestPath

    access_order = (
        k
        for (k, v) in sorted(
            access_log.items(),
            key=lambda x: x[1]
        )
    )

    working_set_size = 0
    new_working_set = set()
    for digest in access_order:
        path = digest_to_path(digest)
        working_set_size += path.stat().st_size

        if working_set_size >= max_working_set_size:
            app.logger.info(f'Unlinking {digest}')

            path.unlink()
            del access_log[digest]
        else:
            new_working_set.add(path)

    # Check that there are no orphans that are not in the access log:
    working_dir = app['config']['db_cache_dir']
    for potentialOrphan in working_dir.iterdir():
        if potentialOrphan not in new_working_set:
            app.logger.info(f'Unlinking orphan {potentialOrphan}')
            potentialOrphan.unlink()
