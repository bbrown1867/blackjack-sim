"""Core blackjack classes"""

from dataclasses import dataclass
from enum import StrEnum
from typing import List, Tuple


class Action(StrEnum):
    HIT = "[H]it"
    STAND = "[S]tand"
    SURRENDER = "Su[r]render"
    DOUBLE = "[D]ouble"
    SPLIT = "S[p]lit"


@dataclass
class Card:
    name: str
    value: int

    def __repr__(self) -> str:
        return self.name

    def is_ace(self) -> bool:
        return self.value == 11


class Hand(List[Card]):
    def __init__(self, cards: List[Card], name: str = "", wager: int = 0):
        self._name = name
        self._wager = wager
        self._surrender = False
        super().__init__(cards)

    def __repr__(self) -> str:
        prefix = self._name + ": " if self._name else ""
        return prefix + "  ".join([c.name for c in self])

    @property
    def name(self) -> str:
        return self._name

    @property
    def wager(self) -> float:
        return self._wager

    def _value(self) -> Tuple[int, bool]:
        value = sum([c.value for c in self])
        ace_count = sum([c.is_ace() for c in self])
        while value > 21 and ace_count:
            value -= 10
            ace_count -= 1

        return value, (ace_count > 0)

    def value(self) -> int:
        return self._value()[0]

    def is_soft(self) -> bool:
        return self._value()[1]

    def has_ace(self) -> bool:
        return any(c.is_ace() for c in self)

    def is_bust(self) -> bool:
        return self.value() > 21

    def is_blackjack(self) -> bool:
        return self.value() == 21

    def can_split(self) -> bool:
        return (len(self) == 2) and (self[0].name[0] == self[1].name[0])

    def double(self):
        self._wager *= 2

    def surrender(self):
        self._surrender = True

    def is_surrender(self) -> bool:
        return self._surrender
