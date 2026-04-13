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
    """Raised when parsing fails."""

    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.line = line
        self.column = column


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.index = 0

    def current(self) -> Token:
        return self.tokens[self.index]

    def advance(self) -> Token:
        token = self.current()
        if self.index < len(self.tokens) - 1:
            self.index += 1
        return token

    def match(self, *kinds: str) -> Token | None:
        if self.current().kind in kinds:
            return self.advance()
        return None

    def expect(self, kind: str) -> Token:
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
        declarations: list = []

        while self.current().kind in {"TYPE", "VAR"}:
            if self.match("TYPE"):
                while self.current().kind == "ID":
                    name_token = self.expect("ID")
                    self.expect("EQ")
                    type_spec = self.parse_type_spec()
                    declarations.append(
                        TypeDeclNode(name=name_token.lexeme, type_spec=type_spec, position=name_token.position)
                    )
                    self.match("SEMI")
            elif self.match("VAR"):
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
        token = self.current()

        if token.kind in {"INTEGER", "CHAR", "ID"}:
            self.advance()
            return token.lexeme if token.kind == "ID" else token.kind

        if self.match("ARRAY"):
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
        names = [self.expect("ID").lexeme]
        while self.match("COMMA"):
            names.append(self.expect("ID").lexeme)
        return names

    def parse_procedures(self) -> list[ProcedureDeclNode]:
        procedures = []
        while self.current().kind == "PROCEDURE":
            keyword = self.expect("PROCEDURE")
            name_token = self.expect("ID")
            params = []
            if self.match("LPAREN"):
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
        begin_token = self.expect("BEGIN")
        statements = self.parse_statement_sequence({end_kind})
        self.expect(end_kind)
        return CompoundStmtNode(statements=statements, position=begin_token.position)

    def parse_statement_sequence(self, stop_kinds: set[str]) -> list:
        statements = []
        while self.current().kind not in stop_kinds and self.current().kind != "EOF":
            statements.append(self.parse_statement())
            if self.current().kind in stop_kinds:
                break
            self.match("SEMI")
        return statements

    def parse_statement(self):
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
        token = self.expect("READ")
        self.expect("LPAREN")
        target = self.parse_variable_ref()
        self.expect("RPAREN")
        return ReadStmtNode(target=target, position=token.position)

    def parse_write_statement(self) -> WriteStmtNode:
        token = self.expect("WRITE")
        self.expect("LPAREN")
        expression = self.parse_expression()
        self.expect("RPAREN")
        return WriteStmtNode(expression=expression, position=token.position)

    def parse_return_statement(self) -> ReturnStmtNode:
        token = self.expect("RETURN")
        expression = None
        if self.current().kind not in {"SEMI", "END", "ELSE", "FI", "ENDWH", "EOF"}:
            expression = self.parse_expression()
        return ReturnStmtNode(expression=expression, position=token.position)

    def parse_assignment_or_call(self):
        identifier = self.expect("ID")

        if self.current().kind == "LPAREN":
            self.advance()
            arguments = []
            if self.current().kind != "RPAREN":
                arguments.append(self.parse_expression())
                while self.match("COMMA"):
                    arguments.append(self.parse_expression())
            self.expect("RPAREN")
            return CallStmtNode(name=identifier.lexeme, arguments=arguments, position=identifier.position)

        variable = self.parse_variable_ref_after_identifier(identifier)
        self.expect("ASSIGN")
        value = self.parse_expression()
        return AssignStmtNode(target=variable, value=value, position=identifier.position)

    def parse_expression(self):
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
        token = self.current()

        if token.kind == "INTC":
            self.advance()
            return ConstNode(value=int(token.lexeme), position=token.position)

        if token.kind == "CHARC":
            self.advance()
            return ConstNode(value=token.lexeme, position=token.position)

        if token.kind == "LPAREN":
            self.advance()
            expression = self.parse_expression()
            self.expect("RPAREN")
            return expression

        if token.kind == "ID":
            return self.parse_variable_ref()

        raise ParserError(
            f"unexpected token {token.kind} in expression",
            token.position.line,
            token.position.column,
        )

    def parse_variable_ref(self) -> VarRefNode:
        identifier = self.expect("ID")
        return self.parse_variable_ref_after_identifier(identifier)

    def parse_variable_ref_after_identifier(self, identifier: Token) -> VarRefNode:
        selectors = []
        while True:
            if self.match("LMIDPAREN"):
                selectors.append({"kind": "index", "expression": self.parse_expression()})
                self.expect("RMIDPAREN")
                continue
            if self.match("DOT"):
                field = self.expect("ID")
                selectors.append({"kind": "field", "name": field.lexeme})
                continue
            break

        return VarRefNode(name=identifier.lexeme, position=identifier.position, selectors=selectors)


def parse(tokens: list[Token]):
    return Parser(tokens).parse_program()
