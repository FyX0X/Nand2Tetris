from pathlib import Path
from JackTokenizer import JackTokenizer
from SymbolTable import SymbolTable
from VMWriter import VMWriter


class CompilationEngine:
    UNARY_OP = ['~', '-']
    U_OP_TO_VM = {'~': "not", '-': "neg"}
    BINARY_OP = ['+', '-', '*', '/', '&amp;', '|', '&lt;', '&gt;', '=']
    B_OP_TO_VM = {'+': "add", '-': "sub", '&amp;': "and", '|': "or", '&lt;': "lt", '&gt;': "gt", '=': "eq"}
    KEYWORD_CONST = ["true", "false", "null", "this"]
    CLASS_VAR_DEC_KW = ["static", "field"]
    SUBROUTINE_DEC_KW = ["constructor", "function", "method"]
    TYPE_KW = ["int", "char", "boolean"]
    RETURN_TYPE_KW = ["int", "char", "boolean", "void"]
    STATEMENT_KW = ["while", "if", "let", "return", "do"]

    KIND_TO_SEGMENT = {"var": "local", "argument": "argument", "field": "this", "static": "static"}

    if_count = -1
    while_count = -1

    def __init__(self, tokenizer: JackTokenizer, output_path: Path):
        self.tokenizer = tokenizer
        self.writer = VMWriter(output_path)
        self.symbol_table = SymbolTable()
        self.output = ""
        self.indentation = 0
        self.current_class = None

        self.tokenizer.advance()
        self.compile_class()

        self.writer.write_file()
    """
    def next(self) -> None:
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
    """
    def eat(self, expected: str | list, advance: bool = True) -> str:
        if not self.check(expected):
            raise SyntaxError(f"Expected {expected} but {self.tokenizer.current_token} was found.")
        token = self.tokenizer.current_token
        if advance:
            self.tokenizer.advance()
        return token

    def eat_type(self, expected: str | list) -> str:
        if not self.check_type(expected):
            raise SyntaxError(f"Expected {expected} but {self.tokenizer.current_type} was found.")
        token = self.tokenizer.current_token
        self.tokenizer.advance()
        return token

    def check(self, expected: str | list) -> bool:
        if type(expected) is not list:
            expected = [expected]
        return self.tokenizer.current_token in expected

    def check_type(self, expected: str | list) -> bool:
        if type(expected) is not list:
            expected = [expected]
        return self.tokenizer.current_type in expected

    def eat_var_type(self, return_type: bool = False) -> str:
        allowed_kw = CompilationEngine.TYPE_KW
        if return_type:
            allowed_kw = CompilationEngine.RETURN_TYPE_KW

        if self.check_type("keyword"):
            return self.eat(allowed_kw)                 # type | className
        elif self.check_type("identifier"):
            return self.eat_type("identifier")
        else:
            raise SyntaxError(f"Excepted variable type but found : {self.tokenizer.current_token}")

    def compile_class(self):
        self.eat("class")
        self.current_class = self.eat_type("identifier")     # class_name
        self.eat('{')
        while self.check(CompilationEngine.CLASS_VAR_DEC_KW):   # classVarDec*
            self.compile_class_var_dec()
        while self.check(CompilationEngine.SUBROUTINE_DEC_KW):  # subroutineDec*
            self.compile_subroutine_dec()
        self.eat('}', False)

    def compile_class_var_dec(self):
        var_kind = self.eat(CompilationEngine.CLASS_VAR_DEC_KW)         # static / field
        var_type = self.eat_var_type()                                  # type | className
        var_name = self.eat_type("identifier")                          # varName
        self.symbol_table.define(var_name, var_type, var_kind)
        while not self.check(';'):                                      # (, varName)*
            self.eat(',')
            var_name = self.eat_type("identifier")                      # varName
            self.symbol_table.define(var_name, var_type, var_kind)
        self.eat(';')

    def compile_subroutine_dec(self):
        self.symbol_table.start_subroutine()                                # reset subroutine symbol table

        subroutine_type = self.eat(CompilationEngine.SUBROUTINE_DEC_KW)     # constructor | method | function
        if subroutine_type == "method":
            self.symbol_table.define("this", "int", "argument")

        self.eat_var_type(True)                                             # return type
        subroutine_name = self.eat_type("identifier")                       # subroutineName
        self.eat('(')
        self.compile_parameter_list()
        self.eat(')')
        self.compile_subroutine_body(self.current_class + '.' + subroutine_name, subroutine_type)

    def compile_parameter_list(self):
        if not self.check(')'):             # optional
            var_type = self.eat_var_type()
            var_name = self.eat_type("identifier")
            self.symbol_table.define(var_name, var_type, "argument")
            while not self.check(')'):      # (, type varName)*
                self.eat(',')
                var_type = self.eat_var_type()
                var_name = self.eat_type("identifier")
                self.symbol_table.define(var_name, var_type, "argument")

    def compile_subroutine_body(self, function_name, subroutine_type):
        var_count = 0
        self.eat('{')
        while self.check("var"):        # varDec*
            var_count += self.compile_var_dec()
        self.writer.write_function(function_name, var_count)
        match subroutine_type:
            case "constructor":
                instance_size = self.symbol_table.var_count("field")
                self.writer.write_push("constant", instance_size)
                self.writer.write_call("Memory.alloc", 1)
                self.writer.write_pop("pointer", 0)
            case "method":
                self.writer.write_push("argument", 0)       # current object
                self.writer.write_pop("pointer", 0)

        self.compile_statements()
        self.eat('}')

    def compile_var_dec(self) -> int:
        var_count = 1
        self.eat("var")
        var_type = self.eat_var_type()
        var_name = self.eat_type("identifier")
        self.symbol_table.define(var_name, var_type, "var")
        while not self.check(';'):          # (, varName)*
            var_count += 1
            self.eat(',')
            var_name = self.eat_type("identifier")
            self.symbol_table.define(var_name, var_type, "var")
        self.eat(';')
        return var_count

    def compile_statements(self):
        while self.check(CompilationEngine.STATEMENT_KW):
            match self.tokenizer.current_token:
                case "while":
                    self.compile_while()
                case "if":
                    self.compile_if()
                case "let":
                    self.compile_let()
                case "return":
                    self.compile_return()
                case "do":
                    self.compile_do()

    def compile_let(self):
        self.eat("let")
        var_name = self.eat_type("identifier")
        var_kind = self.symbol_table.kind_of(var_name)
        segment = CompilationEngine.KIND_TO_SEGMENT[var_kind]
        var_index = self.symbol_table.index_of(var_name)
        if self.check('['):                                         # only for array
            self.writer.write_push(segment, var_index)              # push array base address
            self.eat('[')
            self.compile_expression()                               # comp(expr) -> index
            self.eat(']')
            self.writer.write_arithmetic("add")                     # add index with base address
            self.eat('=')
            self.compile_expression()                               # compute and push RHS
            self.eat(';')
            self.writer.write_pop("temp", 0)
            self.writer.write_pop("pointer", 1)
            self.writer.write_push("temp", 0)
            self.writer.write_pop("that", 0)
        else:                                                       # only for not array
            self.eat('=')
            self.compile_expression()                               # comp(expr) -> RHS
            self.eat(';')
            self.writer.write_pop(segment, var_index)

    def compile_if(self):
        CompilationEngine.if_count += 1
        this_if = CompilationEngine.if_count

        self.eat("if")
        self.eat('(')
        self.compile_expression()                       # comp(expr) condition
        self.writer.write_arithmetic("not")             # negate condition
        self.eat(')')
        self.writer.write_if(f"IF_FALSE_{this_if}")     # if-goto L1
        self.eat('{')
        self.compile_statements()                       # comp(expr)    condition is true
        self.eat('}')
        self.writer.write_goto(f"IF_END_{this_if}")     # goto L2
        self.writer.write_label(f"IF_FALSE_{this_if}")  # label L1
        if self.check("else"):      # optional else
            self.eat('else')
            self.eat('{')
            self.compile_statements()                   # comp(expr) condition is false
            self.eat('}')
        self.writer.write_label(f"IF_END_{this_if}")    # label L2

    def compile_while(self):
        CompilationEngine.while_count += 1
        this_while = CompilationEngine.while_count

        self.eat("while")
        self.writer.write_label(f"WHILE_LOOP_{this_while}")         # label L1
        self.eat('(')
        self.compile_expression()                                   # comp(expr) condition
        self.writer.write_arithmetic("not")                         # negate condition
        self.writer.write_if(f"WHILE_END_{this_while}")             # if goto L2
        self.eat(')')
        self.eat('{')
        self.compile_statements()                                   # comp(statement) loop
        self.eat('}')
        self.writer.write_goto(f"WHILE_LOOP_{this_while}")
        self.writer.write_label(f"WHILE_END_{this_while}")

    def compile_do(self):
        self.eat("do")
        self.write_subroutine_call()
        self.eat(';')
        self.writer.write_pop("temp", 0)            # pop for void subroutine

    def write_subroutine_call(self):
        n_args = 0
        name = self.eat_type("identifier")                          # subroutineName or className | varName
        if self.check('.'):                                         # optional . (preceded by a class or var name)
            kind = self.symbol_table.kind_of(name)
            if kind is None:                                        # className -> function or constructor
                class_name = name
            else:                                                   # varName   -> method
                class_name = self.symbol_table.type_of(name)
                var_index = self.symbol_table.index_of(name)
                segment = CompilationEngine.KIND_TO_SEGMENT[kind]
                self.writer.write_push(segment, var_index)
                n_args = 1
            self.eat('.')
            subroutine_name = self.eat_type("identifier")
            callee = class_name + '.' + subroutine_name
        else:                                                       # subroutine name only -> method
            callee = self.current_class + '.' + name
            self.writer.write_push("pointer", 0)      # method so push THIS
            n_args = 1

        self.eat('(')
        n_args += self.compile_expression_list()                    # expr0, expr1, expr2, ...
        self.eat(')')
        self.writer.write_call(callee, n_args)                      # call function

    def compile_return(self):
        self.eat("return")
        if not self.check(';'):
            self.compile_expression()
        else:
            self.writer.write_push("constant", 0)
        self.eat(';')
        self.writer.write_return()

    def compile_expression(self):
        self.compile_term()                                         # write exp 1
        while self.check(CompilationEngine.BINARY_OP):              # optional operation
            operation = self.eat(CompilationEngine.BINARY_OP)
            self.compile_term()                                     # write exp 2
            vm_op = CompilationEngine.B_OP_TO_VM.get(operation)
            if vm_op is None:
                if operation == "*":
                    self.writer.write_call("Math.multiply", 2)
                elif operation == "/":
                    self.writer.write_call("Math.divide", 2)
            else:
                self.writer.write_arithmetic(vm_op)                     # write operation after (postfix)

    def compile_term(self):
        if self.check_type("integerConstant"):                          # push constant n
            number = self.eat_type("integerConstant")
            self.writer.write_push("constant", int(number))
        elif self.check_type("stringConstant"):
            string = self.eat_type("stringConstant")
            self.writer.write_push("constant", len(string))     # push length
            self.writer.write_call("String.new", 1)         # call String.new(length)
            for char in string:
                self.writer.write_push("constant", ord(char))
                self.writer.write_call("String.appendChar", 2)
        elif self.check(CompilationEngine.KEYWORD_CONST):
            keyword = self.eat(CompilationEngine.KEYWORD_CONST)
            if keyword == "true":
                self.writer.write_push("constant", 1)
                self.writer.write_arithmetic("neg")
            elif keyword == "this":
                self.writer.write_push("pointer", 0)
            else:   # false and null
                self.writer.write_push("constant", 0)
        elif self.check('('):                                           # '(' expr ')'
            self.eat('(')
            self.compile_expression()
            self.eat(')')
        elif self.check(CompilationEngine.UNARY_OP):
            operation = self.eat(CompilationEngine.UNARY_OP)
            self.compile_term()                                         # exp
            vm_op = CompilationEngine.U_OP_TO_VM[operation]
            self.writer.write_arithmetic(vm_op)                         # operation (postfix)
        elif self.check_type("identifier"):
            if self.tokenizer.peek_token() == '[':                      # array entry
                var_name = self.eat_type("identifier")                  # variableName
                var_kind = self.symbol_table.kind_of(var_name)
                segment = CompilationEngine.KIND_TO_SEGMENT[var_kind]
                var_index = self.symbol_table.index_of(var_name)
                self.writer.write_push(segment, var_index)              # push address of array
                self.eat('[')
                self.compile_expression()                               # comp(expr) and push
                self.eat(']')
                self.writer.write_arithmetic("add")                     # add base address to expr => addr of array[expr]
                self.writer.write_pop("pointer", 1)       # set THAT pointer
                self.writer.write_push("that", 0)         # push value
            elif self.tokenizer.peek_token() in ['(', '.']:             # subroutineCall
                self.write_subroutine_call()
            else:                                                       # variableName
                var_name = self.eat_type("identifier")                  # push segment i
                var_kind = self.symbol_table.kind_of(var_name)
                var_index = self.symbol_table.index_of(var_name)
                segment = CompilationEngine.KIND_TO_SEGMENT[var_kind]
                self.writer.write_push(segment, var_index)

    def compile_expression_list(self) -> int:
        expression_counter = 0
        if not self.check(')'):
            self.compile_expression()
            expression_counter += 1
            while self.check(','):          # (, expression)*
                self.eat(',')
                self.compile_expression()
                expression_counter += 1
        return expression_counter
