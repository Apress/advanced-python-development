from contextvars import ContextVar
import functools
import logging

sensorname_var = ContextVar("sensorname", default="none")

def add_sensorname_record_factory(existing_factory, *args, **kwargs):
    record = existing_factory(*args, **kwargs)
    record.sensorname = sensorname_var.get()
    return record

def add_record_factory_wrapper(fn):
    old_factory = logging.getLogRecordFactory()
    wrapped = functools.partial(fn, old_factory)
    logging.setLogRecordFactory(wrapped)

add_record_factory_wrapper(add_sensorname_record_factory)
logging.basicConfig(
    format="[{sensorname}/{levelname}] - {message}", style="{", level=logging.INFO
)

