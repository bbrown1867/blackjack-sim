import logging
from unittest.mock import patch

from blackjack_sim.cli import app
from typer.testing import CliRunner

runner = CliRunner()


@patch("blackjack_sim.cli.Game")
def test_play(mock_game, caplog):
    bankroll = 500
    game_instance = mock_game.return_value
    game_instance.play.return_value = (bankroll, 0.0)

    caplog.set_level(logging.INFO)
    result = runner.invoke(app, ["--bankroll", str(bankroll), "play"])
    assert result.exit_code == 0
    assert f"Final Bankroll: ${bankroll}" in caplog.records[1].getMessage()
    assert "House Edge" in caplog.records[2].getMessage()
    game_instance.play.assert_called_once()


@patch("blackjack_sim.cli.Game")
def test_play_with_training(mock_game, caplog):
    game_instance = mock_game.return_value
    game_instance.play.return_value = (500, 0.0)

    caplog.set_level(logging.INFO)
    result = runner.invoke(app, ["play", "--training-strategy", "basic"])
    assert result.exit_code == 0
    assert "Final Bankroll" in caplog.records[1].getMessage()
    assert "House Edge" in caplog.records[2].getMessage()
    game_instance.play.assert_called_once()


def test_simulate(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app, ["--bet", "10", "--bankroll", "20", "simulate", "--num-games", "100"]
    )
    assert result.exit_code == 0
    assert "Running simulation" in result.output
    assert "Risk of Ruin" in caplog.records[0].getMessage()
    assert "House Edge" in caplog.records[1].getMessage()
