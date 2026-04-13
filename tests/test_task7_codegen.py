import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout


def compile_semantic_result(source: str):
    from lexer import tokenize
    from parser import parse
    from semantic import analyze

    ast = parse(tokenize(source))
    semantic_result = analyze(ast)
    return ast, semantic_result


class CodegenTests(unittest.TestCase):
    def test_mips_emitter_renders_sections_and_unique_labels(self):
        from codegen import MipsEmitter

        emitter = MipsEmitter()
        emitter.emit_data("value: .word 0")
        emitter.emit_text("main:")
        emitter.emit_text("li $v0, 10")
        emitter.emit_text("syscall")

        first = emitter.new_label("loop")
        second = emitter.new_label("loop")
        rendered = emitter.render()

        self.assertNotEqual(first, second)
        self.assertIn(".data", rendered)
        self.assertIn(".text", rendered)
        self.assertIn("value: .word 0", rendered)
        self.assertIn("main:", rendered)

    def test_generate_assignment_expression_and_write(self):
        from codegen import generate

        ast, semantic_result = compile_semantic_result(
            """
PROGRAM demo
VAR x : INTEGER;
BEGIN
  x := 1 + 2 * 3;
  WRITE(x);
END
"""
        )

        assembly = generate(ast, semantic_result)

        self.assertIn(".data", assembly)
        self.assertIn(".text", assembly)
        self.assertIn("x: .word 0", assembly)
        self.assertIn("main:", assembly)
        self.assertIn("mul", assembly)
        self.assertIn("add", assembly)
        self.assertIn("la $t1, x", assembly)
        self.assertIn("sw $t0, 0($t1)", assembly)
        self.assertIn("lw $a0, x", assembly)
        self.assertIn("li $v0, 1", assembly)
        self.assertIn("li $v0, 10", assembly)

    def test_generate_read_statement_uses_syscall(self):
        from codegen import generate

        ast, semantic_result = compile_semantic_result(
            """
PROGRAM demo
VAR x : INTEGER;
BEGIN
  READ(x);
  WRITE(x);
END
"""
        )

        assembly = generate(ast, semantic_result)

        self.assertIn("li $v0, 5", assembly)
        self.assertIn("la $t1, x", assembly)
        self.assertIn("sw $v0, 0($t1)", assembly)

    def test_generate_selector_addressing_for_array_and_record(self):
        from codegen import generate

        ast, semantic_result = compile_semantic_result(
            """
PROGRAM demo
TYPE pair = RECORD
  left, right : INTEGER;
END;
VAR nums : ARRAY [1..3] OF INTEGER;
VAR item : pair;
BEGIN
  nums[2] := 7;
  item.right := nums[2];
  WRITE(item.right);
END
"""
        )

        assembly = generate(ast, semantic_result)

        self.assertIn("nums: .space 12", assembly)
        self.assertIn("item: .space 8", assembly)
        self.assertIn("la $t1, nums", assembly)
        self.assertIn("addi $t2, $t0, -1", assembly)
        self.assertIn("mul $t2, $t2, 4", assembly)
        self.assertIn("add $t1, $t1, $t2", assembly)
        self.assertIn("sw $t0, 0($t1)", assembly)
        self.assertIn("la $t1, item", assembly)
        self.assertIn("addi $t1, $t1, 4", assembly)
        self.assertIn("move $a0, $t0", assembly)

    def test_compile_file_writes_asm_output(self):
        import main

        source = """
PROGRAM hello
VAR x : INTEGER;
BEGIN
  x := 7;
  WRITE(x);
END
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = os.path.join(temp_dir, "hello.snl")
            with open(source_path, "w", encoding="utf-8") as handle:
                handle.write(source)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main.compile_file(source_path)

            output_path = os.path.join(temp_dir, "hello.asm")
            self.assertEqual(exit_code, 0)
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, "r", encoding="utf-8") as handle:
                assembly = handle.read()
            self.assertIn(".data", assembly)
            self.assertIn(".text", assembly)
            self.assertIn("Output artifact:", stdout.getvalue())
            self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
