# blackjack-sim

An interactive blackjack simulator written in Python.

- `play` blackjack from the comfort of your terminal.
- `simulate` many blackjack games using an automated strategy.

## Dependencies

No dependencies except Python 3.12 or higher. However the following tools are recommended:

- [`uv`](https://docs.astral.sh/uv/) for Python project management.
- [`just`](https://github.com/casey/just) for running common workflows in the `justfile`.

## User Guide

The game engine supports a number of common rule adjustments with the ``GameOptions()``
class. All of these options are also available on the command-line.

    % uv run blackjack --help

     Usage: blackjack [OPTIONS] COMMAND [ARGS]...

    ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
    │ --bet                                              INTEGER  Minumum bet [default: 10]                                                │
    │ --payout                                           FLOAT    Payout for natural blackjack [default: 1.5]                              │
    │ --num-decks                                        INTEGER  Number of 52 card decks in a shoe [default: 6]                           │
    │ --shoe-min-percent                                 FLOAT    Percent of shoe remaining when game ends [default: 20.0]                 │
    │ --hit-soft-seventeen    --no-hit-soft-seventeen             Dealer hits or stands on soft seventeen [default: no-hit-soft-seventeen] │
    │ --double-after-split    --no-double-after-split             Double after split allowed or disallowed [default: double-after-split]   │
    │ --late-surrender        --no-late-surrender                 Late surrender allowed or disallowed [default: late-surrender]           │
    │ --max-split                                        INTEGER  Max number of splits allowed (2 splits = 4 hands) [default: 2]           │
    │ --bankroll                                         INTEGER  Player bankroll [default: 500]                                           │
    │ --help                                                      Show this message and exit.                                              │
    ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
    ╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
    │ play       Play blackjack                                                                                                            │
    │ simulate   Simulate many blackjack games to evaluate a strategy                                                                      │
    ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

The following game engine behavior is not configurable:

- No insurance offered
- Can double any first two cards
- Must stand after splitting Aces
- Heads-up play (one player against dealer)
- Natural blackjack checked before any play
    - No early surrender
    - Only original bets lost on dealer blackjack
