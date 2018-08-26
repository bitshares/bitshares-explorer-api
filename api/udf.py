import psycopg2
import datetime
import time
import calendar
import connexion

from services.bitshares_websocket_client import client as bitshares_ws_client
import config


def get_config():

    results = {}

    results["supports_search"] = True
    results["supports_group_request"] = False
    results["supported_resolutions"] = ["1", "5", "15", "30", "60", "240", "1D"]
    results["supports_marks"] = False
    results["supports_time"] = True

    return results

def get_symbols(symbol):
    base,quote = symbol.split('_')

    asset = bitshares_ws_client.request('database', 'lookup_asset_symbols', [ [ base ], 0])[0]
    base_precision = 10**asset["precision"]

    results = {}

    results["name"] = symbol
    results["ticker"] = symbol
    results["description"] = base + "/" + quote
    results["type"] = ""
    results["session"] = "24x7"
    results["exchange"] = ""
    results["listed_exchange"] = ""
    results["timezone"] = "Europe/London"
    results["minmov"] = 1
    results["pricescale"] = base_precision
    results["minmove2"] = 0
    results["fractional"] = False
    results["has_intraday"] = True
    results["supported_resolutions"] = ["1", "5", "15", "30", "60", "240", "1D"]
    results["intraday_multipliers"] = ""
    results["has_seconds"] = False
    results["seconds_multipliers"] = ""
    results["has_daily"] = True
    results["has_weekly_and_monthly"] = False
    results["has_empty_bars"] = True
    results["force_session_rebuild"] = ""
    results["has_no_volume"] = False
    results["volume_precision"] = ""
    results["data_status"] = ""
    results["expired"] = ""
    results["expiration_date"] = ""
    results["sector"] = ""
    results["industry"] = ""
    results["currency_code"] = ""

    return results


def search(query, type, exchange, limit):
    final = []

    con = psycopg2.connect(**config.POSTGRES)
    cur = con.cursor()

    query = "SELECT * FROM markets WHERE pair LIKE '%" + query + "%'"
    #print query
    cur.execute(query)
    result = cur.fetchall()
    con.close()

    for w in range(0, len(result)):

        results = {}
        #print w
        base, quote = result[w][1].split('/')

        results["symbol"] = base + "_" + quote

        results["full_name"] = result[w][1]
        results["description"] = result[w][1]
        results["exchange"] = ""
        results["ticker"] = base + "_" + quote
        results["type"] = ""
        final.append(results)

    #print final
    return final

def get_history(symbol, to, resolution):
    from_ = connexion.request.args.get('from')

    buckets = "86400"
    if resolution == "1":
        buckets = "60"
    elif resolution == "5":
        buckets = "300"
    elif resolution == "15":
        buckets = "900"
    elif resolution == "30":
        buckets = "1800"
    elif resolution == "60":
        buckets = "3600"
    elif resolution == "240":
        buckets = "14400"
    elif resolution == "1D":
        buckets = "86400"

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
    divide = False
    if int(base_3) > int(quote_3):
        divide = True
        #base_id, quote_id = quote_id, base_id
        base_precision, quote_precision = quote_precision, base_precision

    #print base_precision
    #print quote_precision

    left = datetime.datetime.fromtimestamp(int(from_)).strftime('%Y-%m-%dT%H:%M:%S')
    right = datetime.datetime.fromtimestamp(int(to)).strftime('%Y-%m-%dT%H:%M:%S')

    history = bitshares_ws_client.request('history', 'get_market_history', [ base_id, quote_id, buckets, left, right ])


    t = []
    c = []
    o = []
    h = []
    l = []
    v = []

    for w in range(0, len(history)):

        open_quote = float(history[w]["open_quote"])
        high_quote = float(history[w]["high_quote"])
        low_quote = float(history[w]["low_quote"])
        close_quote = float(history[w]["close_quote"])
        close_quote = float(history[w]["close_quote"])
        quote_volume = int(history[w]["quote_volume"])

        open_base = float(history[w]["open_base"])
        high_base = float(history[w]["high_base"])
        low_base = float(history[w]["low_base"])
        close_base = float(history[w]["close_base"])
        base_volume = int(history[w]["base_volume"])

        if divide:
            open = 1/(float(open_base/base_precision)/float(open_quote/quote_precision))
            high = 1/(float(high_base/base_precision)/float(high_quote/quote_precision))
            low = 1/(float(low_base/base_precision)/float(low_quote/quote_precision))
            close = 1/(float(close_base/base_precision)/float(close_quote/quote_precision))
            volume = base_volume
        else:
            open = (float(open_base/base_precision)/float(open_quote/quote_precision))
            high = (float(high_base/base_precision)/float(high_quote/quote_precision))
            low = (float(low_base/base_precision)/float(low_quote/quote_precision))
            close = (float(close_base/base_precision)/float(close_quote/quote_precision))
            volume = quote_volume

        c.append(close)
        o.append(open)
        h.append(high)
        l.append(low)
        v.append(volume)

        date = datetime.datetime.strptime(history[w]["key"]["open"], "%Y-%m-%dT%H:%M:%S")
        ts = calendar.timegm(date.utctimetuple())
        t.append(ts)


    len_result = len(history)
    counter = 0
    while len_result == 200:

        counter = counter + 200

        left = datetime.datetime.fromtimestamp(int(t[-1]+1)).strftime('%Y-%m-%dT%H:%M:%S')
        history = bitshares_ws_client.request('history', 'get_market_history', [ base_id, quote_id, buckets, left, right ])

        len_result = len(history)

        for w in range(0, len(history)):

            open_quote = float(history[w]["open_quote"])
            high_quote = float(history[w]["high_quote"])
            low_quote = float(history[w]["low_quote"])
            close_quote = float(history[w]["close_quote"])
            quote_volume = int(history[w]["quote_volume"])

            open_base = float(history[w]["open_base"])
            high_base = float(history[w]["high_base"])
            low_base = float(history[w]["low_base"])
            close_base = float(history[w]["close_base"])
            base_volume = int(history[w]["base_volume"])

            if divide:
                open = 1 / (float(open_base / base_precision) / float(open_quote / quote_precision))
                high = 1 / (float(high_base / base_precision) / float(high_quote / quote_precision))
                low = 1 / (float(low_base / base_precision) / float(low_quote / quote_precision))
                close = 1 / (float(close_base / base_precision) / float(close_quote / quote_precision))
                volume = quote_volume
            else:
                open = (float(open_base / base_precision) / float(open_quote / quote_precision))
                high = (float(high_base / base_precision) / float(high_quote / quote_precision))
                low = (float(low_base / base_precision) / float(low_quote / quote_precision))
                close = (float(close_base / base_precision) / float(close_quote / quote_precision))
                volume = base_volume

            c.append(close)
            o.append(open)
            h.append(high)
            l.append(low)
            v.append(volume)

            date = datetime.datetime.strptime(history[w]["key"]["open"], "%Y-%m-%dT%H:%M:%S")
            ts = calendar.timegm(date.utctimetuple())
            t.append(ts)

    results["s"] = "ok"
    results["t"] = t
    results["c"] = c
    results["o"] = o
    results["h"] = h
    results["l"] = l
    results["v"] = v

    #results["v"] = ""

    # if s = error ; results["errmsg"] = "Some eror msg here"

    return results

def get_time():
    dynamic_global_properties = bitshares_ws_client.request('database', 'get_dynamic_global_properties', [])
    date = datetime.datetime.strptime(dynamic_global_properties["time"], "%Y-%m-%dT%H:%M:%S")
    return str(calendar.timegm(date.utctimetuple()))
