from websocket import create_connection
import time

import json
import urllib

import psycopg2

ws = create_connection("ws://127.0.0.1:8090/ws") # localhost

con = psycopg2.connect(database='explorer', user='postgres', host='localhost', password='posta')
cur = con.cursor()

query = "TRUNCATE assets"
cur.execute(query)
con.commit()

all = []

ws.send('{"id":1, "method":"call", "params":[0,"list_assets",["AAAAA", 100]]}')
result = ws.recv()
j = json.loads(result)

all.append(j);

len_result = len(j["result"])

#print len_result
#print all

while  len_result == 100:
    ws.send('{"id":1, "method":"call", "params":[0,"list_assets",["'+j["result"][99]["symbol"]+'", 100]]}')
    result = ws.recv()
    j = json.loads(result)
    len_result = len(j["result"])
    all.append(j);

for x in range (0, len(all)):
    for i in range(0, 100):
        symbol = all[x]["result"][i]["symbol"]

        if symbol == "BTS":
            type = "Core Token"
        elif all[x]["result"][i]["issuer"] == "1.2.0":
            type = "SmartCoin"
        else:
            type = "User Issued"
        #print all[x]["result"][i]
        id = all[x]["result"][i]["id"]

        url = "http://23.94.69.140:5000/get_volume?base=BTS&quote=" + symbol
        response = urllib.urlopen(url)

        try:
            data = json.loads(response.read())
        except:
            continue

        #print symbol
        #print data["quote_volume"]

        url = "http://23.94.69.140:5000/get_ticker?base=BTS&quote=" + symbol
        response2 = urllib.urlopen(url)
        try:
            data2 = json.loads(response2.read())
            price = data2["latest"]
            #print price
        except:
            price = 0
            continue

        url = "http://23.94.69.140:5000/get_asset?asset_id=" + id
        print url
        response3 = urllib.urlopen(url)
        try:
            data3 = json.loads(response3.read())
            current_supply = data3[0]["current_supply"]
            #print current_supply
        except:
            price = 0
            continue

        mcap = int(current_supply) * float(price)

        url = "http://23.94.69.140:5000/get_asset_holders_count?asset_id=" + id
        #print url
        response4 = urllib.urlopen(url)
        try:
            data4 = json.loads(response4.read())
            holders = data4
            #print holders
        except:
            holders = 0
            continue

        query = "INSERT INTO assets (aname, aid, price, volume, mcap, type, current_supply, holders) VALUES('"+symbol+"', '"+id+"', '"+price+"', '"+data['quote_volume']+"', '"+str(mcap)+"', '"+type+"', '"+str(current_supply)+"', '"+str(holders)+"')"
        print query
        cur.execute(query)
        con.commit()



con.close()
