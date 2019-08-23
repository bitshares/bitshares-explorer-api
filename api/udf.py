from datetime import datetime
import calendar
import connexion

from services.bitshares_websocket_client import client as bitshares_ws_client
from services.bitshares_elasticsearch_client import client as bitshares_es_client
from services.cache import cache
import api.explorer
import config


def get_config():
    return {
        "supports_search": True,
        "supports_group_request": False,
        "supported_resolutions": ["1", "5", "15", "30", "60", "240", "1D"],
        "supports_marks": False,
        "supports_time": True
    }

def get_symbols(symbol):
    base, quote = symbol.split('_')

    _, base_precision = api.explorer._get_asset_id_and_precision(base)

    return {
        "name": symbol,
        "ticker": symbol,
        "description": base + "/" + quote,
        "type": "",
        "session": "24x7",
        "exchange": "",
        "listed_exchange": "",
        "timezone": "Europe/London",
        "minmov": 1,
        "pricescale": base_precision,
        "minmove2": 0,
        "fractional": False,
        "has_intraday": True,
        "supported_resolutions": ["1", "5", "15", "30", "60", "240", "1D"],
        "intraday_multipliers": "",
        "has_seconds": False,
        "seconds_multipliers": "",
        "has_daily": True,
        "has_weekly_and_monthly": False,
        "has_empty_bars": True,
        "force_session_rebuild": "",
        "has_no_volume": False,
        "volume_precision": "",
        "data_status": "",
        "expired": "",
        "expiration_date": "",
        "sector": "",
        "industry": "",
        "currency_code": ""
    }

@cache.memoize(86400) # 1d TTL
def _get_market_pairs():
    markets = bitshares_es_client.get_markets('now-1d', 'now')
    result = []
    for base_id, quotes in markets.items():
        base = api.explorer.get_asset(base_id)['symbol']
        for quote_id, _ in quotes.items():
            quote = api.explorer.get_asset(quote_id)['symbol']
            result.append((base, quote))
    return result

def search(query, type, exchange, limit):

    pairs = [ (base, quote) for (base, quote) in _get_market_pairs() if query in base or query in quote ] 
    final = []
    for (base, quote) in pairs:
        slashed = '{}/{}'.format(base, quote)
        underscored = '{}_{}'.format(base, quote)
        final.append({
            "symbol": underscored,
            "full_name": slashed,
            "description": slashed,
            "exchange": "",
            "ticker": underscored,
            "type": "",
        })

    return final


BUCKET_CONFIG = {
    '1': '60',
    '5': '300',
    '15': '900',
    '30': '1800',
    '60': '3600',
    '240': '14400',
    '1D': '86400'
}

def _load_next_market_history(base_id, base_precision, quote_id, quote_precision, invert, buckets, from_, to_, results):
    history = bitshares_ws_client.request('history', 'get_market_history', [ base_id, quote_id, buckets, from_, to_ ])

    for quote in history:

        open_quote = float(quote["open_quote"])
        high_quote = float(quote["high_quote"])
        low_quote = float(quote["low_quote"])
        close_quote = float(quote["close_quote"])
        close_quote = float(quote["close_quote"])
        quote_volume = int(quote["quote_volume"])

        open_base = float(quote["open_base"])
        high_base = float(quote["high_base"])
        low_base = float(quote["low_base"])
        close_base = float(quote["close_base"])
        base_volume = int(quote["base_volume"])

        if invert:
            open = 1/(float(open_base/quote_precision)/float(open_quote/base_precision))
            high = 1/(float(high_base/quote_precision)/float(high_quote/base_precision))
            low = 1/(float(low_base/quote_precision)/float(low_quote/base_precision))
            close = 1/(float(close_base/quote_precision)/float(close_quote/base_precision))
            volume = base_volume
        else:
            open = (float(open_base/base_precision)/float(open_quote/quote_precision))
            high = (float(high_base/base_precision)/float(high_quote/quote_precision))
            low = (float(low_base/base_precision)/float(low_quote/quote_precision))
            close = (float(close_base/base_precision)/float(close_quote/quote_precision))
            volume = quote_volume

        results['c'].append(close)
        results['o'].append(open)
        results['h'].append(high)
        results['l'].append(low)
        results['v'].append(volume)

        date = datetime.strptime(quote["key"]["open"], "%Y-%m-%dT%H:%M:%S")
        ts = calendar.timegm(date.utctimetuple())
        results['t'].append(ts)
    
    return len(history)

def get_history(symbol, to, resolution):
    from_ = connexion.request.args.get('from')

    buckets = BUCKET_CONFIG.get(resolution, '86400')
    base, quote = symbol.split('_')

    results = {}

    base_id, base_precision = api.explorer._get_asset_id_and_precision(base)
    quote_id, quote_precision = api.explorer._get_asset_id_and_precision(quote)

    base_1, base_2, base_3 = base_id.split('.')
    quote_1, quote_2, quote_3 = quote_id.split('.')
    invert = bool(int(base_3) > int(quote_3))

    left = datetime.fromtimestamp(int(from_)).strftime('%Y-%m-%dT%H:%M:%S')
    right = datetime.fromtimestamp(int(to)).strftime('%Y-%m-%dT%H:%M:%S')

    results = {
        't': [],
        'c': [],
        'o': [],
        'h': [],
        'l': [],
        'v': []
    }

    len_result = _load_next_market_history(base_id, base_precision, quote_id, quote_precision, invert, buckets, left, right, results)

    counter = 0
    while len_result == 200:
        counter = counter + 200

        left = datetime.fromtimestamp(int(results['t'][-1]+1)).strftime('%Y-%m-%dT%H:%M:%S')
        len_result = _load_next_market_history(base_id, base_precision, quote_id, quote_precision, invert, buckets, left, right, results)

    results["s"] = "ok"

    return results

def get_time():
    dynamic_global_properties = bitshares_ws_client.request('database', 'get_dynamic_global_properties', [])
    date = datetime.strptime(dynamic_global_properties["time"], "%Y-%m-%dT%H:%M:%S")
    return str(calendar.timegm(date.utctimetuple()))
