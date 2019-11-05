from functools import wraps
import elasticsearch
from flask import abort


def index_exists(es, index_name):
    if not es.indices.exists(index=index_name):
        raise Exception("Index does not exist")


def needs_es(index_name=None):

    def inner_function(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if index_name is not None:
                # TODO pre-check, might not be necessary
                pass
            try:
                return function(*args, **kwargs)
            except elasticsearch.exceptions.NotFoundError as e:
                not_found = getattr(e, "info", {}).get("error", {}).get("root_cause", [{}])[0].get("resource.id", None)
                message = "The required index does not exist in this ElasticSearch database"
                if not_found is not None:
                    message = message + " (" + str(not_found) + ")"
                print(message)
                abort(404, message)
        return wrapper

    return inner_function
