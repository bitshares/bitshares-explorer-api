from websocket import create_connection
import time

import json
import urllib

import psycopg2

websocket_url = "ws://127.0.0.1:8090/ws"
postgres_host = 'localhost'
postgres_database = 'explorer'
postgres_username = 'postgres'
postgres_password = 'posta'
# end config

ws = create_connection(websocket_url) # localhost

con = psycopg2.connect(database=postgres_database, user=postgres_username, host=postgres_host, password=postgres_password)
cur = con.cursor()


#query = "TRUNCATE referrers"
#cur.execute(query)
#query = "ALTER SEQUENCE referrers_rid_seq RESTART WITH 1"
#cur.execute(query)
#con.commit()

query = "SELECT rid FROM referrers ORDER BY rid DESC LIMIT 1"
cur.execute(query)
in_database = cur.fetchone()
#print in_database[0]
#con.close()

ws.send('{"id":1, "method":"call", "params":[0,"get_account_count",[]]}')
result = ws.recv()
j = json.loads(result)
account_count = int(j["result"])

print account_count

for ac in range(in_database[0], account_count):

    ws.send('{"id":1, "method":"call", "params":[0,"get_objects",[["1.2.' + str(ac) + '"]]]}')
    result = ws.recv()
    j = json.loads(result)

    try:
        account_id = j["result"][0]["id"]
        account_name = j["result"][0]["name"]

        referrer = j["result"][0]["referrer"]
        referrer_rewards_percentage = j["result"][0]["referrer_rewards_percentage"]
        lifetime_referrer = j["result"][0]["lifetime_referrer"]
        lifetime_referrer_fee_percentage = j["result"][0]["lifetime_referrer_fee_percentage"]

        print account_id
        print referrer
        print lifetime_referrer
        print ""

        query = "INSERT INTO referrers (account_id, account_name, referrer, referrer_rewards_percentage, lifetime_referrer, lifetime_referrer_fee_percentage) " \
                "VALUES('"+account_id+"', '"+account_name+"','"+referrer+"', '"+str(referrer_rewards_percentage)+"','"+lifetime_referrer+"', '"+str(lifetime_referrer_fee_percentage)+"')"
        cur.execute(query)
        con.commit()

    except:
        continue

con.close()
