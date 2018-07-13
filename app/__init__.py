from flask import Flask
from werkzeug.wsgi import DispatcherMiddleware
from config import load_config
from flask_basicauth import BasicAuth
from flask_cors import CORS

app = Flask(__name__)
cfg = load_config()
app.config.from_object(cfg)

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    app.config['APPLICATION_ROOT']: app,
})
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

from api import api
from .util import *
basic_auth = BasicAuth(app)
app.register_blueprint(api, url_prefix='/api')