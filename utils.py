from pathlib import Path
from base64 import b16decode
from datetime import datetime
import re


class Utils(object):
    def __init__(self, app):
        self.app = app

    def digestPath(self, digest):
        if not isinstance(digest, str):
            digest = digest.hexdigest()
        digest = digest.lower()
        return Path(self.app['config']['db_cache_dir']) / digest

    def hash_combine(self, h1, h2):
        m = self.app['hash_algo']()
        for h in [h1, h2]:
            m.update(b16decode(h.upper().strip()))
        return m.hexdigest()

    def logAccess(self, digest):
        self.app.logger.debug(f'Logging access to {digest}')
        log = self.app['persistent'].setdefault('access_log', {})

        # This _could_ be a race condition potentially with threads,
        # but we don't really care about the difference of a few ms.
        log[digest] = datetime.utcnow().timestamp()


exponents = {
    "": 0,
    "K": 1,
    "M": 2,
    "G": 3,
    "T": 4,
}


def parseSize(size):
    m = re.match(r'^(\d+)\s*([KMGT])?(i?)B$', size)

    if m is None:
        raise ValueError('Could not parse size')

    mantissa, exponent, base = m.groups()

    exponent = exponents[exponent]
    base = 1024 if base else 1000
    mantissa = int(mantissa)

    return mantissa * base ** exponent
