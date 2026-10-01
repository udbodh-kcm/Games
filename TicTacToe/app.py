"""KCM Memory — dependency-free Python web server.

Run with: python3 app.py
Then open: http://127.0.0.1:8000
"""

from __future__ import annotations

import json
import os
import secrets
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
WEB_DIRECTORY = ROOT / "dist"
PAIR_COUNTS = {"easy": 6, "classic": 8, "expert": 10}
RANDOM = secrets.SystemRandom()
WINNING_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def create_deck(difficulty: str) -> list[int]:
    """Create a shuffled list containing two cards for every symbol."""
    pair_count = PAIR_COUNTS[difficulty]
    deck = list(range(pair_count)) * 2
    RANDOM.shuffle(deck)
    return deck


def winning_move(board: list[str], mark: str) -> int | None:
    """Return a move that wins immediately for mark, when one exists."""
    for line in WINNING_LINES:
        values = [board[index] for index in line]
        if values.count(mark) == 2 and values.count("") == 1:
            return line[values.index("")]
    return None


def choose_tictactoe_move(board: list[str]) -> int:
    """Choose a lively but fair computer move using simple strategy."""
    available = [index for index, value in enumerate(board) if not value]
    if not available:
        raise ValueError("The board is full.")

    for mark in ("O", "X"):
        move = winning_move(board, mark)
        if move is not None:
            return move

    if 4 in available:
        return 4
    corners = [index for index in (0, 2, 6, 8) if index in available]
    return RANDOM.choice(corners or available)


class KCMRequestHandler(SimpleHTTPRequestHandler):
    """Serve the game files and its small Python game API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIRECTORY), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - inherited HTTP method name
        request = urlparse(self.path)
        if request.path == "/api/new-game":
            self._send_new_game(parse_qs(request.query))
            return
        if request.path == "/api/health":
            self._send_json({"status": "ok", "game": "KCM Memory"})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - inherited HTTP method name
        request = urlparse(self.path)
        if request.path != "/api/tictactoe/move":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length < 1 or content_length > 2_048:
                raise ValueError("Invalid request size.")
            payload = json.loads(self.rfile.read(content_length))
            board = payload.get("board")
            if (
                not isinstance(board, list)
                or len(board) != 9
                or any(value not in ("", "X", "O") for value in board)
                or board.count("X") != board.count("O") + 1
            ):
                raise ValueError("Board must contain nine valid cells after X's turn.")
            move = choose_tictactoe_move(board)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_json({"game": "KCM Tic-Tac-Toe", "mark": "O", "move": move})

    def _send_new_game(self, query: dict[str, list[str]]) -> None:
        difficulty = query.get("difficulty", ["classic"])[0]
        if difficulty not in PAIR_COUNTS:
            self._send_json(
                {
                    "error": "Difficulty must be easy, classic, or expert.",
                    "allowed": list(PAIR_COUNTS),
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        self._send_json(
            {
                "game": "KCM Memory",
                "difficulty": difficulty,
                "pairs": PAIR_COUNTS[difficulty],
                "deck": create_deck(difficulty),
            }
        )

    def _send_json(
        self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK
    ) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def run() -> None:
    host = os.getenv("KCM_HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), KCMRequestHandler)
    print(f"KCM Memory is running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKCM Memory stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
