from elasticsearch import Elasticsearch
import config

if      'user' in config.ELASTICSEARCH and config.ELASTICSEARCH['user'] \
    and 'password' in config.ELASTICSEARCH and config.ELASTICSEARCH['password']:
    es = Elasticsearch(config.ELASTICSEARCH['hosts'], \
                        http_auth=(config.ELASTICSEARCH['user'], config.ELASTICSEARCH['password']),\
                        timeout=60)
else:
    es = Elasticsearch(config.ELASTICSEARCH['hosts'], timeout=60)
