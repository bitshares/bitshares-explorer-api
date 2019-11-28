from .utils import needs_es, verify_es_response

from elasticsearch_dsl import Search, Q
from services.bitshares_elasticsearch_client import es
from datetime import datetime, timedelta
from services.cache import cache


@needs_es()
def get_account_history(
        account_id=None,
        operation_type=None,
        from_=0,
        size=10,
        from_date='2015-10-10',
        to_date='now',
        sort_by='-operation_id_num',
        search_after=None,
        type='data',  # @ReservedAssignment
        agg_field='operation_type'
):
    s = Search(using=es, index="bitshares-*")
    if type == "data":
        s = s.extra(size=size)
        if search_after and search_after != '':
            s = s.extra(search_after=search_after.split(','))
        else:
            s = s.extra(**{"from": from_})

    q = Q()

    if account_id and account_id != '':
        q = q & Q("match", account_history__account=account_id)
    if (operation_type and operation_type != -1) or operation_type == 0:
        q = q & Q("match", operation_type=operation_type)

    range_query = Q("range", block_data__block_time={'gte': from_date, 'lte': to_date})
    s.query = q & range_query

    if type != "data":
        s.aggs.bucket('per_field', 'terms', field=agg_field, size=size)

    s = s.sort(*sort_by.split(','))
    response = s.execute()
    verify_es_response(response)

    if type == "data":
        return [hit.to_dict() for hit in response]
    else:
        return [field.to_dict() for field in response.aggregations.per_field.buckets]


@needs_es()
@cache.memoize()
def get_single_operation(operation_id):
    s = Search(using=es, index="bitshares-*")
    s.query = Q("match", account_history__operation_id=operation_id)

    response = s.execute()
    verify_es_response(response)

    return [hit.to_dict() for hit in response][0]


@needs_es()
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

    response = s.execute()
    verify_es_response(response)

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

    return json_response


@needs_es()
@cache.memoize()
def get_trx(trx, from_=0, size=10):
    s = Search(using=es, index="bitshares-*", extra={"size": size, "from": from_})
    s.query = Q("match", block_data__trx_id=trx)

    response = s.execute()
    verify_es_response(response)

    return [hit.to_dict() for hit in response]


@needs_es()
def get_trade_history(size=10, from_date='2015-10-10', to_date='now', sort_by='-operation_id_num',
                      search_after=None, base="1.3.0", quote="1.3.121"):

    s = Search(using=es, index="bitshares-*")

    s = s.extra(size=size)
    if search_after and search_after != '':
        s = s.extra(search_after=search_after.split(','))

    q = Q()
    q = q & Q("match", operation_type=4)
    q = q & Q("match", operation_history__op_object__is_maker=True)

    q = q & Q("match", operation_history__op_object__fill_price__base__asset_id=base)
    q = q & Q("match", operation_history__op_object__fill_price__quote__asset_id=quote)

    range_query = Q("range", block_data__block_time={'gte': from_date, 'lte': to_date})
    s.query = q & range_query

    s = s.sort(*sort_by.split(','))
    response = s.execute()
    verify_es_response(response)

    return [hit.to_dict() for hit in response]
