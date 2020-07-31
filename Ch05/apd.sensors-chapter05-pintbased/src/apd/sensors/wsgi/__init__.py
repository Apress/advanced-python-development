import flask

from .base import set_up_config
from . import v10
from . import v20


__all__ = ["app", "set_up_config"]

app = flask.Flask(__name__)
app.register_blueprint(v10.version, url_prefix="/v/1.0")
app.register_blueprint(v20.version, url_prefix="/v/2.0")
