import pytest

from services.bitshares_websocket_client import BitsharesWebsocketClient
import config

@pytest.fixture
def bitshares_client():
    return BitsharesWebsocketClient(config.WEBSOCKET_URL)

def test_ws_request(bitshares_client):
    response = bitshares_client.request('database', "get_dynamic_global_properties", [])
    assert response['id'] == '2.1.0'
    assert 'head_block_number' in response

def test_automatic_api_id_retrieval(bitshares_client):
    bitshares_client.request('asset', 'get_asset_holders', ['1.3.0', 0, 100])

def test_get_object(bitshares_client):
    object = bitshares_client.get_object('1.3.0')
    assert object