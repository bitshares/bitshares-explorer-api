from websocket import create_connection
import json
from services.cache import cache

class RPCError(Exception):
    pass

class BitsharesWebsocketClient():
    def __init__(self, websocket_url):
        self.ws = create_connection(websocket_url)
        self.request_id = 1
        self.api_ids = {
            'database': 0,
            'login': 1
        }
    
    def request(self, api, method_name, params):
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
        #print('> {}'.format(request_string))
        self.ws.send(request_string)
        self.request_id += 1
        reply =  self.ws.recv()
        #print('< {}'.format(reply))

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
            api_id = self.request('login', api, [])
            self.api_ids[api] = api_id
        return self.api_ids[api]

    def get_object(self, object_id):
        return self.request('database', 'get_objects', [[object_id]])[0]

    @cache.memoize()
    def get_global_properties(self):
        return self.request('database', 'get_global_properties', [])

import config
client = BitsharesWebsocketClient(config.WEBSOCKET_URL)
