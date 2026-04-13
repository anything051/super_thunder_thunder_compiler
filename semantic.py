from dataclasses import dataclass, field
from typing import Any

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


SEMANTIC_ERROR_TYPES = {
    "DUPLICATE_DECLARATION",
    "UNDEFINED_IDENTIFIER",
    "UNDEFINED_TYPE",
    "ASSIGNMENT_TYPE_MISMATCH",
    "INVALID_ARRAY_INDEX_TYPE",
    "NON_ARRAY_INDEXED",
    "INVALID_RECORD_FIELD",
    "NON_RECORD_FIELD_ACCESS",
    "CALL_ARGUMENT_COUNT_MISMATCH",
    "CALL_ARGUMENT_TYPE_MISMATCH",
    "INVALID_RETURN",
    "INVALID_IO_OPERAND",
}


@dataclass(frozen=True)
class BuiltinType:
    name: str


@dataclass(frozen=True)
class ArrayType:
    lower: int
    upper: int
    element_type: Any


@dataclass(frozen=True)
class RecordType:
    fields: dict[str, Any]


@dataclass
class Symbol:
    name: str
    kind: str
    type_info: Any = None
    position: Any = None
    params: list[Any] = field(default_factory=list)
    scope: Any = None


@dataclass
class Scope:
    name: str
    parent: Any = None
    symbols: dict[str, Symbol] = field(default_factory=dict)

    def define(self, symbol: Symbol) -> None:
        if symbol.name in self.symbols:
            raise SemanticError(
                f"duplicate declaration '{symbol.name}'",
                _line_of(symbol.position),
                _column_of(symbol.position),
                "DUPLICATE_DECLARATION",
            )
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Symbol | None:
        scope = self
        while scope is not None:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None


@dataclass
class SemanticResult:
    program_name: str
    global_scope: Scope


class SemanticError(Exception):
    """Raised when semantic analysis fails."""

    def __init__(self, message: str, line: int | None, column: int | None, error_code: str):
        super().__init__(message)
        self.line = line
        self.column = column
        self.error_code = error_code


INTEGER_TYPE = BuiltinType("INTEGER")
CHAR_TYPE = BuiltinType("CHAR")
BOOLEAN_TYPE = BuiltinType("BOOLEAN")


class SemanticAnalyzer:
    def analyze(self, ast: ProgramNode) -> SemanticResult:
        global_scope = Scope(name=ast.name)
        self._define_builtin_types(global_scope)
        self._declare_definitions(ast.declarations, global_scope)
        self._declare_procedure_headers(ast.procedures, global_scope)

        for procedure in ast.procedures:
            self._analyze_procedure(procedure, global_scope)

        self._analyze_compound(ast.body, global_scope, in_procedure=False)
        return SemanticResult(program_name=ast.name, global_scope=global_scope)

    def _define_builtin_types(self, scope: Scope) -> None:
        scope.define(Symbol(name="INTEGER", kind="type", type_info=INTEGER_TYPE))
        scope.define(Symbol(name="CHAR", kind="type", type_info=CHAR_TYPE))

    def _declare_definitions(self, declarations: list[Any], scope: Scope) -> None:
        for declaration in declarations:
            if isinstance(declaration, TypeDeclNode):
                resolved = self._resolve_type_spec(declaration.type_spec, scope, declaration.position)
                scope.define(Symbol(declaration.name, "type", resolved, declaration.position))
            elif isinstance(declaration, VarDeclNode):
                resolved = self._resolve_type_spec(declaration.type_spec, scope, declaration.position)
                for name in declaration.names:
                    scope.define(Symbol(name, "var", resolved, declaration.position))

    def _declare_procedure_headers(self, procedures: list[ProcedureDeclNode], scope: Scope) -> None:
        for procedure in procedures:
            params = []
            for parameter_decl in procedure.params:
                parameter_type = self._resolve_type_spec(parameter_decl.type_spec, scope, procedure.position)
                for name in parameter_decl.names:
                    params.append(Symbol(name=name, kind="param", type_info=parameter_type, position=procedure.position))
            scope.define(
                Symbol(
                    name=procedure.name,
                    kind="procedure",
                    params=params,
                    position=procedure.position,
                )
            )

    def _analyze_procedure(self, procedure: ProcedureDeclNode, global_scope: Scope) -> None:
        procedure_symbol = global_scope.lookup(procedure.name)
        procedure_scope = Scope(name=procedure.name, parent=global_scope)

        for param_symbol in procedure_symbol.params:
            procedure_scope.define(Symbol(param_symbol.name, "param", param_symbol.type_info, param_symbol.position))

        self._declare_definitions(procedure.declarations, procedure_scope)
        procedure_symbol.scope = procedure_scope
        self._analyze_compound(procedure.body, procedure_scope, in_procedure=True)

    def _analyze_compound(self, compound: CompoundStmtNode, scope: Scope, in_procedure: bool) -> None:
        for statement in compound.statements:
            self._analyze_statement(statement, scope, in_procedure)

    def _analyze_statement(self, statement: Any, scope: Scope, in_procedure: bool) -> None:
        if isinstance(statement, AssignStmtNode):
            target_type = self._resolve_var_ref(statement.target, scope)
            value_type = self._evaluate_expression(statement.value, scope)
            if not self._types_equal(target_type, value_type):
                self._raise_error(
                    "assignment type mismatch",
                    statement.position,
                    "ASSIGNMENT_TYPE_MISMATCH",
                )
            return

        if isinstance(statement, IfStmtNode):
            self._evaluate_expression(statement.condition, scope)
            self._analyze_compound(statement.then_branch, scope, in_procedure)
            if statement.else_branch is not None:
                self._analyze_compound(statement.else_branch, scope, in_procedure)
            return

        if isinstance(statement, WhileStmtNode):
            self._evaluate_expression(statement.condition, scope)
            self._analyze_compound(statement.body, scope, in_procedure)
            return

        if isinstance(statement, ReadStmtNode):
            target_type = self._resolve_var_ref(statement.target, scope)
            if not self._is_scalar(target_type):
                self._raise_error("READ target must be scalar", statement.position, "INVALID_IO_OPERAND")
            return

        if isinstance(statement, WriteStmtNode):
            expr_type = self._evaluate_expression(statement.expression, scope)
            if not self._is_scalar(expr_type):
                self._raise_error("WRITE operand must be scalar", statement.position, "INVALID_IO_OPERAND")
            return

        if isinstance(statement, ReturnStmtNode):
            if not in_procedure or statement.expression is not None:
                self._raise_error("invalid return statement", statement.position, "INVALID_RETURN")
            return

        if isinstance(statement, CallStmtNode):
            symbol = scope.lookup(statement.name)
            if symbol is None or symbol.kind != "procedure":
                self._raise_error(
                    f"undefined identifier '{statement.name}'",
                    statement.position,
                    "UNDEFINED_IDENTIFIER",
                )
            if len(statement.arguments) != len(symbol.params):
                self._raise_error(
                    f"procedure '{statement.name}' expects {len(symbol.params)} arguments, got {len(statement.arguments)}",
                    statement.position,
                    "CALL_ARGUMENT_COUNT_MISMATCH",
                )
            for argument, parameter in zip(statement.arguments, symbol.params):
                argument_type = self._evaluate_expression(argument, scope)
                if not self._types_equal(argument_type, parameter.type_info):
                    self._raise_error(
                        f"argument type mismatch for '{statement.name}'",
                        statement.position,
                        "CALL_ARGUMENT_TYPE_MISMATCH",
                    )
            return

    def _evaluate_expression(self, expression: Any, scope: Scope):
        if isinstance(expression, ConstNode):
            if isinstance(expression.value, int):
                return INTEGER_TYPE
            if isinstance(expression.value, str):
                return CHAR_TYPE

        if isinstance(expression, VarRefNode):
            return self._resolve_var_ref(expression, scope)

        if isinstance(expression, BinaryExprNode):
            left_type = self._evaluate_expression(expression.left, scope)
            right_type = self._evaluate_expression(expression.right, scope)
            if expression.operator in {"+", "-", "*", "/"}:
                if not self._types_equal(left_type, INTEGER_TYPE) or not self._types_equal(right_type, INTEGER_TYPE):
                    self._raise_error("arithmetic operands must be INTEGER", expression.position, "ASSIGNMENT_TYPE_MISMATCH")
                return INTEGER_TYPE
            if expression.operator in {"<", "="}:
                if not self._types_equal(left_type, right_type):
                    self._raise_error("comparison operands must match", expression.position, "ASSIGNMENT_TYPE_MISMATCH")
                return BOOLEAN_TYPE

        return None

    def _resolve_var_ref(self, var_ref: VarRefNode, scope: Scope):
        symbol = scope.lookup(var_ref.name)
        if symbol is None or symbol.kind not in {"var", "param"}:
            self._raise_error(
                f"undefined identifier '{var_ref.name}'",
                var_ref.position,
                "UNDEFINED_IDENTIFIER",
            )

        current_type = symbol.type_info
        for selector in var_ref.selectors:
            if selector["kind"] == "index":
                if not isinstance(current_type, ArrayType):
                    self._raise_error("cannot index non-array value", var_ref.position, "NON_ARRAY_INDEXED")
                index_type = self._evaluate_expression(selector["expression"], scope)
                if not self._types_equal(index_type, INTEGER_TYPE):
                    self._raise_error("array index must be INTEGER", var_ref.position, "INVALID_ARRAY_INDEX_TYPE")
                current_type = current_type.element_type
                continue

            if selector["kind"] == "field":
                if not isinstance(current_type, RecordType):
                    self._raise_error("cannot access field on non-record value", var_ref.position, "NON_RECORD_FIELD_ACCESS")
                field_name = selector["name"]
                if field_name not in current_type.fields:
                    self._raise_error(f"record has no field '{field_name}'", var_ref.position, "INVALID_RECORD_FIELD")
                current_type = current_type.fields[field_name]

        return current_type

    def _resolve_type_spec(self, type_spec: Any, scope: Scope, position: Any):
        if type_spec == "INTEGER":
            return INTEGER_TYPE
        if type_spec == "CHAR":
            return CHAR_TYPE

        if isinstance(type_spec, str):
            symbol = scope.lookup(type_spec)
            if symbol is None or symbol.kind != "type":
                self._raise_error(f"undefined type '{type_spec}'", position, "UNDEFINED_TYPE")
            return symbol.type_info

        if isinstance(type_spec, dict) and type_spec.get("kind") == "ARRAY":
            return ArrayType(
                lower=type_spec["lower"],
                upper=type_spec["upper"],
                element_type=self._resolve_type_spec(type_spec["element_type"], scope, position),
            )

        if isinstance(type_spec, dict) and type_spec.get("kind") == "RECORD":
            fields: dict[str, Any] = {}
            for field in type_spec["fields"]:
                field_type = self._resolve_type_spec(field["type"], scope, position)
                for field_name in field["names"]:
                    if field_name in fields:
                        self._raise_error(
                            f"duplicate declaration '{field_name}'",
                            position,
                            "DUPLICATE_DECLARATION",
                        )
                    fields[field_name] = field_type
            return RecordType(fields=fields)

        self._raise_error("invalid type specification", position, "UNDEFINED_TYPE")

    def _is_scalar(self, type_info: Any) -> bool:
        return isinstance(type_info, BuiltinType) and type_info.name in {"INTEGER", "CHAR"}

    def _types_equal(self, left: Any, right: Any) -> bool:
        return left == right

    def _raise_error(self, message: str, position: Any, error_code: str):
        raise SemanticError(message, _line_of(position), _column_of(position), error_code)


def _line_of(position: Any):
    return getattr(position, "line", None)


def _column_of(position: Any):
    return getattr(position, "column", None)


def analyze(ast):
    return SemanticAnalyzer().analyze(ast)
