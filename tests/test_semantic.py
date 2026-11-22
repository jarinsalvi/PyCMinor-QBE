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
