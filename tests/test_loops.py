from parser import parse
from semantic import analyze
from ir_generator import generate_ir


def test_valid_for_loop():
    source = """
    int main(void) {
        int sum = 0;
        for (int i = 0; i < 10; i = i + 1) {
            if (i == 5) continue;
            if (i == 8) break;
            sum = sum + i;
        }
        return sum;
    }
    """
    result = analyze(parse(source))
    assert result.ok


def test_break_outside_loop():
    source = """
    int main(void) {
        break;
        return 0;
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E010" for error in result.diagnostics)


def test_continue_outside_loop():
    source = """
    int main(void) {
        continue;
        return 0;
    }
    """
    result = analyze(parse(source))
    assert not result.ok
    assert any(error.code == "E011" for error in result.diagnostics)


def test_for_loop_ir_targets():
    source = """
    int main(void) {
        int sum = 0;
        for (int i = 0; i < 10; i = i + 1) {
            if (i == 5) continue;
            if (i == 8) break;
            sum = sum + i;
        }
        return sum;
    }
    """
    ast = parse(source)
    result = analyze(ast)
    ir = generate_ir(ast, result)

    instructions = ir.functions[0].instructions

    labels = {
        ins.a for ins in instructions
        if ins.op == "LABEL"
    }
    jump_targets = {
        ins.a for ins in instructions
        if ins.op == "JMP"
    }

    update_label = next(
        label for label in labels if label.startswith("forupdate")
    )
    end_label = next(
        label for label in labels if label.startswith("endfor")
    )

    assert update_label in jump_targets
    assert end_label in jump_targets


def test_valid_while_loop():
    source = """
    int main(void) {
        int i = 0;
        int sum = 0;
        while (i < 10) {
            i = i + 1;
            if (i == 3) continue;
            if (i == 7) break;
            sum = sum + i;
        }
        return sum;
    }
    """
    result = analyze(parse(source))
    assert result.ok


def test_while_loop_ir_targets():
    source = """
    int main(void) {
        int i = 0;
        while (i < 10) {
            i = i + 1;
            if (i == 3) continue;
            if (i == 7) break;
        }
        return i;
    }
    """
    ast = parse(source)
    result = analyze(ast)
    ir = generate_ir(ast, result)

    instructions = ir.functions[0].instructions

    labels = {
        ins.a for ins in instructions
        if ins.op == "LABEL"
    }
    jump_targets = {
        ins.a for ins in instructions
        if ins.op == "JMP"
    }

    condition_label = next(
        label for label in labels if label.startswith("while")
    )
    end_label = next(
        label for label in labels if label.startswith("endwhile")
    )

    assert condition_label in jump_targets
    assert end_label in jump_targets
