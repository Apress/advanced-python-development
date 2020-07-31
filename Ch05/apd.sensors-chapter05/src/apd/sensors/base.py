#!/usr/bin/env python
# coding: utf-8
import typing as t


T_value = t.TypeVar("T_value")


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
    def to_json_compatible(cls, value: T_value) -> t.Any:
        raise NotImplementedError()

    @classmethod
    def from_json_compatible(cls, json_version: t.Any) -> T_value:
        raise NotImplementedError()


class JSONSensor(Sensor[T_value]):
    @classmethod
    def to_json_compatible(cls, value: T_value) -> t.Any:
        return value

    @classmethod
    def from_json_compatible(cls, json_version: t.Any) -> T_value:
        return t.cast(T_value, json_version)


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
