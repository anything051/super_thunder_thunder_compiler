from dataclasses import dataclass, field
from typing import Any

from ast_node import AssignStmtNode, BinaryExprNode, ConstNode, ReadStmtNode, VarRefNode, WriteStmtNode
from semantic import ArrayType, BuiltinType, RecordType


class CodegenError(Exception):
    """Raised when code generation fails."""


@dataclass
class MipsEmitter:
    data_lines: list[str] = field(default_factory=list)
    text_lines: list[str] = field(default_factory=list)
    _label_counters: dict[str, int] = field(default_factory=dict)

    def emit_data(self, line: str) -> None:
        self.data_lines.append(line)

    def emit_text(self, line: str) -> None:
        self.text_lines.append(line)

    def new_label(self, prefix: str) -> str:
        current = self._label_counters.get(prefix, 0)
        self._label_counters[prefix] = current + 1
        return f"{prefix}_{current}"

    def render(self) -> str:
        data = [".data", *self.data_lines] if self.data_lines else [".data"]
        text = [".text", *self.text_lines] if self.text_lines else [".text"]
        return "\n".join(data + [""] + text) + "\n"


class CodeGenerator:
    def __init__(self, semantic_result):
        self.semantic_result = semantic_result
        self.emitter = MipsEmitter()
        self.variable_types: dict[str, Any] = {}

    def generate(self, ast) -> str:
        self._declare_global_storage()
        self.emitter.emit_text(".globl main")
        self.emitter.emit_text("main:")

        for statement in ast.body.statements:
            self._emit_statement(statement)

        self.emitter.emit_text("li $v0, 10")
        self.emitter.emit_text("syscall")
        return self.emitter.render()

    def _declare_global_storage(self) -> None:
        for name, symbol in self.semantic_result.global_scope.symbols.items():
            if symbol.kind != "var":
                continue
            self.variable_types[name] = symbol.type_info
            self.emitter.emit_data(f"{name}: {self._storage_for_type(symbol.type_info)}")

    def _storage_for_type(self, type_info: Any) -> str:
        if isinstance(type_info, BuiltinType):
            return ".word 0"
        if isinstance(type_info, ArrayType):
            count = max(type_info.upper - type_info.lower + 1, 0)
            return f".space {count * self._byte_size(type_info.element_type)}"
        if isinstance(type_info, RecordType):
            size = sum(self._byte_size(field_type) for field_type in type_info.fields.values())
            return f".space {size}"
        raise CodegenError(f"unsupported storage type: {type_info!r}")

    def _byte_size(self, type_info: Any) -> int:
        if isinstance(type_info, BuiltinType):
            return 4
        if isinstance(type_info, ArrayType):
            return max(type_info.upper - type_info.lower + 1, 0) * self._byte_size(type_info.element_type)
        if isinstance(type_info, RecordType):
            return sum(self._byte_size(field_type) for field_type in type_info.fields.values())
        raise CodegenError(f"unsupported type size for {type_info!r}")

    def _emit_statement(self, statement: Any) -> None:
        if isinstance(statement, AssignStmtNode):
            self._emit_expression(statement.value)
            target = self._resolve_scalar_target(statement.target)
            self.emitter.emit_text(f"sw $t0, {target}")
            return

        if isinstance(statement, ReadStmtNode):
            target = self._resolve_scalar_target(statement.target)
            self.emitter.emit_text("li $v0, 5")
            self.emitter.emit_text("syscall")
            self.emitter.emit_text(f"sw $v0, {target}")
            return

        if isinstance(statement, WriteStmtNode):
            self._emit_expression(statement.expression)
            if isinstance(statement.expression, VarRefNode) and not statement.expression.selectors:
                self.emitter.emit_text(f"lw $a0, {statement.expression.name}")
            else:
                self.emitter.emit_text("move $a0, $t0")
            self.emitter.emit_text("li $v0, 1")
            self.emitter.emit_text("syscall")
            return

        raise CodegenError(f"statement not supported in task 7 codegen: {type(statement).__name__}")

    def _emit_expression(self, expression: Any) -> None:
        if isinstance(expression, ConstNode):
            self.emitter.emit_text(f"li $t0, {self._const_value(expression.value)}")
            return

        if isinstance(expression, VarRefNode):
            target = self._resolve_scalar_target(expression)
            self.emitter.emit_text(f"lw $t0, {target}")
            return

        if isinstance(expression, BinaryExprNode):
            self._emit_expression(expression.left)
            self.emitter.emit_text("addi $sp, $sp, -4")
            self.emitter.emit_text("sw $t0, 0($sp)")
            self._emit_expression(expression.right)
            self.emitter.emit_text("lw $t1, 0($sp)")
            self.emitter.emit_text("addi $sp, $sp, 4")

            operator_map = {
                "+": "add $t0, $t1, $t0",
                "-": "sub $t0, $t1, $t0",
                "*": "mul $t0, $t1, $t0",
                "/": "div $t1, $t0",
                "<": "slt $t0, $t1, $t0",
                "=": "seq $t0, $t1, $t0",
            }
            if expression.operator not in operator_map:
                raise CodegenError(f"unsupported operator '{expression.operator}'")
            self.emitter.emit_text(operator_map[expression.operator])
            if expression.operator == "/":
                self.emitter.emit_text("mflo $t0")
            return

        raise CodegenError(f"expression not supported in task 7 codegen: {type(expression).__name__}")

    def _resolve_scalar_target(self, var_ref: VarRefNode) -> str:
        if var_ref.selectors:
            raise CodegenError("selector-based assignments are not supported until task 8")
        if var_ref.name not in self.variable_types:
            raise CodegenError(f"unknown storage target '{var_ref.name}'")
        return var_ref.name

    def _const_value(self, value: Any) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, str) and len(value) == 1:
            return ord(value)
        raise CodegenError(f"unsupported constant value {value!r}")


def generate(ast, semantic_result):
    return CodeGenerator(semantic_result).generate(ast)
