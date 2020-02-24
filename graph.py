
import os,sys

def comment(text,width=80):
    pfx = '#' * (width - len(text) - 1)
    print(pfx + ' ' + text) ; sys.exit(-1)
# comment('debug')#,40)


########################################### Marvin Minsky's extended frame model

class Frame:
    def __init__(self,V):
        self.type = self.__class__.__name__.lower()
        self.val  = V
        self.slot = {}
        self.nest = []

    ################################### dump

    def __repr__(self):
        return self.dump()
    def dump(self,depth=0,prefix=''):
        tree = self.pad(depth) + self.head(prefix)
        if not depth: Frame.dumped = []
        if self in Frame.dumped: return tree + ' _/'
        else: Frame.dumped.append(self)
        for i in self.slot:
            tree += self.slot[i].dump(depth+1, prefix = '%s = ' % i)
        idx = 0
        for j in self.nest:
            tree += j.dump(depth+1, prefix='%s = ' % idx) ; idx += 1
        return tree
    def head(self,prefix=''):
        return '%s<%s:%s> @%x' % (prefix,self.type,self._val(),id(self))
    def pad(self,depth):
        return '\n' + '\t' * depth
    def _val(self): return str(self.val)

    ############################## operators

    def __getitem__(self,key):
        return self.slot[key]
    def __setitem__(self,key,that):
        if callable(that): return self.__setitem__(key,Cmd(that))
        self.slot[key] = that ; return self
    def __lshift__(self,that):
        return self.__setitem__(that.type,that)
    def __rshift__(self,that):
        return self.__setitem__(that.val,that)
    def __floordiv__(self,that):
        self.nest.append(that) ; return self

    ############################## stack ops

    def pop(self): return self.nest.pop()
    def top(self): return self.nest[-1]


################################################################ primitive types

class Primitive(Frame):
    def eval(self,env): env // self

class Symbol(Primitive): pass
class String(Primitive): pass
class Number(Primitive): pass
class Integer(Number): pass
class Hex(Integer): pass
class Bin(Integer): pass


################################################ EDS: executable data structures

class Active(Frame): pass

class Cmd(Active):
    def __init__(self,F):
        Active.__init__(self,F.__name__)
        self.fn = F
    def eval(self,env):
        self.fn(env)

class VM(Active): pass

############################################################# global environment

vm = VM('metaL') ; vm << vm

########################################################################## debug

def BYE(env): sys.exit(0)

def Q(env): print(env)
vm['?'] = Q

def QQ(env): print(env) ; BYE(env)
vm['??'] = QQ

################################################################## manipulations

def PUSH(env): that = env.pop() ; env.top() // that
vm['//'] = PUSH

########################################################## PLY: no-syntax parser

import ply.lex as lex

tokens = ['symbol']

t_ignore         = ' \t\r\n'
t_ignore_comment = r'[\#\\].*'

def t_symbol(t):
    r'[`]|[^ \t\r\n\#\\]+'
    return Symbol(t.value)

def t_ANY_error(t): raise SyntaxError(t)

lexer = lex.lex()


#################################################################### interpreter

def WORD(env):
    token = lexer.token()
    if token: env // token
    return token
vm['`'] = WORD

def FIND(env):
    token = env.pop()
    try: env // env[token.val] ; return True
    except KeyError: env // token ; return False

def EVAL(env): env.pop().eval(env)

def INTERP(env):
    lexer.input(env.pop().val)
    while True:
        if not WORD(env): break
        if isinstance(env.top(),Symbol):
            if not FIND(env): raise SyntaxError(env.top())
        EVAL(env)
    print(env)

#################################################################### system init

if __name__ == '__main__':
    print(vm)
    for infile in sys.argv[1:]:
        with open(infile) as src:
            vm // String(src.read()) ; INTERP(vm)
