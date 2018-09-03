from elasticsearch_dsl import connections, Search, Q, A
import config

class BitsharesElasticSearchClient():
    def __init__(self, elasticsearch_config):
        
        if      'user' in elasticsearch_config and elasticsearch_config['user'] \
            and 'password' in elasticsearch_config and elasticsearch_config['password']:
            connections.create_connection(hosts=elasticsearch_config['hosts'],
                                          http_auth=(elasticsearch_config['user'], elasticsearch_config['password']),
                                          timeout=60)
        else:
            connections.create_connection(hosts=elasticsearch_config['hosts'], timeout=60)

    def get_markets(self, from_date, to_date, base=None, quote=None):
        query = {
            "size": 0,  
            "query": {
                "bool": {
                    "filter": [
                        { "term": { "operation_type": 4 } },
                        { 
                            "range": { 
                                "block_data.block_time": { 
                                    "gte": from_date, 
                                    "lte": to_date
                                } 
                            } 
                        }
                    ]
                }
            },
            "aggs": {
                "pairs": {
                    "composite" : {
                        "size": 10000, # TODO use a generator function instead of a big size, see https://github.com/elastic/elasticsearch-dsl-py/blob/master/examples/composite_agg.py#L21
                        "sources" : [
                            { "pays_asset": { "terms" : { "field": "additional_data.fill_data.pays_asset_id.keyword" } } },
                            { "recieves_asset": { "terms" : { "field": "additional_data.fill_data.receives_asset_id.keyword" } } }
                        ]
                    },
                    "aggs": {
                        "volume": { "sum" : { "field" : "additional_data.fill_data.receives_amount" } }
                    }
                }
            }
        }

        if base:
            query['query']['bool']['filter'].append({ "term": { "additional_data.fill_data.pays_asset_id": base } })
        if quote:
            query['query']['bool']['filter'].append({ "term": { "additional_data.fill_data.receives_asset_id": quote } })

        client = connections.get_connection()
        response = client.search(index="bitshares-*", body=query)

        markets = {}
        for bucket in response['aggregations']['pairs']['buckets']:
            pays_asset = bucket['key']['pays_asset']
            recieves_asset = bucket['key']['recieves_asset']
            volume = bucket['volume']['value']
            nb_operations = bucket['doc_count']

            if pays_asset not in markets:
                markets[pays_asset] = {}
            markets[pays_asset][recieves_asset] = { 'volume': volume, 'nb_operations': nb_operations }

        return markets

    # This is only to keep a trace of the code somewhere as it does not work due to a bug in elasticsearch-dsl.
    def _get_markets_with_dsl(self, from_date, to_date):
        # Could not use DSL due to a bug on multi sources composite aggregation:
        # https://github.com/elastic/elasticsearch-dsl-py/issues/963

        s = Search(index="bitshares-*")
        s = s.extra(size=0)
        s = s.query('bool', filter = [
            Q('term', operation_type=4),
            Q("range", block_data__block_time={'gte': from_date, 'lte': to_date})
        ])

        sources = [ 
            { 'pays_asset': A('terms', field='additional_data.fill_data.pays_asset_id.keyword') },
            { 'recieves_asset': A('terms', field='additional_data.fill_data.receives_asset_id.keyword') }
        ]

        # Bug here as 'sources' does not support a list.
        a = A('composite', sources=sources, size=10000).metric('volume', 'sum', field='additional_data.fill_data.receives_amount')
        s.aggs.bucket('pairs', a)
        response = s.execute()

        # TODO...

    def get_asset_ids(self):
        s = Search(index="objects-asset") \
            .extra(size=10000)               \
            .query('match_all')              \
            .source(['object_id'])

        response = s.execute()

        asset_ids = [ hit.object_id for hit in response]
        return asset_ids

    def get_asset_names(self, start):
        s = Search(index="objects-asset") \
            .query('prefix', symbol__keyword=start)              \
            .source(['symbol'])

        print(s.to_dict())

        response = s.execute()

        asset_names = [ hit.symbol for hit in response]
        return asset_names



client = BitsharesElasticSearchClient(config.ELASTICSEARCH)
es = connections.get_connection()

if __name__ == "__main__":
    import pprint
    asset_names = client.get_asset_names('T')
    pprint.pprint(asset_names)
