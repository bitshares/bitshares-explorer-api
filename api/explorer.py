import itertools
import datetime
import json
import psycopg2
from services.bitshares_websocket_client import client as bitshares_ws_client
from services.bitshares_elasticsearch_client import client as bitshares_es_client
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


@cache.memoize()
def get_account(account_id):
    return bitshares_ws_client.request('database', 'get_accounts', [[account_id]])

def get_account_name(account_id):
    account = get_account(account_id)
    return account[0]['name']

@cache.memoize()
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


@cache.memoize()
def get_assets():
    results = []
    
    # Get all assets active the last 24h.

    # FIXME: Use objects-assets instead? 
    # asset_ids = bitshares_es_client.get_asset_ids()
    # for asset_id in asset_ids:

    markets = bitshares_es_client.get_markets('now-1d', 'now', quote=config.CORE_ASSET_ID)
    bts_volume = 0.0 # BTS volume is the sum of all the others.
    for asset_id in itertools.chain(markets.keys(), [config.CORE_ASSET_ID]):
        asset = get_asset_and_volume(asset_id)[0]
        holders_count = get_asset_holders_count(asset_id)
        bts_volume += float(asset['volume'])
        results.append([
            None, # db id (legacy, no purpose)
            asset['symbol'], # asset name
            asset_id, # asset id
            asset['latest_price'], # price in bts
            float(asset['volume']) if asset_id != config.CORE_ASSET_ID else bts_volume, # 24h volume
            #float(markets[asset_id][config.CORE_ASSET_ID]['volume']), # 24h volume (from ES) / should be divided by core asset precision
            asset['mcap'], # market cap
            _get_asset_type(asset), # type: Core Asset / Smart Asset / User Issued Asset
            int(asset['current_supply']), # Supply
            holders_count, #Number of holders
            '', # Wallet Type (useless value)
            asset['precision'] # Asset precision
        ])

    results.sort(key=lambda a : -a[4]) # sort by volume
    return results


def get_fees():
    return bitshares_ws_client.get_global_properties()

def get_asset(asset_id):
    return [ _get_asset(asset_id) ]

@cache.memoize()
def _get_asset_id_and_precision(asset_name):
    asset = bitshares_ws_client.request('database', 'lookup_asset_symbols', [[asset_name], 0])[0]
    return (asset["id"], 10 ** asset["precision"])


@cache.memoize()
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


@cache.memoize()
def get_asset_and_volume(asset_id):
    asset = _get_asset(asset_id)
    
    core_symbol = _get_core_asset_name()

    if asset['symbol'] != core_symbol:
        volume = _get_volume(core_symbol, asset['symbol'])
        asset['volume'] = volume['base_volume']

        ticker = get_ticker(core_symbol, asset['symbol'])
        latest_price = float(ticker['latest'])
        asset['latest_price'] = latest_price

        asset['mcap'] = int(asset['current_supply']) * latest_price
    else:
        asset['volume'] = 0
        asset['mcap'] = int(asset['current_supply'])
        asset['latest_price'] = 1

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
        id, _ = _get_asset_id_and_precision(asset_id)
        return id
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


@cache.memoize()
def _get_markets(asset_id):
    markets = bitshares_es_client.get_markets('now-1d', 'now', quote=asset_id)

    results = []
    for (base_id, quotes) in markets.items():
        base_asset = _get_asset(base_id)
        for (quote_id, data) in quotes.items():
            quote_asset = _get_asset(quote_id)
            ticker = get_ticker(base_id, quote_id)
            latest_price = float(ticker['latest'])
            results.append([
                0, # db_id
                '{}/{}'.format(quote_asset['symbol'], base_asset['symbol']), # pair
                0, # quote_asset_db_id
                latest_price, # price
                data['volume'] / 10**quote_asset['precision'], # volume
                quote_id # quote_id
            ])

    return results

def get_markets(asset_id):
    asset_id = _ensure_asset_id(asset_id)
    return _get_markets(asset_id)


@cache.memoize()
def get_most_active_markets():
    markets = bitshares_es_client.get_markets('now-1d', 'now')

    flatten_markets = []
    for (base, quotes) in markets.items():
        for (quote, data) in quotes.items():
            flatten_markets.append({
                'base': base,
                'quote': quote,
                'volume': data['volume'],
                'nb_operations': data['nb_operations']
            })
    flatten_markets.sort(key=lambda m: -m['nb_operations'])

    top_markets = flatten_markets[:100]

    results = []
    for m in top_markets:
        base_asset = _get_asset(m['base'])
        quote_asset = _get_asset(m['quote'])
        ticker = get_ticker(m['base'], m['quote'])
        latest_price = float(ticker['latest'])
        results.append([
            0, # db_id
            '{}/{}'.format(quote_asset['symbol'], base_asset['symbol']), # pair
            0, # quote_asset_db_id
            latest_price, # price
            m['volume'] / 10**quote_asset['precision'], # volume
            m['quote'] # quote_id
        ])   
    
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
    base_id, base_precision = _get_asset_id_and_precision(base)
    quote_id, quote_precision = _get_asset_id_and_precision(quote)

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

def get_top_proxies():
    holders = _get_holders()

    total_votes = reduce(lambda acc, h: acc + int(h['balance']), holders, 0)

    proxies = []
    for holder in holders:
        total_votes += int(holder['balance'])
        if 'follower_count' in holder:
            proxy_amount =  int(holder['balance']) + int(holder['follower_amount'])
            proxy_total_percentage = float(int(proxy_amount) * 100.0/ int(total_votes))
            proxies.append([
                holder['owner']['object_id'],
                holder['owner']['name'],
                proxy_amount,
                holder['follower_count'],
                proxy_total_percentage
            ])

    proxies = sorted(proxies, key=lambda k: -k[2]) # Reverse amount order

    return proxies


@cache.memoize()
def _get_holders():
    balances = bitshares_es_client.get_balances(asset_id=config.CORE_ASSET_ID)
    account_ids = [ balance['owner'] for balance in balances ]
    accounts = bitshares_es_client.get_accounts(account_ids)
    holders_by_account_id = {}
    for balance in balances:
        holders_by_account_id[balance['owner']] = balance
    for account in accounts:
        holders_by_account_id[account['object_id']]['owner'] = account
    for holder in holders_by_account_id.values():
        proxy_id = holder['owner']['voting_account']
        if proxy_id != '1.2.5':
            if proxy_id not in holders_by_account_id:
                print(proxy_id)
            else:
                proxy = holders_by_account_id[proxy_id] 
                if 'follower_amount' not in proxy:
                    proxy['follower_amount'] = 0
                    proxy['follower_count'] = 0
                proxy['follower_amount'] += int(holder['balance']) 
                proxy['follower_count'] += 1 

    return holders_by_account_id.values()    


def get_top_holders():
    holders = _get_holders()
    holders_without_vote_delegation = [ holder for holder in holders if holder['owner']['voting_account'] == '1.2.5' ]
    holders_without_vote_delegation.sort(key=lambda h : -int(h['balance']))
    top_holders = []
    for holder in holders_without_vote_delegation[:10]:
        top_holders.append([
            0,                                  # (legacy) database id
            holder['owner']['object_id'],       # account id
            holder['owner']['name'],            # account name
            int(holder['balance']),           # BTS amount
            holder['owner']['voting_account']   # voting account
        ]) 
    return top_holders


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
    markets = get_most_active_markets()
    top = markets[:7]
    return [ [m[1], m[4]] for m in top ]


def get_top_smartcoins():
    smartcoins = [[a[1], a[4]] for a in get_assets() if a[6] == 'SmartCoin']
    return smartcoins[:7]


@cache.memoize()
def get_top_uias():
    uias = [[a[1], a[4]] for a in get_assets() if a[6] == 'User Issued']
    return uias[:7]


def lookup_accounts(start):
    accounts = bitshares_ws_client.request('database', 'lookup_accounts', [start, 1000])
    return accounts


def lookup_assets(start):
    matched_assets = [ [a[1]] for a in get_assets() if a[1].startswith(start) ]
    return matched_assets

    # FIXME: use objects-asset:
    #return bitshares_es_client.get_asset_names(start)


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
    volume = 0.0
    market_cap = 0.0
    usd_price = 0
    cny_price = 0
    for a in get_assets():
        if a[2] != config.CORE_ASSET_ID:
            volume += a[4]
        if a[1] == 'USD':
            usd_price = a[3]
        if a[1] == 'CNY':
            cny_price = a[3]
        market_cap += a[5]

    res = {
        "volume_bts": round(volume), 
        "volume_usd": round(volume/usd_price) if usd_price != 0 else 'nan', 
        "volume_cny": round(volume/cny_price) if cny_price != 0 else 'nan',
        "market_cap_bts": round(market_cap), 
        "market_cap_usd": round(market_cap/usd_price) if usd_price != 0 else 'nan', 
        "market_cap_cny": round(market_cap/cny_price) if cny_price != 0 else 'nan'
    }

    return res


def get_daily_volume_dex_dates():
    base = datetime.date.today()
    date_list = [base - datetime.timedelta(days=x) for x in range(0, 60)]
    date_list = [d.strftime("%Y-%m-%d") for d in date_list]
    return list(reversed(date_list))

 
@cache.memoize(86400) # 1d TTL
def get_daily_volume_dex_data():
    daily_volumes = bitshares_es_client.get_daily_volume('now-60d', 'now')
    core_asset_precision = 10 ** _get_asset(config.CORE_ASSET_ID)['precision']

    results = [ int(daily_volume['volume'] / core_asset_precision) for daily_volume in daily_volumes]
    return results

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

    count, _ = bitshares_es_client.get_accounts_with_referrer(account_id, size=0)

    return [count]


def get_all_referrers(account_id, page=0):
    account_id = _get_account_id(account_id)
    
    page_size = 20
    offset = int(page) * page_size
    _, accounts = bitshares_es_client.get_accounts_with_referrer(account_id, size=page_size, from_=offset)
    
    results = []
    for account in accounts:
        results.append([
            0, # db_id
            account['object_id'],                           # account_id
            account['name'],                                # account name
            account['referrer'],                            # referrer id
            account['referrer_rewards_percentage'],         # % of reward that goes to referrer
            account['lifetime_referrer'],                   # lifetime referrer id
            account['lifetime_referrer_fee_percentage']     #  % of reward that goes to lifetime referrer
        ])

    return results


def get_grouped_limit_orders(quote, base, group=10, limit=False):
    limit = _ensure_safe_limit(limit)    

    base = _ensure_asset_id(base)
    quote = _ensure_asset_id(quote)

    grouped_limit_orders = bitshares_ws_client.request('orders', 'get_grouped_limit_orders', [base, quote, group, None, limit])

    return grouped_limit_orders

def _get_asset_type(asset):
    if asset['id'] == config.CORE_ASSET_ID:
        return 'Core Token'
    elif asset['issuer'] == '1.2.0':
        return 'SmartCoin'
    else:
        return 'User Issued'
