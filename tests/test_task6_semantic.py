import unittest


def analyze_source(source: str):
    from lexer import tokenize
    from parser import parse
    from semantic import analyze

    return analyze(parse(tokenize(source)))


class SemanticAnalyzerTests(unittest.TestCase):
    def test_analyze_valid_program_returns_semantic_result(self):
        result = analyze_source(
            """
PROGRAM demo
TYPE IntAlias = INTEGER;
VAR x : IntAlias;
PROCEDURE show(a : INTEGER);
BEGIN
  WRITE(a);
END
BEGIN
  x := 1;
  show(x);
END
"""
        )

        self.assertEqual(result.program_name, "demo")
        self.assertIn("x", result.global_scope.symbols)
        self.assertIn("show", result.global_scope.symbols)

    def test_semantic_error_catalog_has_12_categories(self):
        from semantic import SEMANTIC_ERROR_TYPES

        self.assertEqual(len(SEMANTIC_ERROR_TYPES), 12)
        self.assertIn("DUPLICATE_DECLARATION", SEMANTIC_ERROR_TYPES)
        self.assertIn("UNDEFINED_IDENTIFIER", SEMANTIC_ERROR_TYPES)
        self.assertIn("INVALID_IO_OPERAND", SEMANTIC_ERROR_TYPES)

    def test_duplicate_declaration_error(self):
        from semantic import SemanticError

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
VAR x : INTEGER;
VAR x : INTEGER;
BEGIN
  WRITE(1);
END
"""
            )

        self.assertEqual(context.exception.error_code, "DUPLICATE_DECLARATION")

    def test_undefined_identifier_error(self):
        from semantic import SemanticError

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
BEGIN
  x := 1;
END
"""
            )

        self.assertEqual(context.exception.error_code, "UNDEFINED_IDENTIFIER")

    def test_undefined_type_error(self):
        from semantic import SemanticError

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
VAR x : MissingType;
BEGIN
  WRITE(1);
END
"""
            )

        self.assertEqual(context.exception.error_code, "UNDEFINED_TYPE")

    def test_assignment_type_mismatch_error(self):
        from semantic import SemanticError

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
VAR x : INTEGER;
BEGIN
  x := 'a';
END
"""
            )

        self.assertEqual(context.exception.error_code, "ASSIGNMENT_TYPE_MISMATCH")

    def test_array_related_errors(self):
        from semantic import SemanticError

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
VAR x : INTEGER;
BEGIN
  x[1] := 2;
END
"""
            )

        self.assertEqual(context.exception.error_code, "NON_ARRAY_INDEXED")

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
VAR arr : ARRAY[1..5] OF INTEGER;
BEGIN
  arr['a'] := 2;
END
"""
            )

        self.assertEqual(context.exception.error_code, "INVALID_ARRAY_INDEX_TYPE")

    def test_record_related_errors(self):
        from semantic import SemanticError

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
VAR x : INTEGER;
BEGIN
  x.foo := 1;
END
"""
            )

        self.assertEqual(context.exception.error_code, "NON_RECORD_FIELD_ACCESS")

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
TYPE Pair = RECORD
  left : INTEGER;
END;
VAR p : Pair;
BEGIN
  p.right := 1;
END
"""
            )

        self.assertEqual(context.exception.error_code, "INVALID_RECORD_FIELD")

    def test_call_argument_errors(self):
        from semantic import SemanticError

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
PROCEDURE show(a : INTEGER);
BEGIN
  WRITE(a);
END
BEGIN
  show();
END
"""
            )

        self.assertEqual(context.exception.error_code, "CALL_ARGUMENT_COUNT_MISMATCH")

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
PROCEDURE show(a : INTEGER);
BEGIN
  WRITE(a);
END
BEGIN
  show('a');
END
"""
            )

        self.assertEqual(context.exception.error_code, "CALL_ARGUMENT_TYPE_MISMATCH")

    def test_invalid_return_and_io_operand_errors(self):
        from semantic import SemanticError

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
BEGIN
  RETURN 1;
END
"""
            )

        self.assertEqual(context.exception.error_code, "INVALID_RETURN")

        with self.assertRaises(SemanticError) as context:
            analyze_source(
                """
PROGRAM demo
VAR arr : ARRAY[1..3] OF INTEGER;
BEGIN
  WRITE(arr);
END
"""
            )

        self.assertEqual(context.exception.error_code, "INVALID_IO_OPERAND")


if __name__ == "__main__":
    unittest.main()
