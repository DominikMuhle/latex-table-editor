from dataclasses import dataclass
from enum import Enum
from typing import Union, get_args, get_origin


class Axis(str, Enum):
    ROW = "row"
    COLUMN = "column"


class Order(str, Enum):
    MINIMUM = "min"
    NEUTRAL = "neutral"
    MAXIMUM = "max"


@dataclass
class Rule:
    order: Order | None = None
    highlighting: list[str] | None = None
    default: str | None = None
    precision: int | None = None

    def __setattr__(self, name, value):
        expected_type = self.__annotations__.get(name)
        if expected_type is not None and value is not None:
            if not self._is_instance_of(value, expected_type):
                raise TypeError(f"Attribute '{name}' must be of type {expected_type}, got {type(value)}")
        super().__setattr__(name, value)

    def _is_instance_of(self, value, expected_type):
        origin = get_origin(expected_type)
        args = get_args(expected_type)
        if len(args) > 1:
            return any(self._is_instance_of(value, arg) for arg in args)
        if origin is Union:
            return any(self._is_instance_of(value, arg) for arg in args)
        elif origin is list:
            return isinstance(value, list) and all(isinstance(item, args[0]) for item in value)
        elif origin is float:
            return isinstance(value, float)
        elif origin is int:
            return isinstance(value, int)
        else:
            return isinstance(value, expected_type)

DEFAULT_RULES = Rule(
    order=Order.NEUTRAL,
    highlighting=["\\bfseries{%s}", "\\underline{%s}"],
    default="%s",
    precision=2,  # Updated default precision to an integer
)

