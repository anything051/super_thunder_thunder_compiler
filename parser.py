"""SNL 编译器的递归下降语法分析模块。

负责把 Token 序列解析成 AST，供 semantic 和 codegen 使用。
"""

from ast_node import (
    AssignStmtNode,
    BinaryExprNode,
    CallStmtNode,
    CompoundStmtNode,
    ConstNode,
    IfStmtNode,
    ProcedureDeclNode,
    ProgramNode,
    ReadStmtNode,
    ReturnStmtNode,
    TypeDeclNode,
    VarDeclNode,
    VarRefNode,
    WhileStmtNode,
    WriteStmtNode,
)
from lexer import Token


class ParserError(Exception):
    """语法分析失败时抛出的异常。"""

    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.line = line
        self.column = column


class Parser:
    """递归下降语法分析器。"""

    def __init__(self, tokens: list[Token]):
        """保存 token 序列并初始化当前位置。"""
        self.tokens = tokens
        self.index = 0

    def current(self) -> Token:
        """返回当前尚未消费的 token。"""
        return self.tokens[self.index]

    def advance(self) -> Token:
        """消费当前 token，并移动到下一个位置。"""
        token = self.current()
        if self.index < len(self.tokens) - 1:
            self.index += 1
        return token

    def match(self, *kinds: str) -> Token | None:
        """如果当前 token 类型匹配，则消费并返回它。"""
        if self.current().kind in kinds:
            return self.advance()
        return None

    def expect(self, kind: str) -> Token:
        """要求当前 token 必须是指定类型，否则直接报语法错误。"""
        token = self.current()
        if token.kind != kind:
            raise ParserError(
                f"expected {kind}, got {token.kind}",
                token.position.line,
                token.position.column,
            )
        self.advance()
        return token

    def parse_program(self) -> ProgramNode:
        """解析整个程序入口。"""
        self.expect("PROGRAM")
        name_token = self.expect("ID")
        declarations = self.parse_declarations()
        procedures = self.parse_procedures()
        body = self.parse_block("END")
        self.expect("EOF")
        return ProgramNode(
            name=name_token.lexeme,
            declarations=declarations,
            procedures=procedures,
            body=body,
            position=name_token.position,
        )

    def parse_declarations(self) -> list:
        """解析 TYPE / VAR 声明区。"""
        declarations: list = []

        while self.current().kind in {"TYPE", "VAR"}:
            if self.match("TYPE"):
                # TYPE 区允许连续出现多个类型别名定义。
                while self.current().kind == "ID":
                    name_token = self.expect("ID")
                    self.expect("EQ")
                    type_spec = self.parse_type_spec()
                    declarations.append(
                        TypeDeclNode(name=name_token.lexeme, type_spec=type_spec, position=name_token.position)
                    )
                    self.match("SEMI")
            elif self.match("VAR"):
                # VAR 区允许连续出现多个变量声明。
                while self.current().kind == "ID":
                    names = self.parse_identifier_list()
                    self.expect("COLON")
                    type_spec = self.parse_type_spec()
                    declarations.append(
                        VarDeclNode(names=names, type_spec=type_spec, position=self.current().position)
                    )
                    self.match("SEMI")

        return declarations

    def parse_type_spec(self):
        """解析类型说明，支持基本类型、数组和记录。"""
        token = self.current()

        if token.kind in {"INTEGER", "CHAR", "ID"}:
            # 基本类型或类型别名直接返回标记值。
            self.advance()
            return token.lexeme if token.kind == "ID" else token.kind

        if self.match("ARRAY"):
            # 数组类型保存上下界和元素类型，后续语义分析再解析成正式类型对象。
            self.expect("LMIDPAREN")
            lower = self.expect("INTC")
            self.expect("UNDERANGE")
            upper = self.expect("INTC")
            self.expect("RMIDPAREN")
            self.expect("OF")
            element_type = self.parse_type_spec()
            return {
                "kind": "ARRAY",
                "lower": int(lower.lexeme),
                "upper": int(upper.lexeme),
                "element_type": element_type,
            }

        if self.match("RECORD"):
            # 记录类型按字段列表组织，字段类型稍后在语义阶段解析。
            fields = []
            while self.current().kind != "END":
                names = self.parse_identifier_list()
                self.expect("COLON")
                field_type = self.parse_type_spec()
                fields.append({"names": names, "type": field_type})
                self.match("SEMI")
            self.expect("END")
            return {"kind": "RECORD", "fields": fields}

        raise ParserError(
            f"expected type specification, got {token.kind}",
            token.position.line,
            token.position.column,
        )

    def parse_identifier_list(self) -> list[str]:
        """解析以逗号分隔的标识符列表。"""
        names = [self.expect("ID").lexeme]
        while self.match("COMMA"):
            names.append(self.expect("ID").lexeme)
        return names

    def parse_procedures(self) -> list[ProcedureDeclNode]:
        """解析过程声明列表。"""
        procedures = []
        while self.current().kind == "PROCEDURE":
            keyword = self.expect("PROCEDURE")
            name_token = self.expect("ID")
            params = []
            if self.match("LPAREN"):
                # 过程参数可为空，也可为参数列表。
                if self.current().kind != "RPAREN":
                    params = self.parse_param_list()
                self.expect("RPAREN")
            self.expect("SEMI")
            declarations = self.parse_declarations()
            body = self.parse_block("END")
            self.match("SEMI")
            procedures.append(
                ProcedureDeclNode(
                    name=name_token.lexeme,
                    params=params,
                    declarations=declarations,
                    body=body,
                    position=keyword.position,
                )
            )
        return procedures

    def parse_param_list(self) -> list[VarDeclNode]:
        """解析过程形参列表。"""
        params = []
        while True:
            names = self.parse_identifier_list()
            self.expect("COLON")
            type_spec = self.parse_type_spec()
            params.append(VarDeclNode(names=names, type_spec=type_spec))
            if not self.match("SEMI"):
                break
        return params

    def parse_block(self, end_kind: str) -> CompoundStmtNode:
        """解析 BEGIN...END 形式的复合语句块。"""
        begin_token = self.expect("BEGIN")
        statements = self.parse_statement_sequence({end_kind})
        self.expect(end_kind)
        return CompoundStmtNode(statements=statements, position=begin_token.position)

    def parse_statement_sequence(self, stop_kinds: set[str]) -> list:
        """持续解析语句，直到遇到指定的结束符号。"""
        statements = []
        while self.current().kind not in stop_kinds and self.current().kind != "EOF":
            statements.append(self.parse_statement())
            if self.current().kind in stop_kinds:
                break
            self.match("SEMI")
        return statements

    def parse_statement(self):
        """根据当前 token 分派到具体语句解析函数。"""
        token = self.current()

        if token.kind == "IF":
            return self.parse_if_statement()
        if token.kind == "WHILE":
            return self.parse_while_statement()
        if token.kind == "READ":
            return self.parse_read_statement()
        if token.kind == "WRITE":
            return self.parse_write_statement()
        if token.kind == "RETURN":
            return self.parse_return_statement()
        if token.kind == "ID":
            return self.parse_assignment_or_call()

        raise ParserError(
            f"unexpected token {token.kind} in statement",
            token.position.line,
            token.position.column,
        )

    def parse_if_statement(self) -> IfStmtNode:
        """解析 IF THEN ELSE FI 语句。"""
        token = self.expect("IF")
        condition = self.parse_expression()
        self.expect("THEN")
        then_branch = CompoundStmtNode(
            statements=self.parse_statement_sequence({"ELSE", "FI"}),
            position=token.position,
        )
        else_branch = None
        if self.match("ELSE"):
            else_branch = CompoundStmtNode(
                statements=self.parse_statement_sequence({"FI"}),
                position=token.position,
            )
        self.expect("FI")
        return IfStmtNode(condition=condition, then_branch=then_branch, else_branch=else_branch, position=token.position)

    def parse_while_statement(self) -> WhileStmtNode:
        """解析 WHILE DO ENDWH 循环语句。"""
        token = self.expect("WHILE")
        condition = self.parse_expression()
        self.expect("DO")
        body = CompoundStmtNode(
            statements=self.parse_statement_sequence({"ENDWH"}),
            position=token.position,
        )
        self.expect("ENDWH")
        return WhileStmtNode(condition=condition, body=body, position=token.position)

    def parse_read_statement(self) -> ReadStmtNode:
        """解析 READ 语句。"""
        token = self.expect("READ")
        self.expect("LPAREN")
        target = self.parse_variable_ref()
        self.expect("RPAREN")
        return ReadStmtNode(target=target, position=token.position)

    def parse_write_statement(self) -> WriteStmtNode:
        """解析 WRITE 语句。"""
        token = self.expect("WRITE")
        self.expect("LPAREN")
        expression = self.parse_expression()
        self.expect("RPAREN")
        return WriteStmtNode(expression=expression, position=token.position)

    def parse_return_statement(self) -> ReturnStmtNode:
        """解析 RETURN 语句，允许无返回值或携带表达式。"""
        token = self.expect("RETURN")
        expression = None
        if self.current().kind not in {"SEMI", "END", "ELSE", "FI", "ENDWH", "EOF"}:
            expression = self.parse_expression()
        return ReturnStmtNode(expression=expression, position=token.position)

    def parse_assignment_or_call(self):
        """解析以标识符开头的语句，可能是赋值也可能是过程调用。"""
        identifier = self.expect("ID")

        if self.current().kind == "LPAREN":
            # 紧跟左括号时按过程调用处理。
            self.advance()
            arguments = []
            if self.current().kind != "RPAREN":
                arguments.append(self.parse_expression())
                while self.match("COMMA"):
                    arguments.append(self.parse_expression())
            self.expect("RPAREN")
            return CallStmtNode(name=identifier.lexeme, arguments=arguments, position=identifier.position)

        # 否则按变量引用 + 赋值语句处理。
        variable = self.parse_variable_ref_after_identifier(identifier)
        self.expect("ASSIGN")
        value = self.parse_expression()
        return AssignStmtNode(target=variable, value=value, position=identifier.position)

    def parse_expression(self):
        """解析表达式的比较层。"""
        left = self.parse_additive()
        while self.current().kind in {"LT", "EQ"}:
            operator = self.advance()
            right = self.parse_additive()
            left = BinaryExprNode(
                operator=operator.lexeme,
                left=left,
                right=right,
                position=operator.position,
            )
        return left

    def parse_additive(self):
        """解析加减表达式。"""
        left = self.parse_term()
        while self.current().kind in {"PLUS", "MINUS"}:
            operator = self.advance()
            right = self.parse_term()
            left = BinaryExprNode(
                operator=operator.lexeme,
                left=left,
                right=right,
                position=operator.position,
            )
        return left

    def parse_term(self):
        """解析乘除表达式。"""
        left = self.parse_factor()
        while self.current().kind in {"TIMES", "OVER"}:
            operator = self.advance()
            right = self.parse_factor()
            left = BinaryExprNode(
                operator=operator.lexeme,
                left=left,
                right=right,
                position=operator.position,
            )
        return left

    def parse_factor(self):
        """解析最基本的表达式单元。"""
        token = self.current()

        if token.kind == "INTC":
            # 整数字面量直接转成整数常量节点。
            self.advance()
            return ConstNode(value=int(token.lexeme), position=token.position)

        if token.kind == "CHARC":
            # 字符常量保持为单字符字符串。
            self.advance()
            return ConstNode(value=token.lexeme, position=token.position)

        if token.kind == "LPAREN":
            # 括号表达式优先解析内部，再返回内部结果。
            self.advance()
            expression = self.parse_expression()
            self.expect("RPAREN")
            return expression

        if token.kind == "ID":
            # 表达式中出现标识符时，按变量引用解析。
            return self.parse_variable_ref()

        raise ParserError(
            f"unexpected token {token.kind} in expression",
            token.position.line,
            token.position.column,
        )

    def parse_variable_ref(self) -> VarRefNode:
        """解析完整变量引用，入口要求当前位置是标识符。"""
        identifier = self.expect("ID")
        return self.parse_variable_ref_after_identifier(identifier)

    def parse_variable_ref_after_identifier(self, identifier: Token) -> VarRefNode:
        """在已经读到变量名后，继续解析数组下标或记录字段 selector。"""
        selectors = []
        while True:
            if self.match("LMIDPAREN"):
                # 数组下标会记录成 selector，后续语义和 codegen 继续处理。
                selectors.append({"kind": "index", "expression": self.parse_expression()})
                self.expect("RMIDPAREN")
                continue
            if self.match("DOT"):
                # 记录字段访问同样记录为 selector 链。
                field = self.expect("ID")
                selectors.append({"kind": "field", "name": field.lexeme})
                continue
            break

        return VarRefNode(name=identifier.lexeme, position=identifier.position, selectors=selectors)


def parse(tokens: list[Token]):
    """对外暴露的语法分析入口。"""
    return Parser(tokens).parse_program()
