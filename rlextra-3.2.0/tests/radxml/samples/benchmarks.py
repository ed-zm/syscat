# benchmark



# MSXML:  This can be downloaded from many places.  You need 3.0
# which is NOT in most newly installed Windows boxes. (650kb)
# http://download.microsoft.com/download/xml/Install/3.0/WIN98Me/EN-US/msxml3.exe
#    for a quick tutorial on MSXML 3.0, see
# http://www.perfectxml.com/articles/xml/msxml30.asp

# you should then run the COM MakePY utility on the Pythonwin menu.
# to get it going as fast as possible.


## apparently time.clock is the fine grained one e.g.
##>>> time.clock() - time.clock()
##-1.1733331545471515e-005
##>>> time.time() - time.time()
##0.0
##>>> 
import sys
import glob
import time
from types import TupleType
from reportlab.lib.utils import getStringIO
    
def tupleTreeStats(node):
    # counts tags and attributes recursively
    # use for all reportlab parsers
    if node[1] is None:
        attrCount = 0
    else:
        attrCount = len(node[1])
    nodeCount = 1
    if node[2] is not None:
        for child in node[2]:
            if type(child) is TupleType:
                a, n = tupleTreeStats(child)
                attrCount = attrCount + a
                nodeCount = nodeCount + n
    return attrCount, nodeCount

###  pyRXP - our wrapper around Univ of Edinburgh

def getPyRXPParser():
    import pyRXP
    p = pyRXP.Parser()
    return p


def parseWithPyRXP(parser, rawdata):
    return parser.parse(rawdata)

###  rparsexml - Aaron's very fast pure python parser

def loadRparseXML():
    #it's a module, what the heck
    from reportlab.lib import rparsexml
    return rparsexml

def parseWithRParseXML(rparsexml, rawdata):
    #first argument is a dummy holding none
    return rparsexml.parsexml0(rawdata)[0] 

###  expattree - Andy's expat parser
def loadExpatTree():
    from rlextra.radxml.expattree import ExpatTreeParser
    return ExpatTreeParser

def parseWithExpatTree(ExpatTreeParser,text):
    P = ExpatTreeParser()
    return P.parseText(text)

####### minidom - non-validating DOM parser in the Python distro

def loadMiniDOM():
    import xml.dom.minidom
    return xml.dom.minidom

def parseWithMiniDOM(dom_module, rawdata):
    #parser is None
    return dom_module.parseString(rawdata)
    
def statsWithMiniDOM(node):
    return (1, 0)

#########  Microsoft XML Parser via COM ######################


def loadMSXML30():
    from win32com.client import Dispatch
    msx = Dispatch('Microsoft.XMLDOM')
    return msx

def parseWithMSXML30(msx, rawdata):
    msx.loadXML(rawdata)
    return msx

def statsWithMSXML30(node):
    #not done
    return (1,0)    

###########4DOM ###############
def load4DOM():
    from xml.dom.ext.reader import PyExpat
    from xml.dom import Node
    reader = PyExpat.Reader()
    return reader

def parseWith4DOM(reader, rawdata):
    return reader.fromString(rawdata)


def statsWith4DOM(node):
    #node
    return (1,0)

def loadCDomlette():
    from Ft.Lib import cDomlettec
    return cDomlettec

def parseWithCDomlette(modul, rawdata):
    io = getStringIO(rawdata)
    return modul.parse(io, '')

def statsWithCDomlette(node):
    #node
    return (1,0)

##########put them all together################

TESTMAP = [
    # name of parser; function to initialize if needed;
    # function to parse; function to do stats
    ('pyRXP', getPyRXPParser, parseWithPyRXP, tupleTreeStats),
    ('rparsexml', loadRparseXML, parseWithRParseXML, tupleTreeStats),
    ('expattree', loadExpatTree, parseWithExpatTree, tupleTreeStats),
    ('minidom', loadMiniDOM, parseWithMiniDOM, statsWithMiniDOM),
    ('msxml30', loadMSXML30, parseWithMSXML30, statsWithMSXML30),
    ('4dom', load4DOM, parseWith4DOM, statsWith4DOM),
    ('cdomlette', loadCDomlette, parseWithCDomlette, statsWithCDomlette)
    ]    

def runtest(sampleText,num,memPause):
    (name, loadFunc, parseFunc, statFunc) = TESTMAP[num-1]
    print('testing %s' % name)
    #load the parser
    t0 = time.clock()
    try:
        parser = loadFunc()
    except:
        print('!!!!!Load Failed')
        return
    loadTime = time.clock() - t0
    
    if memPause: baseMem = float(input("Please input process base memory in kb >"))
    t1 = time.clock()
    parsedOutput = parseFunc(parser, sampleText)
    t2 = time.clock()
    parseTime = t2 - t1
    
    if memPause:
        totalMem = float(input('Please enter memory allocation in kb >'))
        usedMem = totalMem - baseMem
        memFactor = usedMem * 1024.0 / len(sampleText)
    t3 = time.clock()
    n, a = statFunc(parsedOutput)
    t4 = time.clock()
    traverseTime = t4 - t3
    print('%d tags, %d attributes' % (n, a))
    if memPause:
        print('%s: init %0.4f, parse %0.4f, traverse %0.4f, mem used %dkb, mem factor %0.2f' % (
            name, loadTime, parseTime, traverseTime, usedMem, memFactor))
    else:
        print('%s: init %0.4f, parse %0.4f, traverse %0.4f' % (
            name, loadTime, parseTime, traverseTime))
    print()

def interact():
    print("""
    Interactive benchmark suite for Python XML parsers.
    Parsers available:
    """)
    auto = '--auto' in sys.argv
    if auto: sys.argv.remove('--auto')
    try:
        sample = sys.argv[1]
    except:
        sample = 'rml_a.xml'

    sampleText = open(sample).read()
    i = 1
    for (name, a, b, c) in TESTMAP:
        print('\t%d.  %s' % (i, name))
        i = i + 1
    if not auto:
        print()
        inp = input("Shall we do memory tests?  i.e. I pause while you look at Task Manager? y/n  ")
        assert inp in 'yn', 'enter "y" or "n".  Please run again!'
        pause = (inp == 'y')
        inp = input('Test number (or x to exit)>')
        if inp == 'x':
            print('bye')
            return
        else:
            runtest(sampleText,int(inp),pause)
    else:
        for num in range(1,len(TESTMAP)+1):
            runtest(sampleText,num,0)

if __name__=='__main__':
    interact()
