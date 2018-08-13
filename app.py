from flask_cors import CORS
import connexion

options = {'swagger_url': '/apidocs'}
app = connexion.FlaskApp('bitshares-explorer-api', options=options)
CORS(app.app)
app.add_api('api.yaml')
application = app.app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)


