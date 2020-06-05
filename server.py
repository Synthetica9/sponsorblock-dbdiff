from aiohttp import web
import asyncio
from aiochron import every

import yaml
import hashlib
import sys
import logging
from pathlib import Path

from utils import Utils, parseSize
from fetcher import fetcher
from purge_working_set import purge_working_set
from routes import routes

try:
    import coloredlogs
except ImportError:
    pass


async def load_persistent(app):
    try:
        with open(app['config']['persistent_path'], 'r') as f:
            app['persistent'] = yaml.load(f, Loader=yaml.SafeLoader) or {}
    except FileNotFoundError:
        app['persistent'] = {}


async def store_persistent(app):
    app.logger.info('Storing persistent data...')
    with open(app['config']['persistent_path'], 'w') as f:
        yaml.dump(app['persistent'], f)


async def add_recurring_tasks(app):
    tasks = {
        'fetch_every': (fetcher, app),
        'persistent_store_interval': (store_persistent, app),
        'purge_interval': (purge_working_set, app),
    }

    for k, v in tasks.items():
        delay = app['config'][k]
        app.loop.create_task(every(delay, *v))


async def print_module_versions(app):
    app.logger.info(f'Using Python {sys.version}')
    app.logger.info('Using the following library versions:')
    for k, v in sys.modules.items():
        if not k.startswith('_') and hasattr(v, '__version__'):
            app.logger.info(f'  {k} {v.__version__}')


async def setup_logging(app):
    level = app['config'].get('log_level')
    if isinstance(level, str):
        level = level.upper()

    try:
        coloredlogs.install(level=level)
    except NameError:
        pass

    app.logger.debug('Logging set up.')


def massage_config(config):
    max_working_set_size = config['max_working_set_size']

    if isinstance(max_working_set_size, str):
        max_working_set_size = parseSize(max_working_set_size)

    config['max_working_set_size'] = max_working_set_size

    config['persistent_path'] = Path(config['persistent_path'])
    config['db_cache_dir'] = Path(config['db_cache_dir'])
    config['db_staging_location'] = Path(config['db_staging_location'])


def build_app(config):
    app = web.Application()

    app.add_routes(routes)

    app['config'] = config
    massage_config(app['config'])

    app['utils'] = Utils(app)

    app['hash_algo'] = getattr(hashlib, config['hash_algo'])

    logging.basicConfig(level=logging.DEBUG)

    app.on_startup.append(setup_logging)
    app.on_startup.append(print_module_versions)

    app.on_startup.append(load_persistent)
    app.on_shutdown.append(store_persistent)

    app.on_startup.append(add_recurring_tasks)

    return app
