import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch


class ParserDiagnosticTests(unittest.TestCase):
    def test_parser_error_includes_expected_and_actual_token(self):
        from lexer import tokenize
        from parser import ParserError, parse

        with self.assertRaises(ParserError) as context:
            parse(tokenize("PROGRAM demo BEGIN WRITE(1);"))

        message = str(context.exception)
        self.assertIn("expected END", message)
        self.assertIn("got EOF", message)
        self.assertIsNotNone(context.exception.line)
        self.assertIsNotNone(context.exception.column)


class CliDumpTests(unittest.TestCase):
    def test_compile_file_can_dump_tokens_and_ast_before_later_stage_failure(self):
        import main

        source = "PROGRAM demo BEGIN WRITE(1); END"
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".snl") as handle:
            handle.write(source)
            source_path = handle.name

        try:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main.compile_file(source_path, dump_tokens=True, dump_ast=True)

            self.assertNotEqual(exit_code, 0)
            self.assertIn("Token dump:", stdout.getvalue())
            self.assertIn("PROGRAM", stdout.getvalue())
            self.assertIn("AST dump:", stdout.getvalue())
            self.assertIn("ProgramNode", stdout.getvalue())
            self.assertIn("SEMANTIC", stderr.getvalue())
        finally:
            os.unlink(source_path)

    def test_main_accepts_dump_flags(self):
        import main

        source = "PROGRAM demo BEGIN WRITE(1); END"
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".snl") as handle:
            handle.write(source)
            source_path = handle.name

        try:
            stdout = io.StringIO()
            stderr = io.StringIO()
            argv = ["main.py", source_path, "--dump-tokens", "--dump-ast"]

            with redirect_stdout(stdout), redirect_stderr(stderr):
                with patch("sys.argv", argv):
                    exit_code = main.main()

            self.assertNotEqual(exit_code, 0)
            self.assertIn("Token dump:", stdout.getvalue())
            self.assertIn("AST dump:", stdout.getvalue())
        finally:
            os.unlink(source_path)


if __name__ == "__main__":
    unittest.main()
