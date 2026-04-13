import os
import unittest
from pathlib import Path


class SampleProgramTests(unittest.TestCase):
    def test_required_sample_files_exist(self):
        required = [
            "test/hello.snl",
            "test/lexer_cases/comments.snl",
            "test/parser_cases/if_while.snl",
            "test/semantic_errors/undefined_identifier.snl",
            "test/semantic_errors/type_mismatch.snl",
            "test/semantic_errors/duplicate_decl.snl",
            "test/codegen_cases/selectors.snl",
            "test/codegen_cases/procedure_frame.snl",
            "test/codegen_cases/multi_param.snl",
            "test/codegen_cases/multi_locals.snl",
            "test/codegen_cases/local_selector.snl",
            "test/codegen_cases/read_write_selector.snl",
            "test/codegen_cases/recursive_countdown.snl",
        ]

        for path in required:
            self.assertTrue(os.path.exists(path), path)

    def test_comment_sample_lexes(self):
        from lexer import tokenize

        with open("test/lexer_cases/comments.snl", "r", encoding="utf-8") as handle:
            tokens = tokenize(handle.read())

        kinds = [token.kind for token in tokens]
        self.assertIn("PROGRAM", kinds)
        self.assertIn("WRITE", kinds)
        self.assertEqual(kinds[-1], "EOF")

    def test_if_while_sample_parses(self):
        from lexer import tokenize
        from parser import parse

        with open("test/parser_cases/if_while.snl", "r", encoding="utf-8") as handle:
            ast = parse(tokenize(handle.read()))

        self.assertEqual(ast.name, "flowdemo")
        self.assertEqual(len(ast.body.statements), 2)

    def test_negative_semantic_samples_fail_with_distinct_errors(self):
        from lexer import tokenize
        from parser import parse
        from semantic import SemanticError, analyze

        expectations = {
            "test/semantic_errors/undefined_identifier.snl": "UNDEFINED_IDENTIFIER",
            "test/semantic_errors/type_mismatch.snl": "ASSIGNMENT_TYPE_MISMATCH",
            "test/semantic_errors/duplicate_decl.snl": "DUPLICATE_DECLARATION",
        }

        for path, error_code in expectations.items():
            with self.subTest(path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    source = handle.read()

                with self.assertRaises(SemanticError) as context:
                    analyze(parse(tokenize(source)))

                self.assertEqual(context.exception.error_code, error_code)

    def test_mars_validation_samples_exist_and_compile(self):
        import main

        sample_paths = [
            "test/codegen_cases/selectors.snl",
            "test/codegen_cases/procedure_frame.snl",
            "test/codegen_cases/multi_param.snl",
            "test/codegen_cases/multi_locals.snl",
            "test/codegen_cases/local_selector.snl",
            "test/codegen_cases/read_write_selector.snl",
            "test/codegen_cases/recursive_countdown.snl",
        ]

        for sample_path in sample_paths:
            with self.subTest(sample_path=sample_path):
                self.assertTrue(os.path.exists(sample_path), sample_path)
                exit_code = main.compile_file(sample_path)
                self.assertEqual(exit_code, 0)
                self.assertTrue(Path(sample_path).with_suffix(".asm").exists())


if __name__ == "__main__":
    unittest.main()
