"""Blackjack strategy implementations"""

import logging
import re
from abc import abstractmethod
from typing import List, Optional

from .core import Action, Hand

logger = logging.getLogger(__name__)


class Strategy:
    """Interface between game engine and strategy implementations."""

    def show_hand(self, hand: Hand):
        pass

    def show_result(self, hand: Hand, result: str):
        pass

    def get_bet(self, min_bet: int, bankroll: int) -> Optional[int]:
        """Return ``None`` to  terminate the game."""
        return min_bet

    @abstractmethod
    def get_action(
        self, hand: Hand, actions: List[Action], upcard: Optional[int] = None
    ) -> Action: ...


class Manual(Strategy):
    """Prompt user for strategy decisions."""

    _GET_BET_PROMPT = "Provide new bet or hit ENTER to use same bet (CTRL-C to quit)"

    def show_hand(self, hand: Hand):
        logger.info(hand)

    def show_result(self, hand: Hand, result: str):
        logger.info(f"{hand.name} Result: {result}")

    def get_bet(self, min_bet: int, bankroll: int) -> Optional[int]:
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        logger.info(f"Bankroll is ${bankroll}, minimum bet is ${min_bet}")

        try:
            bet_str = input(f"{self._GET_BET_PROMPT}\n")
        except KeyboardInterrupt:
            return None
        else:
            try:
                bet = int(bet_str)
            except ValueError:
                return min_bet
            else:
                return bet

    def get_action(
        self, hand: Hand, actions: List[Action], upcard: Optional[int] = None
    ) -> Action:
        assert actions
        assert not (hand.is_bust() or hand.is_blackjack())

        get_action_prompt = " ".join([str(a) for a in actions])
        while True:
            move_str = input(f"{get_action_prompt}\n").strip().lower()
            for action in actions:
                long_form = self._get_action_str_long_form(action)
                short_form = self._get_action_str_short_form(action)
                if move_str in [long_form, short_form]:
                    return action

            logger.error("Invalid input, try again")

    @staticmethod
    def _get_action_str_long_form(action: Action) -> str:
        return str(action).lower().replace("[", "").replace("]", "")

    @staticmethod
    def _get_action_str_short_form(action: Action) -> str:
        match = re.search(r"\[(.*?)\]", str(action).lower())
        assert match
        return match.group(1)


class Training(Manual):
    """Manual strategy with comparison to an automated strategy."""

    def __init__(self, strategy: Strategy):
        self._other = strategy

    def get_action(
        self, hand: Hand, actions: List[Action], upcard: Optional[int] = None
    ) -> Action:
        manual = super().get_action(hand, actions, upcard=upcard)
        automated = self._other.get_action(hand, actions, upcard=upcard)
        if manual == automated:
            logger.info("\u2705 Correct!")
        else:
            automated_str = super()._get_action_str_long_form(automated).title()
            logger.info(f"\u274c Incorrect! Correct choice: {automated_str}")

        return manual


class Dealer(Strategy):
    """Hit until 17, with an option to hit or stand on soft 17."""

    def __init__(self, hit_soft_seventeen: bool):
        self._hit_soft_seventeen = hit_soft_seventeen

    def get_action(
        self, hand: Hand, actions: List[Action], upcard: Optional[int] = None
    ) -> Action:
        assert (Action.HIT in actions) and (Action.STAND in actions)
        assert not (hand.is_bust() or hand.is_blackjack())

        if hand.value() < 17:
            return Action.HIT
        elif hand.value() > 17:
            return Action.STAND
        elif hand.is_soft() and self._hit_soft_seventeen:
            return Action.HIT
        else:
            return Action.STAND


class AlwaysHit(Strategy):
    """YOLO"""

    def get_action(
        self, hand: Hand, actions: List[Action], upcard: Optional[int] = None
    ) -> Action:
        assert Action.HIT in actions
        assert not (hand.is_bust() or hand.is_blackjack())

        return Action.HIT


class Basic(Strategy):
    """Basic strategy makes the optimal player decision for every hand.

    Adjustment for rule variations is not supported. The strategy assumes
    the default rule set from ``GameOptions()``. Implementation reference:
    <https://en.wikipedia.org/wiki/Blackjack#Basic_strategy>

    Implementation is basically a big look-up table.
    """

    def get_action(
        self, hand: Hand, actions: List[Action], upcard: Optional[int] = None
    ) -> Action:
        assert upcard
        assert not (hand.is_bust() or hand.is_blackjack())
        assert (Action.HIT in actions) and (Action.STAND in actions)

        can_surrender = Action.SURRENDER in actions
        can_double = Action.DOUBLE in actions
        can_split = Action.SPLIT in actions

        if can_split:
            return self._handle_split(hand[0].value, upcard, can_surrender, can_double)
        elif (len(hand) == 2) and hand.has_ace():
            other_card = hand[0] if hand[1].is_ace() else hand[1]
            return self._handle_soft_total(other_card.value, upcard, can_double)
        else:
            return self._handle_hard_total(
                hand.value(), upcard, can_surrender, can_double
            )

    @staticmethod
    def _handle_split(
        player: int, dealer: int, can_surrender: bool, can_double: bool
    ) -> Action:
        """Argument "player" is the value of one card in the pair."""
        if player == 11:
            return Action.SPLIT
        elif player == 10:
            return Action.STAND
        elif player == 9:
            if (2 <= dealer <= 9) and (dealer != 7):
                return Action.SPLIT
            else:
                return Action.STAND
        elif player == 8:
            if can_surrender and (dealer == 11):
                return Action.SURRENDER
            else:
                return Action.SPLIT
        elif player == 7:
            return Action.SPLIT if dealer <= 7 else Action.HIT
        elif player == 6:
            return Action.SPLIT if dealer <= 6 else Action.HIT
        elif player == 5:
            return Action.DOUBLE if can_double and (dealer <= 9) else Action.HIT
        elif player == 4:
            return Action.SPLIT if 5 <= dealer <= 6 else Action.HIT
        elif 2 <= player <= 3:
            return Action.SPLIT if dealer <= 7 else Action.HIT
        else:
            raise AssertionError("Incomplete strategy")

    @staticmethod
    def _handle_soft_total(player: int, dealer: int, can_double: bool) -> Action:
        """Argument "player" is the value of the non-Ace in the hand of 2 cards."""
        if player == 11:
            # Ace pair that can't be split (e.g. max split reached)
            return Action.DOUBLE if can_double and (dealer == 6) else Action.HIT
        elif player == 10:
            # Should never happen: This is blackjack and gets handled automatically
            raise AssertionError("Game engine bug")
        elif player == 9:
            return Action.STAND
        elif player == 8:
            return Action.DOUBLE if can_double and (dealer == 6) else Action.STAND
        elif player == 7:
            if dealer >= 9:
                return Action.HIT
            elif 7 <= dealer <= 8:
                return Action.STAND
            else:
                return Action.DOUBLE if can_double else Action.STAND
        elif player == 6:
            return Action.DOUBLE if can_double and (3 <= dealer <= 6) else Action.HIT
        elif 4 <= player <= 5:
            return Action.DOUBLE if can_double and (4 <= dealer <= 6) else Action.HIT
        elif 2 <= player <= 3:
            return Action.DOUBLE if can_double and (5 <= dealer <= 6) else Action.HIT
        else:
            raise AssertionError("Incomplete strategy")

    @staticmethod
    def _handle_hard_total(
        player: int, dealer: int, can_surrender: bool, can_double: bool
    ) -> Action:
        """Argument "player" is the hard total of the hand."""
        if player >= 18:
            return Action.STAND
        elif player == 17:
            if dealer == 11:
                return Action.SURRENDER if can_surrender else Action.STAND
            else:
                return Action.STAND
        elif player == 16:
            if dealer <= 6:
                return Action.STAND
            elif dealer <= 8:
                return Action.HIT
            else:
                return Action.SURRENDER if can_surrender else Action.HIT
        elif player == 15:
            if dealer <= 6:
                return Action.STAND
            elif dealer <= 9:
                return Action.HIT
            else:
                return Action.SURRENDER if can_surrender else Action.HIT
        elif 13 <= player <= 14:
            return Action.STAND if dealer <= 6 else Action.HIT
        elif player == 12:
            return Action.STAND if 4 <= dealer <= 6 else Action.HIT
        elif player == 11:
            return Action.DOUBLE if can_double else Action.HIT
        elif player == 10:
            if dealer <= 9:
                return Action.DOUBLE if can_double else Action.HIT
            else:
                return Action.HIT
        elif player == 9:
            if 3 <= dealer <= 6:
                return Action.DOUBLE if can_double else Action.HIT
            else:
                return Action.HIT
        elif 4 <= player <= 8:
            return Action.HIT
        else:
            raise AssertionError("Incomplete strategy")
