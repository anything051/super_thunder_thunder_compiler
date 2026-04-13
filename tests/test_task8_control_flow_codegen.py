import unittest


def compile_semantic_result(source: str):
    from lexer import tokenize
    from parser import parse
    from semantic import analyze

    ast = parse(tokenize(source))
    semantic_result = analyze(ast)
    return ast, semantic_result


class ControlFlowCodegenTests(unittest.TestCase):
    def test_generate_if_and_while_control_flow(self):
        from codegen import generate

        ast, semantic_result = compile_semantic_result(
            """
PROGRAM demo
VAR x : INTEGER;
BEGIN
  IF 1 < 2 THEN WRITE(1); ELSE WRITE(2); FI;
  WHILE x < 3 DO x := x + 1; ENDWH;
END
"""
        )

        assembly = generate(ast, semantic_result)

        self.assertIn("if_else_", assembly)
        self.assertIn("if_end_", assembly)
        self.assertIn("while_start_", assembly)
        self.assertIn("while_end_", assembly)
        self.assertIn("beq $t0, $zero", assembly)
        self.assertIn("j while_start_", assembly)

    def test_generate_procedure_call_and_return(self):
        from codegen import generate

        ast, semantic_result = compile_semantic_result(
            """
PROGRAM demo
VAR x : INTEGER;
PROCEDURE show(a : INTEGER);
BEGIN
  WRITE(a);
  RETURN;
END
BEGIN
  x := 7;
  show(x);
END
"""
        )

        assembly = generate(ast, semantic_result)

        self.assertIn("show:", assembly)
        self.assertIn("show__a: .word 0", assembly)
        self.assertIn("sw $t0, show__a", assembly)
        self.assertIn("jal show", assembly)
        self.assertIn("jr $ra", assembly)
        self.assertIn("lw $a0, show__a", assembly)


if __name__ == "__main__":
    unittest.main()
