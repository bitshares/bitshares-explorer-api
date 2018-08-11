import pytest

from repositories.bitshares_websocket_client import BitsharesWebsocketClient
import config

def test_ws_request():
    bitshares_client = BitsharesWebsocketClient(config.WEBSOCKET_URL)
    response = bitshares_client.request('database', "get_dynamic_global_properties", [])
    assert response['id'] == '2.1.0'
    assert 'head_block_number' in response

def test_automatic_api_id_retrieval():
    bitshares_client = BitsharesWebsocketClient(config.WEBSOCKET_URL)
    bitshares_client.request('asset', 'get_asset_holders', ['1.3.0', 0, 100])