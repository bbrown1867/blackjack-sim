"""Blackjack game engine"""

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .core import Action, Card, Hand
from .strategy import Dealer, Strategy


class EmptyShoeError(IndexError): ...


class Shoe(List[Card]):
    _SUITS = ["\u2660\ufe0f", "\u2665\ufe0f", "\u2666\ufe0f", "\u2663\ufe0f"]
    _FACES = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]

    def __init__(self, num_decks: int):
        self._num_cards = num_decks * 52

        cards = []
        for _ in range(num_decks):
            for suit in self._SUITS:
                for face in self._FACES:
                    if face == "A":
                        value = 11
                    elif face in ["T", "J", "Q", "K"]:
                        value = 10
                    else:
                        value = int(face)

                    cards.append(Card(f"{face}{suit}", value))

        super().__init__(cards)
        random.shuffle(self)

    def percent_full(self) -> float:
        return (len(self) / self._num_cards) * 100.0

    def draw(self) -> Card:
        try:
            return self.pop()
        except IndexError:
            raise EmptyShoeError(
                "Empty shoe: Increase num decks or min shoe percent to avoid this"
            )


@dataclass
class GameOptions:
    min_bet: int = 10
    payout: float = 1.5
    num_decks: int = 6
    shoe_min_percent: float = 20.0
    hit_soft_seventeen: bool = False
    double_after_split: bool = True
    late_surrender: bool = True
    max_split: int = 2


class Game:
    def __init__(self, options: Optional[GameOptions] = None):
        # Game config
        self._options = GameOptions() if not options else options

        # Game state
        self._bankroll = 0.0
        self._total_bet = 0
        self._shoe: Optional[Shoe] = None
        self._strategy: Optional[Strategy] = None
        self._upcard: Optional[int] = None

    def _make_bet(self, bet: int):
        assert self._bankroll >= bet

        self._bankroll -= bet
        self._total_bet += bet

    def _draw_card(self, hand: Hand, is_upcard: bool = False, show_hand: bool = True):
        assert self._shoe

        card = self._shoe.draw()
        hand.append(card)
        if is_upcard:
            self._upcard = card.value
        if show_hand and self._strategy:
            self._strategy.show_hand(hand)

    def _play_hand(
        self, strategy: Strategy, hand: Hand, bet: int, num_split: int
    ) -> List[Hand]:
        actions = [Action.HIT, Action.STAND]
        if len(hand) == 2:
            if self._options.late_surrender and (num_split == 0):
                actions.append(Action.SURRENDER)

            if self._bankroll >= bet:
                if self._options.double_after_split or (num_split == 0):
                    actions.append(Action.DOUBLE)

                if hand.can_split() and (num_split < self._options.max_split):
                    actions.append(Action.SPLIT)

        action = strategy.get_action(hand, actions, upcard=self._upcard)
        assert action in actions, f"Invalid action: {action}"

        if action == Action.HIT:
            self._draw_card(hand)
            if not (hand.is_bust() or hand.is_blackjack()):
                return self._play_hand(strategy, hand, bet, num_split)
        elif action == Action.STAND:
            pass
        elif action == Action.SURRENDER:
            hand.surrender()
        elif action == Action.DOUBLE:
            self._make_bet(bet)
            self._draw_card(hand)
            hand.double()
        elif action == Action.SPLIT:
            self._make_bet(bet)
            new_hands = []
            for i in range(2):
                new_hand = Hand([hand[i]], name=f"{hand.name} Split {i + 1}", wager=bet)
                self._draw_card(new_hand)
                if hand.has_ace():
                    # Game rule: Must stand after splitting Aces
                    new_hands.append(new_hand)
                else:
                    new_hands += self._play_hand(strategy, new_hand, bet, num_split + 1)

            return new_hands

        else:
            raise AssertionError(f"Invalid action: {action}")

        return [hand]

    def _compare_hands(self, player_hand: Hand, dealer_hand: Hand):
        assert self._strategy

        if player_hand.is_bust():
            self._strategy.show_result(player_hand, "Player bust")
        elif dealer_hand.is_bust():
            self._strategy.show_result(player_hand, "Dealer bust")
            self._bankroll += 2.0 * player_hand.wager
        else:
            pv = player_hand.value()
            dv = dealer_hand.value()
            if pv > dv:
                self._strategy.show_result(player_hand, f"Player wins ({pv} > {dv})")
                self._bankroll += 2.0 * player_hand.wager
            elif pv == dv:
                self._strategy.show_result(player_hand, f"Push ({pv} = {dv})")
                self._bankroll += player_hand.wager
            else:
                self._strategy.show_result(player_hand, f"Dealer wins ({pv} < {dv})")

    def _play_round(self, bet: int):
        assert self._strategy

        # Deal initial hands
        player_hand = Hand([], name="Player", wager=bet)
        dealer_hand = Hand([], name="Dealer")
        self._draw_card(player_hand, show_hand=False)
        self._draw_card(dealer_hand, is_upcard=True)
        self._draw_card(player_hand)
        self._draw_card(dealer_hand, show_hand=False)

        # Check for natural blackjack before any play
        if player_hand.is_blackjack() or dealer_hand.is_blackjack():
            self._strategy.show_hand(dealer_hand)
            if player_hand.is_blackjack() and dealer_hand.is_blackjack():
                self._strategy.show_result(player_hand, "Push (blackjack)")
                self._bankroll += bet
            elif player_hand.is_blackjack() and not dealer_hand.is_blackjack():
                self._strategy.show_result(player_hand, "Player has blackjack")
                self._bankroll += bet + (self._options.payout * bet)
            else:
                self._strategy.show_result(player_hand, "Dealer has blackjack")
        else:
            # Player plays one or more hands
            player_hands = self._play_hand(self._strategy, player_hand, bet, 0)

            # Check for surrender before dealer plays
            if (len(player_hands) == 1) and player_hands[0].is_surrender():
                self._strategy.show_result(player_hand, "Player surrender")
                self._bankroll += 0.5 * bet
            else:
                # Dealer plays their hand
                self._strategy.show_hand(dealer_hand)
                dealer = Dealer(self._options.hit_soft_seventeen)
                dealer_hands = self._play_hand(dealer, dealer_hand, 0, 0)
                assert len(dealer_hands) == 1
                dealer_hand = dealer_hands[0]

                # Compare outcomes, adjust bankroll (no change if dealer wins)
                for player_hand in player_hands:
                    self._compare_hands(player_hand, dealer_hand)

    def play(self, strategy: Strategy, bankroll: int) -> Tuple[float, float]:
        self._bankroll = bankroll
        self._total_bet = 0
        self._shoe = Shoe(self._options.num_decks)
        self._strategy = strategy

        while True:
            bet = strategy.get_bet(self._options.min_bet, self._bankroll)
            if (
                not bet
                or (self._bankroll < bet)
                or (self._shoe.percent_full() <= self._options.shoe_min_percent)
            ):
                break

            try:
                self._make_bet(bet)
                self._play_round(bet)
            except EmptyShoeError:
                break

        ev = (self._bankroll - bankroll) / self._total_bet if self._total_bet else 0.0
        return self._bankroll, ev
