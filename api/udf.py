from datetime import datetime
import calendar
import psycopg2
import connexion

from services.bitshares_websocket_client import client as bitshares_ws_client
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

    asset = bitshares_ws_client.request('database', 'lookup_asset_symbols', [ [ base ], 0])[0]
    base_precision = 10**asset["precision"]

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


def search(query, type, exchange, limit):

    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()
    cur.execute("SELECT * FROM markets WHERE pair LIKE %s", ('%{}%'.format(query),))
    rows = cur.fetchall()
    con.close()

    final = []
    for row in rows:
        base, quote = row[1].split('/')
        final.append({
            "symbol": base + "_" + quote,
            "full_name": row[1],
            "description": row[1],
            "exchange": "",
            "ticker": base + "_" + quote,
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

    base_asset = bitshares_ws_client.request('database', 'lookup_asset_symbols', [ [ base ], 0])[0]
    base_id = base_asset["id"]
    base_precision = 10**base_asset["precision"]

    quote_asset = bitshares_ws_client.request('database', 'lookup_asset_symbols', [ [ quote ], 0])[0]
    quote_id = quote_asset["id"]
    quote_precision = 10**quote_asset["precision"]


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

        left = datetime.fromtimestamp(int(result['t'][-1]+1)).strftime('%Y-%m-%dT%H:%M:%S')
        len_result = _load_next_market_history(base_id, base_precision, quote_id, quote_precision, invert, buckets, left, right, results)

    results["s"] = "ok"

    return results

def get_time():
    dynamic_global_properties = bitshares_ws_client.request('database', 'get_dynamic_global_properties', [])
    date = datetime.strptime(dynamic_global_properties["time"], "%Y-%m-%dT%H:%M:%S")
    return str(calendar.timegm(date.utctimetuple()))
