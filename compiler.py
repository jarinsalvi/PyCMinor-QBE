from pathlib import Path
import shutil
import subprocess
import tempfile

from lexer import tokenize
from parser import parse
from semantic import analyze
from ir_generator import generate_ir
from ir import dump_ir
from qbe_codegen import generate_qbe


class CompilerError(Exception):
    pass


def find_qbe():
    qbe = shutil.which("qbe")
    if qbe:
        return qbe

    local_qbe = Path.home() / "qbe" / "qbe"
    if local_qbe.is_file():
        return str(local_qbe)

    raise CompilerError(
        "QBE backend not found. Install QBE or add it to PATH."
    )


def compile_source(source, filename="input.cm"):
    try:
        ast = parse(source)
    except Exception as exc:
        raise CompilerError(f"Parsing failed: {exc}") from exc

    result = analyze(ast, filename)

    if not result.ok:
        messages = [
            f"{d.code}: {d.message}" for d in result.diagnostics
        ]
        raise CompilerError("\n".join(messages))

    try:
        ir_program = generate_ir(ast, result)
        backend_ir = generate_qbe(ir_program)
    except Exception as exc:
        raise CompilerError(f"Code generation failed: {exc}") from exc

    return ast, result, ir_program, backend_ir


def compile_file(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.is_file():
        raise CompilerError(f"Input file not found: {input_path}")

    source = input_path.read_text(encoding="utf-8")
    _, _, _, backend_ir = compile_source(source, str(input_path))

    qbe = find_qbe()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        dir=str(output_path.parent)
    ) as temp_dir:
        temp_dir = Path(temp_dir)
        ssa_file = temp_dir / "input.ssa"
        asm_file = temp_dir / "output.s"

        ssa_file.write_text(backend_ir, encoding="utf-8")

        try:
            subprocess.run(
                [
                    qbe,
                    "-t", "amd64_sysv",
                    "-o", str(asm_file),
                    str(ssa_file),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.strip() or exc.stdout.strip()
            raise CompilerError(
                f"QBE failed: {detail}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise CompilerError("QBE backend timed out.") from exc

        if not asm_file.is_file():
            raise CompilerError("QBE did not produce assembly output.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        asm_file.replace(output_path)

    return output_path
