"""SNL 编译器的 MIPS 代码生成模块。

负责把通过语义分析的 AST 翻译成可在 MARS 中运行的 MIPS 汇编。
"""

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
    """代码生成失败时抛出的异常。"""


@dataclass(frozen=True)
class StorageLocation:
    """描述变量最终存储在静态标签还是过程栈帧中。"""

    kind: str
    identifier: str
    type_info: Any


@dataclass(frozen=True)
class FrameLayout:
    """描述一个过程栈帧中参数和局部变量的偏移布局。"""

    size: int
    param_offsets: dict[str, int]
    local_offsets: dict[str, int]


@dataclass
class MipsEmitter:
    """简单的 MIPS 文本输出器，分别维护 data/text 段。"""

    data_lines: list[str] = field(default_factory=list)
    text_lines: list[str] = field(default_factory=list)
    _label_counters: dict[str, int] = field(default_factory=dict)

    def emit_data(self, line: str) -> None:
        """向 .data 段追加一行。"""
        self.data_lines.append(line)

    def emit_text(self, line: str) -> None:
        """向 .text 段追加一行。"""
        self.text_lines.append(line)

    def new_label(self, prefix: str) -> str:
        """生成带自增编号的唯一标签。"""
        current = self._label_counters.get(prefix, 0)
        self._label_counters[prefix] = current + 1
        return f"{prefix}_{current}"

    def render(self) -> str:
        """拼出最终汇编文本。"""
        data = [".data", *self.data_lines] if self.data_lines else [".data"]
        text = [".text", *self.text_lines] if self.text_lines else [".text"]
        return "\n".join(data + [""] + text) + "\n"


class CodeGenerator:
    """MIPS 代码生成器主类。"""

    def __init__(self, semantic_result):
        """保存语义信息，并初始化存储布局表。"""
        self.semantic_result = semantic_result
        self.emitter = MipsEmitter()
        self.storage_labels: dict[tuple[str | None, str], str] = {}
        self.variable_types: dict[tuple[str | None, str], Any] = {}
        self.procedure_scopes: dict[str, Any] = {}
        self.frame_layouts: dict[str, FrameLayout] = {}

    def generate(self, ast) -> str:
        """生成整个程序的汇编文本。"""
        self._declare_global_storage()
        self._prepare_procedure_layouts()
        self.emitter.emit_text(".globl main")
        self.emitter.emit_text("main:")

        # 主程序中的语句顺序直接翻译到 main 标签下。
        for statement in ast.body.statements:
            self._emit_statement(statement, current_scope=None)

        # 主程序执行完成后以 syscall 10 退出。
        self.emitter.emit_text("li $v0, 10")
        self.emitter.emit_text("syscall")

        for procedure in ast.procedures:
            # 每个过程都生成独立标签，并带完整 prologue/epilogue。
            self.emitter.emit_text(f"{procedure.name}:")
            self._emit_procedure_prologue(procedure.name)
            self._emit_compound(procedure.body, procedure.name)
            self._emit_procedure_epilogue(procedure.name)

        return self.emitter.render()

    def _declare_global_storage(self) -> None:
        """为全局变量分配静态存储区。"""
        for name, symbol in self.semantic_result.global_scope.symbols.items():
            if symbol.kind != "var":
                continue
            self.variable_types[(None, name)] = symbol.type_info
            self.storage_labels[(None, name)] = name
            self.emitter.emit_data(f"{name}: {self._storage_for_type(symbol.type_info)}")

    def _prepare_procedure_layouts(self) -> None:
        """根据语义分析结果预先计算每个过程的栈帧布局。"""
        for name, symbol in self.semantic_result.global_scope.symbols.items():
            if symbol.kind != "procedure":
                continue
            if symbol.scope is None:
                continue
            self.procedure_scopes[name] = symbol.scope
            self.frame_layouts[name] = self._build_frame_layout(symbol)

    def _build_frame_layout(self, procedure_symbol: Any) -> FrameLayout:
        """计算一个过程的参数和局部变量偏移。"""
        param_offsets: dict[str, int] = {}
        local_offsets: dict[str, int] = {}
        next_offset = 8

        # 0($fp) 和 4($fp) 保留给保存的 $ra 和旧 $fp，所以参数从 8 开始。
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
        """把类型对象映射成 .data 段中的存储声明。"""
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
        """计算一个类型占用的字节数。"""
        if isinstance(type_info, BuiltinType):
            return 4
        if isinstance(type_info, ArrayType):
            return max(type_info.upper - type_info.lower + 1, 0) * self._byte_size(type_info.element_type)
        if isinstance(type_info, RecordType):
            return sum(self._byte_size(field_type) for field_type in type_info.fields.values())
        raise CodegenError(f"unsupported type size for {type_info!r}")

    def _emit_statement(self, statement: Any, current_scope: str | None) -> None:
        """按语句种类生成对应 MIPS 指令。"""
        if isinstance(statement, AssignStmtNode):
            self._emit_expression(statement.value, current_scope)
            # 先把右值压栈暂存，避免后续求左值地址时覆盖寄存器内容。
            self.emitter.emit_text("addi $sp, $sp, -4")
            self.emitter.emit_text("sw $t0, 0($sp)")
            self._emit_var_address(statement.target, current_scope, target_register="$t1")
            self.emitter.emit_text("lw $t0, 0($sp)")
            self.emitter.emit_text("addi $sp, $sp, 4")
            self.emitter.emit_text("sw $t0, 0($t1)")
            return

        if isinstance(statement, ReadStmtNode):
            # READ 先求目标地址，再通过 syscall 5 读入整数写回内存。
            self._emit_var_address(statement.target, current_scope, target_register="$t1")
            self.emitter.emit_text("li $v0, 5")
            self.emitter.emit_text("syscall")
            self.emitter.emit_text("sw $v0, 0($t1)")
            return

        if isinstance(statement, WriteStmtNode):
            # WRITE 统一把结果放到 $a0，再通过 syscall 1 输出。
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
            # 条件为 0 时跳到 else，否则顺序执行 then 分支。
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
            # while 使用“开始标签 + 结束标签”循环控制。
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
                # 调用方按逆序压栈，保证被调过程按声明顺序取到参数。
                self._emit_expression(argument, current_scope)
                self.emitter.emit_text("addi $sp, $sp, -4")
                self.emitter.emit_text("sw $t0, 0($sp)")
            self.emitter.emit_text(f"jal {statement.name}")
            if params:
                # 调用结束后由调用方回收实参空间。
                self.emitter.emit_text(f"addi $sp, $sp, {len(params) * 4}")
            return

        if isinstance(statement, ReturnStmtNode):
            # 过程内 RETURN 直接跳到统一 epilogue，集中恢复现场。
            if current_scope is None:
                self.emitter.emit_text("jr $ra")
                return
            self.emitter.emit_text(f"j {self._procedure_end_label(current_scope)}")
            return

        raise CodegenError(f"statement not supported in task 8 codegen: {type(statement).__name__}")

    def _emit_compound(self, compound: CompoundStmtNode, current_scope: str | None) -> None:
        """顺序生成复合语句块中的每条语句。"""
        for statement in compound.statements:
            self._emit_statement(statement, current_scope)

    def _emit_expression(self, expression: Any, current_scope: str | None) -> None:
        """生成表达式求值代码，约定结果放在 $t0。"""
        if isinstance(expression, ConstNode):
            self.emitter.emit_text(f"li $t0, {self._const_value(expression.value)}")
            return

        if isinstance(expression, VarRefNode):
            # 变量表达式先求地址，再从内存中取值。
            self._emit_var_address(expression, current_scope, target_register="$t1")
            self.emitter.emit_text("lw $t0, 0($t1)")
            return

        if isinstance(expression, BinaryExprNode):
            # 左操作数先压栈保存，再计算右操作数，最后组合结果。
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
                # div 的商在 LO 寄存器里，需要再取回到 $t0。
                self.emitter.emit_text("mflo $t0")
            return

        raise CodegenError(f"expression not supported in task 7 codegen: {type(expression).__name__}")

    def _emit_var_address(self, var_ref: VarRefNode, current_scope: str | None, target_register: str = "$t1") -> Any:
        """计算变量或 selector 的最终地址，结果放入指定寄存器。"""
        storage = self._resolve_storage(var_ref.name, current_scope)
        self._emit_storage_address(storage, target_register)
        current_type = storage.type_info

        for selector in var_ref.selectors:
            if selector["kind"] == "index":
                # 数组偏移 = (下标 - 下界) * 元素大小。
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
                # 记录字段偏移 = 前面字段大小之和。
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
        """根据存储位置生成基地址。"""
        if storage.kind == "label":
            self.emitter.emit_text(f"la {target_register}, {storage.identifier}")
            return
        if storage.kind == "frame":
            self.emitter.emit_text(f"addi {target_register}, $fp, {storage.identifier}")
            return
        raise CodegenError(f"unsupported storage kind '{storage.kind}'")

    def _record_field_offset(self, record_type: RecordType, field_name: str) -> int:
        """计算记录字段相对记录起始地址的偏移。"""
        offset = 0
        for current_name, current_type in record_type.fields.items():
            if current_name == field_name:
                return offset
            offset += self._byte_size(current_type)
        raise CodegenError(f"record has no field '{field_name}'")

    def _resolve_scalar_target(self, var_ref: VarRefNode, current_scope: str | None) -> str:
        """旧版按标签取标量目标的方法，当前主要保留兼容用途。"""
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
        """解析变量最终位于过程栈帧还是全局静态区。"""
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
        """生成过程入口代码：建栈帧并复制实参到本过程参数槽。"""
        frame_layout = self.frame_layouts[procedure_name]
        self.emitter.emit_text(f"addi $sp, $sp, -{frame_layout.size}")
        self.emitter.emit_text("sw $ra, 0($sp)")
        self.emitter.emit_text("sw $fp, 4($sp)")
        self.emitter.emit_text("move $fp, $sp")

        incoming_base = frame_layout.size
        param_names = list(frame_layout.param_offsets.keys())
        for index, name in enumerate(param_names):
            # 调用者压入的实参位于当前栈帧之上，这里复制到过程自己的参数槽。
            source_offset = incoming_base + index * 4
            target_offset = frame_layout.param_offsets[name]
            self.emitter.emit_text(f"lw $t0, {source_offset}($fp)")
            self.emitter.emit_text(f"sw $t0, {target_offset}($fp)")

    def _emit_procedure_epilogue(self, procedure_name: str) -> None:
        """生成过程出口代码：恢复 $ra/$fp 并回收当前栈帧。"""
        frame_layout = self.frame_layouts[procedure_name]
        end_label = self._procedure_end_label(procedure_name)
        self.emitter.emit_text(f"{end_label}:")
        self.emitter.emit_text("lw $ra, 0($fp)")
        self.emitter.emit_text("lw $t1, 4($fp)")
        self.emitter.emit_text(f"addi $sp, $fp, {frame_layout.size}")
        self.emitter.emit_text("move $fp, $t1")
        self.emitter.emit_text("jr $ra")

    def _procedure_end_label(self, procedure_name: str) -> str:
        """返回某个过程统一出口标签名。"""
        return f"{procedure_name}_epilogue"

    def _const_value(self, value: Any) -> int:
        """把常量节点的值转换成 MIPS 立即数。"""
        if isinstance(value, int):
            return value
        if isinstance(value, str) and len(value) == 1:
            return ord(value)
        raise CodegenError(f"unsupported constant value {value!r}")


def generate(ast, semantic_result):
    """对外暴露的代码生成入口。"""
    return CodeGenerator(semantic_result).generate(ast)
