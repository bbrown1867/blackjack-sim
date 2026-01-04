from blackjack_sim.core import Hand

from common import make_ace, make_face_card, make_low_card


def test_hand():
    hand = Hand([make_ace(), make_ace()], name="My Hand", wager=10)
    assert hand.has_ace()
    assert hand.is_soft()
    assert hand.wager == 10
    assert str(hand) == "My Hand: Ax  Ax"

    assert hand.value() == 12
    assert not hand.is_bust()
    assert not hand.is_blackjack()
    assert hand.can_split()

    hand.append(make_low_card(9))
    assert hand.value() == 21
    assert not hand.is_bust()
    assert hand.is_blackjack()
    assert not hand.can_split()

    hand.append(make_face_card())
    assert hand.value() == 21


def test_hand_surrender():
    hand = Hand([make_ace(), make_ace()])
    hand.surrender()
    assert hand.is_surrender()


def test_hand_double():
    hand = Hand([make_low_card(8), make_low_card(2)], wager=10)
    hand.double()
    assert hand.wager == 20
