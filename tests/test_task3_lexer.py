import unittest


class LexerBehaviorTests(unittest.TestCase):
    def test_tokenize_keywords_identifiers_literals_and_symbols(self):
        from lexer import tokenize

        code = (
            "PROGRAM demo VAR x : INTEGER ; "
            "BEGIN x := 12 ; WRITE ( 'a' ) ; END"
        )

        tokens = tokenize(code)

        self.assertEqual(
            [token.kind for token in tokens],
            [
                "PROGRAM",
                "ID",
                "VAR",
                "ID",
                "COLON",
                "INTEGER",
                "SEMI",
                "BEGIN",
                "ID",
                "ASSIGN",
                "INTC",
                "SEMI",
                "WRITE",
                "LPAREN",
                "CHARC",
                "RPAREN",
                "SEMI",
                "END",
                "EOF",
            ],
        )

        self.assertEqual(tokens[1].lexeme, "demo")
        self.assertEqual(tokens[10].lexeme, "12")
        self.assertEqual(tokens[14].lexeme, "a")

    def test_tokenize_skips_brace_comments_and_tracks_lines(self):
        from lexer import tokenize

        code = "PROGRAM demo { skip me }\nBEGIN\nx := 1\nEND"
        tokens = tokenize(code)

        self.assertEqual([token.kind for token in tokens[:3]], ["PROGRAM", "ID", "BEGIN"])
        self.assertEqual(tokens[2].position.line, 2)
        self.assertEqual(tokens[3].position.line, 3)
        self.assertEqual(tokens[-1].kind, "EOF")

    def test_unclosed_comment_raises_lexer_error(self):
        from lexer import LexerError, tokenize

        with self.assertRaises(LexerError) as context:
            tokenize("PROGRAM demo { unterminated")

        self.assertIn("unclosed comment", str(context.exception).lower())

    def test_illegal_character_raises_lexer_error(self):
        from lexer import LexerError, tokenize

        with self.assertRaises(LexerError) as context:
            tokenize("PROGRAM demo @")

        self.assertIn("@", str(context.exception))


if __name__ == "__main__":
    unittest.main()
