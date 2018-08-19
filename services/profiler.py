import flask_profiler
import config

def init_app(app):
    app.config["flask_profiler"] = {
        "enabled": config.PROFILER['enabled'],
        "storage": {
            "engine": "sqlite"
        },
        "endpointRoot": "profiler",
        "basicAuth":{
            "enabled": bool(config.PROFILER['password']),
            "username": config.PROFILER['username'],
            "password": config.PROFILER['password']
        },
        "ignore": [
            "^/static/.*"
        ]
    }
    flask_profiler.init_app(app)
