from elasticsearch_dsl import Search, Q
from services.bitshares_elasticsearch_client import es
from elasticsearch.exceptions import NotFoundError
from datetime import datetime, timedelta

def get_account_history(account_id=None, operation_type=None, from_=0, size=10, 
                        from_date='2015-10-10', to_date='now', sort_by='-block_data.block_time',
                        type='data', agg_field='operation_type'):
    if type != "data":
        s = Search(using=es, index="bitshares-*")
    else:
        s = Search(using=es, index="bitshares-*", extra={"size": size, "from": from_})

    q = Q()

    if account_id and account_id != '':
        q = q & Q("match", account_history__account=account_id)
    if operation_type and operation_type != -1:
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

    return [ hit.to_dict() for hit in response ][0]


def is_alive():
    find_string = datetime.utcnow().strftime("%Y-%m")
    from_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    s = Search(using=es, index="bitshares-" + find_string)
    s.query = Q("range", block_data__block_time={'gte': from_date, 'lte': "now"})
    s.aggs.metric("max_block_time", "max", field="block_data.block_time")

    json_response = {
        "server_time": datetime.utcnow(),
        "head_block_timestamp": None,
        "head_block_time": None
    }

    try:
        response = s.execute()
        if response.aggregations.max_block_time.value is not None:
            json_response["head_block_time"] = str(response.aggregations.max_block_time.value_as_string)
            json_response["head_block_timestamp"] = response.aggregations.max_block_time.value
            json_response["deltatime"] = abs((datetime.utcfromtimestamp(json_response["head_block_timestamp"] / 1000) - json_response["server_time"]).total_seconds())
            if json_response["deltatime"] < 30:
                json_response["status"] = "ok"
            else:
                json_response["status"] = "out_of_sync"
                json_response["error"] = "last_block_too_old"
        else:
            json_response["status"] = "out_of_sync"
            json_response["deltatime"] = "Infinite"
            json_response["query_index"] = find_string
            json_response["query_from_date"] = from_date
            json_response["error"] = "no_blocks_last_24_hours"
    except NotFoundError:
        json_response["status"] = "out_of_sync"
        json_response["deltatime"] = "Infinite"
        json_response["error"] = "index_not_found"
        json_response["query_index"] = find_string

    return json_response


def get_trx(trx, from_=0, size=10):
    s = Search(using=es, index="bitshares-*", extra={"size": size, "from": from_})
    s.query = Q("match", block_data__trx_id=trx)

    response = s.execute()

    return [ hit.to_dict() for hit in response ]
