from typing import get_args, get_origin
from enum import Enum


class Axis(str, Enum):
    ROW = "row"
    COLUMN = "column"


class Order(str, Enum):
    MINIMUM = "min"
    NEUTRAL = "neutral"
    MAXIMUM = "max"


AVAILABLE_RULES = {
    "order": Order | str,
    "highlight": list[str],
    "default": str,
    "precision": int,
}
RULE_TYPES = Order | str | list[str]
RULES = dict[str, RULE_TYPES]

def is_instance_of_union(var, union_type):
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


def filter_rule_keys(rules: RULES) -> tuple[RULES, list[str]]:
    """Filter out the keys that are not available in the rules dictionary"""
    pop_keys = []
    for key in rules.keys():
        if key not in AVAILABLE_RULES:
            pop_keys.append(key)
    for key in pop_keys:
        rules.pop(key)
        
    return rules, pop_keys
