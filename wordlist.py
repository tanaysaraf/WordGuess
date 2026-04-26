"""Load (and cache) a list of valid English 4-letter words.

Strategy:
1. If a local cache file `words4.txt` exists next to this module, use it.
2. Otherwise, try to download the dwyl/english-words list from GitHub,
   filter it down to N-letter alphabetic words, and cache the result.
3. If the download fails (e.g. offline), fall back to the system dictionary
   at /usr/share/dict/words on macOS/Linux.
4. If everything fails, return an empty set; the caller can then disable
   word validation and continue.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

WORDLIST_URL = (
    "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
)
CACHE_FILE = Path(__file__).resolve().parent / "words4.txt"
SYSTEM_DICT = Path("/usr/share/dict/words")

FALLBACK_WORDS_4 = {
    "able", "acid", "aged", "also", "area", "army", "away", "baby", "back", "ball",
    "band", "bank", "base", "bath", "bear", "beat", "been", "beer", "bell", "belt",
    "best", "bird", "blue", "boat", "body", "bomb", "bond", "bone", "book", "boom",
    "born", "boss", "both", "bowl", "bulk", "burn", "bush", "busy", "call", "calm",
    "came", "camp", "card", "care", "case", "cash", "cast", "cell", "chat", "chip",
    "city", "club", "coal", "coat", "code", "cold", "come", "cook", "cool", "cope",
    "copy", "core", "cost", "crew", "crop", "dark", "data", "date", "dawn", "days",
    "dead", "deal", "dear", "debt", "deep", "deny", "desk", "dial", "diet", "disc",
    "disk", "does", "done", "door", "dose", "down", "draw", "drew", "drop", "drug",
    "dual", "duke", "dust", "duty", "each", "earn", "ease", "east", "easy", "edge",
    "else", "even", "ever", "evil", "exit", "face", "fact", "fail", "fair", "fall",
    "farm", "fast", "fate", "fear", "feed", "feel", "feet", "fell", "felt", "file",
    "fill", "film", "find", "fine", "fire", "firm", "fish", "five", "flag", "flat",
    "flew", "flow", "food", "foot", "ford", "form", "fort", "four", "free", "from",
    "fuel", "full", "fund", "gain", "game", "gate", "gave", "gear", "gene", "gift",
    "girl", "give", "glad", "goal", "goes", "gold", "golf", "gone", "good", "gray",
    "grew", "grey", "grow", "gulf", "hair", "half", "hall", "hand", "hang", "hard",
    "harm", "hate", "have", "head", "hear", "heat", "held", "hell", "help", "here",
    "hero", "high", "hill", "hint", "hire", "hold", "hole", "holy", "home", "hope",
    "host", "hour", "huge", "hung", "hunt", "hurt", "idea", "inch", "into", "iron",
    "item", "jack", "jane", "jean", "john", "join", "jump", "jury", "just", "keen",
    "keep", "kept", "kick", "kill", "kind", "king", "knee", "knew", "know", "lack",
    "lady", "laid", "lake", "land", "lane", "last", "late", "lead", "left", "less",
    "life", "lift", "like", "line", "link", "list", "live", "load", "loan", "lock",
    "logo", "long", "look", "lord", "lose", "loss", "lost", "love", "luck", "made",
    "mail", "main", "make", "male", "many", "mark", "mass", "matt", "meal", "mean",
    "meat", "meet", "menu", "mere", "mike", "mile", "milk", "mill", "mind", "mine",
    "miss", "mode", "mood", "moon", "more", "most", "move", "much", "must", "name",
    "navy", "near", "neck", "need", "news", "next", "nice", "nick", "nine", "none",
    "nose", "note", "okay", "once", "only", "onto", "open", "oral", "over", "pace",
    "pack", "page", "paid", "pain", "pair", "palm", "park", "part", "pass", "past",
    "path", "peak", "pick", "pink", "pipe", "plan", "play", "plot", "plug", "plus",
    "poll", "pool", "poor", "port", "post", "pour", "pull", "pure", "push", "race",
    "rail", "rain", "rank", "rare", "rate", "read", "real", "rear", "rely", "rent",
    "rest", "rice", "rich", "ride", "ring", "rise", "risk", "road", "rock", "role",
    "roll", "roof", "room", "root", "rose", "rule", "rush", "ruth", "safe", "said",
    "sake", "sale", "salt", "same", "sand", "save", "seat", "seed", "seek", "seem",
    "seen", "self", "sell", "send", "sent", "sept", "ship", "shop", "shot", "show",
    "shut", "sick", "side", "sign", "site", "size", "skin", "slip", "slow", "snow",
    "soft", "soil", "sold", "sole", "some", "song", "soon", "sort", "soul", "spot",
    "star", "stay", "step", "stop", "such", "suit", "sure", "take", "tale", "talk",
    "tall", "tank", "tape", "task", "team", "tech", "tell", "tend", "term", "test",
    "text", "than", "that", "them", "then", "they", "thin", "this", "thus", "till",
    "time", "tiny", "told", "toll", "tone", "tony", "took", "tool", "tour", "town",
    "tree", "trip", "true", "tune", "turn", "twin", "type", "unit", "upon", "used",
    "user", "uses", "vary", "vast", "very", "vice", "view", "vote", "wage", "wait",
    "wake", "walk", "wall", "want", "ward", "warm", "wash", "wave", "ways", "weak",
    "wear", "week", "well", "went", "were", "west", "what", "when", "whom", "wide",
    "wife", "wild", "will", "wind", "wine", "wing", "wire", "wise", "wish", "with",
    "wood", "word", "wore", "work", "worn", "yard", "yeah", "year", "your", "zero",
    "zone",
}


def load_wordlist(length: int = 4) -> set[str]:
    """Return a set of lowercase English words of the given length."""
    cached = _load_cache(length)
    if cached:
        return cached

    downloaded = _download(length)
    if downloaded:
        _save_cache(downloaded)
        return downloaded

    return _load_system_dict(length)


def _load_cache(length: int) -> set[str]:
    if not CACHE_FILE.exists():
        return set()
    try:
        return {
            w.strip().lower()
            for w in CACHE_FILE.read_text(encoding="utf-8").splitlines()
            if len(w.strip()) == length and w.strip().isalpha()
        }
    except OSError:
        return set()


def _save_cache(words: set[str]) -> None:
    try:
        CACHE_FILE.write_text("\n".join(sorted(words)), encoding="utf-8")
    except OSError:
        pass


def _download(length: int, timeout: float = 15.0) -> set[str]:
    try:
        with urllib.request.urlopen(WORDLIST_URL, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return set()

    return {
        w.strip().lower()
        for w in data.splitlines()
        if len(w.strip()) == length and w.strip().isalpha()
    }


def _load_system_dict(length: int) -> set[str]:
    if not SYSTEM_DICT.exists():
        return set()
    try:
        return {
            w.strip().lower()
            for w in SYSTEM_DICT.read_text(encoding="utf-8", errors="ignore").splitlines()
            if len(w.strip()) == length and w.strip().isalpha()
        }
    except OSError:
        return set()


if __name__ == "__main__":
    words = load_wordlist()
    print(f"Loaded {len(words)} four-letter words.")
    if words:
        sample = sorted(words)[:10]
        print("Sample:", ", ".join(sample))
