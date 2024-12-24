from pathlib import Path
from JackTokenizer import JackTokenizer


class CompilationEngine:
    UNARY_OP = ['~', '-']
    BINARY_OP = ['+', '-', '*', '/', '&', '|', '>', '<', '=']
    KEYWORD_CONST = ["true", "false", "null", "this"]
    CLASS_VAR_DEC_KW = ["static", "field"]
    SUBROUTINE_DEC_KW = ["constructor", "function", "method"]
    TYPE_KW = ["int", "char", "boolean"]
    RETURN_TYPE_KW = ["int", "char", "boolean", "void"]
    STATEMENT_KW = ["while", "if", "let", "return", "do"]

    def __init__(self, tokenizer: JackTokenizer):
        self.tokenizer = tokenizer
        self.output = ""
        self.indentation = 0
        self.compile_class()

    def write_file(self, output_path: Path) -> None:
        with open(output_path, 'w') as file:
            file.writelines(self.output)

    def write(self, type: str, value: str | int) -> None:
        self.output += "\t" * self.indentation + f"<{type}> {value} </{type}>\n"

    def write_non_terminal(self, string: str, entry: bool) -> None:
        self.output += "\t" * self.indentation + f"<{'/' * (not entry)}{string}>\n"

    def next(self) -> None:
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

    def eat(self, expected: str | list) -> str:
        if not self.check(expected):
            raise SyntaxError(f"Expected {expected} but {self.tokenizer.current_token} was found.")
        word = self.tokenizer.current_token
        self.next()
        return word

    def check(self, expected: str | list) -> bool:
        if type(expected) is not list:
            expected = [expected]
        return self.tokenizer.current_token in expected

    def compile_class(self):
        self.write_non_terminal("class", True)
        self.indentation += 1
        self.next()
        # 'class'
        self.eat("class")
        self.write("keyword", "class")
        # class_name
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.write("identifier", self.tokenizer.identifier())
        else:
            raise SyntaxError(f"Excepted className identifier but found : {self.tokenizer.current_token}")
        self.next()
        # '{'
        self.eat('{')
        self.write("symbol", '{')
        # classVarDec*
        while self.check(CompilationEngine.CLASS_VAR_DEC_KW):
            self.compile_class_var_dec()
        # subroutineDec*
        while self.check(CompilationEngine.SUBROUTINE_DEC_KW):
            self.compile_subroutine_dec()
        # '}'
        self.eat('}')
        self.write("symbol", '}')

        self.indentation -= 1
        self.write_non_terminal("class", False)

    def compile_class_var_dec(self):
        self.write_non_terminal("classVarDec", True)
        self.indentation += 1
        # static / field
        word = self.eat(CompilationEngine.CLASS_VAR_DEC_KW)
        self.write("keyword", word)
        # type
        if self.check(CompilationEngine.TYPE_KW):
            word = self.eat(CompilationEngine.TYPE_KW)
            self.write("keyword", word)
        elif self.tokenizer.token_type() == "IDENTIFIER":
            self.write("identifier", self.tokenizer.current_token)
            self.next()
        else:
            raise SyntaxError(f"Excepted variable type but found : {self.tokenizer.current_token}")
        # varName
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.write("identifier", self.tokenizer.current_token)
        else:
            raise SyntaxError(f"Excepted varName identifier but found : {self.tokenizer.current_token}")
        self.next()
        # (, varName)*
        while not self.check(';'):
            #,
            self.eat(',')
            self.write("symbol", ',')
            # varName
            if self.tokenizer.token_type() == "IDENTIFIER":
                self.write("identifier", self.tokenizer.current_token)
            else:
                raise SyntaxError(f"Excepted varName identifier but found : {self.tokenizer.current_token}")
            self.next()
        self.eat(';')
        self.write("symbol", ';')

        self.indentation -= 1
        self.write_non_terminal("classVarDec", False)

    def compile_subroutine_dec(self):
        self.write_non_terminal("subroutineDec", True)
        self.indentation += 1

        # constructor | method | function
        word = self.eat(CompilationEngine.SUBROUTINE_DEC_KW)
        self.write("keyword", word)
        # type | className
        if self.check(CompilationEngine.RETURN_TYPE_KW):
            word = self.eat(CompilationEngine.RETURN_TYPE_KW)
            self.write("keyword", word)
        elif self.tokenizer.token_type() == "IDENTIFIER":
            self.write("identifier", self.tokenizer.current_token)
            self.next()
        else:
            raise SyntaxError(f"Excepted subroutine type but found : {self.tokenizer.current_token}")
        # subroutineName
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.write("identifier", self.tokenizer.current_token)
        else:
            raise SyntaxError(f"Excepted subroutineName identifier but found : {self.tokenizer.current_token}")
        self.next()
        # (
        self.eat('(')
        self.write("symbol", '(')
        # parameter list
        self.compile_parameter_list()
        # )
        self.eat(')')
        self.write("symbol", ')')
        # subroutine body
        self.compile_subroutine_body()

        self.indentation -= 1
        self.write_non_terminal("subroutineDec", False)

    def compile_parameter_list(self):
        self.write_non_terminal("parameterList", True)
        self.indentation += 1
        # optional
        if self.check(')'):
            self.indentation -= 1
            self.write_non_terminal("parameterList", False)
            return
        # type | className
        if self.check(CompilationEngine.TYPE_KW):
            word = self.eat(CompilationEngine.TYPE_KW)
            self.write("keyword", word)
        elif self.tokenizer.token_type() == "IDENTIFIER":
            self.write("identifier", self.tokenizer.current_token)
            self.next()
        else:
            raise SyntaxError(f"Excepted subroutine type but found : {self.tokenizer.current_token}")
        # varName
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.write("identifier", self.tokenizer.current_token)
        else:
            raise SyntaxError(f"Excepted varName identifier but found : {self.tokenizer.current_token}")
        self.next()
        # (, type varName)*
        while not self.check(')'):
            #,
            self.eat(',')
            self.write("symbol", ',')
            # type | className
            if self.check(CompilationEngine.TYPE_KW):
                word = self.eat(CompilationEngine.TYPE_KW)
                self.write("keyword", word)
            elif self.tokenizer.token_type() == "IDENTIFIER":
                self.write("identifier", self.tokenizer.current_token)
                self.next()
            else:
                raise SyntaxError(f"Excepted subroutine type but found : {self.tokenizer.current_token}")
            # varName
            if self.tokenizer.token_type() == "IDENTIFIER":
                self.write("identifier", self.tokenizer.current_token)
            else:
                raise SyntaxError(f"Excepted varName identifier but found : {self.tokenizer.current_token}")
            self.next()
        self.indentation -= 1
        self.write_non_terminal("parameterList", False)

    def compile_subroutine_body(self):
        self.write_non_terminal("subroutineBody", True)
        self.indentation += 1

        # {
        self.eat('{')
        self.write("symbol", '{')
        # varDec*
        while self.check("var"):
            self.compile_var_dec()
        # statements
        self.compile_statements()
        # }
        self.eat('}')
        self.write("symbol", '}')

        self.indentation -= 1
        self.write_non_terminal("subroutineBody", False)

    def compile_var_dec(self):
        self.write_non_terminal("varDec", True)
        self.indentation += 1

        # var
        self.eat("var")
        self.write("keyword", "var")
        # type | className
        if self.check(CompilationEngine.TYPE_KW):
            word = self.eat(CompilationEngine.TYPE_KW)
            self.write("keyword", word)
        elif self.tokenizer.token_type() == "IDENTIFIER":
            self.write("identifier", self.tokenizer.current_token)
            self.next()
        else:
            raise SyntaxError(f"Excepted subroutine type but found : {self.tokenizer.current_token}")
        # varName
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.write("identifier", self.tokenizer.current_token)
        else:
            raise SyntaxError(f"Excepted varName identifier but found : {self.tokenizer.current_token}")
        self.next()
        # (, varName)*
        while not self.check(';'):
            #,
            self.eat(',')
            self.write("symbol", ',')
            # varName
            if self.tokenizer.token_type() == "IDENTIFIER":
                self.write("identifier", self.tokenizer.current_token)
            else:
                raise SyntaxError(f"Excepted varName identifier but found : {self.tokenizer.current_token}")
            self.next()
        self.eat(';')
        self.write("symbol", ';')

        self.indentation -= 1
        self.write_non_terminal("varDec", False)

    def compile_statements(self):
        self.write_non_terminal("statements", True)
        self.indentation += 1
        while self.check(CompilationEngine.STATEMENT_KW):
            word = self.eat(CompilationEngine.STATEMENT_KW)
            match word:
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
        self.indentation -= 1
        self.write_non_terminal("statements", False)

    def compile_let(self):
        print("let", self.tokenizer.current_token)
        self.write_non_terminal("letStatement", True)
        self.indentation += 1

        # let
        self.write("keyword", "let")
        # varName
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.write("identifier", self.tokenizer.current_token)
        else:
            raise SyntaxError(f"Excepted varName identifier but found : {self.tokenizer.current_token}")
        self.next()
        # optional
        if self.check('['):
            # [
            self.eat('[')
            self.write("symbol", '[')
            # expression
            self.compile_expression()
            # ]
            self.eat(']')
            self.write("symbol", ']')
        # =
        self.eat('=')
        self.write("symbol", '=')
        # expression
        self.compile_expression()
        # ;
        self.eat(';')
        self.write("symbol", ';')

        self.indentation -= 1
        self.write_non_terminal("letStatement", False)

    def compile_if(self):
        print("if")
        self.write_non_terminal("ifStatement", True)
        self.indentation += 1
        self.write("keyword", "if")
        # (
        self.eat('(')
        self.write("symbol", '(')
        # expression
        self.compile_expression()
        # )
        self.eat(')')
        self.write("symbol", ')')
        # {
        self.eat('{')
        self.write("symbol", '{')
        # statements
        self.compile_statements()
        # }
        self.eat('}')
        self.write("symbol", '}')
        # optional else
        print("else")
        if self.check("else"):
            self.eat("else")
            self.write("keyword", "else")
            # {
            self.eat('{')
            self.write("symbol", '{')
            # statements
            self.compile_statements()
            # }
            self.eat('}')
            self.write("symbol", '}')

        self.indentation -= 1
        self.write_non_terminal("ifStatement", False)

    def compile_while(self):
        print("while")
        self.write_non_terminal("whileStatement", True)
        self.indentation += 1

        self.write("keyword", "while")
        # (
        self.eat('(')
        self.write("symbol", '(')
        # expression
        self.compile_expression()
        # )
        self.eat(')')
        self.write("symbol", ')')
        # {
        self.eat('{')
        self.write("symbol", '{')
        # statements
        self.compile_statements()
        # }
        self.eat('}')
        self.write("symbol", '}')

        self.indentation -= 1
        self.write_non_terminal("whileStatement", False)

    def compile_do(self):
        print("do")
        self.write_non_terminal("doStatement", True)
        self.indentation += 1
        # do
        self.write("keyword", "do")
        # subroutineCall
        self.write_subroutine_call()
        # ;
        self.eat(';')
        self.write("symbol", ';')

        self.indentation -= 1
        self.write_non_terminal("doStatement", False)

    def write_subroutine_call(self, token: str = None, token_type: str = None):
        print("call")
        # subroutineCall
        # subroutineName or className | varName
        overwrite = True
        if token_type is None:
            token_type = self.tokenizer.token_type()
            token = self.tokenizer.current_token
            overwrite = False
        if token_type == "IDENTIFIER":
            self.write("identifier", token)
            if not overwrite:
                self.next()
        else:
            raise SyntaxError(f"Expected identifier but found {self.tokenizer.current_token}")
        # optional .
        if self.check('.'):
            # .
            self.eat('.')
            self.write("symbol", '.')
            # subroutineName
            if self.tokenizer.token_type() == "IDENTIFIER":
                self.write("identifier", self.tokenizer.current_token)
                self.next()
            else:
                raise SyntaxError(f"Expected subroutine identifier but found {self.tokenizer.current_token}")
        # (
        self.eat('(')
        self.write("symbol", '(')
        # expression list
        self.compile_expression_list()
        # )
        self.eat(')')
        self.write("symbol", ')')

    def compile_return(self):
        print("return", self.tokenizer.current_token)
        self.write_non_terminal("returnStatement", True)
        self.indentation += 1

        self.write("keyword", "return")
        # expression
        # check beforehand to not generate empty branches
        if self.tokenizer.token_type() in ["IDENTIFIER", "integerConst", "stringConst"] or \
                self.tokenizer.current_token in CompilationEngine.KEYWORD_CONST or \
                self.tokenizer.current_token in CompilationEngine.UNARY_OP + ['(']:
            self.compile_expression()
        # ;
        self.eat(';')
        self.write("symbol", ';')

        self.indentation -= 1
        self.write_non_terminal("returnStatement", False)

    def compile_expression(self):
        self.write_non_terminal("expression", True)
        self.indentation += 1
        print("comp expr", self.tokenizer.current_token)
        print("comp expr curr type", self.tokenizer.token_type())
        # term
        self.compile_term()
        # optional repeat
        while self.check(CompilationEngine.BINARY_OP):
            # binary operation
            op = self.eat(CompilationEngine.BINARY_OP)
            self.write("symbol", self.tokenizer.symbol(op))
            # term
            self.compile_term()

        self.indentation -= 1
        self.write_non_terminal("expression", False)

    def compile_term(self):
        self.write_non_terminal("term", True)
        self.indentation += 1
        print("compile term", self.tokenizer.current_token)
        if self.tokenizer.token_type() == "INT_CONST":
            self.write("integerConstant", self.tokenizer.int_val())
            self.next()
        elif self.tokenizer.token_type() == "STRING_CONST":
            print("string constant")
            self.write("stringConstant", self.tokenizer.string_val())
            self.next()
        elif self.tokenizer.current_token in CompilationEngine.KEYWORD_CONST:
            self.write("keyword", self.tokenizer.keyword())
            self.next()
        elif self.check('('):       # '(' expr ')'
            # (
            self.eat('(')
            self.write("symbol", '(')
            # expression
            self.compile_expression()
            # )
            self.eat(')')
            self.write("symbol", ')')
        elif self.check(CompilationEngine.UNARY_OP):
            print("unary op", self.tokenizer.symbol())
            # op
            op = self.eat(CompilationEngine.UNARY_OP)
            self.write("symbol", op)
            # term
            self.compile_term()
        elif self.tokenizer.token_type() == "IDENTIFIER":
            token_pre = self.tokenizer.current_token
            token_pre_type = self.tokenizer.token_type()
            self.next()
            if self.check('['):  # array entry
                # variableName
                self.write("identifier", token_pre)
                # [
                self.eat('[')
                self.write("symbol", '[')
                # expression
                self.compile_expression()
                # ]
                self.eat(']')
                self.write("symbol", ']')
            elif self.check(['(', '.']):  # subroutineCall
                self.write_subroutine_call(token_pre, token_pre_type)
            else:  # variable name
                self.write("identifier", token_pre)

        self.indentation -= 1
        self.write_non_terminal("term", False)

    def compile_expression_list(self):
        print("expr list")
        self.write_non_terminal("expressionList", True)
        self.indentation += 1

        # check beforehand to not generate empty branches
        if self.tokenizer.token_type() in ["IDENTIFIER", "INT_CONST", "STRING_CONST"] or \
                self.tokenizer.current_token in CompilationEngine.KEYWORD_CONST or \
                self.tokenizer.current_token in CompilationEngine.UNARY_OP + ['(']:
            print("no skip", self.tokenizer.current_token)
            # expression
            self.compile_expression()
            # (, expression)*
            while self.check(','):
                # ,
                self.eat(',')
                self.write("symbol", ',')
                print(self.tokenizer.current_token)
                # expression
                self.compile_expression()

        self.indentation -= 1
        self.write_non_terminal("expressionList", False)
