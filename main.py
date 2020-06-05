#! /usr/bin/env nix-shell
#! nix-shell -p "python3.withPackages (p: with p; [aiohttp aiosqlite pyyaml aiofiles coloredlogs])" -i python3

from aiohttp import web
import asyncio

from settings import config
from server import build_app
from fetcher import fetcher

if __name__ == '__main__':
    web.run_app(build_app(config))
