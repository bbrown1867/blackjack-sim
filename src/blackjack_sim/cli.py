"""Command-line interface."""

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Dict, Optional

import typer
from rich.progress import track

from .engine import Game, GameOptions
from .strategy import AlwaysHit, Basic, Manual, Training

app = typer.Typer(add_completion=False)

logger = logging.getLogger(__name__)


@dataclass
class CommonOptions:
    game_options: GameOptions
    bankroll: int


class PlayerStrategy(StrEnum):
    Basic = "basic"
    AlwaysHit = "always_hit"


_STRATEGY_MAP: Dict = {
    PlayerStrategy.Basic: Basic,
    PlayerStrategy.AlwaysHit: AlwaysHit,
}


@app.command()
def play(
    ctx: typer.Context,
    training_strategy: Annotated[
        Optional[PlayerStrategy],
        typer.Option(case_sensitive=False, help="Training strategy"),
    ] = None,
):
    """Play blackjack!

    User is prompted for betting and strategy decisions. The game ends when the
    user quits, goes bankrupt, or the shoe is out of cards, which is defined by
    a minimum percent remaining.

    An optional training strategy can be specified to compare with user decisions.
    """
    if training_strategy:
        strategy_cls = _STRATEGY_MAP[training_strategy]
        strategy = Training(strategy_cls())
    else:
        strategy = Manual()

    game = Game(options=ctx.obj.game_options)
    bankroll, ev = game.play(strategy, ctx.obj.bankroll)

    logger.info("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    logger.info(f"Final Bankroll: ${bankroll}")
    logger.info(f"House Edge: {-100.0 * ev:.2f}%")


@app.command()
def simulate(
    ctx: typer.Context,
    player_strategy: Annotated[
        PlayerStrategy, typer.Option(case_sensitive=False, help="Player strategy")
    ] = PlayerStrategy.Basic,
    num_games: Annotated[
        int, typer.Option(help="Number of games to simulate")
    ] = 1000000,
):
    """Simulate many blackjack games to evaluate a strategy."""
    strategy_cls = _STRATEGY_MAP[player_strategy]

    avg_ev = 0.0
    num_bankrupt = 0
    for _ in track(range(num_games), description="Running simulation"):
        game = Game(options=ctx.obj.game_options)
        bankroll, ev = game.play(strategy_cls(), ctx.obj.bankroll)
        if bankroll == 0:
            num_bankrupt += 1

        avg_ev += ev

    logger.info(f"Bankruptcy Chance: {(num_bankrupt / num_games) * 100.0:.2f}%")
    logger.info(f"House Edge: {-100.0 * (avg_ev / num_games):.2f}%")


@app.callback()
def common_options(
    ctx: typer.Context,
    bet: Annotated[
        int, typer.Option(help="Minumum bet")
    ] = GameOptions.__dataclass_fields__["min_bet"].default,
    payout: Annotated[
        float, typer.Option(help="Payout for natural blackjack")
    ] = GameOptions.__dataclass_fields__["payout"].default,
    num_decks: Annotated[
        int, typer.Option(help="Number of 52 card decks in a shoe")
    ] = GameOptions.__dataclass_fields__["num_decks"].default,
    shoe_min_percent: Annotated[
        float, typer.Option(help="Percent of shoe remaining when game ends")
    ] = GameOptions.__dataclass_fields__["shoe_min_percent"].default,
    hit_soft_seventeen: Annotated[
        bool, typer.Option(help="Dealer hits or stands on soft seventeen")
    ] = GameOptions.__dataclass_fields__["hit_soft_seventeen"].default,
    double_after_split: Annotated[
        bool, typer.Option(help="Double after split allowed or disallowed")
    ] = GameOptions.__dataclass_fields__["double_after_split"].default,
    late_surrender: Annotated[
        bool, typer.Option(help="Late surrender allowed or disallowed")
    ] = GameOptions.__dataclass_fields__["late_surrender"].default,
    max_split: Annotated[
        int, typer.Option(help="Max number of splits allowed (2 splits = 4 hands)")
    ] = GameOptions.__dataclass_fields__["max_split"].default,
    bankroll: Annotated[int, typer.Option(help="Player bankroll")] = 500,
):
    logging.basicConfig(format="", level=logging.INFO)

    game_options = GameOptions(
        bet,
        payout,
        num_decks,
        shoe_min_percent,
        hit_soft_seventeen,
        double_after_split,
        late_surrender,
        max_split,
    )
    ctx.obj = CommonOptions(game_options, bankroll)


def main():
    app()
