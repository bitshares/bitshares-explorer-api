import websocket
import thread
import time

import json
import urllib
#from flask import jsonify

import psycopg2

# config
websocket_url = "ws://127.0.0.1:8090/ws"
postgres_host = 'localhost'
postgres_database = 'explorer'
postgres_username = 'postgres'
postgres_password = 'posta'
# end config

def on_message(ws, message):
    #print(message)
    j = json.loads(message)
    try:
        #print j["params"][1][0][0]["id"]
        id = j["params"][1][0][0]["id"]
        #print id[:4]
        if id[:4] == "2.9.":
            #print j["params"][1][0][0]
            url = "http://23.94.69.140:5000/get_object?object=" + id
            #print url
            response = urllib.urlopen(url)
            data = json.loads(response.read())
            #print data[0]
            account_id = data[0]["account"]
            url = "http://23.94.69.140:5000/account?account_id=" + account_id
            response_a = urllib.urlopen(url)
            data_a = json.loads(response_a.read())
            #print data_a[0]["name"]
            account_name = data_a[0]["name"]


            #print account
            #print data.operation_id
            url = "http://23.94.69.140:5000/get_object?object=" + data[0]["operation_id"]
            #print url
            #print data.operation_id
            response2 = urllib.urlopen(url)
            data2 = json.loads(response2.read())
            #print data2
            block_num = data2[0]["block_num"]

            op_type = data2[0]["op"][0]

            #print block_num
            trx_in_block =  data2[0]["trx_in_block"]
            op_in_trx =  data2[0]["op_in_trx"]

            con = psycopg2.connect(database=postgres_database, user=postgres_username, host=postgres_host,
                                   password=postgres_password)
            cur = con.cursor()
            query = "INSERT INTO ops (oh, ath, block_num, trx_in_block, op_in_trx, datetime, account_id, op_type, account_name) VALUES('"+id+"', '"+data[0]["operation_id"]+"', '"+str(block_num)+"', '"+str(trx_in_block)+"', '"+str(op_in_trx)+"', NOW(), '"+account_id+"', '"+str(op_type)+"', '"+account_name+"')"
            print query
            cur.execute(query)
            con.commit()

    except:
        pass

def on_error(ws, error):
    print(error)
    #print ""

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    def run(*args):

        ws.send('{"method": "call", "params": [1, "database", []], "id": 3}')
        ws.send('{"method": "call", "params": [2, "set_subscribe_callback", [5, true]], "id": 6}')

    thread.start_new_thread(run, ())

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(websocket_url,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open


    ws.run_forever()
