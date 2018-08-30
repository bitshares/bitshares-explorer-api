# BitShares Explorer REST API

BitShares Explorer REST API is the backend service of the BitShares explorer that retrieve the infotmation from the blockchain.  

http://185.208.208.184:5000/apidocs/

Index:

- [BitShares Explorer REST API](#bitshares-explorer-rest-api)
    - [Installation](#installation)
        - [Manual](#manual)
            - [Install ElasticSearch](#install-elasticsearch)
            - [Install a BitShares node with requirements.](#install-a-bitshares-node-with-requirements)
            - [Install and setup postgres.](#install-and-setup-postgres)
            - [Install BitShares Explorer API and dependencies.](#install-bitshares-explorer-api-and-dependencies)
            - [Real Time ops grabber](#real-time-ops-grabber)
            - [Cronjobs](#cronjobs)
            - [Simple running](#simple-running)
            - [Nginx and uwsgi](#nginx-and-uwsgi)
            - [Domain setup and SSL](#domain-setup-and-ssl)
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

For full elasticsearch installation and usage tutorial please go to: https://github.com/bitshares/bitshares-core/wiki/ElasticSearch-Plugin

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

#### Install a BitShares node with requirements.

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

#### Install and setup postgres.

Postgres is needed as a helper to store some data as stats we want to have and takes too much time to do client side so they are made once a day with cronjobs. Data is saved to postgres and available all the time to serve REST calls.

It is expected that the use of postgres gets deprecated in future versions of this program, most likely with the introduction of `es_objects` plugin.

By now, you need postgres, install by:

`apt-get install postgresql`

Make sure postgres is up and running. Start with `/etc/init.d/postgresql start`.
If you get a warning of no cluster solve with:

`pg_createcluster 9.4 main --start`

where `9.4` is your postgres version.

Create username and database:

    su postgres
    createuser postgres
    createdb explorer
    psql
    psql=# alter user postgres with encrypted password 'posta';
    psql=# grant all privileges on database explorer to postgres ;

Import schema:

    cd 
    wget https://raw.githubusercontent.com/oxarbitrage/explorer-api/master/postgres/schema.txt
    psql explorer < schema.txt

Check your database tables were created:

    postgres@oxarbitrage:~$ psql -d explorer
    psql (9.5.12)
    Type "help" for help.
    explorer=# \dt
               List of relations
     Schema |   Name    | Type  |  Owner   
    --------+-----------+-------+----------
     public | assets    | table | postgres
     public | holders   | table | postgres
     public | markets   | table | postgres
     public | ops       | table | postgres
     public | proxies   | table | postgres
     public | referrers | table | postgres
     public | stats     | table | postgres
    (7 rows)
    
    explorer=# select * from ops;
     oid | oh | ath | block_num | trx_in_block | op_in_trx | datetime | account_id | account_name | op_type 
    -----+----+-----+-----------+--------------+-----------+----------+------------+--------------+---------
    (0 rows)
    
    explorer=# 

#### Install BitShares Explorer API and dependencies.

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

If you have errors in the output about websocket or psycopg you may need to also do:
```
apt-get install python-websocket
apt-get install python-psycopg2
```

#### Real Time ops grabber

<strike>
First step to check if everything is correctly installed is by installing the real time operation grabber. This will subscribe by websocket to the bitshares-core backend and add every operation broadcasted by the node into the postgres database. This data is cleaned at the end of the day by one of the cronjobs, during that time data stored is used for daily calculations of network state.
</strike>


<strike>
  
Make sure you have `PYTHONPATH` set up and run the following command(can be in a `screen` session as the script will have to run permanently, can run in the background, can be added to init, etc:
</strike>

`python postgres/import_realtime_ops.py`


<strike>
You should see some output of sql queries being sent to postgres, make sure data is inserted by `select * from ops;` inside postgres `explorer` database.
</strike>

The realtime ops grabber had been deprecated by elasticsearch.

#### Cronjobs

Similar as postgres, it is expected that the cronjobs will not be needed in the future but by now, they are.

Add the following taks to cron file with `crontab -e`:

    0 1 * * *  export PYTHONPATH=/root/bitshares/bitshares-explorer-api; /root/bitshares/wrappers/bin/python /root/bitshares/bitshares-explorer-api/postgres/import_holders.py > /tmp/cronlog_holders.txt 2>&1 
    0 2 * * *  export PYTHONPATH=/root/bitshares/bitshares-explorer-api; /root/bitshares/wrappers/bin/python /root/bitshares/bitshares-explorer-api/postgres/import_assets.py > /tmp/cronlog_assets.txt 2>&1
    15 2 * * * export PYTHONPATH=/root/bitshares/bitshares-explorer-api; /root/bitshares/wrappers/bin/python /root/bitshares/bitshares-explorer-api/postgres/import_markets.py > /tmp/cronlog_markets.txt 2>&1
    30 2 * * * export PYTHONPATH=/root/bitshares/bitshares-explorer-api; /root/bitshares/wrappers/bin/python /root/bitshares/bitshares-explorer-api/postgres/import_referrers.py > /tmp/cronlog_refs.txt 2>&1
                                                  
    
#### Simple running

In order to simply test and run the backend api you can do:

    export FLASK_APP=app.py
    flask run --host=0.0.0.0

Then go to apidocs with your server external address:

http://185.208.208.184:5000/apidocs/

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

#### Domain setup and SSL

[Todo]


### Docker

Installation is too long, docker is here to automate this things. [Todo]

## Usage

There are a lot of ways and application for this collection of API calls, at the moment of writing there are mainly 2 use cases.

### Swagger

http://185.208.208.184:5000/apidocs/

Allows to make calls directly from that address by changing the parameters of the request and getting the results. This is very convenient to make quick calls to the blockchain looking for specific data. 

### Profiler

To activate profiler use:

    PROFILER_ENABLED=true flask run

Then you will be able to access profiling data at `http://localhost:5000/profiler`.

By default the profiler is not protected, to add basic authentification add username and password in `config.py` or using environment variables `PROFILER_USERNAME` and `PROFILER_PASSWORD`.


### Open Explorer

- http://open-explorer.io
- http://bitshares-explorer.io/
- http://bitshares-testnet.xyz

All versions of open-explorer uses this backend to get data.

### Development

Run tests:

```
PYTHONPATH=. pytest
```

And for non regression see `non_reg/README.md`
