import logging

from blackjack_sim.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_simulate(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app, ["--bet", "10", "--bankroll", "20", "simulate", "--num-games", "100"]
    )
    assert result.exit_code == 0
    assert "Running simulation" in result.output
    assert "Risk of Ruin" in caplog.records[0].getMessage()
    assert "House Edge" in caplog.records[1].getMessage()
