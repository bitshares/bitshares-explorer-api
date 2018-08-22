from flask_caching import Cache

import config
cache = Cache(config=config.CACHE)
