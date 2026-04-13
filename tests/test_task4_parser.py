import unittest


class ParserBehaviorTests(unittest.TestCase):
    def test_parse_minimal_program(self):
        from ast_node import ProgramNode, WriteStmtNode
        from lexer import tokenize
        from parser import parse

        ast = parse(tokenize("PROGRAM demo BEGIN WRITE(1); END"))

        self.assertIsInstance(ast, ProgramNode)
        self.assertEqual(ast.name, "demo")
        self.assertEqual(len(ast.body.statements), 1)
        self.assertIsInstance(ast.body.statements[0], WriteStmtNode)

    def test_parse_declarations_and_procedure(self):
        from ast_node import ProcedureDeclNode, TypeDeclNode, VarDeclNode
        from lexer import tokenize
        from parser import parse

        source = """
PROGRAM demo
TYPE IntAlias = INTEGER;
VAR x, y : INTEGER;
PROCEDURE add(a : INTEGER);
BEGIN
  WRITE(a);
END
BEGIN
  add(x);
END
"""
        ast = parse(tokenize(source))

        self.assertEqual(len(ast.declarations), 2)
        self.assertIsInstance(ast.declarations[0], TypeDeclNode)
        self.assertIsInstance(ast.declarations[1], VarDeclNode)
        self.assertEqual(ast.declarations[1].names, ["x", "y"])
        self.assertEqual(len(ast.procedures), 1)
        self.assertIsInstance(ast.procedures[0], ProcedureDeclNode)
        self.assertEqual(ast.procedures[0].name, "add")

    def test_parse_control_flow_and_calls(self):
        from ast_node import CallStmtNode, IfStmtNode, WhileStmtNode
        from lexer import tokenize
        from parser import parse

        source = """
PROGRAM demo
BEGIN
  IF 1 < 2 THEN WRITE(1); ELSE WRITE(2); FI;
  WHILE x < 10 DO x := x + 1; ENDWH;
  proc(x);
END
"""
        ast = parse(tokenize(source))

        self.assertIsInstance(ast.body.statements[0], IfStmtNode)
        self.assertIsInstance(ast.body.statements[1], WhileStmtNode)
        self.assertIsInstance(ast.body.statements[2], CallStmtNode)

    def test_parse_assignment_expression_precedence(self):
        from ast_node import AssignStmtNode, BinaryExprNode
        from lexer import tokenize
        from parser import parse

        ast = parse(tokenize("PROGRAM demo BEGIN x := 1 + 2 * 3; END"))

        stmt = ast.body.statements[0]
        self.assertIsInstance(stmt, AssignStmtNode)
        self.assertIsInstance(stmt.value, BinaryExprNode)
        self.assertEqual(stmt.value.operator, "+")
        self.assertIsInstance(stmt.value.right, BinaryExprNode)
        self.assertEqual(stmt.value.right.operator, "*")


if __name__ == "__main__":
    unittest.main()
