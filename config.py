import os


WEBSOCKET_URL = os.environ.get('WEBSOCKET_URL', "ws://127.0.0.1:8090/ws")

POSTGRES = {'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'database': os.environ.get('POSTGRES_DATABASE', 'explorer'),
            'user': os.environ.get('POSTGRES_USER', 'postgres'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'posta'),
}

# a connection to a bitshares full node
FULL_WEBSOCKET_URL = os.environ.get('FULL_WEBSOCKET_URL', "ws://88.99.145.10:9999/ws")

# a connection to an ElasticSearch wrapper
ES_WRAPPER = os.environ.get('ES_WRAPPER', "http://185.208.208.184:5000")


CORE_ASSET_SYMBOL = 'BTS'
CORE_ASSET_ID = '1.3.0'
