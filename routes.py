from aiohttp import web
from dbdiff import dbdiff

routes = web.RouteTableDef()


@routes.get('/')
async def hello(request):
    return web.Response(text="Hello, world")


@routes.get('/latest')
async def latest(request):
    return web.Response(text=request.app['persistent']['latest'])


@routes.get('/snapshot/{digest:[0-9a-fA-F]+}')
async def snapshot(request):
    digest = request.match_info['digest']
    request.app['utils'].logAccess(digest)
    path = request.app['utils'].digestPath(digest)
    return web.FileResponse(path)


@routes.get('/diff/{old:[0-9a-fA-F]+}/{new:[0-9a-fA-F]+}')
async def diff(request):
    old, new = (request.match_info[x] for x in ('old', 'new'))
    try:
        diff = await dbdiff(request.app, old, new)
    except FileNotFoundError:
        return web.Response(status=404, text='Not found.')
    except RuntimeError as e:
        return web.Response(status=400, text=str(e))

    return web.Response(text=diff)
