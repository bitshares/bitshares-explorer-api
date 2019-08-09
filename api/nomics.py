import datetime
import calendar
import connexion

from services.bitshares_websocket_client import client as bitshares_ws_client
from services.bitshares_elasticsearch_client import client as bitshares_es_client
from services.cache import cache
import api.explorer
import es_wrapper
import config


def info():
    return {
        "name": "Bitshares",
        "description": "The BitShares Blockchain is an industrial-grade decentralized platform built for "
                       "high-performance financial smart contracts mostly known for: its token factory,"
                       " a decentralized exchange as a built-in native dapp (known as the DEX) and its stablecoins"
                       " or, as they are called in BitShares, Smartcoins. It represents the first decentralized"
                       " autonomous community that lets its core token holders decide on its future direction and"
                       " products by means of on-chain voting. It is also the first DPoS blockchain in existence and"
                       " the first blockchain to implement stablecoins.",
        "location": "Worldwide",
        "logo": "https://bitshares.org/exchange-logo.png",
        "website": "https://bitshares.org/",
        "twitter": "https://twitter.com/bitshares",
        "capability": {
            "markets": True,
            "trades": True,
            "tradesSocket": False,
            "orders": False,
            "ordersSocket": False,
            "ordersSnapshot": True,
            "candles": False
        }
    }


def markets():
    result = []
    top_markets = bitshares_ws_client.request('database', 'get_top_markets', [100])

    for market in top_markets:
        result.append({
            'id': market["base"] + "-" + market["quote"],
            'base': market["base"],
            'quote': market["quote"]
        })
    return result


@cache.memoize()
def trades(market, since):

    market_id = market.split('-')
    base = market_id[0]
    quote = market_id[1]

    now = datetime.datetime.now()
    start = now
    stop = now - datetime.timedelta(days=3)

    results = []

    _trades = bitshares_ws_client.request('database', 'get_trade_history',
                                          [base, quote, start.strftime("%Y-%m-%dT%H:%M:%S"),
                                           stop.strftime("%Y-%m-%dT%H:%M:%S"), 100])

    for trade in _trades:
        results.append({
            "id": trade["sequence"],
            "timestamp": trade["date"],
            "price": trade["price"],
            "amount": trade["amount"],
            "order": "",
            "type": "",
            "side": "",
            "raw": ""
        })

    while len(_trades) == 100:
        start_seq = _trades[99]["sequence"]
        _trades = bitshares_ws_client.request('database', 'get_trade_history_by_sequence',
                                              [base, quote, start_seq, stop.strftime("%Y-%m-%dT%H:%M:%S"), 100])
        for trade in _trades:
            results.append({
                "id": trade["sequence"],
                "timestamp": trade["date"],
                "price": trade["price"],
                "amount": trade["amount"],
                "order": "",
                "type": "",
                "side": "",
                "raw": ""
            })

    if not since:
        return list(reversed(results))[0:100]
    else:
        new_results = []
        for r in results:
            if int(r["id"]) > int(since):
                new_results.append(r)
        return list(reversed(new_results))[0:100]


def snapshot(market):
    result = {}

    market_id = market.split('-')
    base = market_id[0]
    quote = market_id[1]

    order_book = api.explorer.get_order_book(base, quote, 100)

    bids = []
    asks = []

    for bid in order_book["bids"]:
        bids.append([bid["price"], bid["base"]])

    result["bids"] = bids

    for ask in order_book["asks"]:
        asks.append([ask["price"], ask["base"]])

    result["asks"] = asks

    result["timestamp"] = api.explorer.get_last_block_time()

    return result
