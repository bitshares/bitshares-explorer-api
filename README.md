# bitshares-python-api-backend
Simple Python wrapper for front end applications to be called by GET urls. api calls are added on demand as front end applications requiere it. 


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

## Install and setup Postgres

## Setup Cron

 `crontab -e`

 Add 2 lines:

```
0 23 * * *  python /full/path/to/repo/bitshares-python-api-backend/postgres/import_assets.py >/dev/null
15 23 * * *  python /full/path/to/repo/bitshares-python-api-backend/postgres/markets.py >/dev/null
```

## Setup real time operation grabber

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







