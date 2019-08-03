# BitShares Explorer REST API

BitShares Explorer REST API is the backend service of the BitShares explorer that retrieve the infotmation from the blockchain.  

[http://185.208.208.184:5000/apidocs/](http://185.208.208.184:5000/apidocs/)

[https://explorer.bitshares-kibana.info/apidocs/](https://explorer.bitshares-kibana.info/apidocs/)

Index:

- [BitShares Explorer REST API](#bitshares-explorer-rest-api)
  - [Installation](#installation)
    - [Manual](#manual)
      - [Install ElasticSearch](#install-elasticsearch)
      - [Install a BitShares node with requirements](#install-a-bitshares-node-with-requirements)
      - [Install BitShares Explorer API and dependencies](#install-bitshares-explorer-api-and-dependencies)
      - [Simple running](#simple-running)
      - [Nginx and uwsgi](#nginx-and-uwsgi)
    - [Docker](#docker)
  - [Usage](#usage)
    - [Swagger](#swagger)
    - [Profiler](#profiler)
    - [Open Explorer](#open-explorer)
    - [Development](#development)

## Installation

The following procedure will work in Debian based Linux, more specifically the commands to make the guide were executed in `Ubuntu 16.04.4 LTS` with `Python 2.7`.

### Manual

Step by step on everything needed to have your own BitShares Explorer API up and running for a production environment.

#### Install ElasticSearch

For full elasticsearch installation and usage tutorial please go to: [https://github.com/bitshares/bitshares-core/wiki/ElasticSearch-Plugin](https://github.com/bitshares/bitshares-core/wiki/ElasticSearch-Plugin).

The following is a  quick installation guide for elasticsearch in Ubuntu.

Install the requirements:

    apt-get install default-jre
    apt-get install default-jdk
    apt-get install software-properties-common
    add-apt-repository ppa:webupd8team/java
    apt-get update
    apt-get install oracle-java8-installer
    apt-get install unzip
    apt-get install libcurl4-openssl-dev

Add an elasticsearch account to the system as the database can not run by root:

    root@oxarbitrage ~ # adduser elastic
    Adding user `elastic' ...
    Adding new group `elastic' (1000) ...
    Adding new user `elastic' (1000) with group `elastic' ...
    Creating home directory `/home/elastic' ...
    Copying files from `/etc/skel' ...
    Enter new UNIX password: 
    Retype new UNIX password: 
    passwd: password updated successfully
    Changing the user information for elastic
    Enter the new value, or press ENTER for the default
            Full Name []: 
            Room Number []: 
            Work Phone []: 
            Home Phone []: 
            Other []: 
    Is the information correct? [Y/n] 
    root@oxarbitrage ~ # 

Download and run elasticsearch  database:

    root@oxarbitrage ~ # su elastic
    elastic@oxarbitrage:/root$ cd
    elastic@oxarbitrage:~$ 
    elastic@oxarbitrage:~$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.2.4.zip
    elastic@oxarbitrage:~$ unzip elasticsearch-6.2.0.zip
    elastic@oxarbitrage:~$ cd elasticsearch-6.2.0
    elastic@oxarbitrage:~$ ./bin/elasticsearch

Stop the program with ctrl-c, daemonize and forget:

    elastic@oxarbitrage:~$ ./elasticsearch-6.2.0/bin/elasticsearch --daemonize
    elastic@oxarbitrage:~$ netstat -an | grep 9200
    tcp6       0      0 127.0.0.1:9200          :::*                    LISTEN     
    tcp6       0      0 ::1:9200                :::*                    LISTEN     
    elastic@oxarbitrage:~$ 

#### Install a BitShares node with requirements

This API backend connects to a BitShares `witness_node` to get data. This witness node must be configured with the following plugins:

- `market_history`
- `grouped_orders`
- `elasticsearch`

Additionally, the node must have `asset_api` and `orders_api` enabled(off by default).

First download and build `bitshares-core`:

    git clone https://github.com/bitshares/bitshares-core.git
    cd bitshares-core/
    
    git submodule update --init --recursive
    cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo .
    make

Next, create `api-access.json` file as shown:

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

Finally run the start command with the required plugins and api-access.json, please note elasticsearch must be running on port 9200 of localhost in order for this command to work:

    programs/witness_node/witness_node --data-dir blockchain --rpc-endpoint "127.0.0.1:8091" --plugins "witness elasticsearch market_history grouped_orders" --api-access /full/path/to/api-access.json

If you adding the wrapper to a testnet/private network backend you will need to change a bit the elasticsearch default parameters to start getting data faster. For example a testnet setup command may look as:

    programs/witness_node/witness_node --data-dir blockchain --rpc-endpoint "127.0.0.1:8091" --plugins "witness elasticsearch market_history grouped_orders" --elasticsearch-bulk-replay 1000 elasticsearch-bulk-sync 10 --elasticsearch-logs true --elasticsearch-visitor true --api-access /full/path/to/api-access.json

Check if it is working with:

    curl -X GET 'http://localhost:9200/graphene-*/data/_count?pretty=true' -H 'Content-Type: application/j
    son' -d '
    {
        "query" : {
            "bool" : { "must" : [{"match_all": {}}] }
        }
    }
    '

note: ask @clockwork about performance increment suggested for mainnet and elasticsearch.

#### Install BitShares Explorer API and dependencies

Install python and pip:

`apt-get install -y python python-pip`

Clone the app:

    git clone https://github.com/oxarbitrage/bitshares-explorer-api
    cd bitshares-explorer-api/

Install virtual environment and setup:

    pip install virtualenv 
    virtualenv -p python2 wrappers_env/ 
    source wrappers_env/bin/activate

Now you are in an isolated environment where you install dependencies with `pip install` without affecting anything else or creating version race conditions.
You can also simply switch or recreate the environment by deleting the env folder that will be created in your working directory.

    root@oxarbitrage ~/bitshares #  source wrappers_env/bin/activate
    (wrappers_env) root@oxarbitrage ~/bitshares # 

Deactivate with:

`deactivate`

Install dependencies in virtual env activated:

    pip install -r requirements/production.pip

To run the api, always need to have the full path to program in `PYTHONPATH` environment variable exported:

`export PYTHONPATH=/root/bitshares/bitshares-explorer-api`

If you have errors in the output about websocket you may need to also do:

    apt-get install python-websocket

If you see a problem similar to:

     WARNING:connexion.options:The swagger_ui directory could not be found.
        Please install connexion with extra install: pip install connexion[swagger-ui]
        or provide the path to your local installation by passing swagger_path=<your path>

You need to execute:
`pip install connexion[swagger-ui]`

#### Simple running

In order to simply test and run the backend api you can do:

    export FLASK_APP=app.py
    flask run --host=0.0.0.0

Then go to apidocs with your server external address:

[http://185.208.208.184:5000/apidocs/](http://185.208.208.184:5000/apidocs/)

#### Nginx and uwsgi

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

Another common error is currently:

    WARNING:connexion.options:The swagger_ui directory could not be found.
    Please install connexion with extra install: pip install connexion[swagger-ui]
    or provide the path to your local installation by passing swagger_path=<your path>

### Docker

Installation is too long, docker is here to automate this things. [Todo]

## Usage

There are a lot of ways and application for this collection of API calls, at the moment of writing there are mainly 2 use cases.

### Swagger

[http://185.208.208.184:5000/apidocs/](http://185.208.208.184:5000/apidocs/)

[https://explorer.bitshares-kibana.info/apidocs/](https://explorer.bitshares-kibana.info/apidocs/)

Allows to make calls directly from that address by changing the parameters of the request and getting the results. This is very convenient to make quick calls to the blockchain looking for specific data.

### Profiler

To activate profiler use:

    PROFILER_ENABLED=true flask run

Then you will be able to access profiling data at `http://localhost:5000/profiler`.

By default the profiler is not protected, to add basic authentification add username and password in `config.py` or using environment variables `PROFILER_USERNAME` and `PROFILER_PASSWORD`.

### Open Explorer

- [http://open-explorer.io](http://open-explorer.io)
- [http://bitshares-explorer.io/](http://bitshares-explorer.io/)
- [http://bitshares-testnet.xyz](http://bitshares-testnet.xyz)

All versions of open-explorer uses this backend to get data.

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
