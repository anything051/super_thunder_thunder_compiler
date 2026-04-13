import os
import unittest


class ReadmeTests(unittest.TestCase):
    def test_readme_exists_and_mentions_core_usage(self):
        self.assertTrue(os.path.exists("README.md"))

        with open("README.md", "r", encoding="utf-8") as handle:
            content = handle.read()

        self.assertIn("python main.py test/hello.snl", content)
        self.assertIn("lexer.py", content)
        self.assertIn("parser.py", content)
        self.assertIn("semantic.py", content)
        self.assertIn("codegen.py", content)
        self.assertIn("完成标准对照", content)
        self.assertIn("MARS", content)
        self.assertIn("12 类语义错误", content)


if __name__ == "__main__":
    unittest.main()
