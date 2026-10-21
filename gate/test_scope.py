import unittest
from check_scope import evaluate


class ScopeGateTests(unittest.TestCase):
    def test_allowed_examples(self):
        self.assertEqual([], evaluate([("A", "examples/sample.txt")], {"examples/sample.txt": "100644"}))

    def test_allowed_docs(self):
        self.assertEqual([], evaluate([("M", "docs/note.md")], {"docs/note.md": "100644"}))

    def test_forbidden_workflow(self):
        self.assertTrue(evaluate([("M", ".github/workflows/harness-scope-check.yml")], {".github/workflows/harness-scope-check.yml": "100644"}))

    def test_forbidden_checker(self):
        self.assertTrue(evaluate([("M", "gate/check_scope.py")], {"gate/check_scope.py": "100644"}))

    def test_deleted_file(self):
        self.assertTrue(evaluate([("D", "examples/removed.txt")], {}))

    def test_symlink(self):
        self.assertTrue(evaluate([("A", "examples/link")], {"examples/link": "120000"}))

    def test_executable(self):
        self.assertTrue(evaluate([("A", "examples/run.sh")], {"examples/run.sh": "100755"}))

    def test_noop(self):
        self.assertTrue(evaluate([], {}))

    def test_prefix_only(self):
        self.assertTrue(evaluate([("A", "examples/")], {"examples/": "100644"}))


if __name__ == "__main__":
    unittest.main()
