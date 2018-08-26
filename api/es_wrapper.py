from elasticsearch_dsl import Search, Q
from services.elasticsearch_client import es


def get_account_history(account_id=None, operation_type=None, from_=0, size=10, 
                        from_date='2015-10-10', to_date='now', sort_by='-block_data.block_time',
                        type='data', agg_field='operation_type'):
    if type != "data":
        s = Search(using=es, index="bitshares-*")
    else:
        s = Search(using=es, index="bitshares-*", extra={"size": size, "from": from_})

    q = Q()

    if account_id:
        q = q & Q("match", account_history__account=account_id)
    if operation_type:
        q = q & Q("match", operation_type=operation_type)

    range_query = Q("range", block_data__block_time={'gte': from_date, 'lte': to_date})
    s.query = q & range_query

    if type != "data":
        s.aggs.bucket('per_field', 'terms', field=agg_field, size=size)

    s = s.sort(sort_by)
    response = s.execute()

    if type == "data":
        return [ hit.to_dict() for hit in response ]
    else:
        return [ field.to_dict() for field in response.aggregations.per_field.buckets ]


def get_single_operation(operation_id):
    s = Search(using=es, index="bitshares-*", extra={"size": 1})
    s.query = Q("match", account_history__operation_id=operation_id)

    response = s.execute()

    return [ hit.to_dict() for hit in response ]

def get_trx(trx, from_=0, size=10):
    s = Search(using=es, index="bitshares-*", extra={"size": size, "from": from_})
    s.query = Q("match", block_data__trx_id=trx)

    response = s.execute()

    return [ hit.to_dict() for hit in response ]
