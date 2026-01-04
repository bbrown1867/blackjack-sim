from contextlib import nullcontext
from unittest.mock import patch, MagicMock

import pytest
from blackjack_sim.core import Action, Hand
from blackjack_sim.engine import Game, GameOptions, Shoe

from common import make_ace, make_face_card, make_low_card


def test_shoe():
    num_decks = 2
    shoe = Shoe(num_decks)
    assert len(shoe) == (52 * num_decks)
    assert shoe.percent_full() == 100.0

    shoe.draw()
    assert shoe.percent_full() < 100.0


@pytest.mark.parametrize("allowed", [True, False])
def test_game_play_hand_late_surrender(allowed: bool):
    strategy = MagicMock()
    strategy.get_action.side_effect = [Action.SURRENDER]

    shoe = Shoe(1)
    hand = Hand([make_low_card(2), make_low_card(3)])
    options = GameOptions(late_surrender=allowed)
    game = Game(options=options)
    game._shoe = shoe
    context = nullcontext() if allowed else pytest.raises(AssertionError)
    with context:
        hands = game._play_hand(strategy, hand, 10, 0)
        if allowed:
            assert len(hands) == 1
            assert hands[0].is_surrender()


def test_game_play_hand_split():
    strategy = MagicMock()
    strategy.get_action.side_effect = [Action.SPLIT, Action.STAND, Action.STAND]

    shoe = MagicMock()
    shoe.draw.side_effect = [make_face_card(), make_low_card(9)]

    hand = Hand([make_low_card(2), make_low_card(2)])
    game = Game()
    game._bankroll = 10
    game._shoe = shoe
    hands = game._play_hand(strategy, hand, 10, 0)
    assert len(hands) == 2
    assert hands[0].value() == 12
    assert hands[1].value() == 11


def test_game_play_hand_max_split():
    strategy = MagicMock()
    strategy.get_action.side_effect = [Action.SPLIT]

    shoe = Shoe(1)
    hand = Hand([make_low_card(2), make_low_card(2)])
    options = GameOptions(max_split=2)
    game = Game()
    game._shoe = shoe
    with pytest.raises(AssertionError):
        game._play_hand(strategy, hand, 10, options.max_split)


def test_game_compare_hands_player_bust():
    bet = 10
    bankroll = 100
    player_hand = Hand(
        [make_face_card(), make_face_card(), make_face_card()], wager=bet
    )
    game = Game()
    game._bankroll = bankroll
    game._strategy = MagicMock()
    game._make_bet(bet)
    game._compare_hands(player_hand, MagicMock())
    assert game._bankroll == (bankroll - bet)


def test_game_compare_hands_dealer_bust():
    bet = 10
    bankroll = 100
    player_hand = Hand([make_low_card(3), make_low_card(2)], wager=bet)
    dealer_hand = Hand([make_face_card(), make_face_card(), make_face_card()])
    game = Game()
    game._bankroll = bankroll
    game._strategy = MagicMock()
    game._make_bet(bet)
    game._compare_hands(player_hand, dealer_hand)
    assert game._bankroll == (bankroll + bet)


def test_game_compare_hands_player_win():
    bet = 10
    bankroll = 100
    player_hand = Hand([make_low_card(3), make_low_card(2)], wager=bet)
    dealer_hand = Hand([make_low_card(2), make_low_card(2)])
    game = Game()
    game._bankroll = bankroll
    game._strategy = MagicMock()
    game._make_bet(bet)
    game._compare_hands(player_hand, dealer_hand)
    assert game._bankroll == (bankroll + bet)


def test_game_compare_hands_dealer_win():
    bet = 10
    bankroll = 100
    player_hand = Hand([make_low_card(2), make_low_card(2)], wager=bet)
    dealer_hand = Hand([make_low_card(3), make_low_card(2)])
    game = Game()
    game._bankroll = bankroll
    game._strategy = MagicMock()
    game._make_bet(bet)
    game._compare_hands(player_hand, dealer_hand)
    assert game._bankroll == (bankroll - bet)


def test_game_compare_hands_push():
    bet = 10
    bankroll = 100
    player_hand = Hand([make_low_card(3), make_low_card(2)], wager=bet)
    dealer_hand = Hand([make_low_card(3), make_low_card(2)])
    game = Game()
    game._bankroll = bankroll
    game._strategy = MagicMock()
    game._make_bet(bet)
    game._compare_hands(player_hand, dealer_hand)
    assert game._bankroll == bankroll


def test_game_play_round_player_blackjack():
    shoe = MagicMock()
    shoe.draw.side_effect = [
        make_ace(),
        make_low_card(2),
        make_face_card(),
        make_low_card(2),
    ]

    bet = 10
    options = GameOptions(payout=1.5)
    game = Game(options=options)
    game._shoe = shoe
    game._strategy = MagicMock()
    game._play_round(bet)
    assert game._bankroll == 25


def test_game_play_round_dealer_blackjack():
    shoe = MagicMock()
    shoe.draw.side_effect = [
        make_low_card(2),
        make_ace(),
        make_low_card(2),
        make_face_card(),
    ]

    game = Game()
    game._shoe = shoe
    game._strategy = MagicMock()
    game._play_round(10)
    assert game._bankroll == 0


def test_game_play_round_both_blackjack():
    shoe = MagicMock()
    shoe.draw.side_effect = [
        make_ace(),
        make_ace(),
        make_face_card(),
        make_face_card(),
    ]

    bet = 10
    game = Game()
    game._shoe = shoe
    game._strategy = MagicMock()
    game._play_round(bet)
    assert game._bankroll == bet


@patch("blackjack_sim.engine.Shoe")
def test_game_play(mock_shoe):
    bet = 10
    bankroll = 100

    shoe = mock_shoe.return_value
    shoe.percent_full.return_value = 100.0
    shoe.draw.side_effect = [
        make_face_card(),
        make_face_card(),
        make_face_card(),
        make_low_card(9),
    ]

    strategy = MagicMock()
    strategy.get_bet.side_effect = [bet, None]
    strategy.get_action.side_effect = [Action.STAND]

    game = Game()
    new_bankroll, ev = game.play(strategy, bankroll)
    assert new_bankroll == (bankroll + bet)
