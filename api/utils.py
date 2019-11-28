from functools import wraps
from elasticsearch.exceptions import NotFoundError
from flask import abort


def index_exists(es, index_name):
    if not es.indices.exists(index=index_name):
        raise Exception("Index does not exist")


def needs_es(index_name=None):
    def inner_function(function=None):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if index_name is not None:
                # TODO pre-check, might not be necessary
                pass
            try:
                return function(*args, **kwargs)
            except NotFoundError as e:
                not_found = getattr(e, "info", {}).get("error", {}).get("root_cause", [{}])[0].get("resource.id", None)
                message = "The required index does not exist in this ElasticSearch database"
                if not_found is not None:
                    message = message + " (" + str(not_found) + ")"
                abort(404, message)
        return wrapper

    if index_name is not None and not isinstance(index_name, str):
        return inner_function(index_name)
    else:
        return inner_function


def verify_es_response(response):
    # if the query took 0 it means no index could be matched!
    if response.took == 0:
        raise NotFoundError(404, 'index_not_found_exception', {})

    # if no hits were found, operation_id was invalied
    if len(response.hits) == 0:
        abort(404, "Your search did not result in any hits (wrong id?)")
