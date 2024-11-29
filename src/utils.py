from enum import Enum


class Axis(Enum):
    ROW = 0
    COLUMN = 1

class Order(Enum):
    MINIMUM = -1
    NEUTRAL = 0
    MAXIMUM = 1