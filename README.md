# BPAB - Bitshares Python Api Backend

Simple Python wrapper for front end applications to be called by GET urls. api calls are added on demand as front end applications requiere it. 

The current main purpose of the api is to serve the bitshares explorer: http://bitshares-explorer.io but it is expected to serve more applications. 

## Install API:

For debian based linux distros:

```
apt-get install python-virtualenv

apt-get install python-pip

pip install flask

pip install -U flask-cors

pip install websocket-client

git clone https://github.com/oxarbitrage/bitshares-python-api-backend

cd bitshares-python-api-backend/

virtualenv venv

. venv/bin/activate

export FLASK_APP=api.py

flask run --host=0.0.0.0
```

## Setup Postgres

The explorer use a postgres database to store some temporal data in order to do certain heavy operations and temporal storage of data that are not possible in the current bitshares-node.

You need to have postgres installed somewhere and have host, user, pass and database details.

This details, among with a websocket url need to be added to python files. Here is how the config looks in the header of all the files:

```
# config
websocket_url = "ws://127.0.0.1:8090/ws"
postgres_host = 'localhost'
postgres_database = 'explorer'
postgres_username = 'postgres'
postgres_password = 'posta'
# end config
```

Make sure you add your data in the following files:

- api.cpp
- postgres/import_realtime_ops.oy
- postgres/import_assets.py
- postgres/import_markets.py
- postgres/import_holders.py

You need to create the tables where the data will be stored into postgres. Here is a pg_dump file of what you will need to do in your database:

https://github.com/oxarbitrage/bitshares-python-api-backend/blob/master/postgres/schema.txt

## Setup Cron

The API backend runs 3 scripts once a day and store results in a postgres database. The 3 scripts can be added to cron.

 `crontab -e`

 Add 3 lines:

```
0 22 * * *  python /root/bitshares-munich/explorer/repo/bitshares-python-api-backend/postgres/import_holders.py >/dev/null
0 23 * * *  python /root/bitshares-munich/explorer/repo/bitshares-python-api-backend/postgres/import_assets.py >/dev/null
15 23 * * *  python /root/bitshares-munich/explorer/repo/bitshares-python-api-backend/postgres/markets.py >/dev/null
```

## Setup real time operation grabber

I use `screen` to run the grabber but you can also run it in the background, as a service, etc.

command to start it is just:

`python import_realtime_ops.py`

this need to be constantly running as it is connected to the websocket getting the real time operations and saving them temporally in a database.

expected output for the grabber:

```
GET /ws HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Host: 127.0.0.1:8090
Origin: http://127.0.0.1:8090
Sec-WebSocket-Key: xr2KHygFlayuciZC/Oj63A==
Sec-WebSocket-Version: 13


-----------------------
--- response header ---
HTTP/1.1 101 Switching Protocols
Connection: upgrade
Sec-WebSocket-Accept: 1YT6X2SDtwPzg/iJHtb32vKT9Pw=
Server: WebSocket++/0.7.0
Upgrade: websocket
-----------------------
send: '\x81\xba\xe2\x8bZ\xce\x99\xa97\xab\x96\xe35\xaa\xc0\xb1z\xec\x81\xea6\xa2\xc0\xa7z\xec\x92\xea(\xaf\x8f\xf8x\xf4\xc2\xd0k\xe2\xc2\xa9>\xaf\x96\xea8\xaf\x91\x
eex\xe2\xc2\xd0\x07\x93\xce\xabx\xa7\x86\xa9`\xee\xd1\xf6'
send: '\x81\xcf\x00\xf9\xd6\x80{\xdb\xbb\xe5t\x91\xb9\xe4"\xc3\xf6\xa2c\x98\xba\xec"\xd5\xf6\xa2p\x98\xa4\xe1m\x8a\xf4\xba \xa2\xe4\xac \xdb\xa5\xe5t\xa6\xa5\xf5b\x
8a\xb5\xf2i\x9b\xb3\xdfc\x98\xba\xecb\x98\xb5\xeb"\xd5\xf6\xdb5\xd5\xf6\xf4r\x8c\xb3\xdd]\xd5\xf6\xa2i\x9d\xf4\xba \xcf\xab'
INSERT INTO ops (oh, ath, block_num, trx_in_block, op_in_trx, datetime, account_id, op_type, account_name) VALUES('2.9.62734829', '1.11.61956083', '19533294', '2',
'4', NOW(), '1.2.214390', '1', 'julien430')
INSERT INTO ops (oh, ath, block_num, trx_in_block, op_in_trx, datetime, account_id, op_type, account_name) VALUES('2.9.62734836', '1.11.61956090', '19533295', '5',
'0', NOW(), '1.2.116747', '2', 'lbwbtswithdrawal')
INSERT INTO ops (oh, ath, block_num, trx_in_block, op_in_trx, datetime, account_id, op_type, account_name) VALUES('2.9.62734850', '1.11.61956104', '19533297', '2',
'1', NOW(), '1.2.133075', '1', 'usd-btc-mm')
INSERT INTO ops (oh, ath, block_num, trx_in_block, op_in_trx, datetime, account_id, op_type, account_name) VALUES('2.9.62734856', '1.11.61956110', '19533298', '3',
'2', NOW(), '1.2.214390', '1', 'julien430')

...
```

## Usage:

Point your browser to:

http://yoursever.com:5000/header

## Available API Calls

- `header` - Get explorer data needed for header.

Sample URL: http://23.94.69.140:5000/header

-  `account_name` - Get account data(including account name) from id.

Sample URL: http://23.94.69.140:5000/account_name?account_id=1.2.356589

- `operation` - Get full data from an operation a 1.11.X id.

Sample URL: http://23.94.69.140:5000/operation?operation_id=1.11.2673910

- `operation_full` - Same as above but connecting to a full node to get old operation history data. 

Sample URL: http://23.94.69.140:5000/operation_full?operation_id=1.11.2673910

- `accounts` - Get a list of the 100 richest accounts in the bitshares network.

Sample URL: http://23.94.69.140:5000/accounts

- `full_account` - Get full data from account.

Sample URL: http://23.94.69.140:5000/full_account?account_id=1.2.356589

- `assets` - Get list of active assets.

Sample URL: http://23.94.69.140:5000/assets

- `fees` - Get fees data from the network.

Sample URL: http://23.94.69.140:5000/fees

- `account_history` - Get last history of the account.

Sample URL: http://23.94.69.140:5000/account_history?account_id=1.2.356589

- `get_asset` - Get data from specific asset.

Sample URL: http://23.94.69.140:5000/get_asset?asset_id=1.3.0

- `block_header` - Get block header data.

Sample URL: http://23.94.69.140:5000/block_header?block_num=18584158

-  `get_block` - Get full data of block including operations on it.

Sample URL: http://23.94.69.140:5000/get_block?block_num=18584158

- `get_ticker` - Get ticker data of a base/quote pair.

Sample URL: http://23.94.69.140:5000/get_ticker?base=BTS&quote=CNY

- `get_volume` - Get volume data of a base/quote pair.

Sample URL : http://23.94.69.140:5000/get_volume?base=BTS&quote=CNY

- `lastnetworkops` - Get the last 10 network operations.

Sample URL: http://23.94.69.140:5000/lastnetworkops

-  `get_object` - Get object data from id.

Sample URL: http://23.94.69.140:5000/get_object?object=1.14.55

- `get_asset_holders_count` - Get the count of assets holders from asset id.

Sample URL: http://23.94.69.140:5000/get_asset_holders_count?asset_id=1.3.0

- `get_asset_holders` - Get the list of assets holders from asset id.

Sample URL: http://23.94.69.140:5000/get_asset_holders?asset_id=1.3.113

- `get_workers` - Get full workers list in the network.

Sample URL: http://23.94.69.140:5000/get_workers

-  `get_markets` - Get active markets for asset.

Sample URL: http://23.94.69.140:5000/get_markets?asset_id=1.3.113

-  `get_most_active_markets` - Get the network most active markets by volume in the last 24 hours.

Sample URL http://23.94.69.140:5000/get_most_active_markets

- `get_order_book` - Get the order book for a market.

Sample URL: http://23.94.69.140:5000/get_order_book?base=BTS&quote=CNY

-  `get_margin_positions` - Get the margin positions for an account.

Sample URL: http://23.94.69.140:5000/get_margin_positions?account_id=1.2.12376

- `get_witnesses` - Get all witnesses, ordered by voting, active and inactive.

Sample URL: http://23.94.69.140:5000/get_witnesses

- `get_committee_members` - Get all the committee members, ordered by voting, active and inactive.

Sample URL: http://23.94.69.140:5000/get_committee_members

- `market_chart_dates` - Utility call to get dates from now and back each day in the last 100 days. Used to build market charts.

Sample URL: http://23.94.69.140:5000/market_chart_dates

-  `market_chart_data` - Get 100 days OHLC candlestick data from a market. Data is formatted to build candlestick charts for a market.

Sample URL: http://23.94.69.140:5000/market_chart_data?base=USD&quote=BTS

- `top_proxies` - Get the top network proxies in the Bitshares chain.

Sample URL: http://23.94.69.140:5000/top_proxies

- `top_holders` - Get the individual accounts with most BTS in their accounts.

Sample URL: http://23.94.69.140:5000/top_holders

- `witnesses_votes` - Get proxy votes for each witness.

Sample URL: http://23.94.69.140:5000/witnesses_votes

- `workers_votes` - Get proxy votes for each worker.

Sample URL: http://23.94.69.140:5000/workers_votes

- `committee_votes` - Get proxy votes for each committee member.

Sample URL: http://23.94.69.140:5000/committee_votes

- `top_markets` - Most 6 active markets in the last 24 hours in the chain.

Sample URL: http://23.94.69.140:5000/top_markets

-  `top_smartcoins` - Most active by volume smartcoins in the last24 hours.

Sample URL: http://23.94.69.140:5000/top_smartcoins

-  `top_uias` - Most active by volume user issued assets in the last24 hours.

Sample URL: http://23.94.69.140:5000/top_uias

- `top_operations` - Top 3 most called operations in the last 24 hours.

Sample URL: http://23.94.69.140:5000/top_operations

- `last_network_transactions` - Incomplete - Work in progress in the node side.

Sample URL: None yet

- `lookup_accounts` - Get accounts from the network that start with parameter. Useful for autocomplete.

Sample URL: http://23.94.69.140:5000/lookup_accounts?start=alfredo

-  `lookup_assets` - Get assets from the network that start with parameter. Useful for autocomplete.

Sample URL: http://23.94.69.140:5000/lookup_assets?start=A

-  `getlastblocknumbher` - Utility function that will get the current last block number at the moment of calling.

Sample URL: http://23.94.69.140:5000/getlastblocknumbher







