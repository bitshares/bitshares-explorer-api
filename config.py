import os


WEBSOCKET_URL = os.environ.get('WEBSOCKET_URL', "ws://localhost:8090/ws")
# a connection to a bitshares full node
FULL_WEBSOCKET_URL = os.environ.get('FULL_WEBSOCKET_URL', "ws://88.99.145.10:9999/ws")

# a connection to Elastic Search.
ELASTICSEARCH = {
    #'hosts': os.environ.get('ELASTICSEARCH_URL', 'http://148.251.10.231:5005/').split(','), # oxarbitrage
    'hosts': os.environ.get('ELASTICSEARCH_URL', 'http://bts-es.clockwork.gr:5000').split(','), # clockwork
    'user': os.environ.get('ELASTICSEARCH_USER', None),
    'password': os.environ.get('ELASTICSEARCH_USER', None)
}


# Database connection: see https://www.postgresql.org/docs/current/static/libpq-connect.html#LIBPQ-PARAMKEYWORDS
POSTGRES = {'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': os.environ.get('POSTGRES_PORT', '5432'),
            'database': os.environ.get('POSTGRES_DATABASE', 'explorer'),
            'user': os.environ.get('POSTGRES_USER', 'postgres'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'posta'),
}

# Cache: see https://flask-caching.readthedocs.io/en/latest/#configuring-flask-caching
CACHE = {
    'CACHE_TYPE': os.environ.get('CACHE_TYPE', 'simple'),
    'CACHE_DEFAULT_TIMEOUT': int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 600)) # 10 min
}

# Configure profiler: see https://github.com/muatik/flask-profiler
PROFILER = {
    'enabled': os.environ.get('PROFILER_ENABLED', False),
    'username': os.environ.get('PROFILER_USERNAME', None),
    'password': os.environ.get('PROFILER_PASSWORD', None),
}

CORE_ASSET_SYMBOL = 'BTS'
CORE_ASSET_ID = '1.3.0'

TESTNET = 0 # 0 = not in the testnet, 1 = testnet
CORE_ASSET_SYMBOL_TESTNET = 'TEST'
