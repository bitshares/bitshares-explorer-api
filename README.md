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

-  `account_name` - Get full account data(including account name) from id.

Sample URL: http://23.94.69.140:5000/account_name?account_id=1.2.356589

- `operation` - Get full data from an operation a 1.11.X id.

Sample URL: http://23.94.69.140:5000/operation?operation_id=1.11.2673910





