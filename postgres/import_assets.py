#!/usr/bin/env python2
import json

import psycopg2
from websocket import create_connection

import api
import config

ws = create_connection(config.WEBSOCKET_URL)

con = psycopg2.connect(**config.POSTGRES)
cur = con.cursor()

query = "TRUNCATE assets"
cur.execute(query)

query = "ALTER SEQUENCE assets_id_seq RESTART WITH 1;"
cur.execute(query)

# alter sequence of the ops once a day here
query = "DELETE FROM ops WHERE oid NOT IN (SELECT oid FROM ops ORDER BY oid DESC LIMIT 10);"
cur.execute(query)

for x in range(0, 10):
    query = "UPDATE ops set oid=%s WHERE oid IN (SELECT oid FROM ops ORDER BY oid LIMIT 1 OFFSET %s);"
    cur.execute(query, (x+1, x))

query = "ALTER SEQUENCE ops_oid_seq RESTART WITH 11;"
cur.execute(query)

con.commit()

if config.TESTNET == 1:
    core_symbol = config.CORE_ASSET_SYMBOL_TESTNET
else:
    core_symbol = config.CORE_ASSET_SYMBOL

all_assets = []

ws.send('{"id":1, "method":"call", "params":[0,"list_assets",["AAAAA", 100]]}')
result = ws.recv()
j = json.loads(result)

all_assets.append(j)

len_result = len(j["result"])

print len_result
#print all_assets

while len_result == 100:
    ws.send('{"id":1, "method":"call", "params":[0,"list_assets",["'+j["result"][99]["symbol"]+'", 100]]}')
    result = ws.recv()
    j = json.loads(result)
    len_result = len(j["result"])
    all_assets.append(j)

for x in range(0, len(all_assets)):
    size = len(all_assets[x]["result"])
    print size

    for i in range(0, size):
        symbol = all_assets[x]["result"][i]["symbol"]
        asset_id = all_assets[x]["result"][i]["id"]

        precision = 5
        try:
            data3 = api._get_asset(asset_id)
            current_supply = data3[0]["current_supply"]
            precision = data3[0]["precision"]
        except:
            price = 0
            continue

        try:
            holders = api._get_asset_holders_count(asset_id)
        except:
            holders = 0
            continue

        if symbol == core_symbol:
            type_ = "Core Token"
        elif all_assets[x]["result"][i]["issuer"] == "1.2.0":
            type_ = "SmartCoin"
        else:
            type_ = "User Issued"
        #print all_assets[x]["result"][i]

        try:
            data = api._get_volume(core_symbol, symbol)
        except:
            continue

        #print symbol
        print data["quote_volume"]

        try:
            data2 = api._get_ticker(core_symbol, symbol)
            price = data2["latest"]
            #print price

            if str(price) == 'inf':
               continue
            #    exit

            #print price
        except:
            price = 0
            continue

        mcap = int(current_supply) * float(price)

        query = "INSERT INTO assets (aname, aid, price, volume, mcap, type, current_supply, holders, wallettype, precision) VALUES({})".format(', '.join(('%s',)*10))
        print(symbol)
        cur.execute(query, (symbol, asset_id, price, data['base_volume'], str(mcap), type_, str(current_supply), str(holders), '', str(precision)))
        con.commit()


# with updated volume, add stats
query = "select sum(volume) from assets WHERE aname!='BTS'"
cur.execute(query)
results = cur.fetchone()
volume = results[0]
if volume is None:
    volume = 0

query = "select sum(mcap) from assets"
cur.execute(query)
results = cur.fetchone()
market_cap = results[0]

query = "INSERT INTO stats (type, value, date) VALUES('volume_bts', %s, NOW())"
print query
cur.execute(query, (str(int(round(volume))),))
con.commit()

"""query = "INSERT INTO stats (type, value, date) VALUES('market_cap_bts', '"+str(int(round(market_cap)))+"', NOW())" # out of range for bigint, fix.
print query
cur.execute(query)
con.commit()
"""

# insert core token manually
data3 = api._get_asset(config.CORE_ASSET_ID)
current_supply = data3[0]["current_supply"]

holders = api._get_asset_holders_count(config.CORE_ASSET_ID)

mcap = int(current_supply)

query = "INSERT INTO assets (aname, aid, price, volume, mcap, type, current_supply, holders, wallettype) VALUES('BTS', '1.3.0', '1', %s, %s, %s, %s, %s, %s)"
cur.execute(query, (str(volume), str(mcap), 'Core Token', str(current_supply), str(holders), ''))
con.commit()

cur.close()
con.close()
