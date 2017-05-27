from websocket import create_connection
import json
from flask import jsonify


from flask import Flask
from flask_cors import CORS, cross_origin
app = Flask(__name__)
CORS(app)

from flask import request

#ws = create_connection("wss://eu.openledger.info/ws")
ws = create_connection("ws://127.0.0.1:8090/ws") #munich localhost

@app.route('/header')
def header():

    ws.send('{"id":1, "method":"call", "params":[0,"get_dynamic_global_properties",[]]}')
    result =  ws.recv()
    j = json.loads(result)

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

    #print j["result"]

    return jsonify(j["result"])

@app.route('/accounts')
def accounts():

    account_id = request.args.get('account_id')

    ws.send('{"id":2,"method":"call","params":[1,"login",["",""]]}')
    login =  ws.recv()
    #print  result2

    ws.send('{"id":2,"method":"call","params":[1,"asset",[]]}')

    asset =  ws.recv()
    asset_j = json.loads(asset)

    asset_api = str(asset_j["result"])

    ws.send('{"id":1, "method":"call", "params":['+asset_api+',"get_asset_holders",["1.3.0"]]}')
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

    ws.send('{"id":1, "method":"call", "params":[0,"list_assets",["BTS", 100]]}')
    result =  ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

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

    ws.send('{"id":1, "method":"call", "params":['+history_api+',"get_account_history",["'+account_id+'", "1.11.10", 100, "1.11.0"]]}')
    result =  ws.recv()
    j = json.loads(result)

    #print j["result"]

    return jsonify(j["result"])

@app.route('/get_asset')
def get_asset():
    asset_id = request.args.get('asset_id')

    ws.send('{"id":1, "method":"call", "params":[0,"get_assets",[["' + asset_id + '"], 0]]}')
    result = ws.recv()
    j = json.loads(result)

    # print j["result"]

    return jsonify(j["result"])

