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
    #print j3["result"]["quote_volume"]
    j["result"]["quote_volume"] = j3["result"]["quote_volume"]

    ws.send('{"id":1, "method":"call", "params":[0,"get_witness_count",[]]}')
    result4 = ws.recv()
    j4 = json.loads(result4)
    #print j3["result"]["quote_volume"]
    #print j4["result"]
    j["result"]["witness_count"] = j4["result"]

    #j["result"]["witness_count"] = j4["result"]


    #print j["result"]

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

    ws.send('{"id":1, "method":"call", "params":[0,"get_witness_count",[]]}')
    result4 = ws.recv()
    j4 = json.loads(result4)
    #print j3["result"]["quote_volume"]
    #print j4["result"]
    j["result"][0]["witness_count"] = j4["result"]


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

    ws.send('{"id":1, "method":"call", "params":['+history_api+',"get_account_history",["'+account_id+'", "1.11.0", 20, "1.11.9999999999"]]}')
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


    ws.send('{"jsonrpc": "2.0", "method": "get_workers_count", "params": [], "id": 1}')

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