from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Symbol:
    name: str
    kind: str          # 'function', 'parameter', 'local'
    type_name: str     # 'int', 'void'
    symbol_id: int
    line: int = 0
    column: int = 0
    param_types: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    is_defined: bool = False
    is_array: bool = False

class SymbolTable:
    def __init__(self):
        self.global_functions: Dict[str, Symbol] = {}
        self.scopes: List[Dict[str, Symbol]] = [{}]
        self._next_id: int = 1

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare_variable(self, name: str, type_name: str, kind: str, line: int = 0, col: int = 0, is_array: bool = False) -> Optional[Symbol]:
        current_scope = self.scopes[-1]
        if name in current_scope:
            return None
        sym_id = self._next_id
        self._next_id += 1
        sym = Symbol(name=name, kind=kind, type_name=type_name, symbol_id=sym_id, line=line, column=col, is_array=is_array)
        current_scope[name] = sym
        return sym

    def lookup_variable(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def declare_function(self, name: str, return_type: str, param_types: List[str], line: int = 0, col: int = 0, is_defined: bool = False) -> tuple[Optional[Symbol], Optional[str]]:
        if name in self.global_functions:
            existing = self.global_functions[name]
            if existing.return_type != return_type or existing.param_types != param_types:
                return None, f"Conflicting signature for function '{name}'"
            if is_defined and existing.is_defined:
                return None, f"Redefinition of function '{name}'"
            if is_defined:
                existing.is_defined = True
            return existing, None
        
        sym_id = self._next_id
        self._next_id += 1
        sym = Symbol(
            name=name, kind='function', type_name=return_type, symbol_id=sym_id,
            line=line, column=col, param_types=param_types, return_type=return_type, is_defined=is_defined
        )
        self.global_functions[name] = sym
        return sym, None