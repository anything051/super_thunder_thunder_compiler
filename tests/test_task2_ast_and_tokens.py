import unittest
from dataclasses import is_dataclass


class TokenContractTests(unittest.TestCase):
    def test_source_position_and_token_are_dataclasses(self):
        from lexer import SourcePosition, Token

        self.assertTrue(is_dataclass(SourcePosition))
        self.assertTrue(is_dataclass(Token))

        position = SourcePosition(line=2, column=7)
        token = Token(kind="ID", lexeme="foo", position=position)

        self.assertEqual(position.line, 2)
        self.assertEqual(position.column, 7)
        self.assertEqual(token.kind, "ID")
        self.assertEqual(token.lexeme, "foo")
        self.assertEqual(token.position, position)


class AstShapeTests(unittest.TestCase):
    def test_program_node_and_pretty_print_exist(self):
        from ast_node import CompoundStmtNode, ProgramNode, pretty_print_ast

        program = ProgramNode(
            name="demo",
            declarations=[],
            procedures=[],
            body=CompoundStmtNode(statements=[]),
            position=None,
        )

        rendered = pretty_print_ast(program)

        self.assertIn("ProgramNode", rendered)
        self.assertIn("CompoundStmtNode", rendered)
        self.assertIn("demo", rendered)

    def test_required_ast_nodes_can_be_constructed(self):
        from ast_node import (
            AssignStmtNode,
            BinaryExprNode,
            CallStmtNode,
            CompoundStmtNode,
            ConstNode,
            IfStmtNode,
            ProcedureDeclNode,
            ProgramNode,
            ReadStmtNode,
            ReturnStmtNode,
            TypeDeclNode,
            VarDeclNode,
            VarRefNode,
            WhileStmtNode,
            WriteStmtNode,
        )

        nodes = [
            ProgramNode("demo", [], [], CompoundStmtNode([]), None),
            TypeDeclNode("IntAlias", "INTEGER", None),
            VarDeclNode(["x"], "INTEGER", None),
            ProcedureDeclNode("proc", [], [], CompoundStmtNode([]), None),
            AssignStmtNode(VarRefNode("x", None), ConstNode(1, None), None),
            IfStmtNode(ConstNode(True, None), CompoundStmtNode([]), None, None),
            WhileStmtNode(ConstNode(True, None), CompoundStmtNode([]), None),
            ReadStmtNode(VarRefNode("x", None), None),
            WriteStmtNode(ConstNode(1, None), None),
            ReturnStmtNode(ConstNode(1, None), None),
            CallStmtNode("proc", [], None),
            BinaryExprNode("+", ConstNode(1, None), ConstNode(2, None), None),
            ConstNode(1, None),
            VarRefNode("x", None),
        ]

        self.assertEqual(len(nodes), 14)


if __name__ == "__main__":
    unittest.main()
