from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any


@dataclass
class ASTNode:
    position: Any = None


@dataclass
class ProgramNode(ASTNode):
    name: str = ""
    declarations: list[Any] = field(default_factory=list)
    procedures: list[Any] = field(default_factory=list)
    body: Any = None
    position: Any = None


@dataclass
class TypeDeclNode(ASTNode):
    name: str = ""
    type_spec: Any = None
    position: Any = None


@dataclass
class VarDeclNode(ASTNode):
    names: list[str] = field(default_factory=list)
    type_spec: Any = None
    position: Any = None


@dataclass
class ProcedureDeclNode(ASTNode):
    name: str = ""
    params: list[Any] = field(default_factory=list)
    declarations: list[Any] = field(default_factory=list)
    body: Any = None
    position: Any = None


@dataclass
class CompoundStmtNode(ASTNode):
    statements: list[Any] = field(default_factory=list)
    position: Any = None


@dataclass
class AssignStmtNode(ASTNode):
    target: Any = None
    value: Any = None
    position: Any = None


@dataclass
class IfStmtNode(ASTNode):
    condition: Any = None
    then_branch: Any = None
    else_branch: Any = None
    position: Any = None


@dataclass
class WhileStmtNode(ASTNode):
    condition: Any = None
    body: Any = None
    position: Any = None


@dataclass
class ReadStmtNode(ASTNode):
    target: Any = None
    position: Any = None


@dataclass
class WriteStmtNode(ASTNode):
    expression: Any = None
    position: Any = None


@dataclass
class ReturnStmtNode(ASTNode):
    expression: Any = None
    position: Any = None


@dataclass
class CallStmtNode(ASTNode):
    name: str = ""
    arguments: list[Any] = field(default_factory=list)
    position: Any = None


@dataclass
class BinaryExprNode(ASTNode):
    operator: str = ""
    left: Any = None
    right: Any = None
    position: Any = None


@dataclass
class ConstNode(ASTNode):
    value: Any = None
    position: Any = None


@dataclass
class VarRefNode(ASTNode):
    name: str = ""
    position: Any = None
    selectors: list[Any] = field(default_factory=list)


def pretty_print_ast(node: Any, indent: int = 0) -> str:
    lines: list[str] = []
    _render_node(node, indent, lines)
    return "\n".join(lines)


def _render_node(node: Any, indent: int, lines: list[str]) -> None:
    prefix = "  " * indent

    if is_dataclass(node) and not isinstance(node, type):
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
            lines.append(f"{prefix}  {name}:")
            _render_node(value, indent + 2, lines)
        return

    if isinstance(node, list):
        lines.append(f"{prefix}[")
        for item in node:
            _render_node(item, indent + 1, lines)
        lines.append(f"{prefix}]")
        return

    lines.append(f"{prefix}{node!r}")


def _is_child(value: Any) -> bool:
    if isinstance(value, list):
        return True
    return is_dataclass(value) and not isinstance(value, type)
