from websocket import create_connection
import json
from flask import jsonify


from flask import Flask
from flask_cors import CORS, cross_origin
app = Flask(__name__)
CORS(app)

from flask import request

# postgres
import psycopg2
# end postgres

import datetime

#ws = create_connection("wss://eu.openledger.info/ws")
ws = create_connection("ws://127.0.0.1:8090/ws") # localhost


@app.route('/header')
def header():

    ws.send('{"id":1, "method":"call", "params":[0,"get_dynamic_global_properties",[]]}')
    result =  ws.recv()
    j = json.loads(result)

    ws.send('{"id": 1, "method": "call", "params": [0, "get_objects", [["2.3.0"]]]}')
    result2 = ws.recv()
    j2 = json.loads(result2)

    current_supply = j2["result"][0]["current_supply"]
    confidental_supply = j2["result"][0]["confidential_supply"]

    market_cap = int(current_supply) + int(confidental_supply)
    j["result"]["bts_market_cap"] = int(market_cap/100000000)
    #print j["result"][0]["bts_market_cap"]


    ws.send('{"id":1, "method":"call", "params":[0,"get_24_volume",["BTS", "OPEN.BTC"]]}')
    result3 = ws.recv()
    j3 = json.loads(result3)

    j["result"]["quote_volume"] = j3["result"]["quote_volume"]

    ws.send('{"id":1, "method":"call", "params":[0,"get_global_properties",[]]}')
    result5 = ws.recv()
    j5 = json.loads(result5)
    #print j5

    commitee_count = len(j5["result"]["active_committee_members"])
    witness_count = len(j5["result"]["active_witnesses"])

    j["result"]["commitee_count"] = commitee_count
    j["result"]["witness_count"] = witness_count

    return jsonify(j["result"])

@app.route('/account_name')
def account_name():

    account_id = request.args.get('account_id')
    ws.send('{"id":1, "method":"call", "params":[0,"get_accounts",[["'+account_id+'"]]]}')
    result =  ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/operation')
def get_operation():

    operation_id = request.args.get('operation_id')
    ws.send('{"id":1, "method":"call", "params":[0,"get_objects",[["'+operation_id+'"]]]}')
    result =  ws.recv()
    j = json.loads(result)

    ws.send('{"id":1, "method":"call", "params":[0,"get_dynamic_global_properties",[]]}')
    result2 =  ws.recv()
    j2 = json.loads(result2)

    if not j["result"][0]:
        j["result"][0] = {}

    j["result"][0]["accounts_registered_this_interval"] = j2["result"]["accounts_registered_this_interval"]

    # get market cap
    ws.send('{"id": 1, "method": "call", "params": [0, "get_objects", [["2.3.0"]]]}')
    result2 = ws.recv()
    j2 = json.loads(result2)

    current_supply = j2["result"][0]["current_supply"]
    confidental_supply = j2["result"][0]["confidential_supply"]

    market_cap = int(current_supply) + int(confidental_supply)
    j["result"][0]["bts_market_cap"] = int(market_cap/100000000)
    #print j["result"][0]["bts_market_cap"]


    ws.send('{"id":1, "method":"call", "params":[0,"get_24_volume",["BTS", "OPEN.BTC"]]}')
    result3 = ws.recv()
    j3 = json.loads(result3)
    #print j3["result"]["quote_volume"]
    j["result"][0]["quote_volume"] = j3["result"]["quote_volume"]

    # TODO: making this call with every operation is not very efficient as this are static properties
    ws.send('{"id":1, "method":"call", "params":[0,"get_global_properties",[]]}')
    result5 = ws.recv()
    j5 = json.loads(result5)

    commitee_count = len(j5["result"]["active_committee_members"])
    witness_count = len(j5["result"]["active_witnesses"])

    j["result"][0]["commitee_count"] = commitee_count
    j["result"][0]["witness_count"] = witness_count


    #print j['result']

    return jsonify(j["result"])

@app.route('/accounts')
def accounts():

    ws.send('{"id":2,"method":"call","params":[1,"login",["",""]]}')
    login =  ws.recv()
    #print  result2

    ws.send('{"id":2,"method":"call","params":[1,"asset",[]]}')

    asset =  ws.recv()
    asset_j = json.loads(asset)

    asset_api = str(asset_j["result"])

    ws.send('{"id":1, "method":"call", "params":['+asset_api+',"get_asset_holders",["1.3.0", 0, 100]]}')
    result =  ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/full_account')
def full_account():

    account_id = request.args.get('account_id')

    ws.send('{"id":1, "method":"call", "params":[0,"get_full_accounts",[["'+account_id+'"], 0]]}')
    result =  ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/assets')
def assets():

    con = psycopg2.connect(database='explorer', user='postgres', host='localhost', password='posta')
    cur = con.cursor()

    query = "SELECT * FROM assets WHERE volume > 0 ORDER BY volume DESC"
    cur.execute(query)
    results = cur.fetchall()
    con.close()
    #print results
    return jsonify(results)

@app.route('/fees')
def fees():

    ws.send('{"id":1, "method":"call", "params":[0,"get_global_properties",[]]}')
    result =  ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/account_history')
def account_history():

    ws.send('{"id":2,"method":"call","params":[1,"login",["",""]]}')
    login =  ws.recv()

    ws.send('{"id":2,"method":"call","params":[1,"history",[]]}')
    history =  ws.recv()
    history_j = json.loads(history)
    history_api = str(history_j["result"])
    #print history_api

    account_id = request.args.get('account_id')

    if not isObject(account_id):
        ws.send('{"id":1, "method":"call", "params":[0,"lookup_account_names",[["' + account_id + '"], 0]]}')
        result_l = ws.recv()
        j_l = json.loads(result_l)

        account_id = j_l["result"][0]["id"]

    ws.send('{"id":1, "method":"call", "params":['+history_api+',"get_account_history",["'+account_id+'", "1.11.1", 20, "1.11.9999999999"]]}')
    result =  ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/get_asset')
def get_asset():
    asset_id = request.args.get('asset_id')

    if not isObject(asset_id):
        ws.send('{"id":1, "method":"call", "params":[0,"lookup_asset_symbols",[["' + asset_id + '"], 0]]}')
        result_l = ws.recv()
        j_l = json.loads(result_l)
        asset_id = j_l["result"][0]["id"]

    #print asset_id
    ws.send('{"id":1, "method":"call", "params":[0,"get_assets",[["' + asset_id + '"], 0]]}')
    result = ws.recv()
    j = json.loads(result)

    dynamic_asset_data_id =  j["result"][0]["dynamic_asset_data_id"]

    ws.send('{"id": 1, "method": "call", "params": [0, "get_objects", [["'+dynamic_asset_data_id+'"]]]}')
    result2 = ws.recv()
    j2 = json.loads(result2)
    #print j2["result"][0]["current_supply"]

    j["result"][0]["current_supply"] = j2["result"][0]["current_supply"]
    j["result"][0]["confidential_supply"] = j2["result"][0]["confidential_supply"]
    #print j["result"]

    j["result"][0]["accumulated_fees"] = j2["result"][0]["accumulated_fees"]
    j["result"][0]["fee_pool"] = j2["result"][0]["fee_pool"]

    issuer = j["result"][0]["issuer"]
    ws.send('{"id": 1, "method": "call", "params": [0, "get_objects", [["'+issuer+'"]]]}')
    result3 = ws.recv()
    j3 = json.loads(result3)
    j["result"][0]["issuer_name"] = j3["result"][0]["name"]


    return jsonify(j["result"])

@app.route('/block_header')
def block_header():
    block_num = request.args.get('block_num')

    ws.send('{"id":1, "method":"call", "params":[0,"get_block_header",[' + block_num + ', 0]]}')
    result = ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/get_block')
def get_block():
    block_num = request.args.get('block_num')

    ws.send('{"id":1, "method":"call", "params":[0,"get_block",[' + block_num + ', 0]]}')
    result = ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/get_ticker')
def get_ticker():
    base = request.args.get('base')
    quote = request.args.get('quote')

    ws.send('{"id":1, "method":"call", "params":[0,"get_ticker",["' + base + '", "'+quote+'"]]}')
    result = ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/get_volume')
def get_volume():
    base = request.args.get('base')
    quote = request.args.get('quote')

    ws.send('{"id":1, "method":"call", "params":[0,"get_24_volume",["' + base + '", "'+quote+'"]]}')
    result = ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/lastnetworkops')
def lastnetworkops():

    con = psycopg2.connect(database='explorer', user='postgres', host='localhost', password='posta')
    cur = con.cursor()

    query = "SELECT * FROM ops ORDER BY block_num DESC LIMIT 10"
    cur.execute(query)
    results = cur.fetchall()
    con.close()
    return jsonify(results)

@app.route('/get_object')
def get_object():

    object = request.args.get('object')
    ws.send('{"id":1, "method":"call", "params":[0,"get_objects",[["'+object+'"]]]}')
    result =  ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/get_asset_holders_count')
def get_asset_holders_count():

    asset_id = request.args.get('asset_id')

    if not isObject(asset_id):
        ws.send('{"id":1, "method":"call", "params":[0,"lookup_asset_symbols",[["' + asset_id + '"], 0]]}')
        result_l = ws.recv()
        j_l = json.loads(result_l)
        asset_id = j_l["result"][0]["id"]

    ws.send('{"id":2,"method":"call","params":[1,"login",["",""]]}')
    login =  ws.recv()
    #print  result2

    ws.send('{"id":2,"method":"call","params":[1,"asset",[]]}')

    asset =  ws.recv()
    asset_j = json.loads(asset)

    asset_api = str(asset_j["result"])

    ws.send('{"id":1, "method":"call", "params":['+asset_api+',"get_asset_holders_count",["'+asset_id+'"]]}')
    result =  ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/get_asset_holders')
def get_asset_holders():

    asset_id = request.args.get('asset_id')

    if not isObject(asset_id):
        ws.send('{"id":1, "method":"call", "params":[0,"lookup_asset_symbols",[["' + asset_id + '"], 0]]}')
        result_l = ws.recv()
        j_l = json.loads(result_l)
        asset_id = j_l["result"][0]["id"]

    ws.send('{"id":2,"method":"call","params":[1,"login",["",""]]}')
    login =  ws.recv()

    ws.send('{"id":2,"method":"call","params":[1,"asset",[]]}')

    asset =  ws.recv()
    asset_j = json.loads(asset)

    asset_api = str(asset_j["result"])

    ws.send('{"id":1, "method":"call", "params":['+asset_api+',"get_asset_holders",["'+asset_id+'", 0, 20]]}')
    result =  ws.recv()

    j = json.loads(result)

    return jsonify(j["result"])

@app.route('/get_workers')
def get_workers():


    ws.send('{"jsonrpc": "2.0", "method": "get_worker_count", "params": [], "id": 1}')

    count =  ws.recv()
    count_j = json.loads(count)

    workers_count = int(count_j["result"])

    #print workers_count

    # get the votes of woirker 114.0 - refund 400k
    ws.send('{"id":1, "method":"call", "params":[0,"get_objects",[["1.14.0"]]]}')
    result_0 = ws.recv()
    j_0 = json.loads(result_0)
    #account_id = j["result"][0]["worker_account"]
    thereshold =  int(j_0["result"][0]["total_votes_for"])



    workers = []
    for w in range(0, workers_count):
        ws.send('{"id":1, "method":"call", "params":[0,"get_objects",[["1.14.'+str(w)+'"]]]}')
        result =  ws.recv()

        j = json.loads(result)
        account_id = j["result"][0]["worker_account"]
        ws.send('{"id":1, "method":"call", "params":[0,"get_accounts",[["' + account_id + '"]]]}')
        result2 = ws.recv()
        j2 = json.loads(result2)

        account_name = j2["result"][0]["name"]
        j["result"][0]["worker_account_name"] = account_name

        current_votes = int(j["result"][0]["total_votes_for"])
        perc = (current_votes*100)/thereshold
        j["result"][0]["perc"] = perc

        workers.append(j["result"])

    r_workers = workers[::-1]
    return jsonify(filter(None, r_workers))

def isObject(string):

    parts = string.split(".")
    if len(parts) == 3:
        return True
    else:
        return False


@app.route('/get_markets')
def get_markets():

    asset_id = request.args.get('asset_id')

    if not isObject(asset_id):
        ws.send('{"id":1, "method":"call", "params":[0,"lookup_asset_symbols",[["' + asset_id + '"], 0]]}')
        result_l = ws.recv()
        j_l = json.loads(result_l)
        asset_id = j_l["result"][0]["id"]


    con = psycopg2.connect(database='explorer', user='postgres', host='localhost', password='posta')
    cur = con.cursor()

    query = "SELECT * FROM markets WHERE aid='"+asset_id+"'"
    cur.execute(query)
    results = cur.fetchall()
    con.close()
    return jsonify(results)


@app.route('/get_most_active_markets')
def get_most_active_markets():

    con = psycopg2.connect(database='explorer', user='postgres', host='localhost', password='posta')
    cur = con.cursor()

    query = "SELECT * FROM markets WHERE volume>0 ORDER BY volume DESC LIMIT 20"
    cur.execute(query)
    results = cur.fetchall()
    con.close()
    return jsonify(results)

@app.route('/get_order_book')
def get_order_book():

    base = request.args.get('base')
    quote = request.args.get('quote')
    ws.send('{"id":1, "method":"call", "params":[0,"get_order_book",["'+base+'", "'+quote+'", 50]]}')
    result =  ws.recv()
    j = json.loads(result)

    return jsonify(j["result"])


@app.route('/get_margin_positions')
def get_open_orders():

    account_id = request.args.get('account_id')
    ws.send('{"id":1, "method":"call", "params":[0,"get_margin_positions",["'+account_id+'"]]}')
    result =  ws.recv()
    j = json.loads(result)

    return jsonify(j["result"])

@app.route('/get_witnesses')
def get_witnesses():

    ws.send('{"jsonrpc": "2.0", "method": "get_witness_count", "params": [], "id": 1}')
    count =  ws.recv()
    count_j = json.loads(count)
    witnesses_count = int(count_j["result"])

    witnesses = []
    for w in range(0, witnesses_count):
        ws.send('{"id":1, "method":"call", "params":[0,"get_objects",[["1.6.'+str(w)+'"]]]}')
        result =  ws.recv()

        j = json.loads(result)
        if j["result"][0]:
            account_id = j["result"][0]["witness_account"]
            #print account_id
            ws.send('{"id":1, "method":"call", "params":[0,"get_accounts",[["' + account_id + '"]]]}')
            result2 = ws.recv()
            j2 = json.loads(result2)

            account_name = j2["result"][0]["name"]
            j["result"][0]["witness_account_name"] = account_name
        else:
            #j["result"][0]["witness_account_name"] = ""
            continue

        witnesses.append(j["result"])


    witnesses = sorted(witnesses, key=lambda k: int(k[0]['total_votes']))
    r_witnesses = witnesses[::-1]

    return jsonify(filter(None, r_witnesses))

@app.route('/get_committee_members')
def get_committee_members():

    ws.send('{"jsonrpc": "2.0", "method": "get_committee_count", "params": [], "id": 1}')
    count =  ws.recv()
    count_j = json.loads(count)
    committee_count = int(count_j["result"])

    committee_members = []
    for w in range(0, committee_count):
        ws.send('{"id":1, "method":"call", "params":[0,"get_objects",[["1.5.'+str(w)+'"]]]}')
        result =  ws.recv()

        j = json.loads(result)
        if j["result"][0]:
            account_id = j["result"][0]["committee_member_account"]
            #print account_id
            ws.send('{"id":1, "method":"call", "params":[0,"get_accounts",[["' + account_id + '"]]]}')
            result2 = ws.recv()
            j2 = json.loads(result2)

            account_name = j2["result"][0]["name"]
            j["result"][0]["committee_member_account_name"] = account_name
        else:
            #j["result"][0]["witness_account_name"] = ""
            continue

        committee_members.append(j["result"])

    committee_members = sorted(committee_members, key=lambda k: int(k[0]['total_votes']))
    r_committee = committee_members[::-1] # this reverses array

    return jsonify(filter(None, r_committee))

@app.route('/market_chart_dates')
def market_chart_dates():

    base = datetime.date.today()
    date_list = [base - datetime.timedelta(days=x) for x in range(0, 100)]
    date_list = [d.strftime("%Y-%m-%d") for d in date_list]
    #print len(list(reversed(date_list)))
    return jsonify(list(reversed(date_list)))

@app.route('/market_chart_data')
def market_chart_data():

    ws.send('{"id":2,"method":"call","params":[1,"login",["",""]]}')
    login =  ws.recv()

    ws.send('{"id":2,"method":"call","params":[1,"history",[]]}')
    history =  ws.recv()
    history_j = json.loads(history)
    history_api = str(history_j["result"])

    base = request.args.get('base')
    quote = request.args.get('quote')

    ws.send('{"id":1, "method":"call", "params":[0,"lookup_asset_symbols",[["' + base + '"], 0]]}')
    result_l = ws.recv()
    j_l = json.loads(result_l)
    base_id = j_l["result"][0]["id"]
    base_precision = 10**float(j_l["result"][0]["precision"])
    #print base_id

    ws.send('{"id":1, "method":"call", "params":[0,"lookup_asset_symbols",[["' + quote + '"], 0]]}')
    result_l = ws.recv()
    j_l = json.loads(result_l)
    #print j_l
    quote_id = j_l["result"][0]["id"]
    quote_precision = 10**float(j_l["result"][0]["precision"])
    #print quote_id

    now = datetime.date.today()
    ago = now - datetime.timedelta(days=100)
    ws.send('{"id":1, "method":"call", "params":['+history_api+',"get_market_history", ["'+base_id+'", "'+quote_id+'", 86400, "'+ago.strftime("%Y-%m-%dT%H:%M:%S")+'", "'+now.strftime("%Y-%m-%dT%H:%M:%S")+'"]]}')
    result_l = ws.recv()
    j_l = json.loads(result_l)

    data = []
    for w in range(0, len(j_l["result"])):

        open_quote = float(j_l["result"][w]["open_quote"])
        high_quote = float(j_l["result"][w]["high_quote"])
        low_quote = float(j_l["result"][w]["low_quote"])
        close_quote = float(j_l["result"][w]["close_quote"])

        open_base = float(j_l["result"][w]["open_base"])
        high_base = float(j_l["result"][w]["high_base"])
        low_base = float(j_l["result"][w]["low_base"])
        close_base = float(j_l["result"][w]["close_base"])

        # TODO: wrong way to go over the nothing for something issue bitshares-core #132 #287 #342
        if open_quote == 0:
            open_quote = 1
        if high_quote == 0:
            high_quote = 1
        if low_quote == 0:
            low_quote = 1
        if close_quote == 0:
            close_quote = 1

        if open_base == 0:
            open_base = 1
        if high_base == 0:
            high_base = 1
        if low_base == 0:
            low_base = 1
        if close_base == 0:
            close_base = 1

        open = float(open_base/base_precision)/float(open_quote/quote_precision)
        high = float(high_base/base_precision)/float(high_quote/quote_precision)
        low = float(low_base/base_precision)/float(low_quote/quote_precision)
        close = float(close_base/base_precision)/float(close_quote/quote_precision)

        ohlc = [open,high, low, close]

        high = max(ohlc)
        low = min(ohlc)

        #ohlc = [open, high, low, close]
        ohlc = [open, close, low, high]

        data.append(ohlc)

    append = [0,0,0,0]
    if len(data) < 99:
        complete = 99 - len(data)
        for c in range(0, complete):
            data.insert(0, append)

    return jsonify(data)

@app.route('/top_proxies')
def top_proxies():

    con = psycopg2.connect(database='explorer', user='postgres', host='localhost', password='posta')
    cur = con.cursor()

    query = "SELECT sum(amount) FROM holders"
    cur.execute(query)
    total = cur.fetchone()
    total_votes = total[0]

    query = "SELECT voting_as FROM holders WHERE voting_as<>'1.2.5' group by voting_as"
    cur.execute(query)
    results = cur.fetchall()
    #con.close()

    proxies = []

    for p in range(0, len(results)):

        proxy_line = [0] * 5

        proxy_id = results[p][0]
        proxy_line[0] = proxy_id

        query = "SELECT account_name, amount FROM holders WHERE account_id='"+proxy_id+"' LIMIT 1"
        cur.execute(query)
        proxy = cur.fetchone()

        try:
            proxy_name = proxy[0]
            proxy_amount = proxy[1]
        except:
            proxy_name = "unknown"
            proxy_amount = 0


        proxy_line[1] = proxy_name

        query = "SELECT amount, account_id FROM holders WHERE voting_as='"+proxy_id+"'"
        cur.execute(query)
        results2 = cur.fetchall()

        proxy_line[2] = int(proxy_amount)

        for p2 in range(0, len(results2)):
            amount = results2[p2][0]
            account_id = results2[p2][1]
            proxy_line[2] = proxy_line[2] + int(amount)  # total proxy votes
            proxy_line[3] = proxy_line[3] + 1       # followers

        if proxy_line[3] > 2:
            percentage = float(float(proxy_line[2]) * 100.0/ float(total_votes))
            proxy_line[4] = percentage
            proxies.append(proxy_line)

    con.close()

    proxies = sorted(proxies, key=lambda k: int(k[2]))
    r_proxies = proxies[::-1]

    return jsonify(filter(None, r_proxies))

@app.route('/top_holders')
def top_holders():

    con = psycopg2.connect(database='explorer', user='postgres', host='localhost', password='posta')
    cur = con.cursor()

    query = "SELECT * FROM holders WHERE voting_as='1.2.5' ORDER BY amount DESC LIMIT 10"
    cur.execute(query)
    results = cur.fetchall()
    con.close()
    return jsonify(results)

@app.route('/witnesses_votes')
def witnesses_votes():

    proxies = top_proxies()
    proxies = proxies.response
    proxies = ''.join(proxies)
    proxies = json.loads(proxies)
    proxies = proxies[:10]

    witnesses = get_witnesses()
    witnesses = witnesses.response
    witnesses = ''.join(witnesses)
    witnesses = json.loads(witnesses)
    witnesses = witnesses[:25]

    w, h = len(proxies) + 2, len(witnesses)
    witnesses_votes = [[0 for x in range(w)] for y in range(h)]

    for w in range(0, len(witnesses)):
        vote_id =  witnesses[w][0]["vote_id"]
        id_witness = witnesses[w][0]["id"]
        witness_account_name = witnesses[w][0]["witness_account_name"]

        witnesses_votes[w][0] = witness_account_name
        witnesses_votes[w][1] = id_witness

        c = 2

        for p in range(0, len(proxies)):
            id_proxy = proxies[p][0]

            #witnesses_votes[w][c] = id_proxy

            ws.send('{"id": 1, "method": "call", "params": [0, "get_objects", [["'+id_proxy+'"]]]}')
            result = ws.recv()
            j = json.loads(result)

            votes = j["result"][0]["options"]["votes"]
            #print votes
            p_vote = "-"
            for v in range(0, len(votes)):

                if votes[v] == vote_id:
                    p_vote = "Y"

            witnesses_votes[w][c] = id_proxy + ":" + p_vote

            c = c + 1

    #print witnesses_votes
    return jsonify(witnesses_votes)


@app.route('/workers_votes')
def workers_votes():

    proxies = top_proxies()
    proxies = proxies.response
    proxies = ''.join(proxies)
    proxies = json.loads(proxies)
    proxies = proxies[:10]

    workers = get_workers()
    workers = workers.response
    workers = ''.join(workers)
    workers = json.loads(workers)
    workers = workers[:6]
    #print workers

    w, h = len(proxies) + 2, len(workers)
    workers_votes = [[0 for x in range(w)] for y in range(h)]

    for w in range(0, len(workers)):
        vote_id =  workers[w][0]["vote_for"]
        id_worker = workers[w][0]["id"]
        worker_account_name = workers[w][0]["worker_account_name"]

        workers_votes[w][0] = worker_account_name
        workers_votes[w][1] = id_worker

        c = 2

        for p in range(0, len(proxies)):
            id_proxy = proxies[p][0]

            #witnesses_votes[w][c] = id_proxy

            ws.send('{"id": 1, "method": "call", "params": [0, "get_objects", [["'+id_proxy+'"]]]}')
            result = ws.recv()
            j = json.loads(result)

            votes = j["result"][0]["options"]["votes"]
            #print votes
            p_vote = "-"
            for v in range(0, len(votes)):

                if votes[v] == vote_id:
                    p_vote = "Y"

            workers_votes[w][c] = id_proxy + ":" + p_vote

            c = c + 1

    #print witnesses_votes
    return jsonify(workers_votes)

@app.route('/committee_votes')
def committee_votes():

    proxies = top_proxies()
    proxies = proxies.response
    proxies = ''.join(proxies)
    proxies = json.loads(proxies)
    proxies = proxies[:10]

    committee = get_committee_members()
    committee = committee.response
    committee = ''.join(committee)
    committee = json.loads(committee)
    committee = committee[:11]
    #print workers

    w, h = len(proxies) + 2, len(committee)
    committee_votes = [[0 for x in range(w)] for y in range(h)]

    for w in range(0, len(committee)):
        vote_id =  committee[w][0]["vote_id"]
        id_committee = committee[w][0]["id"]
        committee_account_name = committee[w][0]["committee_member_account_name"]

        committee_votes[w][0] = committee_account_name
        committee_votes[w][1] = id_committee

        c = 2

        for p in range(0, len(proxies)):
            id_proxy = proxies[p][0]

            #witnesses_votes[w][c] = id_proxy

            ws.send('{"id": 1, "method": "call", "params": [0, "get_objects", [["'+id_proxy+'"]]]}')
            result = ws.recv()
            j = json.loads(result)

            votes = j["result"][0]["options"]["votes"]
            #print votes
            p_vote = "-"
            for v in range(0, len(votes)):

                if votes[v] == vote_id:
                    p_vote = "Y"
                    committee_votes[w][c] = id_proxy + ":" + p_vote
                    break
                else:
                    p_vote = "-"
                    committee_votes[w][c] = id_proxy + ":" + p_vote

            c = c + 1

    #print witnesses_votes
    return jsonify(committee_votes)

