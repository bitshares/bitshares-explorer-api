import os


WEBSOCKET_URL = os.environ.get('WEBSOCKET_URL', "ws://localhost:8090/ws")
# a connection to a bitshares full node
FULL_WEBSOCKET_URL = os.environ.get('FULL_WEBSOCKET_URL', "ws://88.99.145.10:9999/ws")

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

# a connection to an ElasticSearch wrapper
#ES_WRAPPER = os.environ.get('ES_WRAPPER', "http://185.208.208.184:5000") # oxarbitrage
ES_WRAPPER = os.environ.get('ES_WRAPPER', "http://95.216.32.252:5000") # clockwork
#ES_WRAPPER = os.environ.get('ES_WRAPPER', "https://eswrapper.bitshares.eu") # Infrastructure worker


CORE_ASSET_SYMBOL = 'BTS'
CORE_ASSET_ID = '1.3.0'

TESTNET = 0 # 0 = not in the testnet, 1 = testnet
CORE_ASSET_SYMBOL_TESTNET = 'TEST'
