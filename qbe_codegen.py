"""Generate QBE IL from the project's intermediate representation."""

import re
from ir import IRProgram, IRFunction


class QBECodegenError(Exception):
    pass


class QBECodeGenerator:
    def __init__(self):
        self.lines = []
        self.cont_count = 0

    def emit(self, line=""):
        self.lines.append(line)

    def fresh_label(self):
        self.cont_count += 1
        return f"@ir_cont_{self.cont_count}"

    @staticmethod
    def name(value):
        text = str(value)

        # Preserve generated IR temporaries.
        if text.startswith("%t"):
            return text

        safe = re.sub(r"[^A-Za-z0-9_]", "_", text)
        if not safe or safe[0].isdigit():
            safe = "v_" + safe

        return "%v_" + safe

    @staticmethod
    def value(value):
        if value is None:
            return "0"

        text = str(value)

        if re.fullmatch(r"-?\d+", text):
            return text

        return QBECodeGenerator.name(text)

    def generate(self, program: IRProgram):
        self.lines = []
        self.cont_count = 0

        for function in program.functions:
            self.generate_function(function)
            self.emit()

        return "\n".join(self.lines).rstrip() + "\n"

    def generate_function(self, fn: IRFunction):
        if fn.return_type == "void":
            return_type = ""
        elif fn.return_type in ("int", "bool"):
            return_type = "w "
        else:
            raise QBECodegenError(
                f"Unsupported return type: {fn.return_type}"
            )

        params = ", ".join(
            f"w {self.name(param)}" for param in fn.params
        )

        linkage = "export " if fn.name == "main" else ""

        self.emit(
            f"{linkage}function {return_type}${fn.name}({params}) {{"
        )
        self.emit("@start")

        block_terminated = False

        for ins in fn.instructions:
            op = ins.op

            # Ignore unreachable instructions until the next basic block.
            if block_terminated and op != "LABEL":
                continue

            if op == "LABEL":
                block_terminated = False

            dst = self.name(ins.dst) if ins.dst else None
            a = self.value(ins.a)
            b = self.value(ins.b)

            if op == "LABEL":
                self.emit(f"@{ins.a}")

            elif op == "STORE":
                self.emit(
                    f"{self.name(ins.dst)} =w copy {self.value(ins.a)}"
                )

            elif op == "MOV":
                self.emit(f"{dst} =w copy {a}")

            elif op == "NEG":
                self.emit(f"{dst} =w neg {a}")

            elif op == "NOT":
                self.emit(f"{dst} =w ceqw {a}, 0")

            elif op in ("ADD", "SUB", "MUL", "DIV", "MOD"):
                operations = {
                    "ADD": "add",
                    "SUB": "sub",
                    "MUL": "mul",
                    "DIV": "div",
                    "MOD": "rem",
                }
                self.emit(
                    f"{dst} =w {operations[op]} {a}, {b}"
                )

            elif op in ("EQ", "NE", "LT", "GT", "LE", "GE"):
                operations = {
                    "EQ": "ceqw",
                    "NE": "cnew",
                    "LT": "csltw",
                    "GT": "csgtw",
                    "LE": "cslew",
                    "GE": "csgew",
                }
                self.emit(
                    f"{dst} =w {operations[op]} {a}, {b}"
                )

            elif op == "AND":
                self.emit(f"{dst} =w and {a}, {b}")

            elif op == "OR":
                self.emit(f"{dst} =w or {a}, {b}")

            elif op == "JZ":
                continuation = self.fresh_label()
                self.emit(
                    f"jnz {a}, {continuation}, @{ins.b}"
                )
                self.emit(continuation)

            elif op == "JMP":
                self.emit(f"jmp @{ins.a}")
                block_terminated = True

            elif op == "RET":
                if ins.a is None:
                    self.emit("ret")
                else:
                    self.emit(f"ret {a}")
                block_terminated = True

            elif op == "CALL":
                args = []

                if ins.extra:
                    for item in ins.extra.split(","):
                        item = item.strip()
                        if item:
                            args.append(f"w {self.value(item)}")

                call = f"call ${ins.a}({', '.join(args)})"
                self.emit(f"{dst} =w {call}" if dst else call)

            else:
                raise QBECodegenError(
                    f"Unsupported IR operation: {op}"
                )

        self.emit("}")


def generate_qbe(ir_program: IRProgram) -> str:
    return QBECodeGenerator().generate(ir_program)


def write_qbe(ir_program: IRProgram, output_path: str) -> str:
    qbe_text = generate_qbe(ir_program)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(qbe_text)

    return output_path
