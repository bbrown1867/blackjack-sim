"""Text-based user interface built with textual"""

import logging
import threading
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.logging import TextualHandler
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from blackjack_sim.core import Action, Hand
from blackjack_sim.engine import Game
from blackjack_sim.strategy import Strategy

logger = logging.getLogger(__name__)


class BetDialog(ModalScreen[int]):
    CSS = """
    BetDialog { align: center middle; }
    #dialog {
        width: 60%;
        max-width: 60;
        border: round $accent;
        padding: 1 2;
        background: $panel;
    }
    #buttons { margin-top: 1; height: auto; align: right middle; }
    """

    def __init__(self, bet: int):
        super().__init__()
        self._min_bet = bet

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Place Bet")
            yield Input(value=str(self._min_bet), id="bet_input")
            with Horizontal(id="buttons"):
                yield Button("OK", id="ok", variant="primary")
                yield Button("Quit", id="quit", variant="error")

    @on(Button.Pressed, "#ok")
    def _ok(self):
        text = self.query_one("#bet_input", Input).value.strip()
        try:
            bet = int(text)
        except ValueError:
            bet = self._min_bet
        self.dismiss(bet)

    @on(Button.Pressed, "#quit")
    def _quit(self):
        self.app.exit()


class Blackjack(App):
    TITLE = "Blackjack"

    BINDINGS = [Binding(key="ctrl+c", action="quit")]

    CSS = """
    Screen { padding: 1; }

    /* Top area: Player and dealer hands */
    #hands {
        height: 12;
    }

    #dealer_panel, #player_panel, #actions_panel, #info_panel, #log {
        border: round $surface;
        padding: 1;
    }

    #dealer_panel, #player_panel {
        width: 1fr;
    }

    /* Middle area: Action buttons and game info */
    #middle {
        height: 9;
    }

    #actions_panel {
        width: 2fr;
    }

    #info_panel {
        width: 1fr;
    }

    #actions_row {
        height: auto;
    }

    #actions_row Button {
        margin-right: 1;
        min-width: 10;
    }

    .hit { background: $success; color: black; }
    .stand { background: $primary; color: black; }
    .double { background: $warning; color: black; }
    .split { background: $accent; color: black; }
    .surrender { background: $error; color: black; }
    """

    def __init__(self, game: Game, bankroll: int):
        super().__init__()

        self._game = game
        self._waiting_for_action = False
        self._pending: Optional[PendingInput] = None
        self._thread = threading.Thread(
            target=self._game.play, args=(ManualTextual(self), bankroll), daemon=True
        )

    def compose(self) -> ComposeResult:
        with Vertical(id="root"):
            with Horizontal(id="hands"):
                with Vertical(id="dealer_panel"):
                    yield Label("Dealer")
                    yield Static("", id="dealer_hand")
                with Vertical(id="player_panel"):
                    yield Label("Player")
                    yield Static("", id="player_hand")

            with Horizontal(id="middle"):
                with Vertical(id="actions_panel"):
                    yield Label("Actions")
                    with Horizontal(id="actions_row"):
                        yield Button("Hit", id="hit", classes="hit")
                        yield Button("Stand", id="stand", classes="stand")
                        yield Button("Split", id="split", classes="split")
                        yield Button("Surrender", id="surrender", classes="surrender")
                        yield Button("Double", id="double", classes="double")

                with Vertical(id="info_panel"):
                    yield Label("Game Info")
                    yield Static("", id="info_text")

    def on_mount(self):
        logger.info("Hello from Textual!")
        self._thread.start()

    def _refresh_info(self):
        # TODO: Accessing private variables
        assert self._game._shoe
        info = "\n".join(
            [f"Shoe: {self._game._shoe.percent_full():.2f}%"]
            + [f"Bankroll: ${self._game._bankroll}"]
            + [f"Total Bet: ${self._game._total_bet}"]
        )
        self.query_one("#info_text", Static).update(info)

    @work
    async def get_bet(self):
        bet = await self.push_screen_wait(BetDialog(self._game._options.min_bet))
        self._reply_to_engine(bet)

    def get_action(self):
        # TODO: Only show available actions
        self._waiting_for_action = True

    def show_hand(self, hand: Hand):
        self._refresh_info()

        # TODO: Improve card drawings
        hand_without_name = Hand([card for card in hand])
        if "dealer" in hand.name.lower():
            self.query_one("#dealer_hand", Static).update("\n" + str(hand_without_name))
        elif "player" in hand.name.lower():
            self.query_one("#player_hand", Static).update("\n" + str(hand_without_name))
        else:
            raise AssertionError("Unexpected hand")

    @on(Button.Pressed)
    def any_button(self, event: Button.Pressed):
        btn_id = event.button.id

        if not self._waiting_for_action:
            return

        if btn_id in {"hit", "stand", "split", "surrender", "double"}:
            self._waiting_for_action = False

            selected_action = None
            for action in list(Action):
                if btn_id == str(action).lower().replace("[", "").replace("]", ""):
                    selected_action = action
                    break
            else:
                raise AssertionError("No action")

            # TODO: Disable buttons to prevent double-clicks
            # self._set_action_buttons(set())

            # Reply to engine with the action string
            self._reply_to_engine(selected_action)

    def _reply_to_engine(self, value):
        pending = self._pending
        if pending is None:
            return
        pending.value = value
        pending.event.set()


@dataclass
class PendingInput:
    event: threading.Event
    value: Optional[Any] = None


class ManualTextual(Strategy):
    def __init__(self, app: Blackjack):
        self._app = app

    def _get_input(self, func: Callable) -> Any:
        pending = PendingInput(event=threading.Event())
        self._app._pending = pending
        self._app.call_from_thread(func)
        pending.event.wait()
        return pending.value

    def show_hand(self, hand: Hand):
        self._app.call_from_thread(self._app.show_hand, hand)

    def show_result(self, hand: Hand, result: str):
        # TODO: Impement
        pass

    def get_bet(self, min_bet: int, bankroll: int) -> Optional[int]:
        logger.info("Waiting for bet...\n")
        bet = self._get_input(self._app.get_bet)
        logger.info(f"Got bet: {bet}\n")
        return bet

    def get_action(
        self, hand: Hand, actions: List[Action], upcard: Optional[int] = None
    ) -> Action:
        logger.info("Waiting for action...\n")
        action = self._get_input(self._app.get_action)
        logger.info(f"Got action: {action}\n")
        return action


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        handlers=[TextualHandler()],
    )

    game = Game()
    app = Blackjack(game, 500)
    app.run()
