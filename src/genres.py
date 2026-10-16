import difflib
import re
from typing import Callable, Iterable

# AniList's genre list (checked against the GenreCollection query)
VALID_GENRES = (
    "Action", "Adventure", "Comedy", "Drama", "Ecchi", "Fantasy", "Hentai", "Horror",
    "Mahou Shoujo", "Mecha", "Music", "Mystery", "Psychological", "Romance", "Sci-Fi",
    "Slice of Life", "Sports", "Supernatural", "Thriller",
)

# Shorter or alternative spellings, matched case-insensitively
GENRE_ALIASES = {
    "sol": "Slice of Life",
    "magical girl": "Mahou Shoujo",
    "mahou shojo": "Mahou Shoujo",
    "scifi": "Sci-Fi",
    "sci fi": "Sci-Fi",
}

GenreMatcher = Callable[[Iterable[str] | None], bool]
_Predicate = Callable[[frozenset[str]], bool]
_OPERATORS = ("&", "|", "(", ")", "!", "~")
_LOOKUP = {genre.casefold(): genre for genre in VALID_GENRES}
_LOOKUP.update({alias.casefold(): genre for alias, genre in GENRE_ALIASES.items()})


def _has(genre: str) -> _Predicate:
    wanted = genre.casefold()
    return lambda genres: wanted in genres


def _not(node: _Predicate) -> _Predicate:
    return lambda genres: not node(genres)


def _any(nodes: list[_Predicate]) -> _Predicate:
    return lambda genres: any(node(genres) for node in nodes)


def _all(nodes: list[_Predicate]) -> _Predicate:
    return lambda genres: all(node(genres) for node in nodes)


def _tokenize(text: str) -> list[str]:
    """Split an expression into operators and genre names."""
    return [piece.strip() for piece in re.split(r"([&|()!~])", text) if piece.strip()]


class _Parser:
    """Recursive descent parser for genre expressions."""

    def __init__(self, tokens: list[str], option: str):
        self.tokens = tokens
        self.corrected_tokens = list(tokens)
        self.had_typo = False
        self.option = option
        self.pos = 0

    def _error(self, message: str) -> ValueError:
        return ValueError(f"{self.option}: {message}")

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _take(self) -> str | None:
        token = self._peek()
        self.pos += 1
        return token

    def parse(self) -> _Predicate:
        node = self._expr()
        leftover = self._peek()
        if leftover == ")":
            raise self._error("unbalanced ')'")
        if leftover is not None:
            raise self._error(f"expected & or | before '{leftover}'")
        return node

    def _expr(self) -> _Predicate:
        nodes = [self._term()]
        while self._peek() == "|":
            self._take()
            nodes.append(self._term())
        return nodes[0] if len(nodes) == 1 else _any(nodes)

    def _term(self) -> _Predicate:
        nodes = [self._factor()]
        while self._peek() == "&":
            self._take()
            nodes.append(self._factor())
        return nodes[0] if len(nodes) == 1 else _all(nodes)

    def _factor(self) -> _Predicate:
        token = self._take()
        if token is None:
            raise self._error("the expression ends too early, a genre is missing")
        if token in ("!", "~"):
            return _not(self._factor())
        if token == "(":
            node = self._expr()
            closing = self._take()
            if closing is None:
                raise self._error("missing ')'")
            if closing != ")":
                raise self._error(f"expected & or | before '{closing}'")
            return node
        if token in _OPERATORS:
            raise self._error(f"a genre is missing before '{token}'")
        return self._genre(token)

    def _genre(self, name: str) -> _Predicate:
        index = self.pos - 1
        key = " ".join(name.casefold().split())
        if key in _LOOKUP:
            return _has(_LOOKUP[key])

        words = key.split()
        if len(words) > 1 and sum(word in _LOOKUP for word in words) >= 2:
            hint = " Did you forget & or | between genres?"
            raise self._error(
                f"unknown genre '{name}'.{hint} Valid: {', '.join(VALID_GENRES)}. Aliases: {', '.join(GENRE_ALIASES)}"
            )

        close = difflib.get_close_matches(key, list(_LOOKUP), n=1, cutoff=0.6)
        if close:
            matched_canonical = _LOOKUP[close[0]]
            self.corrected_tokens[index] = matched_canonical.lower()
            self.had_typo = True
            return _has(matched_canonical)

        raise self._error(
            f"unknown genre '{name}'. Valid: {', '.join(VALID_GENRES)}. Aliases: {', '.join(GENRE_ALIASES)}"
        )


def parse_genre_expression(text: str, option: str) -> tuple[GenreMatcher, tuple[str, str] | None]:
    """
    Parse a genre expression into a matcher.

    Operators are `&` for both, `|` for either, `!` or `~` for not, and
    parentheses for grouping. Operators bind in the order not, and, or.
    """
    if not text.strip():
        raise ValueError(f'{option} needs an expression, like {option} "comedy&!romance"')

    parser = _Parser(_tokenize(text), option)
    predicate = parser.parse()
    correction = (text.strip(), "".join(parser.corrected_tokens)) if parser.had_typo else None

    def matches(genres: Iterable[str] | None) -> bool:
        return predicate(frozenset(genre.casefold() for genre in genres or ()))

    return matches, correction
