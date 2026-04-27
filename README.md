# 4-Letter Word Guess

A small Wordle-style guessing game that runs entirely in the browser via [PyScript](https://pyscript.net). Zero server, zero install — host it free on GitHub Pages.

## Rules

- Pick a mode:
  - **Single player** — the game picks a random 4-letter word for you.
  - **Two players** — one person sets a secret 4-letter word, the other guesses.
- The guesser has **8 attempts**. If they run out, the game offers **2 extra chances** (one-time bonus).
- After every guess two numbers appear next to the guess:
  - **GREEN** — letters in the right spot.
  - **YELLOW** — letters that exist in the word but in the wrong spot (each secret letter is consumed at most once, standard Wordle rules).
- Guesses must be real English words — validated against the bundled `words4.txt` (~7,200 four-letter words from the [dwyl/english-words](https://github.com/dwyl/english-words) list).
- Words must have **all 4 letters different** (e.g. `BEET` is not allowed because `E` repeats).
- **Proper nouns are not allowed** (names, places, brands).
- Crack the word and you get a confetti / fireworks burst.

## Run locally

PyScript runs entirely client-side, but the browser needs the file to be served via HTTP (not `file://`) so it can fetch `words4.txt` and `propernames4.txt`.

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/index.html>.

## Deploy free on GitHub Pages

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
| `index.html` | The whole app — HTML, CSS, PyScript, and the confetti animation. |
| `words4.txt` | Bundled 4-letter English wordlist. |
| `propernames4.txt` | Bundled 4-letter proper-noun blocklist. |
| `.nojekyll` | Tells GitHub Pages to serve files as-is. |
