"""task 387 회고 — plain_words.py의 묶음(SETS)은 run_night.py 묶음 표에도 있어야 한다(385·387 두 번 시험 1장에서 KeyError).
두 파일을 import하지 않고 AST로 SETS 키만 읽는다(무거운 생성 모듈을 불러오지 않게)."""
import ast, os, unittest

BATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch")


def set_keys(name):
    tree = ast.parse(open(os.path.join(BATCH, name), encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SETS" for t in node.targets):
            return {k.value for k in node.value.keys}
    raise AssertionError(f"{name}에 SETS 없음")


class BundleRegistry(unittest.TestCase):
    def test_plain_words_sets_in_run_night(self):
        missing = set_keys("plain_words.py") - set_keys("run_night.py")
        self.assertFalse(missing, f"run_night.py SETS에 등록 안 된 묶음: {sorted(missing)}")


if __name__ == "__main__":
    unittest.main()
