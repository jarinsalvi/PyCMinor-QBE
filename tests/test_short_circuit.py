from parser import parse
from semantic import analyze
from ir_generator import generate_ir


def compile_to_ir(source):
    ast = parse(source)
    result = analyze(ast)
    assert result.ok
    return generate_ir(ast, result).functions[0].instructions


def test_logical_and_uses_short_circuit_branch():
    source = """
    int main(void) {
        int a = 0 && 5;
        return a;
    }
    """

    instructions = compile_to_ir(source)

    conditional_jumps = [
        ins for ins in instructions if ins.op == "JZ"
    ]

    assert len(conditional_jumps) >= 2

    false_label = conditional_jumps[0].b
    assert conditional_jumps[1].b == false_label

    labels = {
        ins.a for ins in instructions if ins.op == "LABEL"
    }
    assert false_label in labels


def test_logical_or_uses_short_circuit_branch():
    source = """
    int main(void) {
        int a = 1 || 0;
        return a;
    }
    """

    instructions = compile_to_ir(source)

    conditional_jumps = [
        ins for ins in instructions if ins.op == "JZ"
    ]
    unconditional_jumps = [
        ins for ins in instructions if ins.op == "JMP"
    ]

    assert len(conditional_jumps) >= 2
    assert conditional_jumps[0].b.startswith("or_right")
    assert unconditional_jumps[0].a.startswith("or_true")


def test_nested_logical_operators_generate_ir():
    source = """
    int main(void) {
        int a = (0 && 5) || (1 && 7);
        return a;
    }
    """

    instructions = compile_to_ir(source)

    assert sum(ins.op == "JZ" for ins in instructions) >= 4
    assert sum(ins.op == "LABEL" for ins in instructions) >= 6
