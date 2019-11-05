# BitShares Explorer REST API

BitShares Explorer REST API allows your programs to query the blockchain. 

[https://explorer.bitshares-kibana.info/apidocs/](https://explorer.bitshares-kibana.info/apidocs/)

- [Installation](#installation)
  - [Elasticsearch node](#Elasticsearch-node)
  - [BitShares node](#BitShares-node)
  - [Install BitShares Explorer API and dependencies](#Install-BitShares-Explorer-API-and-dependencies)
- [Usage](#Usage)
  - [Simple running](#Simple-running)
  - [Nginx and uwsgi](#Nginx-and-uwsgi)
  - [Profiler](#Profiler)
  - [Development](#Development)

## Installation

The following procedure will work in Debian based Linux, more specifically the commands to make the guide were executed in `Ubuntu 18.04` with `Python 3.7`.

### Elasticsearch node

Some API calls make use of elasticsearch plugins for Bitshares. This plugins are `elasticsearch` and `es-objects`.

For elasticsearch installation and usage tutorial please go to: [https://github.com/bitshares/bitshares-core/wiki/ElasticSearch-Plugin](https://github.com/bitshares/bitshares-core/wiki/ElasticSearch-Plugin).

To avoid installation the API comes with public elasticsearch node that can be updated from config.

### BitShares node

This API backend connects to a BitShares `witness_node` to get data. Additionally from elasticsearch API makes use of the following bitshares plugins:

- `market_history`
- `grouped_orders`

The node must have `asset_api` and `orders_api` enabled.

`api-access.json`:

    {
       "permission_map" :
       [
          [
             "*",
             {
                "password_hash_b64" : "*",
                "password_salt_b64" : "*",
                "allowed_apis" : ["database_api", "network_broadcast_api", "history_api", "asset_api", "orders_api"]
             }
          ]
       ]
    }

To install a bitshares node please refer to: https://github.com/bitshares/bitshares-core/blob/master/README.md

You can use/change public bitshares API nodes for this by updating the config.

### Install BitShares Explorer API and dependencies

Install python and pip if you dont have them:

`apt-get install -y python python-pip`

Clone the app:

    git clone https://github.com/bitshares/bitshares-explorer-api
    cd bitshares-explorer-api/

Install virtual environment and setup:

    pip install virtualenv 
    virtualenv -p python3 wrappers_env/ 
    source wrappers_env/bin/activate

Deactivate with:

`deactivate`

Install dependencies in virtual env activated:

    pip install -r requirements/production.pip

Note: If you have errors in the output about websocket you may need to also do:

    apt-get install python-websocket

Note: If you see a problem similar to:

     WARNING:connexion.options:The swagger_ui directory could not be found.
        Please install connexion with extra install: pip install connexion[swagger-ui]
        or provide the path to your local installation by passing swagger_path=<your path>

You need to execute:
    
    pip install connexion[swagger-ui]

## Usage

### Simple running

In order to simply test and run the backend api you can do:

    export FLASK_APP=app.py
    flask run --host=0.0.0.0

Then go to apidocs with your IP:

[http://127.0.0.1:5000/apidocs/](http://127.0.0.1:5000/apidocs/)

### Nginx and uwsgi

In a production environment, when multiple requests start to happen at the same time, flask alone is not enough to handle the load. Nginx and uwsgi are alternatives to host a production backend.

Install nginx:

    apt-get install nginx

Install uwgsi:

    pip install uwsgi

Create config file in /etc/nginx/sites-available:

    server {
        listen 5000;
        server_name 185.208.208.184;
        location / {
            include uwsgi_params;
            uwsgi_pass unix:/tmp/app.sock;
        }
    }

Create symbolic link to sites-enabled and restart nginx:

    ln -s /etc/nginx/sites-available/api /etc/nginx/sites-enabled/api
    /etc/init.d/nginx restart

Now api can be started with:

    (wrappers) root@oxarbitrage ~/bitshares/bitshares-explorer-api # uwsgi --ini app.ini

### Profiler

To activate profiler use:

    PROFILER_ENABLED=true flask run

Then you will be able to access profiling data at `http://localhost:5000/profiler`.

By default the profiler is not protected, to add basic authentification add username and password in `config.py` or using environment variables `PROFILER_USERNAME` and `PROFILER_PASSWORD`.

### Development

To run the server in development mode to have an auto reload on code change:

    FLASK_ENV=development flask run

Run all tests:

    PYTHONPATH=. pytest

This will also run API tests (using [Tavern](https://taverntesting.github.io/)), that needs an local server to run, so make sure your development server is started.

To run one specific test:

    PYTHONPATH=. pytest -k test_ws_request

Or for API tests:

    PYTHONPATH=. py.test tests/test_api_explorer.tavern.yaml -k get_asset_holders_count

You can run API tests on a non localhost server using the command:

    PYTHONPATH=. py.test tavern-global-cfg=your_customized_environment.yaml tests/test_api_explorer.tavern.yaml

See `tests/local_urls.yaml` to see how to define a new environment.

And for non regression see `non_reg/README.md`
