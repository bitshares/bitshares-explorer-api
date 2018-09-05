import os


WEBSOCKET_URL = os.environ.get('WEBSOCKET_URL', "ws://localhost:8090/ws")

# Default connection to Elastic Search.
ELASTICSEARCH = {
     'hosts': os.environ.get('ELASTICSEARCH_URL', 'https://es.bitshares.eu/').split(','),
     'user': os.environ.get('ELASTICSEARCH_USER', 'BitShares'),
     'password': os.environ.get('ELASTICSEARCH_USER', '******')
}

# Optional ElasticSearch cluster to access other data.
# Currently expect:
#   - 'operations': for bitshares-* indexes where operations are stored
#   - 'objects': for object-* indexes where Chain data is stored.
#
# Sample:
#
# ELASTICSEARCH_ADDITIONAL {
#   'operations': None, # Use default cluster.
#   'objects': {
#     'hosts': ['https://es.mycompany.com/'],
#     'user': 'myself',
#     'password': 'secret'
#    }
# }
ELASTICSEARCH_ADDITIONAL = {
    # Overwrite cluster to use to retrieve bitshares-* index.
    'operations': None,
    # Overwrite cluster to use to retrieve bitshares-* index.
    'objects': {
        'hosts': ['http://148.251.10.231:5005/'] # oxarbitrage (no credentials)
    }
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
    'CACHE_TYPE': os.environ.get('CACHE_TYPE', 'simple'), # use 'uwsgi' when running under uWSGI server.
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
