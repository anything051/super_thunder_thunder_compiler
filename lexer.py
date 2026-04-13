"""SNL 编译器的词法分析模块。

负责把源代码字符串扫描成带位置的 Token 序列，供 parser 使用。
"""

from dataclasses import dataclass


# SNL 语言的关键字集合，用于把普通字母串区分成关键字或标识符。
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

# 单字符符号到 token 类型的映射表。
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
    """记录源码中的行列位置，便于后续报错定位。"""

    line: int
    column: int


@dataclass(frozen=True)
class Token:
    """表示一个词法单元，包含类型、原始文本和值出现位置。"""

    kind: str
    lexeme: str
    position: SourcePosition


class LexerError(Exception):
    """词法分析失败时抛出的异常。"""

    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.line = line
        self.column = column


def tokenize(source_code: str) -> list[Token]:
    """把 SNL 源代码切分成 Token 序列。"""

    tokens: list[Token] = []
    index = 0
    line = 1
    column = 1
    length = len(source_code)

    def current_position() -> SourcePosition:
        """返回当前扫描位置。"""
        return SourcePosition(line=line, column=column)

    def peek(offset: int = 0) -> str:
        """查看当前位置之后的字符，但不真正消耗它。"""
        target = index + offset
        if target >= length:
            return ""
        return source_code[target]

    def advance() -> str:
        """向前移动一个字符，并同步更新行列号。"""
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
        """连续读取满足条件的字符，常用于读标识符或数字。"""
        chars: list[str] = []
        while index < length and predicate(peek()):
            chars.append(advance())
        return "".join(chars)

    while index < length:
        char = peek()

        if char.isspace():
            # 空白字符直接跳过，不生成 token。
            advance()
            continue

        if char == "{":
            # SNL 注释使用花括号包围，整段跳过。
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
            # 连续字母数字串先读出来，再判断是关键字还是普通标识符。
            lexeme = consume_while(lambda ch: ch.isalnum())
            upper_lexeme = lexeme.upper()
            kind = upper_lexeme if upper_lexeme in KEYWORDS else "ID"
            tokens.append(Token(kind=kind, lexeme=lexeme, position=start))
            continue

        if char.isdigit():
            start = current_position()
            # 连续数字构成整数字面量。
            lexeme = consume_while(str.isdigit)
            tokens.append(Token(kind="INTC", lexeme=lexeme, position=start))
            continue

        if char == "'":
            start = current_position()
            # 字符常量要求形如 'a'，这里只接受单个字符。
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
            # 识别赋值符号 :=。
            advance()
            advance()
            tokens.append(Token(kind="ASSIGN", lexeme=":=", position=start))
            continue

        if char == "." and peek(1) == ".":
            start = current_position()
            # 识别数组下界上界使用的区间符 ..
            advance()
            advance()
            tokens.append(Token(kind="UNDERANGE", lexeme="..", position=start))
            continue

        if char in SINGLE_CHAR_TOKENS:
            start = current_position()
            # 普通单字符符号直接查表生成 token。
            advance()
            tokens.append(Token(kind=SINGLE_CHAR_TOKENS[char], lexeme=char, position=start))
            continue

        raise LexerError(f"unexpected character {char!r}", line, column)

    # 在末尾补一个 EOF，方便 parser 判断输入结束。
    tokens.append(Token(kind="EOF", lexeme="", position=SourcePosition(line, column)))
    return tokens
