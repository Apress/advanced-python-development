#!/usr/bin/env python
# coding: utf-8
import typing as t


JSON_0 = t.Union[str, int, float, bool, None]
JSON_1 = t.Union[t.Dict[str, JSON_0], t.Iterable[JSON_0], JSON_0]
JSON_2 = t.Union[t.Dict[str, JSON_1], t.Iterable[JSON_1], JSON_1]
JSON_3 = t.Union[t.Dict[str, JSON_2], t.Iterable[JSON_2], JSON_2]
JSON_4 = t.Union[t.Dict[str, JSON_3], t.Iterable[JSON_3], JSON_3]
JSON_5 = t.Union[t.Dict[str, JSON_4], t.Iterable[JSON_4], JSON_4]
JSON_like = JSON_5


T_value = t.TypeVar("T_value")
JSONT_value = t.TypeVar("JSONT_value", bound=JSON_like)


class Sensor(t.Generic[T_value]):
    name: str
    title: str

    def value(self) -> T_value:
        raise NotImplementedError

    @classmethod
    def format(cls, value: T_value) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.format(self.value())

    @classmethod
    def to_json_compatible(cls, value: T_value) -> JSON_like:
        raise NotImplementedError()

    @classmethod
    def from_json_compatible(cls, json_version: JSON_like) -> T_value:
        raise NotImplementedError()


class JSONSensor(Sensor[JSONT_value]):
    @classmethod
    def to_json_compatible(cls, value: JSONT_value) -> JSONT_value:
        return value

    @classmethod
    def from_json_compatible(cls, json_version: JSON_like) -> JSONT_value:
        return t.cast(JSONT_value, json_version)


version_info_type = t.NamedTuple(
    "version_info_type",
    [
        ("major", int),
        ("minor", int),
        ("micro", int),
        ("releaselevel", str),
        ("serial", int),
    ],
)
