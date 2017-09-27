from websocket import create_connection
import time

import json
import urllib

import psycopg2

# config
websocket_url = "ws://127.0.0.1:8090/ws"
postgres_host = 'localhost'
postgres_database = 'explorer'
postgres_username = 'postgres'
postgres_password = 'posta'
# end config

ws = create_connection(websocket_url) # localhost

con = psycopg2.connect(database=postgres_database, user=postgres_username, host=postgres_host, password=postgres_password)
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

                url = "http://23.94.69.140:5000/get_volume?base="+symbol+"&quote=" + row[1]
                #print "http://23.94.69.140:5000/get_volume?base="+row[1]+"&quote=" + symbol

                response = urllib.urlopen(url)

                try:
                    data = json.loads(response.read())
                except:
                    pass
                    continue


                url = "http://23.94.69.140:5000/get_ticker?base="+symbol+"&quote="+ row[1]
                response2 = urllib.urlopen(url)
                try:
                    data2 = json.loads(response2.read())
                    price = data2["latest"]
                    #print price
                except:
                    price = 0
                    continue

                print row[1] + " / " + symbol + " vol: " + str(data["base_volume"]) + " price: " + str(price)

                # update asset volume
                #if row[1] == "BTS":
                #    divide_by = 1
                #else:
                #    divide_by = row[3]
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

                if float(price) > 0 and float(data['base_volume']) > 0:
                    query = "INSERT INTO markets (pair, asset_id, price, volume, aid) VALUES('"+row[1]+ "/" + symbol+"', '"+str(row[0])+"', '"+price+"', '"+data['base_volume'] +"', '"+row[2]+"')"
                    print query
                    cur.execute(query)
                    con.commit()

    except:
        continue


con.close()
