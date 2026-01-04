from blackjack_sim.core import Action, Hand
from blackjack_sim.strategy import AlwaysHit, Basic, Dealer

from common import make_ace, make_face_card, make_low_card

_ALL_ACTIONS = list(Action)
_DEFAULT_ACTIONS = [Action.HIT, Action.STAND]
_ALL_ACTIONS_NO_SPLIT = [Action.HIT, Action.STAND, Action.SURRENDER, Action.DOUBLE]
_ALL_ACTIONS_NO_SURRENDER = [Action.HIT, Action.STAND, Action.DOUBLE, Action.SPLIT]


def test_dealer():
    dealer = Dealer(True)

    hand = Hand([make_low_card(6), make_low_card(2)])
    assert dealer.get_action(hand, _DEFAULT_ACTIONS) == Action.HIT

    hand = Hand([make_ace(), make_low_card(6), make_low_card(2)])
    assert dealer.get_action(hand, _DEFAULT_ACTIONS) == Action.STAND

    hand = Hand([make_face_card(), make_face_card()])
    assert dealer.get_action(hand, _DEFAULT_ACTIONS) == Action.STAND

    hand = Hand([make_ace(), make_ace()])
    assert dealer.get_action(hand, _DEFAULT_ACTIONS) == Action.HIT


def test_dealer_seventeen():
    dealer_hit = Dealer(True)
    dealer_stand = Dealer(False)

    soft_seventeen = Hand([make_ace(), make_low_card(6)])
    hard_seventeen = Hand([make_face_card(), make_low_card(7)])

    assert dealer_hit.get_action(soft_seventeen, _DEFAULT_ACTIONS) == Action.HIT
    assert dealer_stand.get_action(soft_seventeen, _DEFAULT_ACTIONS) == Action.STAND

    assert dealer_hit.get_action(hard_seventeen, _DEFAULT_ACTIONS) == Action.STAND
    assert dealer_stand.get_action(hard_seventeen, _DEFAULT_ACTIONS) == Action.STAND


def test_player_always_hit():
    always_hit = AlwaysHit()

    hand = Hand([make_ace(), make_low_card(6)])
    assert always_hit.get_action(hand, _DEFAULT_ACTIONS) == Action.HIT


def test_player_basic_split_ace():
    basic = Basic()
    hand = Hand([make_ace(), make_ace()])
    for upcard in range(2, 12):
        assert basic.get_action(hand, _ALL_ACTIONS, upcard=upcard) == Action.SPLIT


def test_player_basic_split_ten():
    basic = Basic()
    hand = Hand([make_face_card(), make_face_card()])
    for upcard in range(2, 12):
        assert basic.get_action(hand, _ALL_ACTIONS, upcard=upcard) == Action.STAND


def test_player_basic_split_nine():
    basic = Basic()
    hand = Hand([make_low_card(9), make_low_card(9)])
    for upcard in range(2, 12):
        action = Action.STAND if upcard in [7, 10, 11] else Action.SPLIT
        assert basic.get_action(hand, _ALL_ACTIONS, upcard=upcard) == action


def test_player_basic_split_eight_no_surrender():
    basic = Basic()
    hand = Hand([make_low_card(8), make_low_card(8)])
    for upcard in range(2, 12):
        assert (
            basic.get_action(hand, _ALL_ACTIONS_NO_SURRENDER, upcard=upcard)
            == Action.SPLIT
        )


def test_player_basic_split_eight_with_surrender():
    basic = Basic()
    hand = Hand([make_low_card(8), make_low_card(8)])
    assert basic.get_action(hand, _ALL_ACTIONS, upcard=11) == Action.SURRENDER


def test_player_basic_split_seven():
    basic = Basic()
    hand = Hand([make_low_card(7), make_low_card(7)])
    for upcard in range(2, 8):
        assert basic.get_action(hand, _ALL_ACTIONS, upcard=upcard) == Action.SPLIT

    for upcard in range(8, 12):
        assert basic.get_action(hand, _ALL_ACTIONS, upcard=upcard) == Action.HIT


def test_player_basic_split_six():
    basic = Basic()
    hand = Hand([make_low_card(6), make_low_card(6)])
    for upcard in range(2, 7):
        assert basic.get_action(hand, _ALL_ACTIONS, upcard=upcard) == Action.SPLIT

    for upcard in range(7, 12):
        assert basic.get_action(hand, _ALL_ACTIONS, upcard=upcard) == Action.HIT


def test_player_basic_split_five():
    basic = Basic()
    hand = Hand([make_low_card(5), make_low_card(5)])
    for upcard in range(2, 12):
        action = Action.DOUBLE if upcard <= 9 else Action.HIT
        assert basic.get_action(hand, _ALL_ACTIONS, upcard=upcard) == action
        assert basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard) == Action.HIT


def test_player_basic_split_four():
    basic = Basic()
    hand = Hand([make_low_card(4), make_low_card(4)])
    for upcard in range(2, 12):
        action = Action.SPLIT if 5 <= upcard <= 6 else Action.HIT
        assert basic.get_action(hand, _ALL_ACTIONS, upcard=upcard) == action


def test_player_basic_split_two_and_three():
    basic = Basic()
    for i in range(2, 4):
        hand = Hand([make_low_card(i), make_low_card(i)])
        for upcard in range(2, 12):
            action = Action.SPLIT if upcard <= 7 else Action.HIT
            assert basic.get_action(hand, _ALL_ACTIONS, upcard=upcard) == action


def test_player_basic_soft_nineteen_and_twenty():
    basic = Basic()
    for i in range(8, 10):
        hand = Hand([make_ace(), make_low_card(i)])
        for upcard in range(2, 12):
            assert (
                basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard) == Action.STAND
            )
            if (i == 8) and (upcard == 6):
                assert (
                    basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard)
                    == Action.DOUBLE
                )


def test_player_basic_soft_eighteen():
    basic = Basic()
    hand = Hand([make_ace(), make_low_card(7)])
    for upcard in range(2, 12):
        if 7 <= upcard <= 8:
            assert (
                basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard) == Action.STAND
            )
        elif upcard <= 6:
            assert (
                basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard) == Action.STAND
            )
            assert (
                basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard)
                == Action.DOUBLE
            )
        else:
            assert (
                basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard)
                == Action.HIT
            )


def test_player_basic_soft_seventeen():
    basic = Basic()
    hand = Hand([make_ace(), make_low_card(6)])
    for upcard in range(2, 12):
        assert basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard) == Action.HIT
        if 3 <= upcard <= 6:
            assert (
                basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard)
                == Action.DOUBLE
            )


def test_player_basic_soft_fifteen_and_sixteen():
    basic = Basic()
    for i in range(4, 6):
        hand = Hand([make_ace(), make_low_card(i)])
        for upcard in range(2, 12):
            assert basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard) == Action.HIT
            if 4 <= upcard <= 6:
                assert (
                    basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard)
                    == Action.DOUBLE
                )


def test_player_basic_soft_thirteen_and_fourteen():
    basic = Basic()
    for i in range(2, 4):
        hand = Hand([make_ace(), make_low_card(i)])
        for upcard in range(2, 12):
            assert basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard) == Action.HIT
            if upcard == 6:
                assert (
                    basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard)
                    == Action.DOUBLE
                )


def test_player_basic_soft_ace_pair():
    basic = Basic()
    hand = Hand([make_ace(), make_ace()])
    for upcard in range(2, 12):
        assert basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard) == Action.HIT
        if upcard == 6:
            assert (
                basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard)
                == Action.DOUBLE
            )


def test_player_basic_hard_seventeen_to_twenty_no_surrender():
    basic = Basic()
    for i in range(2, 6):
        hand = Hand([make_face_card(), make_low_card(5), make_low_card(i)])
        for upcard in range(2, 12):
            assert (
                basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard) == Action.STAND
            )


def test_player_basic_hard_seventeen_with_surrender():
    basic = Basic()
    hand = Hand([make_face_card(), make_low_card(7)])
    assert basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=11) == Action.SURRENDER


def test_player_basic_hard_twelve_to_sixteen_no_surrender():
    basic = Basic()
    for i in range(2, 7):
        hand = Hand([make_low_card(8), make_low_card(2), make_low_card(i)])
        for upcard in range(2, 12):
            if upcard <= 6:
                action = Action.STAND
                if (i == 2) and (2 <= upcard <= 3):
                    action = Action.HIT
                assert basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard) == action
            else:
                assert (
                    basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard)
                    == Action.HIT
                )


def test_player_basic_hard_sixteen_with_surrender():
    basic = Basic()
    hand = Hand([make_face_card(), make_low_card(6)])
    for upcard in range(9, 12):
        assert (
            basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard)
            == Action.SURRENDER
        )


def test_player_basic_hard_fifteen_with_surrender():
    basic = Basic()
    hand = Hand([make_face_card(), make_low_card(5)])
    for upcard in range(10, 12):
        assert (
            basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard)
            == Action.SURRENDER
        )


def test_player_basic_hard_eleven_with_double():
    basic = Basic()
    hand = Hand([make_low_card(7), make_low_card(4)])
    for upcard in range(2, 12):
        basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard) == Action.DOUBLE


def test_player_basic_hard_ten_with_double():
    basic = Basic()
    hand = Hand([make_low_card(7), make_low_card(3)])
    for upcard in range(2, 10):
        basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard) == Action.DOUBLE


def test_player_basic_hard_nine_with_double():
    basic = Basic()
    hand = Hand([make_low_card(7), make_low_card(2)])
    for upcard in range(3, 7):
        basic.get_action(hand, _ALL_ACTIONS_NO_SPLIT, upcard=upcard) == Action.DOUBLE


def test_player_basic_hard_four_to_eleven_no_double():
    basic = Basic()
    for i in range(2, 10):
        hand = Hand([make_low_card(2), make_low_card(i)])
        for upcard in range(2, 12):
            assert basic.get_action(hand, _DEFAULT_ACTIONS, upcard=upcard) == Action.HIT
