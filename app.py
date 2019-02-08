import connexion
import logging

logging.basicConfig()

options = {'swagger_url': '/apidocs'}
# strict_validation=True: requests that include parameters not defined return a 400 error
app = connexion.App('bitshares-explorer-api', specification_dir='swagger/', options=options)

from flask_cors import CORS
CORS(app.app)

from services.cache import cache
cache.init_app(app.app)

from specsynthase.specbuilder import SpecBuilder
import glob
from os import path

spec = SpecBuilder()
for spec_file in glob.glob(path.join(path.dirname(__file__), 'swagger/*')):
    spec.add_spec(spec_file)
app.add_api(spec)

import services.profiler
services.profiler.init_app(app.app)

application = app.app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)


