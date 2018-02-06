#!/usr/bin/env python2
import json
import os
import time
import urllib

import psycopg2
from websocket import create_connection

import config


ws = create_connection(config.WEBSOCKET_URL)

con = psycopg2.connect(**config.POSTGRES)
cur = con.cursor()

query = "TRUNCATE holders"
cur.execute(query)
query = "ALTER SEQUENCE holders_hid_seq RESTART WITH 1"
cur.execute(query)
con.commit()

ws.send('{"id":1, "method":"call", "params":[0,"get_account_count",[]]}')
result = ws.recv()
j = json.loads(result)
account_count = int(j["result"])

for ac in range(0, account_count):

    ws.send('{"id":1, "method":"call", "params":[0,"get_objects",[["1.2.' + str(ac) + '"]]]}')
    result = ws.recv()
    j = json.loads(result)

    try:
        account_id = j["result"][0]["id"]
        account_name = j["result"][0]["name"]
    except:
        continue


    ws.send('{"id":1, "method":"call", "params":[0,"get_account_balances",["' + account_id + '", ["1.3.0"]]]}')
    result3 = ws.recv()
    jb = json.loads(result3)

    if jb["result"][0]["amount"] == 0:
        continue
    else:
        amount = jb["result"][0]["amount"]

        # add total_core_in_orders to the sum
        ws.send('{"id":1, "method":"call", "params":[0,"get_objects",[["' + j["result"][0]["statistics"] + '"]]]}')
        result = ws.recv()
        js = json.loads(result)

        try:
            total_core_in_orders = js["result"][0]["total_core_in_orders"]
        except:
            total_core_in_orders = 0

        amount = int(amount) + int(total_core_in_orders)

        voting_account = j["result"][0]["options"]["voting_account"]
        query = "INSERT INTO holders (account_id, account_name, amount, voting_as) VALUES('"+account_id+"', '"+account_name+"','"+str(amount)+"', '"+voting_account+"')"
        cur.execute(query)
        con.commit()

con.close()
