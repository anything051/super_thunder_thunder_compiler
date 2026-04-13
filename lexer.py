from dataclasses import dataclass


@dataclass(frozen=True)
class SourcePosition:
    line: int
    column: int


@dataclass(frozen=True)
class Token:
    kind: str
    lexeme: str
    position: SourcePosition


class LexerError(Exception):
    """Raised when lexical analysis fails."""


def tokenize(source_code: str):
    raise NotImplementedError("lexer stage is not implemented yet")
