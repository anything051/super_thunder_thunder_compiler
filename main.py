"""SNL 编译器命令行入口模块。

负责串联词法、语法、语义和代码生成四个阶段，并输出结果文件。
"""

import argparse
import sys
from pathlib import Path

from ast_node import pretty_print_ast
from codegen import generate
from lexer import tokenize
from parser import parse
from semantic import analyze


def _format_error(stage: str, message: str, line=None, column=None) -> str:
    """统一格式化各编译阶段的错误信息。"""
    if line is not None and column is not None:
        return f"[{stage}] line {line}, col {column}: {message}"
    return f"[{stage}] {message}"


def _run_stage(stage: str, func, *args):
    """执行单个编译阶段，并把异常包装成统一输出格式。"""
    try:
        return func(*args)
    except Exception as exc:
        line = getattr(exc, "line", None)
        column = getattr(exc, "column", None)
        print(_format_error(stage, str(exc), line, column), file=sys.stderr)
        raise


def _dump_tokens(tokens) -> None:
    """把 token 序列打印到终端，供调试展示。"""
    print("Token dump:")
    for token in tokens:
        print(f"  {token.kind:<10} {token.lexeme!r:<12} line={token.position.line} col={token.position.column}")


def _dump_ast(ast) -> None:
    """把 AST 树形结构打印到终端。"""
    print("AST dump:")
    print(pretty_print_ast(ast))


def compile_file(source_path: str, dump_tokens: bool = False, dump_ast: bool = False) -> int:
    """编译单个 SNL 源文件，成功时生成同名 .asm 文件。"""
    try:
        source_code = Path(source_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(_format_error("SOURCE", f"file not found: {source_path}"), file=sys.stderr)
        return 1
    except OSError as exc:
        print(_format_error("SOURCE", str(exc)), file=sys.stderr)
        return 1

    try:
        # 四个编译阶段按固定顺序执行，前一阶段失败则后续不再继续。
        tokens = _run_stage("LEXER", tokenize, source_code)
        if dump_tokens:
            _dump_tokens(tokens)
        ast = _run_stage("PARSER", parse, tokens)
        if dump_ast:
            _dump_ast(ast)
        semantic_result = _run_stage("SEMANTIC", analyze, ast)
        assembly = _run_stage("CODEGEN", generate, ast, semantic_result)
    except Exception:
        return 1

    output_path = str(Path(source_path).with_suffix(".asm"))
    try:
        # 把最终汇编输出到与源文件同目录的同名 .asm 文件。
        Path(output_path).write_text(assembly, encoding="utf-8")
    except OSError as exc:
        print(_format_error("OUTPUT", str(exc)), file=sys.stderr)
        return 1

    print(f"Compilation succeeded for {source_path}")
    print(f"Output artifact: {output_path}")
    return 0


def main() -> int:
    """命令行主函数，解析参数并调用编译流程。"""
    parser = argparse.ArgumentParser(description="Compile an SNL source file.")
    parser.add_argument("source", help="Path to the SNL source file")
    parser.add_argument("--dump-tokens", action="store_true", help="Print the token stream before parsing")
    parser.add_argument("--dump-ast", action="store_true", help="Print the AST before semantic analysis")
    args = parser.parse_args()
    return compile_file(args.source, dump_tokens=args.dump_tokens, dump_ast=args.dump_ast)


if __name__ == "__main__":
    # 作为脚本运行时，把 main 的返回值作为进程退出码。
    raise SystemExit(main())
