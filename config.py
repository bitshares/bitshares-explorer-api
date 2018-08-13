import os


WEBSOCKET_URL = os.environ.get('WEBSOCKET_URL', "ws://localhost:8090/ws")
#WEBSOCKET_PUBLIC_HELPER = os.environ.get('WEBSOCKET_URL', "wss://node.bitshares.eu/ws")

POSTGRES = {'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': os.environ.get('POSTGRES_PORT', '5432'),
            'database': os.environ.get('POSTGRES_DATABASE', 'explorer'),
            'user': os.environ.get('POSTGRES_USER', 'postgres'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'posta'),
}

# a connection to a bitshares full node
FULL_WEBSOCKET_URL = os.environ.get('FULL_WEBSOCKET_URL', "wss://api.fr.bitsharesdex.com")

# a connection to an ElasticSearch wrapper
#ES_WRAPPER = os.environ.get('ES_WRAPPER', "http://185.208.208.184:5000")
# clockwork server:
ES_WRAPPER = os.environ.get('ES_WRAPPER', "http://95.216.32.252:5000")
#ES_WRAPPER = os.environ.get('ES_WRAPPER', "https://eswrapper.bitshares.eu")


CORE_ASSET_SYMBOL = 'BTS'
CORE_ASSET_ID = '1.3.0'

TESTNET = 1 # 0 = not in the testnet, 1 = testnet
CORE_ASSET_SYMBOL_TESTNET = 'TEST'
