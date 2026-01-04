from blackjack_sim.core import Card


def make_ace() -> Card:
    return Card("Ax", 11)


def make_face_card() -> Card:
    return Card("Kx", 10)


def make_low_card(num: int) -> Card:
    assert 2 <= num <= 9
    return Card(f"{num}x", num)
