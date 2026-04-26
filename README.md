# 4-Letter Word Guess

A small Wordle-style guessing game. Comes in **two flavours**:

1. **Desktop version** — `game.py`, runs locally with `tkinter`.
2. **Web version** — `index.html`, runs in any modern browser via [PyScript](https://pyscript.net) and can be hosted for free on GitHub Pages.

## Rules

- Pick a mode:
  - **Single player** — the game picks a random 4-letter word for you.
  - **Two players** — one person sets a secret 4-letter word, the other guesses.
- The guesser has **8 attempts**.
- After every guess two numbers appear next to the guess:
  - **GREEN** — letters in the right spot.
  - **YELLOW** — letters that exist in the word but in the wrong spot (each secret letter is consumed at most once, standard Wordle rules).
- Guesses must be real English words — validated against the bundled `words4.txt` (~7,200 four-letter words from the [dwyl/english-words](https://github.com/dwyl/english-words) list).

## Run the desktop version

Requires Python 3.10+ with Tk support.

```bash
python3 game.py
```

If you're on Homebrew Python and see `ModuleNotFoundError: No module named '_tkinter'`, install the Tk extension once:

```bash
brew install python-tk@3.14   # or python-tk@3.12, matching your Python version
```

No pip dependencies — everything is stdlib.

## Run the web version locally

PyScript runs entirely client-side, but the browser needs the file to be served via HTTP (not `file://`) so it can fetch `words4.txt`.

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/index.html>.

## Deploy the web version free on GitHub Pages

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
# Create an empty repo on github.com first (e.g. "ParthGame"), then:
git remote add origin https://github.com/<your-username>/ParthGame.git
git push -u origin main
```

Then on GitHub:

1. Open your repo → **Settings** → **Pages**.
2. Under **Source**, choose `Deploy from a branch`.
3. Set Branch = `main`, Folder = `/ (root)`. Save.
4. Wait ~30 seconds, GitHub will publish at `https://<your-username>.github.io/ParthGame/`.

That URL works on any device with a modern browser, fully free, no servers.

> First page-load takes ~5–10 seconds while PyScript downloads the Python runtime. Subsequent visits are cached.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Web version (PyScript + HTML/CSS) |
| `game.py` | Desktop version (tkinter) |
| `wordlist.py` | Loads / caches `words4.txt` for the desktop version |
| `words4.txt` | Bundled 4-letter English wordlist (used by both versions) |
| `.nojekyll` | Tells GitHub Pages to serve files as-is |
