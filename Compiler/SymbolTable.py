class SymbolTable:

    def __init__(self):
        self.table_var = {}
        self.table_arg = {}
        self.table_field = {}
        self.table_static = {}

    def start_subroutine(self):
        self.table_var = {}
        self.table_arg = {}

    def define(self, name: str, type: str, kind: str):
        match kind:
            case "var":
                self.table_var[name] = (type, len(self.table_var))
            case "argument":
                self.table_arg[name] = (type, len(self.table_arg))
            case "field":
                self.table_field[name] = (type, len(self.table_field))
            case "static":
                self.table_static[name] = (type, len(self.table_static))
            case _:
                raise ValueError(f"Unexpected kind in SymbolTable.define: {kind}")

    def var_count(self, kind: str) -> int:
        match kind:
            case "argument":
                return len(self.table_arg)
            case "var":
                return len(self.table_var)
            case "static":
                return len(self.table_static)
            case "field":
                return len(self.table_field)
            case _:
                raise ValueError(f"Unexpected kind in SymbolTable.var_count: {kind}")

    def kind_of(self, name: str) -> str | None:
        if name in self.table_arg:
            return "argument"
        if name in self.table_var:
            return "var"
        if name in self.table_field:
            return "field"
        if name in self.table_static:
            return "static"
        return None

    def type_of(self, name: str) -> str | None:
        if name in self.table_arg:
            return self.table_arg[name][0]
        if name in self.table_var:
            return self.table_var[name][0]
        if name in self.table_field:
            return self.table_field[name][0]
        if name in self.table_static:
            return self.table_static[name][0]
        return None

    def index_of(self, name: str) -> int | None:
        if name in self.table_arg:
            return self.table_arg[name][1]
        if name in self.table_var:
            return self.table_var[name][1]
        if name in self.table_field:
            return self.table_field[name][1]
        if name in self.table_static:
            return self.table_static[name][1]
        return None
