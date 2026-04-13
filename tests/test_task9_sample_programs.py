import os
import unittest


class SampleProgramTests(unittest.TestCase):
    def test_required_sample_files_exist(self):
        required = [
            "test/hello.snl",
            "test/lexer_cases/comments.snl",
            "test/parser_cases/if_while.snl",
            "test/semantic_errors/undefined_identifier.snl",
            "test/semantic_errors/type_mismatch.snl",
            "test/semantic_errors/duplicate_decl.snl",
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


if __name__ == "__main__":
    unittest.main()
