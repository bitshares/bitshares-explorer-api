from websocket import create_connection
import time

import json
import urllib

import psycopg2

ws = create_connection("ws://127.0.0.1:8090/ws") # localhost

con = psycopg2.connect(database='explorer', user='postgres', host='localhost', password='posta')
cur = con.cursor()

query = "TRUNCATE markets"
cur.execute(query)

query = "ALTER SEQUENCE assets_id_seq RESTART WITH 1;"
cur.execute(query)

con.commit()

query = "SELECT * FROM assets WHERE volume > 0 ORDER BY volume DESC"
cur.execute(query)
rows = cur.fetchall()

for row in rows:

    all = []

    ws.send('{"id":1, "method":"call", "params":[0,"list_assets",["AAAAA", 100]]}')
    result = ws.recv()
    j = json.loads(result)

    all.append(j);

    len_result = len(j["result"])

    while  len_result == 100:
        ws.send('{"id":1, "method":"call", "params":[0,"list_assets",["'+j["result"][99]["symbol"]+'", 100]]}')
        result = ws.recv()
        j = json.loads(result)
        len_result = len(j["result"])
        all.append(j);

    try:
        for x in range (0, len(all)):
            for i in range(0, 100):
                symbol =  all[x]["result"][i]["symbol"]
                id = all[x]["result"][i]["id"]

                url = "http://23.94.69.140:5000/get_volume?base="+row[1]+"&quote=" + symbol

                response = urllib.urlopen(url)

                try:
                    data = json.loads(response.read())
                except:
                    pass
                    continue


                url = "http://23.94.69.140:5000/get_ticker?base=BTS&quote=" + symbol
                response2 = urllib.urlopen(url)
                try:
                    data2 = json.loads(response2.read())
                    price = data2["latest"]
                    #print price
                except:
                    price = 0
                    continue

                print row[1] + " / " + symbol + " vol: " + str(data["quote_volume"]) + " price: " + str(price)
                if float(price) > 0 and float(data['quote_volume']) > 0:
                    query = "INSERT INTO markets (pair, asset_id, price, volume, aid) VALUES('"+row[1]+ "/" + symbol+"', '"+str(row[0])+"', '"+price+"', '"+data['quote_volume'] +"', '"+row[2]+"')"
                    print query
                    cur.execute(query)
                    con.commit()

    except:
        continue

con.close()
