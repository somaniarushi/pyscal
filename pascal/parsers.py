from ctypes.wintypes import FLOAT
from pascal.constants import *

####################### Classes #########################

class AST:
    pass

class NoOp(AST):
    pass

class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class UnaryOp(AST):
    def __init__(self, op, expr):
        self.token = self.op = op
        self.expr = expr

class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right

class Var(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Assign(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.type = self.op = op
        self.right = right

class Compound(AST):
    def __init__(self):
        self.children = []

class Type(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class VarDecl(AST):
    def __init__(self, var_node, type_node):
        self.var_node = var_node
        self.type_node = type_node

class ProcedureDecl(AST):
    def __init__(self, name, block):
        self.name = name
        self.block = block

class Block(AST):
    def __init__(self, declarations, compound_statement):
        self.declarations = declarations
        self.compound_statement = compound_statement

class Program(AST):
    def __init__(self, name, block):
        self.name = name
        self.block = block

########################################################

class Parser:
    def __init__(self, lexer):
        '''
        Accepts a string input from the client as text,
        and maintains an index into text and the
        current token instance.
        '''
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def eat(self, token_type):
        '''
        If the current token matches the passed in
        token type, eat it and update self.current_token
        Otherwise, raise error.
        '''
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def error(self):
        raise Exception('Invalid syntax')

    def parse(self):
        root = self.program()
        if self.current_token.type != EOF:
            self.error()
        return root

    def program(self):
        '''
        program: PROGRAM variable SEMI block DOT
        '''
        self.eat(PROGRAM)
        prog_name = self.variable().value
        self.eat(SEMI)
        block_node = self.block()
        self.eat(DOT)
        return Program(prog_name, block_node)

    def block(self):
        '''
        block: declarations compound_statement
        '''
        decl = self.declarations()
        compound = self.compound_statement()
        return Block(decl, compound)

    def declarations(self):
        '''
        declarations: VAR (variable_declaration SEMI)+ | empty
        '''
        declarations = []
        if self.current_token.type == VAR:
            self.eat(VAR)
            while self.current_token.type == ID:
                var_decl = self.variable_declaration()
                declarations.extend(var_decl)
                self.eat(SEMI)

        while self.current_token.type == PROCEDURE:
            self.eat(PROCEDURE)
            name = self.current_token.value
            self.eat(ID)
            self.eat(SEMI)
            declarations.append(ProcedureDecl(name, self.block()))
            self.eat(SEMI)

        return declarations

    def variable_declaration(self):
        '''
        variable_declaration : ID (COMMA ID)* COLON type_spec
        '''
        var_nodes = [Var(self.current_token)] # first id
        self.eat(ID)

        while self.current_token.type == COMMA:
            self.eat(COMMA)
            var_nodes.append(Var(self.current_token))
            self.eat(ID)
        self.eat(COLON)

        type_node = self.type_spec()
        var_declarations = [ VarDecl(var_node, type_node) for var_node in var_nodes]
        return var_declarations

    def type_spec(self):
        '''
        type_spec: INTEGER | REAL
        '''
        token = self.current_token
        if self.current_token.type == INTEGER:
            self.eat(INTEGER)
        else:
            self.eat(REAL)
        node = Type(token)
        return node

    def compound_statement(self):
        '''
        compound_statement: BEGIN statement_list END
        '''
        self.eat(BEGIN)
        nodes = self.statement_list()
        self.eat(END)

        root = Compound()
        root.children.extend(nodes)
        return root

    def statement_list(self):
        '''
        statement_list: statement | statement SEMI statement_list
        '''
        results = [self.statement()]
        while self.current_token.type == SEMI:
            self.eat(SEMI)
            results.append(self.statement())

        if self.current_token.type == ID:
            self.error()

        return results


    def statement(self):
        '''
        statement: compound_statement | assignment_statement | empty
        '''
        if self.current_token.type == BEGIN:
            return self.compound_statement()
        elif self.current_token.type == ID:
            return self.assignment_statement()
        else:
            return self.empty()

    def assignment_statement(self):
        '''
        assigment_statement: variable ASSIGN expr
        '''
        left = self.variable()
        token = self.current_token
        self.eat(ASSIGN)
        right = self.expr()
        return Assign(left, token, right)

    def variable(self):
        '''
        variable: ID
        '''
        node = Var(self.current_token)
        self.eat(ID)
        return node

    def empty(self):
        '''
        empty:
        '''
        return NoOp()

    def expr(self):
        '''
        Parses the text and returns the expression.

        expr: term ((PLUS | MINUS) term)*
        term: factor ((MUL | DIV) factor)*
        factor: INTEGER
        '''
        node = self.term()
        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
            elif token.type == MINUS:
                self.eat(MINUS)
            node = BinOp(left=node, op=token, right=self.term())
        return node

    def term(self):
        '''
        Returns the AST term starting at current_token and eats values as necessary

        term: factor ((MUL | INTEGER_DIV | FLOAT_DIV) factor)*
        '''
        node = self.factor()
        while self.current_token.type in (MUL, INTEGER_DIV, FLOAT_DIV):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
            elif token.type == INTEGER_DIV:
                self.eat(INTEGER_DIV)
            elif token.type == FLOAT_DIV:
                self.eat(FLOAT_DIV)
            node = BinOp(left=node, op=token, right=self.factor())
        return node

    def factor(self):
        '''
        Returns the factor AST that is current_token and
        eats the current_token

        factor : +/- factor | INTEGER | ( expr ) | variable
        '''
        token = self.current_token

        if token.type == PLUS:
            self.eat(PLUS)
            node = UnaryOp(token, self.factor())
            return node

        elif token.type == MINUS:
            self.eat(MINUS)
            node = UnaryOp(token, self.factor())
            return node

        elif token.type == INTEGER_CONST:
            self.eat(INTEGER_CONST)
            return Num(token)

        elif token.type == REAL_CONST:
            self.eat(REAL_CONST)
            return Num(token)

        elif token.type == LPAREN:
            self.eat(LPAREN)
            node = self.expr()
            self.eat(RPAREN)
            return node

        else:
            node = self.variable()
            return node