"""A simple 4-letter word guessing game built with tkinter.

Rules:
- The host enters a secret 4-letter word and clicks "Start Game".
- The player has 8 chances to guess the word.
- After each guess, two numbers are shown next to the guess:
    * GREEN  -> count of letters that are correct AND in the correct position.
    * YELLOW -> count of letters that are correct but in the wrong position.
- The game ends when the player guesses the word, or runs out of attempts.
"""

import random
import threading
import tkinter as tk
from tkinter import messagebox

from wordlist import FALLBACK_WORDS_4, load_wordlist

WORD_LENGTH = 4
MAX_ATTEMPTS = 8


class PillButton(tk.Label):
    """A Label-based button that honours custom colors on every platform.

    macOS's native tk.Button widget ignores `bg`/`fg`, which makes light text
    on our purple/grey theme unreadable. Using a Label with click bindings
    sidesteps that entirely.
    """

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        command,
        *,
        bg: str = "#7f5af0",
        fg: str = "#ffffff",
        hover_bg: str = "#6d4adf",
        disabled_bg: str = "#3a3a4f",
        disabled_fg: str = "#9a9aac",
        font=("Helvetica", 12, "bold"),
        padx: int = 18,
        pady: int = 8,
    ) -> None:
        super().__init__(
            parent,
            text=text,
            font=font,
            bg=bg,
            fg=fg,
            padx=padx,
            pady=pady,
            cursor="hand2",
        )
        self._command = command
        self._normal_bg = bg
        self._normal_fg = fg
        self._hover_bg = hover_bg
        self._disabled_bg = disabled_bg
        self._disabled_fg = disabled_fg
        self._enabled = True
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_enter(self, _event) -> None:
        if self._enabled:
            self.config(bg=self._hover_bg)

    def _on_leave(self, _event) -> None:
        if self._enabled:
            self.config(bg=self._normal_bg)

    def _on_click(self, _event) -> None:
        if self._enabled and self._command:
            self._command()

    def set_state(self, state: str) -> None:
        if state == "disabled":
            self._enabled = False
            self.config(
                bg=self._disabled_bg,
                fg=self._disabled_fg,
                cursor="arrow",
            )
        else:
            self._enabled = True
            self.config(
                bg=self._normal_bg,
                fg=self._normal_fg,
                cursor="hand2",
            )

    def configure(self, **kwargs):  # type: ignore[override]
        if "state" in kwargs:
            self.set_state(kwargs.pop("state"))
        if kwargs:
            super().configure(**kwargs)

    config = configure  # type: ignore[assignment]


def score_guess(secret: str, guess: str) -> tuple[int, int]:
    """Return (greens, yellows) for the given guess against the secret.

    Greens: correct letter in the correct position.
    Yellows: correct letter, wrong position. Each secret letter is matched
    at most once (standard Wordle-style scoring).
    """
    greens = 0
    secret_remaining: list[str] = []
    guess_remaining: list[str] = []

    for s_ch, g_ch in zip(secret, guess):
        if s_ch == g_ch:
            greens += 1
        else:
            secret_remaining.append(s_ch)
            guess_remaining.append(g_ch)

    yellows = 0
    for g_ch in guess_remaining:
        if g_ch in secret_remaining:
            yellows += 1
            secret_remaining.remove(g_ch)

    return greens, yellows


class WordGuessGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("4-Letter Word Guess")
        self.root.geometry("440x620")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        self.secret: str = ""
        self.attempts_used: int = 0
        self.game_active: bool = False
        self.valid_words: set[str] = set()
        self.wordlist_ready: bool = False

        self._build_setup_frame()
        self._build_game_frame()
        self._show_setup()
        self._start_wordlist_load()

    def _build_setup_frame(self) -> None:
        self.setup_frame = tk.Frame(self.root, bg="#1e1e2e")

        tk.Label(
            self.setup_frame,
            text="4-Letter Word Guess",
            font=("Helvetica", 22, "bold"),
            fg="#f5f5f5",
            bg="#1e1e2e",
        ).pack(pady=(40, 10))

        tk.Label(
            self.setup_frame,
            text="Choose a mode",
            font=("Helvetica", 12),
            fg="#bbbbbb",
            bg="#1e1e2e",
        ).pack(pady=(0, 8))

        self.mode_var = tk.StringVar(value="single")
        mode_frame = tk.Frame(self.setup_frame, bg="#1e1e2e")
        mode_frame.pack(pady=(0, 16))

        radio_style = {
            "font": ("Helvetica", 11),
            "fg": "#f5f5f5",
            "bg": "#1e1e2e",
            "activebackground": "#1e1e2e",
            "activeforeground": "#f5f5f5",
            "selectcolor": "#2a2a3d",
            "highlightthickness": 0,
            "borderwidth": 0,
            "cursor": "hand2",
        }
        tk.Radiobutton(
            mode_frame,
            text="Single player (random word)",
            variable=self.mode_var,
            value="single",
            command=self._on_mode_change,
            **radio_style,
        ).pack(anchor="w")
        tk.Radiobutton(
            mode_frame,
            text="Two players (I'll set the word)",
            variable=self.mode_var,
            value="two",
            command=self._on_mode_change,
            **radio_style,
        ).pack(anchor="w")

        self.secret_container = tk.Frame(self.setup_frame, bg="#1e1e2e")

        tk.Label(
            self.secret_container,
            text="Enter a secret 4-letter word",
            font=("Helvetica", 12),
            fg="#bbbbbb",
            bg="#1e1e2e",
        ).pack(pady=(0, 10))

        self.secret_var = tk.StringVar()
        self.secret_var.trace_add("write", lambda *_: self._uppercase_var(self.secret_var))
        self.secret_entry = tk.Entry(
            self.secret_container,
            textvariable=self.secret_var,
            font=("Helvetica", 18, "bold"),
            justify="center",
            show="*",
            width=12,
            bg="#2a2a3d",
            fg="#f5f5f5",
            insertbackground="#f5f5f5",
            relief="flat",
        )
        self.secret_entry.pack(ipady=8, pady=(0, 10))

        self.start_btn = PillButton(
            self.setup_frame,
            text="Start Game",
            command=self._start_game,
            font=("Helvetica", 14, "bold"),
            padx=24,
            pady=10,
        )
        self.start_btn.set_state("disabled")
        self.start_btn.pack(pady=20)

        self.status_label = tk.Label(
            self.setup_frame,
            text="Loading word list...",
            font=("Helvetica", 10),
            fg="#9999aa",
            bg="#1e1e2e",
        )
        self.status_label.pack(pady=(0, 5))

        tk.Label(
            self.setup_frame,
            text=(
                "How to play:\n"
                "You get 8 chances to guess the word.\n"
                "After each guess you'll see:\n"
                "  GREEN  = correct letters in correct spot\n"
                "  YELLOW = correct letters in wrong spot"
            ),
            font=("Helvetica", 10),
            fg="#9999aa",
            bg="#1e1e2e",
            justify="left",
        ).pack(pady=(30, 0))

    def _build_game_frame(self) -> None:
        self.game_frame = tk.Frame(self.root, bg="#1e1e2e")

        self.title_label = tk.Label(
            self.game_frame,
            text="Guess the 4-letter word",
            font=("Helvetica", 18, "bold"),
            fg="#f5f5f5",
            bg="#1e1e2e",
        )
        self.title_label.pack(pady=(20, 5))

        self.attempts_label = tk.Label(
            self.game_frame,
            text="",
            font=("Helvetica", 12),
            fg="#bbbbbb",
            bg="#1e1e2e",
        )
        self.attempts_label.pack(pady=(0, 10))

        self.history_frame = tk.Frame(self.game_frame, bg="#1e1e2e")
        self.history_frame.pack(pady=10)

        input_row = tk.Frame(self.game_frame, bg="#1e1e2e")
        input_row.pack(pady=20)

        self.guess_var = tk.StringVar()
        self.guess_var.trace_add("write", lambda *_: self._uppercase_var(self.guess_var))
        self.guess_entry = tk.Entry(
            input_row,
            textvariable=self.guess_var,
            font=("Helvetica", 18, "bold"),
            justify="center",
            width=8,
            bg="#2a2a3d",
            fg="#f5f5f5",
            insertbackground="#f5f5f5",
            relief="flat",
        )
        self.guess_entry.pack(side="left", ipady=8, padx=(0, 10))
        self.guess_entry.bind("<Return>", lambda _e: self._submit_guess())

        self.submit_btn = PillButton(
            input_row,
            text="Guess",
            command=self._submit_guess,
        )
        self.submit_btn.pack(side="left")

        self.reset_btn = PillButton(
            self.game_frame,
            text="New Game",
            command=self._show_setup,
            font=("Helvetica", 11),
            bg="#2a2a3d",
            fg="#f5f5f5",
            hover_bg="#3a3a55",
            padx=14,
            pady=6,
        )
        self.reset_btn.pack(pady=10)

    def _uppercase_var(self, var: tk.StringVar) -> None:
        current = var.get()
        cleaned = "".join(ch for ch in current if ch.isalpha())[:WORD_LENGTH].upper()
        if cleaned != current:
            var.set(cleaned)

    def _start_wordlist_load(self) -> None:
        thread = threading.Thread(target=self._load_wordlist_worker, daemon=True)
        thread.start()

    def _load_wordlist_worker(self) -> None:
        words = load_wordlist(WORD_LENGTH)
        self.root.after(0, self._on_wordlist_loaded, words)

    def _on_wordlist_loaded(self, words: set[str]) -> None:
        self.valid_words = words
        self.wordlist_ready = True
        self.start_btn.config(state="normal")
        if words:
            self.status_label.config(
                text=f"Word list ready ({len(words):,} valid 4-letter words).",
                fg="#2cb67d",
            )
        else:
            self.status_label.config(
                text="Couldn't load word list — running without word validation.",
                fg="#f4c430",
            )

    def _show_setup(self) -> None:
        self.game_frame.pack_forget()
        self.setup_frame.pack(fill="both", expand=True)
        self.secret_var.set("")
        self._on_mode_change()

    def _on_mode_change(self) -> None:
        if self.mode_var.get() == "two":
            self.secret_container.pack(pady=(0, 0), before=self.start_btn)
            self.secret_entry.focus_set()
        else:
            self.secret_container.pack_forget()
            self.start_btn.focus_set()

    def _pick_random_word(self) -> str | None:
        pool = self.valid_words & FALLBACK_WORDS_4 if self.valid_words else FALLBACK_WORDS_4
        if not pool:
            pool = self.valid_words or FALLBACK_WORDS_4
        if not pool:
            return None
        return random.choice(sorted(pool))

    def _show_game(self) -> None:
        self.setup_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        self.guess_entry.focus_set()

    def _start_game(self) -> None:
        if self.mode_var.get() == "single":
            word = self._pick_random_word()
            if not word:
                messagebox.showerror(
                    "No words available",
                    "Couldn't pick a random word — word list is empty.",
                )
                return
        else:
            word = self.secret_var.get().strip().lower()
            if len(word) != WORD_LENGTH or not word.isalpha():
                messagebox.showerror(
                    "Invalid word",
                    f"Please enter a {WORD_LENGTH}-letter word (letters only).",
                )
                return

            if self.valid_words and word not in self.valid_words:
                messagebox.showerror(
                    "Not a real word",
                    f"'{word.upper()}' isn't in the dictionary. Pick a real "
                    f"{WORD_LENGTH}-letter word.",
                )
                return

        self.secret = word
        self.attempts_used = 0
        self.game_active = True

        for child in self.history_frame.winfo_children():
            child.destroy()

        self.guess_var.set("")
        self.submit_btn.config(state="normal")
        self.guess_entry.config(state="normal")
        self._update_attempts_label()
        self._show_game()

    def _update_attempts_label(self) -> None:
        remaining = MAX_ATTEMPTS - self.attempts_used
        self.attempts_label.config(text=f"Attempts remaining: {remaining} / {MAX_ATTEMPTS}")

    def _submit_guess(self) -> None:
        if not self.game_active:
            return

        guess = self.guess_var.get().strip().lower()
        if len(guess) != WORD_LENGTH or not guess.isalpha():
            messagebox.showwarning(
                "Invalid guess",
                f"Please enter a {WORD_LENGTH}-letter word.",
            )
            return

        if self.valid_words and guess not in self.valid_words:
            messagebox.showwarning(
                "Not a real word",
                f"'{guess.upper()}' isn't in the dictionary. Try a real "
                f"{WORD_LENGTH}-letter word (this attempt won't count).",
            )
            return

        greens, yellows = score_guess(self.secret, guess)
        self.attempts_used += 1
        self._add_history_row(guess, greens, yellows)
        self.guess_var.set("")
        self._update_attempts_label()

        if guess == self.secret:
            self._end_game(won=True)
        elif self.attempts_used >= MAX_ATTEMPTS:
            self._end_game(won=False)

    def _add_history_row(self, guess: str, greens: int, yellows: int) -> None:
        row = tk.Frame(self.history_frame, bg="#1e1e2e")
        row.pack(pady=3)

        tk.Label(
            row,
            text=f"{self.attempts_used:>2}.",
            font=("Helvetica", 12),
            fg="#888899",
            bg="#1e1e2e",
            width=3,
            anchor="e",
        ).pack(side="left", padx=(0, 8))

        tk.Label(
            row,
            text=guess.upper(),
            font=("Courier", 18, "bold"),
            fg="#f5f5f5",
            bg="#2a2a3d",
            width=6,
        ).pack(side="left", ipady=4, padx=(0, 12))

        tk.Label(
            row,
            text=str(greens),
            font=("Helvetica", 14, "bold"),
            fg="#ffffff",
            bg="#2cb67d",
            width=3,
        ).pack(side="left", ipady=4, padx=(0, 6))

        tk.Label(
            row,
            text=str(yellows),
            font=("Helvetica", 14, "bold"),
            fg="#1e1e2e",
            bg="#f4c430",
            width=3,
        ).pack(side="left", ipady=4)

    def _end_game(self, won: bool) -> None:
        self.game_active = False
        self.submit_btn.config(state="disabled")
        self.guess_entry.config(state="disabled")

        if won:
            messagebox.showinfo(
                "You won!",
                f"Nice! You guessed '{self.secret.upper()}' in {self.attempts_used} "
                f"{'try' if self.attempts_used == 1 else 'tries'}.",
            )
        else:
            messagebox.showinfo(
                "Game over",
                f"Out of attempts. The word was '{self.secret.upper()}'.",
            )


def main() -> None:
    root = tk.Tk()
    WordGuessGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
