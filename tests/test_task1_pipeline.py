import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch


class CompilePipelineTests(unittest.TestCase):
    def test_compile_file_returns_nonzero_for_missing_file(self):
        import main

        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main.compile_file("test/does-not-exist.snl")

        self.assertNotEqual(exit_code, 0)
        self.assertIn("SOURCE", stderr.getvalue())

    def test_compile_file_calls_all_stages_in_order(self):
        import main

        calls = []

        def fake_tokenize(source_code):
            calls.append(("tokenize", source_code))
            return ["TOKENS"]

        def fake_parse(tokens):
            calls.append(("parse", tokens))
            return "AST"

        def fake_analyze(ast):
            calls.append(("analyze", ast))
            return "SEMANTIC"

        def fake_generate(ast, semantic_result):
            calls.append(("generate", ast, semantic_result))
            return "ASM"

        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write("PROGRAM demo")
            source_path = handle.name

        try:
            stdout = io.StringIO()
            stderr = io.StringIO()

            with patch.object(main, "tokenize", side_effect=fake_tokenize), \
                patch.object(main, "parse", side_effect=fake_parse), \
                patch.object(main, "analyze", side_effect=fake_analyze), \
                patch.object(main, "generate", side_effect=fake_generate), \
                redirect_stdout(stdout), \
                redirect_stderr(stderr):
                exit_code = main.compile_file(source_path)

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                calls,
                [
                    ("tokenize", "PROGRAM demo"),
                    ("parse", ["TOKENS"]),
                    ("analyze", "AST"),
                    ("generate", "AST", "SEMANTIC"),
                ],
            )
            self.assertIn("Compilation succeeded", stdout.getvalue())
            self.assertIn("Output artifact:", stdout.getvalue())
            self.assertEqual(stderr.getvalue(), "")
        finally:
            os.unlink(source_path)

    def test_compile_file_returns_nonzero_when_stage_fails(self):
        import main

        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write("PROGRAM demo")
            source_path = handle.name

        try:
            stderr = io.StringIO()
            with patch.object(main, "tokenize", side_effect=NotImplementedError("stub")), \
                redirect_stderr(stderr):
                exit_code = main.compile_file(source_path)

            self.assertNotEqual(exit_code, 0)
            self.assertIn("LEXER", stderr.getvalue())
            self.assertIn("stub", stderr.getvalue())
        finally:
            os.unlink(source_path)


if __name__ == "__main__":
    unittest.main()
