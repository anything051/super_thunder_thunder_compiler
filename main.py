import argparse
import sys
from pathlib import Path

from codegen import generate
from lexer import tokenize
from parser import parse
from semantic import analyze


def _format_error(stage: str, message: str, line=None, column=None) -> str:
    if line is not None and column is not None:
        return f"[{stage}] line {line}, col {column}: {message}"
    return f"[{stage}] {message}"


def _run_stage(stage: str, func, *args):
    try:
        return func(*args)
    except Exception as exc:
        line = getattr(exc, "line", None)
        column = getattr(exc, "column", None)
        print(_format_error(stage, str(exc), line, column), file=sys.stderr)
        raise


def compile_file(source_path: str) -> int:
    try:
        source_code = Path(source_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(_format_error("SOURCE", f"file not found: {source_path}"), file=sys.stderr)
        return 1
    except OSError as exc:
        print(_format_error("SOURCE", str(exc)), file=sys.stderr)
        return 1

    try:
        tokens = _run_stage("LEXER", tokenize, source_code)
        ast = _run_stage("PARSER", parse, tokens)
        semantic_result = _run_stage("SEMANTIC", analyze, ast)
        output = _run_stage("CODEGEN", generate, ast, semantic_result)
    except Exception:
        return 1

    print(f"Compilation succeeded for {source_path}")
    if output is not None:
        print(f"Output artifact: {output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile an SNL source file.")
    parser.add_argument("source", help="Path to the SNL source file")
    args = parser.parse_args()
    return compile_file(args.source)


if __name__ == "__main__":
    raise SystemExit(main())
