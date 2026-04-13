"""SNL 编译器使用的 AST 节点定义与树形打印工具。"""

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any


@dataclass
class ASTNode:
    """所有 AST 节点的公共基类，统一携带源码位置。"""

    position: Any = None


@dataclass
class ProgramNode(ASTNode):
    """表示整个程序的根节点。"""

    name: str = ""
    declarations: list[Any] = field(default_factory=list)
    procedures: list[Any] = field(default_factory=list)
    body: Any = None
    position: Any = None


@dataclass
class TypeDeclNode(ASTNode):
    """表示类型声明节点。"""

    name: str = ""
    type_spec: Any = None
    position: Any = None


@dataclass
class VarDeclNode(ASTNode):
    """表示变量声明节点。"""

    names: list[str] = field(default_factory=list)
    type_spec: Any = None
    position: Any = None


@dataclass
class ProcedureDeclNode(ASTNode):
    """表示过程声明节点。"""

    name: str = ""
    params: list[Any] = field(default_factory=list)
    declarations: list[Any] = field(default_factory=list)
    body: Any = None
    position: Any = None


@dataclass
class CompoundStmtNode(ASTNode):
    """表示复合语句块。"""

    statements: list[Any] = field(default_factory=list)
    position: Any = None


@dataclass
class AssignStmtNode(ASTNode):
    """表示赋值语句。"""

    target: Any = None
    value: Any = None
    position: Any = None


@dataclass
class IfStmtNode(ASTNode):
    """表示条件分支语句。"""

    condition: Any = None
    then_branch: Any = None
    else_branch: Any = None
    position: Any = None


@dataclass
class WhileStmtNode(ASTNode):
    """表示 while 循环语句。"""

    condition: Any = None
    body: Any = None
    position: Any = None


@dataclass
class ReadStmtNode(ASTNode):
    """表示读入语句。"""

    target: Any = None
    position: Any = None


@dataclass
class WriteStmtNode(ASTNode):
    """表示输出语句。"""

    expression: Any = None
    position: Any = None


@dataclass
class ReturnStmtNode(ASTNode):
    """表示返回语句。"""

    expression: Any = None
    position: Any = None


@dataclass
class CallStmtNode(ASTNode):
    """表示过程调用语句。"""

    name: str = ""
    arguments: list[Any] = field(default_factory=list)
    position: Any = None


@dataclass
class BinaryExprNode(ASTNode):
    """表示二元表达式节点。"""

    operator: str = ""
    left: Any = None
    right: Any = None
    position: Any = None


@dataclass
class ConstNode(ASTNode):
    """表示整型或字符常量节点。"""

    value: Any = None
    position: Any = None


@dataclass
class VarRefNode(ASTNode):
    """表示变量引用节点，可带数组下标或记录字段 selector。"""

    name: str = ""
    position: Any = None
    selectors: list[Any] = field(default_factory=list)


def pretty_print_ast(node: Any, indent: int = 0) -> str:
    """把 AST 渲染成层次化字符串，便于调试展示。"""
    lines: list[str] = []
    _render_node(node, indent, lines)
    return "\n".join(lines)


def _render_node(node: Any, indent: int, lines: list[str]) -> None:
    """递归渲染单个节点或节点列表。"""
    prefix = "  " * indent

    if is_dataclass(node) and not isinstance(node, type):
        # dataclass 节点分成“摘要字段”和“子节点字段”两部分输出。
        node_fields = [item for item in fields(node) if item.name != "position"]
        summary_parts = []
        child_values: list[tuple[str, Any]] = []

        for item in node_fields:
            value = getattr(node, item.name)
            if _is_child(value):
                child_values.append((item.name, value))
            else:
                summary_parts.append(f"{item.name}={value!r}")

        summary = f" ({', '.join(summary_parts)})" if summary_parts else ""
        lines.append(f"{prefix}{type(node).__name__}{summary}")

        for name, value in child_values:
            # 子节点换行缩进展示，形成树状结构。
            lines.append(f"{prefix}  {name}:")
            _render_node(value, indent + 2, lines)
        return

    if isinstance(node, list):
        # 列表按同一层级逐个打印。
        lines.append(f"{prefix}[")
        for item in node:
            _render_node(item, indent + 1, lines)
        lines.append(f"{prefix}]")
        return

    lines.append(f"{prefix}{node!r}")


def _is_child(value: Any) -> bool:
    """判断一个字段值是否应当作为子节点递归展开。"""
    if isinstance(value, list):
        return True
    return is_dataclass(value) and not isinstance(value, type)
