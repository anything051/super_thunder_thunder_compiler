from lexer import Token


class ParserError(Exception):
    """Raised when parsing fails."""


def parse(tokens: list[Token]):
    raise NotImplementedError("parser stage is not implemented yet")
