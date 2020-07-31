from hmac import compare_digest
import functools
import os
import typing as t

import flask


ViewFuncReturn = t.TypeVar("ViewFuncReturn")
ErrorReturn = t.Tuple[t.Dict[str, str], int]
REQUIRED_CONFIG_KEYS = {"APD_SENSORS_API_KEY"}


def require_api_key(
    func: t.Callable[[], ViewFuncReturn]
) -> t.Callable[[], t.Union[ViewFuncReturn, ErrorReturn]]:
    @functools.wraps(func)
    def wrapped() -> t.Union[ViewFuncReturn, ErrorReturn]:
        api_key = flask.current_app.config["APD_SENSORS_API_KEY"]
        headers = flask.request.headers
        supplied_key = headers.get("X-API-Key", "")
        if not compare_digest(api_key, supplied_key):
            return {"error": "Supply API key in X-API-Key header"}, 403
        return func()

    return wrapped


def set_up_config(
    environ: t.Optional[t.Dict[str, str]] = None,
    to_configure: t.Optional[flask.Flask] = None,
) -> flask.Flask:
    if environ is None:
        environ = dict(os.environ)
    if to_configure is None:
        from apd.sensors.wsgi import app

        to_configure = app
    missing_keys = REQUIRED_CONFIG_KEYS - environ.keys()
    if missing_keys:
        raise ValueError("Missing config variables: {}".format(", ".join(missing_keys)))
    to_configure.config.from_mapping(environ)
    return to_configure
