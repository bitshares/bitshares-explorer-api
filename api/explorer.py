import datetime
import json
import psycopg2
from services.bitshares_websocket_client import BitsharesWebsocketClient, client as bitshares_ws_client
from services.cache import cache
import es_wrapper
import config

def _get_core_asset_name():
    if config.TESTNET == 1:
        return config.CORE_ASSET_SYMBOL_TESTNET
    else:
        return config.CORE_ASSET_SYMBOL

def get_header():
    response = bitshares_ws_client.request('database', 'get_dynamic_global_properties', [])
    return _add_global_informations(response, bitshares_ws_client)

def get_account(account_id):
    return bitshares_ws_client.request('database', 'get_accounts', [[account_id]])

def get_account_name(account_id):
    account = get_account(account_id)
    return account[0]['name']

def _get_account_id(account_name):
    if not _is_object(account_name):
        account = bitshares_ws_client.request('database', 'lookup_account_names', [[account_name], 0])
        return account[0]['id']
    else:
        return account_name

def _add_global_informations(response, ws_client):
    # get market cap
    core_asset = ws_client.get_object('2.3.0')
    current_supply = core_asset["current_supply"]
    confidental_supply = core_asset["confidential_supply"]
    market_cap = int(current_supply) + int(confidental_supply)
    response["bts_market_cap"] = int(market_cap/100000000)

    if config.TESTNET != 1: # Todo: had to do something else for the testnet
        btsBtcVolume = ws_client.request('database', 'get_24_volume', ["BTS", "OPEN.BTC"])
        response["quote_volume"] = btsBtcVolume["quote_volume"]
    else:
        response["quote_volume"] = 0

    global_properties = ws_client.get_global_properties()
    response["commitee_count"] = len(global_properties["active_committee_members"])
    response["witness_count"] = len(global_properties["active_witnesses"])

    return response

def _enrich_operation(operation, ws_client):
    dynamic_global_properties = ws_client.request('database', 'get_dynamic_global_properties', [])
    operation["accounts_registered_this_interval"] = dynamic_global_properties["accounts_registered_this_interval"]

    return _add_global_informations(operation, ws_client)

def get_operation_full_elastic(operation_id):
    res = es_wrapper.get_single_operation(operation_id)
    operation = { 
        "op": json.loads(res[0]["operation_history"]["op"]),
        "block_num": res[0]["block_data"]["block_num"], 
        "op_in_trx": res[0]["operation_history"]["op_in_trx"],
        "result": json.loads(res[0]["operation_history"]["operation_result"]), 
        "trx_in_block": res[0]["operation_history"]["trx_in_block"],
        "virtual_op": res[0]["operation_history"]["virtual_op"], 
        "block_time": res[0]["block_data"]["block_time"]
    }

    operation = _enrich_operation(operation, bitshares_ws_client)
    return [ operation ]

def get_accounts():
    core_asset_holders = get_asset_holders('1.3.0', start=0, limit=100)
    return core_asset_holders


def get_full_account(account_id):
    account = bitshares_ws_client.request('database', 'get_full_accounts', [[account_id], 0])
    return account


def get_assets():
    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    # TODO for DB2ES: Search for filled orders, grouped by volume
    query = "SELECT * FROM assets WHERE volume > 0 ORDER BY volume DESC"
    cur.execute(query)
    results = cur.fetchall()
    con.close()

    # [ [db_id, asset_name, asset_id, price_in_bts, 24h_volume, market_cap, type, supply, holders,  wallettype (=''), precision]]
    return results


def get_fees():
    return bitshares_ws_client.get_global_properties()

def get_asset(asset_id):
    return [ _get_asset(asset_id) ]


def _get_asset(asset_id_or_name):
    asset = None
    if not _is_object(asset_id_or_name):
        asset = bitshares_ws_client.request('database', 'lookup_asset_symbols', [[asset_id_or_name], 0])[0]
    else:
        asset = bitshares_ws_client.request('database', 'get_assets', [[asset_id_or_name], 0])[0]

    dynamic_asset_data = bitshares_ws_client.get_object(asset["dynamic_asset_data_id"])
    asset["current_supply"] = dynamic_asset_data["current_supply"]
    asset["confidential_supply"] = dynamic_asset_data["confidential_supply"]
    asset["accumulated_fees"] = dynamic_asset_data["accumulated_fees"]
    asset["fee_pool"] = dynamic_asset_data["fee_pool"]

    issuer = bitshares_ws_client.get_object(asset["issuer"])
    asset["issuer_name"] = issuer["name"]

    return asset


def get_asset_and_volume(asset_id):
    asset = _get_asset(asset_id)
    
    core_symbol = _get_core_asset_name()

    volume = _get_volume(asset['symbol'], core_symbol)
    asset['volume'] = volume['base_volume']

    if asset['symbol'] != core_symbol:
        ticker = get_ticker(asset['symbol'], core_symbol)
        asset['mcap'] = int(asset['current_supply']) * float(ticker['latest'])
    else:
        asset['mcap'] = int(asset['current_supply'])

    return [asset]


def get_block(block_num):
    block = bitshares_ws_client.request('database', 'get_block', [block_num, 0])
    return block


def get_ticker(base, quote):
    return bitshares_ws_client.request('database', 'get_ticker', [base, quote])


def _get_volume(base, quote):
    return bitshares_ws_client.request('database', 'get_24_volume', [base, quote])


def get_object(object):
    return [ bitshares_ws_client.get_object(object) ]

def _ensure_asset_id(asset_id):
    if not _is_object(asset_id):
        asset = bitshares_ws_client.request('database', 'lookup_asset_symbols', [[asset_id], 0])[0]
        return asset['id']
    else:
        return asset_id

def get_asset_holders_count(asset_id):
    asset_id = _ensure_asset_id(asset_id)
    return bitshares_ws_client.request('asset', 'get_asset_holders_count', [asset_id])


def get_asset_holders(asset_id, start=0, limit=20):
    asset_id = _ensure_asset_id(asset_id)
    asset_holders = bitshares_ws_client.request('asset', 'get_asset_holders', [asset_id, start, limit])
    return asset_holders


def get_workers():
    workers_count = bitshares_ws_client.request('database', 'get_worker_count', [])
    workers = bitshares_ws_client.request('database', 'get_objects', [ [ '1.14.{}'.format(i) for i in range(0, workers_count) ] ])

    # get the votes of worker 1.14.0 - refund 400k
    refund400k = bitshares_ws_client.get_object("1.14.0")
    thereshold =  int(refund400k["total_votes_for"])

    result = []
    for worker in workers:
        if worker:
            worker["worker_account_name"] = get_account_name(worker["worker_account"])
            current_votes = int(worker["total_votes_for"])
            perc = (current_votes*100)/thereshold
            worker["perc"] = perc
            result.append([worker])

    result = result[::-1] # Reverse list.
    return result


def _is_object(string):
    return len(string.split(".")) == 3

def get_markets(asset_id):
    asset_id = _ensure_asset_id(asset_id)

    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    # # TODO for DB2ES: Use core get_ticker, or query of filled orders on bitshares-*.
    query = "SELECT * FROM markets WHERE aid=%s"
    cur.execute(query, (asset_id,))
    results = cur.fetchall()
    con.close()
    return results


def get_most_active_markets():
    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    # # TODO for DB2ES: use core get_top_markets, or query filled orders on bitshares-*
    # Need this PR: https://github.com/bitshares/bitshares-core/pull/1273
    query = "SELECT * FROM markets WHERE volume>0 ORDER BY volume DESC LIMIT 100"
    cur.execute(query)
    results = cur.fetchall()
    con.close()
    return results


def _ensure_safe_limit(limit):
    if not limit:
        limit = 10
    elif int(limit) > 50:
        limit = 50
    return limit

def get_order_book(base, quote, limit=False):
    limit = _ensure_safe_limit(limit)    
    order_book = bitshares_ws_client.request('database', 'get_order_book', [base, quote, limit])
    return order_book


def get_margin_positions(account_id):
    margin_positions = bitshares_ws_client.request('database', 'get_margin_positions', [account_id])
    return margin_positions


def get_witnesses():
    witnesses_count = bitshares_ws_client.request('database', 'get_witness_count', [])
    witnesses = bitshares_ws_client.request('database', 'get_objects', [ ['1.6.{}'.format(w) for w in range(0, witnesses_count)] ])
    result = []
    for witness in witnesses:
        if witness:
            witness["witness_account_name"] = get_account_name(witness["witness_account"])
            result.append([witness])

    result = sorted(result, key=lambda k: int(k[0]['total_votes']))
    result = result[::-1] # Reverse list.
    return result



def get_committee_members():
    committee_count = bitshares_ws_client.request('database', 'get_committee_count', [])
    committee_members = bitshares_ws_client.request('database', 'get_objects', [ ['1.5.{}'.format(i) for i in range(0, committee_count)] ])

    result = []
    for committee_member in committee_members:
        if committee_member:
            committee_member["committee_member_account_name"] = get_account_name(committee_member["committee_member_account"])
            result.append([committee_member])

    result = sorted(result, key=lambda k: int(k[0]['total_votes']))
    result = result[::-1] # this reverses array

    return result


def get_market_chart_dates():
    base = datetime.date.today()
    date_list = [base - datetime.timedelta(days=x) for x in range(0, 100)]
    date_list = [d.strftime("%Y-%m-%d") for d in date_list]
    return list(reversed(date_list))


def get_market_chart_data(base, quote):
    base_asset = bitshares_ws_client.request('database', 'lookup_asset_symbols', [[base], 0])[0]
    base_id = base_asset["id"]
    base_precision = 10**base_asset["precision"]

    quote_asset = bitshares_ws_client.request('database', 'lookup_asset_symbols', [[quote], 0])[0]
    quote_id = quote_asset["id"]
    quote_precision = 10**quote_asset["precision"]

    now = datetime.date.today()
    ago = now - datetime.timedelta(days=100)
    market_history = bitshares_ws_client.request('history', 'get_market_history', [base_id, quote_id, 86400, ago.strftime("%Y-%m-%dT%H:%M:%S"), now.strftime("%Y-%m-%dT%H:%M:%S")])

    data = []
    for market_operation in market_history:

        open_quote = float(market_operation["open_quote"])
        high_quote = float(market_operation["high_quote"])
        low_quote = float(market_operation["low_quote"])
        close_quote = float(market_operation["close_quote"])

        open_base = float(market_operation["open_base"])
        high_base = float(market_operation["high_base"])
        low_base = float(market_operation["low_base"])
        close_base = float(market_operation["close_base"])

        open = 1/(float(open_base/base_precision)/float(open_quote/quote_precision))
        high = 1/(float(high_base/base_precision)/float(high_quote/quote_precision))
        low = 1/(float(low_base/base_precision)/float(low_quote/quote_precision))
        close = 1/(float(close_base/base_precision)/float(close_quote/quote_precision))

        ohlc = [open, close, low, high]

        data.append(ohlc)

    append = [0,0,0,0]
    if len(data) < 99:
        complete = 99 - len(data)
        for c in range(0, complete):
            data.insert(0, append)

    return data

@cache.memoize()
def get_top_proxies():
    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    # # TODO for DB2ES:
    # 1. Query object_balance for BTS then sum amount
    # 2. query object_account for accounts voting_as <> 1.2.5
    # 3. query their BTS balance
    # 4. query the balance of proxies
    query = "SELECT sum(amount) FROM holders"
    cur.execute(query)
    total = cur.fetchone()
    total_votes = total[0]

    query = """
        SELECT follower.voting_as, proxy.account_name, proxy.amount, sum(follower.amount), count(1)
        FROM holders AS follower 
        LEFT OUTER JOIN holders AS proxy ON proxy.account_id = follower.voting_as 
        WHERE follower.voting_as<>'1.2.5' 
        GROUP BY follower.voting_as, proxy.account_name, proxy.amount
        HAVING count(1) > 2
        """
    cur.execute(query)
    proxy_rows = cur.fetchall()

    proxies = []
    for proxy_row in proxy_rows:
        proxy_id = proxy_row[0]
        proxy_name = proxy_row[1] if proxy_row[1] else "unknown"
        proxy_amount = proxy_row[2] + proxy_row[3] if proxy_row[2] else proxy_row[3]
        proxy_followers = proxy_row[4]
        proxy_total_percentage = float(float(proxy_amount) * 100.0/ float(total_votes))
        
        proxies.append([proxy_id, proxy_name, proxy_amount, proxy_followers, proxy_total_percentage])

    con.close()

    proxies = sorted(proxies, key=lambda k: -k[2]) # Reverse amount order

    return proxies


def get_top_holders():
    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    # TODO for DB2ES:
    # query object_account that do not vote for self
    # query their ammount of bts
    query = "SELECT * FROM holders WHERE voting_as='1.2.5' ORDER BY amount DESC LIMIT 10"
    cur.execute(query)
    results = cur.fetchall()
    con.close()
    return results


def _get_formatted_proxy_votes(proxies, vote_id):
    return list(map(lambda p : '{}:{}'.format(p['id'], 'Y' if vote_id in p["options"]["votes"] else '-'), proxies))

def get_witnesses_votes():
    proxies = get_top_proxies()
    proxies = proxies[:10]
    proxies = bitshares_ws_client.request('database', 'get_objects', [[ p[0] for p in proxies ]])

    witnesses = get_witnesses()
    witnesses = witnesses[:25] # FIXME: Witness number is variable.

    witnesses_votes = []
    for witness in witnesses:
        vote_id =  witness[0]["vote_id"]
        id_witness = witness[0]["id"]
        witness_account_name = witness[0]["witness_account_name"]
        proxy_votes = _get_formatted_proxy_votes(proxies, vote_id)        

        witnesses_votes.append([witness_account_name, id_witness] + proxy_votes)

    return witnesses_votes


def get_workers_votes():
    proxies = get_top_proxies()
    proxies = proxies[:10]
    proxies = bitshares_ws_client.request('database', 'get_objects', [[ p[0] for p in proxies ]])

    workers = get_workers()
    workers = workers[:30]

    workers_votes = []
    for worker in workers:
        vote_id =  worker[0]["vote_for"]
        id_worker = worker[0]["id"]
        worker_account_name = worker[0]["worker_account_name"]
        worker_name = worker[0]["name"]
        proxy_votes = _get_formatted_proxy_votes(proxies, vote_id)        

        workers_votes.append([worker_account_name, id_worker, worker_name] + proxy_votes)

    return workers_votes


def get_committee_votes():
    proxies = get_top_proxies()
    proxies = proxies[:10]
    proxies = bitshares_ws_client.request('database', 'get_objects', [[ p[0] for p in proxies ]])

    committee_members = get_committee_members()
    committee_members = committee_members[:11]

    committee_votes = []
    for committee_member in committee_members:
        vote_id =  committee_member[0]["vote_id"]
        id_committee = committee_member[0]["id"]
        committee_account_name = committee_member[0]["committee_member_account_name"]
        proxy_votes = _get_formatted_proxy_votes(proxies, vote_id)        

        committee_votes.append([committee_account_name, id_committee] + proxy_votes)

    return committee_votes


def get_top_markets():
    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    # TODO for DB2ES:
    # use core get_top_markets, or query filled orders on bitshares-*
    # Need this PR: https://github.com/bitshares/bitshares-core/pull/1273
    query = "SELECT pair, volume FROM markets ORDER BY volume DESC LIMIT 7"
    cur.execute(query)
    results = cur.fetchall()

    con.close()
    return results


@cache.memoize()
def get_top_smartcoins():
    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    #TODO for DB2ES: query filled orders on bitshares-*
    query = "SELECT aname, volume FROM assets WHERE type='SmartCoin' ORDER BY volume DESC LIMIT 7"
    cur.execute(query)
    results = cur.fetchall()

    return results


@cache.memoize()
def get_top_uias():
    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    # TODO for DB2ES: query filled orders on bitshares-*
    query = "SELECT aname, volume FROM assets WHERE TYPE='User Issued' ORDER BY volume DESC LIMIT 7"
    cur.execute(query)
    results = cur.fetchall()
    con.close()
    return results


def lookup_accounts(start):
    accounts = bitshares_ws_client.request('database', 'lookup_accounts', [start, 1000])
    return accounts


def lookup_assets(start):
    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    # TODO for DB2ES: query object_bitasset, then get volume and market cap from core
    query = "SELECT aname FROM assets WHERE aname LIKE %s"
    cur.execute(query, (start+'%',))
    results = cur.fetchall()
    con.close()
    return results


def get_last_block_number():
    dynamic_global_properties = bitshares_ws_client.request('database', 'get_dynamic_global_properties', [])
    return dynamic_global_properties["head_block_number"]


def get_account_history_pager_elastic(account_id, page):
    account_id = _get_account_id(account_id)

    from_ = int(page) * 20
    operations = es_wrapper.get_account_history(account_id=account_id, from_=from_, size=20, sort_by='-block_data.block_time')

    results = []
    for op in operations:
        results.append({
            "op": json.loads(op["operation_history"]["op"]),
            "block_num": op["block_data"]["block_num"],
            "id": op["account_history"]["operation_id"],
            "op_in_trx": op["operation_history"]["op_in_trx"],
            "result": op["operation_history"]["operation_result"],
            "timestamp": op["block_data"]["block_time"],
            "trx_in_block": op["operation_history"]["trx_in_block"],
            "virtual_op": op["operation_history"]["virtual_op"]
        })

    return results


def get_fill_order_history(base, quote):
    fill_order_history = bitshares_ws_client.request('history', 'get_fill_order_history', [base, quote, 100])
    return fill_order_history


def get_dex_total_volume():
    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    # TODO for DB2ES: Use get ticker from core
    query = "select price from assets where aname='USD'"
    cur.execute(query)
    results = cur.fetchone()
    usd_price = results[0]

    # TODO for DB2ES: Use get ticker from core
    query = "select price from assets where aname='CNY'"
    cur.execute(query)
    results = cur.fetchone()
    cny_price = results[0]

    # TODO for DB2ES: Use query on filled orders on bitshares-es
    query = "select sum(volume) from assets WHERE aname!='BTS'"
    cur.execute(query)
    results = cur.fetchone()
    volume = results[0]

    # TODO for DB2ES: ???
    query = "select sum(mcap) from assets"
    cur.execute(query)
    results = cur.fetchone()
    market_cap = results[0]
    con.close()

    res = {"volume_bts": round(volume), "volume_usd": round(volume/usd_price), "volume_cny": round(volume/cny_price),
           "market_cap_bts": round(market_cap), "market_cap_usd": round(market_cap/usd_price), "market_cap_cny": round(market_cap/cny_price)}

    return res


def get_daily_volume_dex_dates():
    base = datetime.date.today()
    date_list = [base - datetime.timedelta(days=x) for x in range(0, 60)]
    date_list = [d.strftime("%Y-%m-%d") for d in date_list]
    return list(reversed(date_list))

 
def get_daily_volume_dex_data():
    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    # Use bitshares-* to get this information.
    query = "select value from stats where type='volume_bts' order by date desc limit 60"
    cur.execute(query)
    results = cur.fetchall()

    mod = [ r[0] for r in results ]

    return list(reversed(mod))


def get_all_asset_holders(asset_id):
    asset_id = _ensure_asset_id(asset_id)

    all = []

    asset_holders = get_asset_holders(asset_id, start=0, limit=100)
    all.extend(asset_holders)

    len_result = len(asset_holders)
    start = 100
    while  len_result == 100:
        start = start + 100
        asset_holders = get_asset_holders(asset_id, start=start, limit=100)
        len_result = len(asset_holders)
        all.extend(asset_holders)

    return all


def get_referrer_count(account_id):
    account_id = _get_account_id(account_id)

    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    # TODO for DB2ES: Use information on object_account
    query = "select count(*) from referrers where referrer=%s"
    cur.execute(query, (account_id,))
    results = cur.fetchone()

    return results


def get_all_referrers(account_id, page=0):
    account_id = _get_account_id(account_id)

    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    offset = int(page) * 20;

    # TODO for DB2ES: Use information on object_account
    query = "select * from referrers where referrer=%s ORDER BY rid DESC LIMIT 20 OFFSET %s"
    cur.execute(query, (account_id,str(offset), ))
    results = cur.fetchall()

    return results

def get_grouped_limit_orders(quote, base, group=10, limit=False):
    limit = _ensure_safe_limit(limit)    

    base = _ensure_asset_id(base)
    quote = _ensure_asset_id(quote)

    grouped_limit_orders = bitshares_ws_client.request('orders', 'get_grouped_limit_orders', [base, quote, group, None, limit])

    return grouped_limit_orders
