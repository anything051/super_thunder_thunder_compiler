from dataclasses import dataclass, field
from typing import Any

from ast_node import (
    AssignStmtNode,
    BinaryExprNode,
    CallStmtNode,
    CompoundStmtNode,
    ConstNode,
    IfStmtNode,
    ReadStmtNode,
    ReturnStmtNode,
    VarRefNode,
    WhileStmtNode,
    WriteStmtNode,
)
from semantic import ArrayType, BuiltinType, RecordType


class CodegenError(Exception):
    """Raised when code generation fails."""


@dataclass(frozen=True)
class StorageLocation:
    kind: str
    identifier: str
    type_info: Any


@dataclass(frozen=True)
class FrameLayout:
    size: int
    param_offsets: dict[str, int]
    local_offsets: dict[str, int]


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
        self.storage_labels: dict[tuple[str | None, str], str] = {}
        self.variable_types: dict[tuple[str | None, str], Any] = {}
        self.procedure_scopes: dict[str, Any] = {}
        self.frame_layouts: dict[str, FrameLayout] = {}

    def generate(self, ast) -> str:
        self._declare_global_storage()
        self._prepare_procedure_layouts()
        self.emitter.emit_text(".globl main")
        self.emitter.emit_text("main:")

        for statement in ast.body.statements:
            self._emit_statement(statement, current_scope=None)

        self.emitter.emit_text("li $v0, 10")
        self.emitter.emit_text("syscall")

        for procedure in ast.procedures:
            self.emitter.emit_text(f"{procedure.name}:")
            self._emit_procedure_prologue(procedure.name)
            self._emit_compound(procedure.body, procedure.name)
            self._emit_procedure_epilogue(procedure.name)

        return self.emitter.render()

    def _declare_global_storage(self) -> None:
        for name, symbol in self.semantic_result.global_scope.symbols.items():
            if symbol.kind != "var":
                continue
            self.variable_types[(None, name)] = symbol.type_info
            self.storage_labels[(None, name)] = name
            self.emitter.emit_data(f"{name}: {self._storage_for_type(symbol.type_info)}")

    def _prepare_procedure_layouts(self) -> None:
        for name, symbol in self.semantic_result.global_scope.symbols.items():
            if symbol.kind != "procedure":
                continue
            if symbol.scope is None:
                continue
            self.procedure_scopes[name] = symbol.scope
            self.frame_layouts[name] = self._build_frame_layout(symbol)

    def _build_frame_layout(self, procedure_symbol: Any) -> FrameLayout:
        param_offsets: dict[str, int] = {}
        local_offsets: dict[str, int] = {}
        next_offset = 8

        for param_symbol in procedure_symbol.params:
            param_offsets[param_symbol.name] = next_offset
            self.variable_types[(procedure_symbol.name, param_symbol.name)] = param_symbol.type_info
            next_offset += self._byte_size(param_symbol.type_info)

        for local_name, local_symbol in procedure_symbol.scope.symbols.items():
            if local_symbol.kind != "var":
                continue
            local_offsets[local_name] = next_offset
            self.variable_types[(procedure_symbol.name, local_name)] = local_symbol.type_info
            next_offset += self._byte_size(local_symbol.type_info)

        return FrameLayout(size=next_offset, param_offsets=param_offsets, local_offsets=local_offsets)

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

    def _emit_statement(self, statement: Any, current_scope: str | None) -> None:
        if isinstance(statement, AssignStmtNode):
            self._emit_expression(statement.value, current_scope)
            self.emitter.emit_text("addi $sp, $sp, -4")
            self.emitter.emit_text("sw $t0, 0($sp)")
            self._emit_var_address(statement.target, current_scope, target_register="$t1")
            self.emitter.emit_text("lw $t0, 0($sp)")
            self.emitter.emit_text("addi $sp, $sp, 4")
            self.emitter.emit_text("sw $t0, 0($t1)")
            return

        if isinstance(statement, ReadStmtNode):
            self._emit_var_address(statement.target, current_scope, target_register="$t1")
            self.emitter.emit_text("li $v0, 5")
            self.emitter.emit_text("syscall")
            self.emitter.emit_text("sw $v0, 0($t1)")
            return

        if isinstance(statement, WriteStmtNode):
            self._emit_expression(statement.expression, current_scope)
            if isinstance(statement.expression, VarRefNode) and not statement.expression.selectors:
                storage = self._resolve_storage(statement.expression.name, current_scope)
                if storage.kind == "label":
                    self.emitter.emit_text(f"lw $a0, {storage.identifier}")
                else:
                    self.emitter.emit_text("move $a0, $t0")
            else:
                self.emitter.emit_text("move $a0, $t0")
            self.emitter.emit_text("li $v0, 1")
            self.emitter.emit_text("syscall")
            return

        if isinstance(statement, IfStmtNode):
            else_label = self.emitter.new_label("if_else")
            end_label = self.emitter.new_label("if_end")
            self._emit_expression(statement.condition, current_scope)
            self.emitter.emit_text(f"beq $t0, $zero, {else_label}")
            self._emit_compound(statement.then_branch, current_scope)
            self.emitter.emit_text(f"j {end_label}")
            self.emitter.emit_text(f"{else_label}:")
            if statement.else_branch is not None:
                self._emit_compound(statement.else_branch, current_scope)
            self.emitter.emit_text(f"{end_label}:")
            return

        if isinstance(statement, WhileStmtNode):
            start_label = self.emitter.new_label("while_start")
            end_label = self.emitter.new_label("while_end")
            self.emitter.emit_text(f"{start_label}:")
            self._emit_expression(statement.condition, current_scope)
            self.emitter.emit_text(f"beq $t0, $zero, {end_label}")
            self._emit_compound(statement.body, current_scope)
            self.emitter.emit_text(f"j {start_label}")
            self.emitter.emit_text(f"{end_label}:")
            return

        if isinstance(statement, CallStmtNode):
            procedure_scope = self.procedure_scopes.get(statement.name)
            if procedure_scope is None:
                raise CodegenError(f"unknown procedure '{statement.name}'")
            params = [sym for sym in procedure_scope.symbols.values() if sym.kind == "param"]
            for argument, parameter in reversed(list(zip(statement.arguments, params))):
                self._emit_expression(argument, current_scope)
                self.emitter.emit_text("addi $sp, $sp, -4")
                self.emitter.emit_text("sw $t0, 0($sp)")
            self.emitter.emit_text(f"jal {statement.name}")
            if params:
                self.emitter.emit_text(f"addi $sp, $sp, {len(params) * 4}")
            return

        if isinstance(statement, ReturnStmtNode):
            if current_scope is None:
                self.emitter.emit_text("jr $ra")
                return
            self.emitter.emit_text(f"j {self._procedure_end_label(current_scope)}")
            return

        raise CodegenError(f"statement not supported in task 8 codegen: {type(statement).__name__}")

    def _emit_compound(self, compound: CompoundStmtNode, current_scope: str | None) -> None:
        for statement in compound.statements:
            self._emit_statement(statement, current_scope)

    def _emit_expression(self, expression: Any, current_scope: str | None) -> None:
        if isinstance(expression, ConstNode):
            self.emitter.emit_text(f"li $t0, {self._const_value(expression.value)}")
            return

        if isinstance(expression, VarRefNode):
            self._emit_var_address(expression, current_scope, target_register="$t1")
            self.emitter.emit_text("lw $t0, 0($t1)")
            return

        if isinstance(expression, BinaryExprNode):
            self._emit_expression(expression.left, current_scope)
            self.emitter.emit_text("addi $sp, $sp, -4")
            self.emitter.emit_text("sw $t0, 0($sp)")
            self._emit_expression(expression.right, current_scope)
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

    def _emit_var_address(self, var_ref: VarRefNode, current_scope: str | None, target_register: str = "$t1") -> Any:
        storage = self._resolve_storage(var_ref.name, current_scope)
        self._emit_storage_address(storage, target_register)
        current_type = storage.type_info

        for selector in var_ref.selectors:
            if selector["kind"] == "index":
                if not isinstance(current_type, ArrayType):
                    raise CodegenError(f"cannot index non-array value '{var_ref.name}'")
                self._emit_expression(selector["expression"], current_scope)
                self.emitter.emit_text(f"addi $t2, $t0, {-current_type.lower}")
                element_size = self._byte_size(current_type.element_type)
                self.emitter.emit_text(f"mul $t2, $t2, {element_size}")
                self.emitter.emit_text(f"add {target_register}, {target_register}, $t2")
                current_type = current_type.element_type
                continue

            if selector["kind"] == "field":
                if not isinstance(current_type, RecordType):
                    raise CodegenError(f"cannot access field on non-record value '{var_ref.name}'")
                field_name = selector["name"]
                field_offset = self._record_field_offset(current_type, field_name)
                self.emitter.emit_text(f"addi {target_register}, {target_register}, {field_offset}")
                current_type = current_type.fields[field_name]
                continue

            raise CodegenError(f"unsupported selector kind '{selector['kind']}'")

        return current_type

    def _emit_storage_address(self, storage: StorageLocation, target_register: str) -> None:
        if storage.kind == "label":
            self.emitter.emit_text(f"la {target_register}, {storage.identifier}")
            return
        if storage.kind == "frame":
            self.emitter.emit_text(f"addi {target_register}, $fp, {storage.identifier}")
            return
        raise CodegenError(f"unsupported storage kind '{storage.kind}'")

    def _record_field_offset(self, record_type: RecordType, field_name: str) -> int:
        offset = 0
        for current_name, current_type in record_type.fields.items():
            if current_name == field_name:
                return offset
            offset += self._byte_size(current_type)
        raise CodegenError(f"record has no field '{field_name}'")

    def _resolve_scalar_target(self, var_ref: VarRefNode, current_scope: str | None) -> str:
        if var_ref.selectors:
            raise CodegenError("selector-based assignments are not supported until task 8")
        scoped_key = (current_scope, var_ref.name)
        global_key = (None, var_ref.name)
        if scoped_key in self.storage_labels:
            return self.storage_labels[scoped_key]
        if global_key in self.storage_labels:
            return self.storage_labels[global_key]
        if scoped_key not in self.variable_types and global_key not in self.variable_types:
            raise CodegenError(f"unknown storage target '{var_ref.name}'")
        raise CodegenError(f"missing storage label for '{var_ref.name}'")

    def _resolve_storage(self, name: str, current_scope: str | None) -> StorageLocation:
        if current_scope is not None and current_scope in self.frame_layouts:
            frame_layout = self.frame_layouts[current_scope]
            if name in frame_layout.local_offsets:
                return StorageLocation("frame", str(frame_layout.local_offsets[name]), self.variable_types[(current_scope, name)])
            if name in frame_layout.param_offsets:
                return StorageLocation("frame", str(frame_layout.param_offsets[name]), self.variable_types[(current_scope, name)])
        scoped_key = (current_scope, name)
        global_key = (None, name)
        if scoped_key in self.storage_labels:
            return StorageLocation("label", self.storage_labels[scoped_key], self.variable_types[scoped_key])
        if global_key in self.storage_labels:
            return StorageLocation("label", self.storage_labels[global_key], self.variable_types[global_key])
        if scoped_key not in self.variable_types and global_key not in self.variable_types:
            raise CodegenError(f"unknown storage target '{name}'")
        raise CodegenError(f"missing storage label for '{name}'")

    def _emit_procedure_prologue(self, procedure_name: str) -> None:
        frame_layout = self.frame_layouts[procedure_name]
        self.emitter.emit_text(f"addi $sp, $sp, -{frame_layout.size}")
        self.emitter.emit_text("sw $ra, 0($sp)")
        self.emitter.emit_text("sw $fp, 4($sp)")
        self.emitter.emit_text("move $fp, $sp")

        incoming_base = frame_layout.size
        param_names = list(frame_layout.param_offsets.keys())
        for index, name in enumerate(param_names):
            source_offset = incoming_base + index * 4
            target_offset = frame_layout.param_offsets[name]
            self.emitter.emit_text(f"lw $t0, {source_offset}($fp)")
            self.emitter.emit_text(f"sw $t0, {target_offset}($fp)")

    def _emit_procedure_epilogue(self, procedure_name: str) -> None:
        frame_layout = self.frame_layouts[procedure_name]
        end_label = self._procedure_end_label(procedure_name)
        self.emitter.emit_text(f"{end_label}:")
        self.emitter.emit_text("lw $ra, 0($fp)")
        self.emitter.emit_text("lw $t1, 4($fp)")
        self.emitter.emit_text(f"addi $sp, $fp, {frame_layout.size}")
        self.emitter.emit_text("move $fp, $t1")
        self.emitter.emit_text("jr $ra")

    def _procedure_end_label(self, procedure_name: str) -> str:
        return f"{procedure_name}_epilogue"

    def _const_value(self, value: Any) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, str) and len(value) == 1:
            return ord(value)
        raise CodegenError(f"unsupported constant value {value!r}")


def generate(ast, semantic_result):
    return CodeGenerator(semantic_result).generate(ast)
