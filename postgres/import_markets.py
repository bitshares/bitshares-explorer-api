#!/usr/bin/env python2
import json

import psycopg2
from websocket import create_connection

import api
import config


ws = create_connection(config.WEBSOCKET_URL)

con = psycopg2.connect(**config.POSTGRES)
cur = con.cursor()

query = "TRUNCATE markets"
cur.execute(query)

query = "ALTER SEQUENCE markets_id_seq RESTART WITH 1"
cur.execute(query)

con.commit()

query = "SELECT * FROM assets WHERE volume > 0 ORDER BY volume DESC"
cur.execute(query)
rows = cur.fetchall()

for row in rows:
    all_assets = []

    ws.send('{"id":1, "method":"call", "params":[0,"list_assets",["AAAAA", 100]]}')
    result = ws.recv()
    j = json.loads(result)

    all_assets.append(j);

    len_result = len(j["result"])

    while len_result == 100:
        ws.send('{"id":1, "method":"call", "params":[0,"list_assets",["'+j["result"][99]["symbol"]+'", 100]]}')
        result = ws.recv()
        j = json.loads(result)
        len_result = len(j["result"])
        all_assets.append(j);

    try:
        for x in range (0, len(all_assets)):
            for i in range(0, 100):

                symbol =  all_assets[x]["result"][i]["symbol"]
                id_ = all_assets[x]["result"][i]["id"]

                try:
                    data = api._get_volume(symbol, row[1])
                    volume = data["base_volume"]
                except:
                    volume = 0
                    continue

                try:
                    data2 = api._get_ticker(symbol, row[1])
                    price = data2["latest"]
                    #print price
                except:
                    price = 0
                    continue

                print row[1] + " / " + symbol + " vol: " + str(volume) + " price: " + str(price)
                #if symbol == "COMPUCEEDS":
                #    exit

                # this was an attempt to sum up volume of not bts crosses to calculate total DEX volume, disabled by now(need better math to convert to bts)
                """
                if float(data["base_volume"]) > 0 and float(row[3]) > 0 and row[1] != "BTS" and symbol != "BTS":
                    ws.send('{"id":1, "method":"call", "params":[0,"lookup_asset_symbols",[["' + symbol + '"], 0]]}')
                    result_l = ws.recv()
                    j_l = json.loads(result_l)
                    base_id = j_l["result"][0]["id"]
                    base_precision = 10 ** float(j_l["result"][0]["precision"])
                    # print base_id

                    ws.send('{"id":1, "method":"call", "params":[0,"lookup_asset_symbols",[["' + row[1] + '"], 0]]}')
                    result_l = ws.recv()
                    j_l = json.loads(result_l)
                    # print j_l
                    quote_id = j_l["result"][0]["id"]
                    quote_precision = 10 ** float(j_l["result"][0]["precision"])

                    print float(row[4])
                    print float(data['base_volume'])
                    print float(row[3])
                    sum_volume = float(row[4]) + (float(data['base_volume']) * float(base_precision) / float(data['quote_volume']) * float(quote_precision)) / float(row[3])
                    print sum_volume
                    exit
                    query_u = "UPDATE assets SET volume='"+str(sum_volume)+"' WHERE id="+str(row[0])
                    #print query_u
                    cur.execute(query_u)
                    con.commit()
                """

                if float(price) > 0 and float(volume) > 0:
                    query = "INSERT INTO markets (pair, asset_id, price, volume, aid) VALUES('"+row[1]+ "/" + symbol+"', '"+str(row[0])+"', '"+str(float(price))+"', '"+str(float(volume))+"', '"+row[2]+"')"
                    print query
                    cur.execute(query)
                    con.commit()

    except:
        continue


cur.close()
con.close()
