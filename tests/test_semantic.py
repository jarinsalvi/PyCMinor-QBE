from parser import parse
from semantic import analyze


class DummyProgram:
    def __init__(self):
        self.declarations = []


def test_missing_main():
    result = analyze(DummyProgram())
    assert not result.ok


def test_function_int_argument_type():
    source = """
    int add(int x) {
        return x;
    }

    int main(void) {
        return add(10);
    }
    """
    result = analyze(parse(source))
    assert result.ok


def test_function_bool_argument_type():
    source = """
    int check(bool value) {
        return 1;
    }

    int main(void) {
        return check(true);
    }
    """
    result = analyze(parse(source))
    assert result.ok


def test_function_wrong_argument_type():
    source = """
    int check(bool value) {
        return 1;
    }

    int main(void) {
        return check(10);
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E013" for error in result.diagnostics)


def test_function_arithmetic_expression_argument():
    source = """
    int add(int x) {
        return x;
    }
    int main(void) {
        return add(5 + 3);
    }
    """
    result = analyze(parse(source))
    assert result.ok


def test_nested_function_call_argument():
    source = """
    int add(int x) {
        return x;
    }
    int check(int value) {
        return value;
    }
    int main(void) {
        return check(add(5));
    }
    """
    result = analyze(parse(source))
    assert result.ok


def test_function_arithmetic_expression_argument():
    source = """
    int add(int x) {
        return x;
    }
    int main(void) {
        return add(5 + 3);
    }
    """
    result = analyze(parse(source))
    assert result.ok


def test_nested_function_call_argument():
    source = """
    int add(int x) {
        return x;
    }
    int check(int value) {
        return value;
    }
    int main(void) {
        return check(add(5));
    }
    """
    result = analyze(parse(source))
    assert result.ok


def test_arithmetic_operator_rejects_bool_operand():
    source = """
    int main(void) {
        bool flag = true;
        return 5 + flag;
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E014" for error in result.diagnostics)


def test_logical_not_rejects_int_operand():
    source = """
    int main(void) {
        return !5;
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E015" for error in result.diagnostics)


def test_unary_minus_rejects_bool_operand():
    source = """
    int main(void) {
        bool flag = true;
        return -flag;
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E015" for error in result.diagnostics)


def test_assignment_rejects_wrong_type():
    source = """
    int main(void) {
        int x = 5;
        x = true;
        return x;
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E016" for error in result.diagnostics)


def test_return_rejects_wrong_type():
    source = """
    int main(void) {
        return true;
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E017" for error in result.diagnostics)


def test_void_function_rejects_return_value():
    source = """
    void show(void) {
        return 10;
    }
    int main(void) {
        show();
        return 0;
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E017" for error in result.diagnostics)


def test_non_void_function_requires_return():
    source = """
    int main(void) {
        int x = 10;
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E018" for error in result.diagnostics)


def test_if_else_both_branches_return():
    source = """
    int main(void) {
        if (true) {
            return 1;
        } else {
            return 0;
        }
    }
    """
    result = analyze(parse(source))
    assert result.ok


def test_nested_block_return_is_recognized():
    source = """
    int main(void) {
        {
            return 5;
        }
    }
    """
    result = analyze(parse(source))
    assert result.ok


def test_if_without_else_does_not_guarantee_return():
    source = """
    int main(void) {
        if (true) {
            return 1;
        }
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E018" for error in result.diagnostics)


def test_loop_return_does_not_guarantee_function_return():
    source = """
    int main(void) {
        while (true) {
            return 1;
        }
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E018" for error in result.diagnostics)


def test_recursive_function_call():
    source = """
    int factorial(int n) {
        if (n <= 1) {
            return 1;
        } else {
            return n * factorial(n - 1);
        }
    }
    int main(void) {
        return factorial(5);
    }
    """
    result = analyze(parse(source))
    assert result.ok


def test_function_wrong_argument_count():
    source = """
    int add(int a, int b) {
        return a + b;
    }
    int main(void) {
        return add(5);
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E009" for error in result.diagnostics)


def test_undeclared_function_call():
    source = """
    int main(void) {
        return unknown(10);
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E008" for error in result.diagnostics)


def test_duplicate_function_definition():
    source = """
    int helper(void) {
        return 1;
    }
    int helper(void) {
        return 2;
    }
    int main(void) {
        return helper();
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E004" for error in result.diagnostics)


def test_conflicting_function_prototype():
    source = """
    int helper(int x);
    bool helper(int x);
    int main(void) {
        return 0;
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E004" for error in result.diagnostics)
def test_array_index_must_be_int():
    source = """
    int main(void) {
        int arr[5];
        int x = arr[true];
        return 0;
    }
    """
    result = analyze(parse(source))
    assert any(e.code == "E019" for e in result.diagnostics)
