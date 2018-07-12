from flask import Flask
from werkzeug.wsgi import DispatcherMiddleware
from config import load_config

app = Flask(__name__)
cfg = load_config()
app.config.from_object(cfg)

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    app.config['APPLICATION_ROOT']: app,
})

from api import api

app.register_blueprint(api, url_prefix='/api')