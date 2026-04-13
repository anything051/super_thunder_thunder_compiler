from dataclasses import dataclass


KEYWORDS = {
    "PROGRAM",
    "VAR",
    "TYPE",
    "PROCEDURE",
    "BEGIN",
    "END",
    "IF",
    "THEN",
    "ELSE",
    "FI",
    "WHILE",
    "DO",
    "ENDWH",
    "READ",
    "WRITE",
    "RETURN",
    "INTEGER",
    "CHAR",
    "ARRAY",
    "RECORD",
    "OF",
}

SINGLE_CHAR_TOKENS = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "TIMES",
    "/": "OVER",
    "=": "EQ",
    "<": "LT",
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LMIDPAREN",
    "]": "RMIDPAREN",
    ".": "DOT",
    ";": "SEMI",
    ",": "COMMA",
    ":": "COLON",
}


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

    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.line = line
        self.column = column


def tokenize(source_code: str) -> list[Token]:
    tokens: list[Token] = []
    index = 0
    line = 1
    column = 1
    length = len(source_code)

    def current_position() -> SourcePosition:
        return SourcePosition(line=line, column=column)

    def peek(offset: int = 0) -> str:
        target = index + offset
        if target >= length:
            return ""
        return source_code[target]

    def advance() -> str:
        nonlocal index, line, column
        char = source_code[index]
        index += 1
        if char == "\n":
            line += 1
            column = 1
        else:
            column += 1
        return char

    def consume_while(predicate) -> str:
        chars: list[str] = []
        while index < length and predicate(peek()):
            chars.append(advance())
        return "".join(chars)

    while index < length:
        char = peek()

        if char.isspace():
            advance()
            continue

        if char == "{":
            start = current_position()
            advance()
            while index < length and peek() != "}":
                advance()
            if index >= length:
                raise LexerError("unclosed comment", start.line, start.column)
            advance()
            continue

        if char.isalpha():
            start = current_position()
            lexeme = consume_while(lambda ch: ch.isalnum())
            upper_lexeme = lexeme.upper()
            kind = upper_lexeme if upper_lexeme in KEYWORDS else "ID"
            tokens.append(Token(kind=kind, lexeme=lexeme, position=start))
            continue

        if char.isdigit():
            start = current_position()
            lexeme = consume_while(str.isdigit)
            tokens.append(Token(kind="INTC", lexeme=lexeme, position=start))
            continue

        if char == "'":
            start = current_position()
            advance()
            value = peek()
            if value in {"", "\n", "'"}:
                raise LexerError("invalid character literal", start.line, start.column)
            advance()
            if peek() != "'":
                raise LexerError("invalid character literal", start.line, start.column)
            advance()
            tokens.append(Token(kind="CHARC", lexeme=value, position=start))
            continue

        if char == ":" and peek(1) == "=":
            start = current_position()
            advance()
            advance()
            tokens.append(Token(kind="ASSIGN", lexeme=":=", position=start))
            continue

        if char == "." and peek(1) == ".":
            start = current_position()
            advance()
            advance()
            tokens.append(Token(kind="UNDERANGE", lexeme="..", position=start))
            continue

        if char in SINGLE_CHAR_TOKENS:
            start = current_position()
            advance()
            tokens.append(Token(kind=SINGLE_CHAR_TOKENS[char], lexeme=char, position=start))
            continue

        raise LexerError(f"unexpected character {char!r}", line, column)

    tokens.append(Token(kind="EOF", lexeme="", position=SourcePosition(line, column)))
    return tokens
