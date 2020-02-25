
import os,sys

def comment(text,width=80):
    pfx = '#' * (width - len(text) - 1)
    print(pfx + ' ' + text) ; sys.exit(-1)
# comment('Web interface')#,40)


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
    def dot(self): self.nest = [] ; return self

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

def DOT(env): env.dot()
vm['.'] = DOT

############################################################################ I/O

class IO(Frame): pass
class Dir(IO): pass
class File(IO): pass

######################################################################## Network

class Net(IO): pass
class Socket(Net): pass
class IP(Net): pass
class Port(Net): pass

########################################################## PLY: no-syntax parser

import ply.lex as lex

tokens = ['symbol','string','number','integer','hex','bin']

t_ignore         = ' \t\r\n'
t_ignore_comment = r'[\#\\].*'

def t_exp(t):
    r'[+\-]?[0-9]+(\.[0-9]*)?[eE][+\-]?[0-9]+'
    return Number(t.value)
def t_number(t):
    r'[+\-]?[0-9]+\.[0-9]*'
    return Number(t.value)

def t_hex(t):
    r'0x[0-9A-Fa-f]+'
    return Hex(t.value)
def t_bin(t):
    r'0b[01]+'
    return Bin(t.value)
def t_integer(t):
    r'[+\-]?[0-9]+'
    return Integer(t.value)

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


################################################################## Web interface

class Web(Net): pass
class Color(Web): pass
class Size(Web): pass
class Font(Web):
    def __init__(self,family,size):
        Web.__init__(self,family)
        self['size'] = Size(size)

############################################################################ GUI

from PyQt5.QtWidgets import QApplication,QWidget,QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QBasicTimer

class GUI(Frame): pass

class Desktop(GUI):
    def eval(self,env):
        self.app = QApplication([])
        self // Window(env.head()).eval(env)
        self.app.exec()

class Window(GUI,QWidget):
    def __init__(self,V):
        GUI.__init__(self,V)
        QWidget.__init__(self)
        self['back'] = Color('#080810')
        self << Color('lightgreen')
        self << Font('monospace',12)
        self.setStyleSheet('background-color: %s; color: %s;' % (self['back'].val,self['color'].val))
    def eval(self,env):
        self.setWindowTitle(self.val) ; self.show()
        self // Label('Hello World',self,env).eval(env)
        return self

class Label(GUI,QLabel):
    def __init__(self,V,parent,monitor=None):
        GUI.__init__(self,V)
        QLabel.__init__(self,parent)
        self.setFont(QFont(parent['font'].val,parent['font']['size'].val))
        self.setStyleSheet('color: %s;' % parent['color'].val)
        self.monitor = monitor
        if self.monitor: self.timer = QBasicTimer()
    count = 0
    def timerEvent(self,e): self.eval(self)
    def eval(self,env):
        if self.monitor:
            self.setText('%s\n%s' % (Label.count,self.monitor.dump())) ; Label.count += 1
            self.timer.start(1111,self)
        else:
            self.setText(self.val)
        self.show() ; return self

vm['GUI'] = Desktop('Qt')

#################################################################### system init

if __name__ == '__main__':
    print(vm)
    for infile in sys.argv[1:]:
        with open(infile) as src:
            vm // String(src.read()) ; INTERP(vm)
