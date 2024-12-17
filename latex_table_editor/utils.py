from dataclasses import dataclass
from enum import Enum
from typing import get_args, get_origin


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
    precision: str | None = None

DEFAULT_RULES = Rule(
    order=Order.NEUTRAL,
    highlighting=["\\bfseries{%s}", "\\underline{%s}"],
    default="%s",
    precision="%.2f",
)


def is_instance_of(var, var_type):
    """Check if a variable is an instance of a type"""

    # check if var_type is a union
    if len(get_args(var_type)) == 0:
        return isinstance(var, var_type)
    else:
        return is_instance_of_union(var, var_type)


def is_instance_of_union(var, union_type):
    """Check if a variable is an instance of a union type"""
    for typ in get_args(union_type):
        origin = get_origin(typ)
        if origin is None:
            if isinstance(var, typ):
                return True
        elif isinstance(var, origin):
            args = get_args(typ)
            if all(isinstance(item, args[0]) for item in var):
                return True
    return False


def filter_rule_keys(rules: dict[str, Rule]) -> tuple[dict[str, Rule], list[str]]:
    """Filter out the keys that are not available in the rules dictionary"""
    pop_keys = []
    for key in rules.keys():
        if key not in DEFAULT_RULES.__annotations__:
            pop_keys.append(key)
    for key in pop_keys:
        rules.pop(key)

    return rules, pop_keys
