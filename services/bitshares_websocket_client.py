from websocket import create_connection, WebSocketConnectionClosedException
import json
from services.cache import cache
import threading

import config


class RPCError(Exception):
    pass


class BitsharesWebsocketClient():

    LOCK = threading.Lock()

    def __init__(self, websocket_url):
        self.url = websocket_url
        self._connect()

    def _connect(self):
        self.ws = create_connection(self.url, enable_multithread=True)
        self.request_id = 1
        self.api_ids = {
            'database': 0,
            'login': 1
        }

    def request(self, api, method_name, params):
        # WebSocket calls are not threadsafe without proper response management
        with BitsharesWebsocketClient.LOCK:
            try:
                return self._safe_request(api, method_name, params)
            except WebSocketConnectionClosedException:
                self.ws.close()
                self._connect()
                return self._safe_request(api, method_name, params)
            except Exception as e:
                print(e)
                self.ws.close()
                self._connect()
                return self._safe_request(api, method_name, params)

    def _safe_request(self, api, method_name, params):
        api_id = self.load_api_id(api)
        payload = {
            'id': self.request_id,
            'method': 'call',
            'params': [
                api_id,
                method_name,
                params
            ]
        }
        request_string = json.dumps(payload)
        # print('> {}'.format(request_string))
        self.ws.send(request_string)
        self.request_id += 1
        reply = self.ws.recv()
        # print('< {}'.format(reply))

        ret = {}
        try:
            ret = json.loads(reply, strict=False)
        except ValueError:
            raise ValueError("Client returned invalid format. Expected JSON!")

        if 'error' in ret:
            if 'detail' in ret['error']:
                raise RPCError(ret['error']['detail'])
            else:
                raise RPCError(ret['error']['message'])
        else:
            return ret["result"]

    def load_api_id(self, api):
        if (api not in self.api_ids):
            api_id = self._safe_request('login', api, [])
            self.api_ids[api] = api_id
        return self.api_ids[api]

    def get_object(self, object_id):
        return self.request('database', 'get_objects', [[object_id]])[0]

    @cache.memoize()
    def get_global_properties(self):
        return self.request('database', 'get_global_properties', [])

    def get_balances(self, asset_id, threshold=100000000, return_as_es=False):
        all_balances = []
        add_balances = self.request(
            'asset',
            'get_asset_holders',
            [asset_id, 0, 100]
        )
        all_balances += add_balances
        while len(add_balances) == 100:
            add_balances = self.request(
                'asset', 
                'get_asset_holders', 
                [asset_id, len(all_balances), 100]
            )
            all_balances += add_balances
            if int(add_balances[-1]["amount"]) < threshold:
                break
        if return_as_es:
            for _balance in all_balances:
                _balance.update({
                    "balance": _balance["amount"],
                    "asset_type": asset_id,
                    "owner": _balance["account_id"]
                })
                del _balance["name"]
                del _balance["account_id"]
        return all_balances


client = BitsharesWebsocketClient(config.WEBSOCKET_URL)
