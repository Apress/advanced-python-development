from . import app
from .base import set_up_config

if __name__ == "__main__":
    import wsgiref.simple_server

    set_up_config(None, app)

    with wsgiref.simple_server.make_server("", 8000, app) as server:
        server.serve_forever()
