from enum import Enum


class Axis(str, Enum):
    ROW = "row"
    COLUMN = "column"

class Order(str, Enum):
    MINIMUM = "min"
    NEUTRAL = "neutral"
    MAXIMUM = "max"