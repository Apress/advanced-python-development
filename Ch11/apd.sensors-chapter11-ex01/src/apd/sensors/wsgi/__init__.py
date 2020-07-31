import flask

try:
    from flask_sqlalchemy import SQLAlchemy
except ImportError:
    sql_support = False
else:
    sql_support = True


from .base import set_up_config
from . import v10
from . import v20
from . import v21
from . import v30


__all__ = ["app", "set_up_config", "db"]

app = flask.Flask(__name__)
app.register_blueprint(v10.version, url_prefix="/v/1.0")
app.register_blueprint(v20.version, url_prefix="/v/2.0")
app.register_blueprint(v21.version, url_prefix="/v/2.1")
app.register_blueprint(v30.version, url_prefix="/v/3.0")

if sql_support:
    from apd.sensors.database import metadata

    db = SQLAlchemy(app, metadata=metadata)
else:
    db = None
