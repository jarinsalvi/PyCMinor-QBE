import argparse
import sys
from pathlib import Path

from lexer import tokenize
from parser import parse
from semantic import analyze, dump_symbols
from ir_generator import generate_ir
from ir import dump_ir
from qbe_codegen import generate_qbe
from compiler import compile_source, compile_file, CompilerError


VERSION = "0.1.0"


def main():
    parser = argparse.ArgumentParser(
        prog="cminorcc",
        description="C Minor Compiler with QBE backend",
    )

    parser.add_argument("input", nargs="?", help="Input .cm file")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dump-tokens", action="store_true")
    parser.add_argument("--dump-ast", action="store_true")
    parser.add_argument("--dump-symbols", action="store_true")
    parser.add_argument("--dump-ir", action="store_true")
    parser.add_argument("--emit-backend-ir", action="store_true")
    parser.add_argument("--capabilities", action="store_true")
    parser.add_argument("--backend", default="qbe")
    parser.add_argument("--version", action="version", version=VERSION)

    args = parser.parse_args()

    if args.capabilities:
        print("Backend: qbe")
        print("Target: amd64_sysv")
        print("Features: lexer, parser, semantic analysis, student IR, QBE")
        return 0

    if not args.input:
        parser.error("input file is required")

    if args.backend != "qbe":
        print("error: only the QBE backend is supported", file=sys.stderr)
        return 2

    input_path = Path(args.input)

    try:
        source = input_path.read_text(encoding="utf-8")

        if args.dump_tokens:
            for token in tokenize(source):
                print(token)
            return 0

        ast, result, ir_program, backend_ir = compile_source(
            source, str(input_path)
        )

        if args.dump_ast:
            print(ast)

        if args.dump_symbols:
            print(dump_symbols(result))

        if args.dump_ir:
            print(dump_ir(ir_program))

        if args.emit_backend_ir:
            output = Path(args.output or input_path.with_suffix(".ssa"))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(backend_ir, encoding="utf-8")
            print(f"Backend IR written to {output}")
            return 0

        if args.check:
            print("Compilation check successful.")
            return 0

        output = args.output or str(input_path.with_suffix(".s"))
        compile_file(input_path, output)
        print(f"Assembly written to {output}")
        return 0

    except (OSError, UnicodeError, CompilerError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"internal compiler error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
