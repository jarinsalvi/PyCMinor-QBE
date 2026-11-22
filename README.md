# PyCMinor-QBE Compiler

A Python-based C Minor compiler with QBE backend.

## Features
- Lexer and parser
- Semantic analysis
- Function declarations and definitions
- Arrays and array access validation
- Intermediate representation
- QBE backend

## Setup
```bash
pip install -r requirements.txt
```

## Run
```bash
python main.py --check examples/hello.cminor
python main.py --capabilities
```

## Tests
```bash
python -m pytest -q
```

Version: 0.1.0
