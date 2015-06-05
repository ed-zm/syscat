#copyright ReportLab Inc. 2000-2012(text,text)
#see license.txt for license details
__version__="$Id$"
import reportlab, os, sys, time, re, base64, zlib, bz2, traceback
import collections
__URL__="$URL$"
import logging
import io
logger = logging.getLogger("reportlab.rml2pdf")

version="1.0"
compatible_versions = ["0.2", "0.3", "1.0"]

from reportlab.lib.utils import recursiveImport, recursiveSetAttr, recursiveGetAttr, getStringIO, open_and_read, \
                                flatten, zipImported, ascii_letters, asUnicode, getBytesIO, \
                                strTypes, rl_exec, isPy3, asUnicodeEx, asBytes, md5, isUnicode, \
                                rawBytes, annotateException
from reportlab.lib.rl_accel import asciiBase85Decode, asciiBase85Encode
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.platypus.flowables import Flowable, Image, Macro, PageBreak, SlowPageBreak, Preformatted, Spacer, XBox, \
                            CondPageBreak, KeepTogether, TraceInfo, FailOnWrap, FailOnDraw, HRFlowable, \
                            PTOContainer, KeepInFrame, KeepTogether, ImageAndFlowables, \
                            DocIf, DocWhile, DocAssign, DocExec, DocAssert, DocPara, \
                            ListFlowable, ListItem, DDIndenter, \
                            TopPadder, PageBreakIfNotEmpty
from reportlab.platypus.figures import FlexFigure
from reportlab.platypus.paragraph import Paragraph, cleanBlockQuotedText, ParaLines, textTransformFrags
from reportlab.platypus.paraparser import ParaFrag
from reportlab.platypus.tables import Table, TableStyle, CellStyle
from reportlab.platypus.frames import Frame
from reportlab.platypus import FrameBG
from reportlab.platypus.doctemplate import BaseDocTemplate, NextPageTemplate, PageTemplate, ActionFlowable, \
                         SimpleDocTemplate, FrameBreak, PageBegin, NextFrameFlowable, NotAtTopPageBreak
from reportlab.platypus.xpreformatted import XPreformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, PropertySet, ListStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.abag import ABag
from reportlab.pdfbase import pdfdoc, pdfutils
from reportlab.rl_config import defaultPageSize, defaultImageCaching, verbose
from reportlab.lib.colors import white, black, toColor, Color, CMYKColor, CMYKColorSep, _chooseEnforceColorSpace, PCMYKColor
from reportlab.lib import colors
from reportlab.lib import sequencer
from rlextra.pageCatcher.pageflow import includePdfFlowables, OutlineEntry

from rlextra.utils.ubold import W
ASV = W.ASV
del W

_zipimporter = zipImported()

# hack to support both kinds of x objects we have defined
if not hasattr(pdfdoc,'xObjectName'): pdfdoc.xObjectName = pdfdoc.formName

def _rml2pdf_locations(D=None):
    if not D: D = []
    elif type(D) not in (type(()),type([])): D = [D]
    from rlextra import rml2pdf
    p = rml2pdf.__file__
    D.append(os.path.dirname(p))
    pyver = '%spython%s.zip%s' % (os.sep,''.join(sys.version.split()[0].split('.'))[:2],os.sep)
    i = p.lower().find(pyver)
    if i>0: D += [p[:i], os.path.join(p[:i],p[i+len(pyver):])]
    return D

class _FS_Checker:
    def __init__(self,dir):
        self._dir = dir

    def __call__(self,target):
        fn = os.path.abspath(os.path.join(self._dir,target))
        if os.path.isfile(fn):
            if sys.platform=='win32':
                return 'file:///'+fn.replace('\\','/')
            else:
                return 'file://'+fn
        return None

class _ZIP_Checker:
    def __init__(self,dir):
        self._dir = dir

    def __call__(self,target):
        try:
            return target, _zipimporter.get_data(os.path.join(self._dir,target))
        except:
            return None

def _rml_dtd_dirs(exe=None):
    D = []
    for d in _rml2pdf_locations():
        c = _zipimporter and d.startswith(_zipimporter.archive) and _ZIP_Checker or _FS_Checker
        D.append(c(d))

    if exe:
        cwd = os.path.abspath(".")
        for i in 1,0:
            try:
                d = os.path.dirname(sys.argv[i])
                if not os.path.isabs(d): d=os.path.join(cwd,d)
                D.append(_FS_Checker(d))
            except:
                pass
    return D

class CanvasParameters:
    "container for canvas parameter storage (trivial at the moment)"
    pageSize = defaultPageSize
    imageCaching = defaultImageCaching

class DeferredInitialization:
    """used to delay initialization of flowables (for example paragraphs in a frame)
       until bind time, so the names get bound correctly, for example"""
    def __init__(self, klass, *args, **kw):
        self.klass = klass
        self.args = args
        self.kw = kw

    def initialize(self):
        return self.klass(*self.args, **self.kw)

    def wrap(self, *args):
        raise ValueError("initialization deferred for %s %s %s %s" %(id(self), self.klass, list(map(asUnicodeEx, self.args)), self.kw))

class RMLError(ValueError):
    pass

### first some lazy object trickery
### (to allow, eg, pageNumbers)

# XXXX even this will not give the right page number for a split paragraph!
# XXXX really need to use the xml tree uniformly!

### maybe these should go in another (or other) module(s)

### probably should also add lazy Table
class LazyStringForm:
    def __init__(self):
        raise ValueError("virtual superclass")

class LazySetItem(LazyStringForm):
    """set the value when converted to a string!"""
    def __init__(self, dict, item, value):
        self.dict = dict
        self.item = item
        self.value = value
    def __str__(self):
        self.dict[self.item] = asUnicodeEx(self.value)
        return ""

class LazyGetItem(LazyStringForm):
    def __init__(self, context, item, default=None):
        self.context = context
        self.item = item
        self.default = default
    def __str__(self):
        if self.default is not None:
            result = self.context.get(self.item, self.default)
        else:
            result = self.context[self.item]
        return asUnicodeEx(result)

### expediency: table wrap seems to be buggy in the x dimension!

class xTable(Table):
    # pretend the table has 0 width!
    def wrap(self, aw, ah):
        (x,y) = Table.wrap(self, aw,ah)
        return (1,y)

# comment to fix
xTable = Table

class LazyJoin(LazyStringForm):
    def __init__(self, seq, sep=''):
        self.seq = seq; self.sep = sep
    def __str__(self):
        return asUnicodeEx(self.sep).join(map(asUnicodeEx, self.seq)) # late string conversion

class LazyAttribute(LazyStringForm):
    def __init__(self, thing, attribute):
        self.thing = thing
        self.attribute = attribute
    def __str__(self):
        val = getattr(self.thing, self.attribute)
        return asUnicodeEx(val)

class LazySubst(LazyStringForm):
    def __init__(self, format, data):
        self.format = format; self.data = data
    def __str__(self):
        return self.format % self.data

### other utilities
def readBool(text,context=None):
    if text.upper() in ("Y", "YES", "TRUE", "1", "TRUE"):
        return 1
    elif text.upper() in ("N", "NO", "FALSE", "0", "FALSE"):
        return 0
    else:
        raise RMLError("true/false attribute has illegal value '%s'" % text)

def readBoolOrNone(text, context=None):
    if text.strip().lower()=='none': return None
    return readBool(text,context=context)

def readAlignment(text,context=None):
    up = text.upper()
    if up == 'LEFT':
        return TA_LEFT
    elif up == 'RIGHT':
        return TA_RIGHT
    elif up in ['CENTER', 'CENTRE']:
        return TA_CENTER
    elif up == 'JUSTIFY':
        return TA_JUSTIFY

def readBorder(text,context=None):
    text = text.strip()
    if text.startswith('border'):
        data = text.replace('border','',1)
        data = data.strip()
        try:
            if not (data.startswith('(') and data.endswith(')')): raise ValueError
            kw = eval('_kw(%s)' % data[1:-1])   #try assuming keyword args
            for k,v in kw.items():
                if k not in ('color','width','dashArray'):
                    del kw[k]
                elif isinstance(v,strTypes):
                    if k=='color':
                        kw['color'] = readColor(v,context=context)
                    elif k=='width':
                        kw['width'] = readLength(v,context=context)
                    elif k=='dashArray':
                        kw['dashArray'] = lengthSequence(sdict["dash"])

            return ABag(**kw) if kw else False
        except:
            raise ValueError('bad border attribute %r' % text)
    else:
        return readBool(text,context)

lengthMatcher=re.compile(r'\s*([-+]?(?:\d+(?:\.\d*)?|\d*\.\d+)(?:[eE][-+]?\d+)?)\s*(\S*)')
def readLength(text, percentTotal = None, context=None):
    """
    Read a dimension measurement: accept "3in", "5cm", "72 pt" and so on.

    If percentTotal is specified then percentages can also be specified
    (e.g. "5%") and function will return number/100 * percentTotal
    or if percentTotal is specified as '%' we get back the original string.
    """
    if context: text = context.lengths.get(text,text)

    match = lengthMatcher.match(text)
    if not match:
        if text.strip()=='*' and percentTotal=='%': return text
        raise ValueError("invalid length attribute '%s'" % text)
    number = float(match.group(1))
    units = match.group(2).lower()
    if not units:
        units = 'pt'
    if units == '%':
        if percentTotal is None:
            raise ValueError("invalid length attribute '%s' - percent not allowed here" % text)
        elif percentTotal=='%':
            return text
        multiplier = percentTotal / 100.0
    else:
        try:
            multiplier = {
                'in': 72,
                'cm': 28.3464566929,  #72/2.54; is this accurate?
                'mm': 2.83464566929,
                'pt': 1
            }[units]
        except KeyError:
            raise RMLError("invalid length attribute '%s'" % text)
    return number * multiplier

def readLengths(text, percentTotal = None, context=None):
    if '|' in text:
        return [readLength(x,percentTotal,context) for x in text.split('|')]
    return readLength(text,percentTotal,context)

def readLengthOrNone(text, percentTotal = None, context=None):
    if text.strip().lower()=='none': return None
    return readLength(text,percentTotal,context)

def readFloatOrNone(text, percentTotal = None, context=None):
    if text.strip().lower()=='none': return None
    return float(text)

def lengthSequence(s, converter=readLength):
    """from "(2, 1)" or "2,1" return [2,1], for example"""
    s = s.strip()
    if s.startswith("(") and s.endswith(")"): s = s[1:-1]
    return [converter(l.strip()) for l in s.split(",")]

def readGapSequence(s, converter=readLength, context=None):
    """Read a number of index/length pairs.  Used by letterboxes.
    e.g. to add 0.1cm space after 2nd and 4th boxes, use
    '2:0.1cm, 4:0.1cm'
    """
    gaps = []
    chunks = s.split(',')
    for chunk in chunks:
        #chunk is like 3:0.1cm or 5:6  - index, length
        strOffset, strLength = chunk.split(':')
        offset = int(strOffset)
        length = converter(strLength, context=context)
        gaps.append((offset, length))
    return gaps

def _readColor(text,context=None):
    """Read color names or tuples, RGB or CMYK, and return a Color object."""
    if not text or text in ('none','None'): return None
    if text[0] in ascii_letters:
        return toColor(text.strip())
    tup = lengthSequence(text)

    msg = "Color tuple must have 3 (or 4) elements for RGB (or CMYK)."
    assert 3 <= len(tup) <= 4, msg
    msg = "Color tuple must have all elements <= 1.0."
    for i in range(len(tup)):
        assert tup[i] <= 1.0, msg

    if len(tup) == 3:
        colClass = colors.Color
    elif len(tup) == 4:
        colClass = colors.CMYKColor
    return colClass(*tup)

def readColor(colorName,context):
    if colorName.startswith('rml:'):
        colorName = context.get(colorName[4:].strip(),'')
    try:
        return toColor(colorName)
    except ValueError:
        try:
            return _readColor(colorName)
        except:
            return toColor(colorName)

def readMask(mask,context):
    mask = mask.strip()
    if mask.lower()!='auto':
        mask = readColor(mask,context)
    return mask

def readColorSequence(colorNames,context):
    """Accepts a semicolon-separated string of colors
    with optional None values e.g.
    aqua;lemonchiffon;None
    """
    stuff = colorNames.split(';')
    output = []
    for item in stuff:
        if item.lower() in ('none','0'):
            output.append(None)
        else:
            output.append(readColor(item, context))
    return output

def readAlign(s,context=None):
    s=s.lower()
    if s in ('center','centre','left','right','decimal'): return s
    raise ValueError('Illegal align attribute "%s"' % s)

def readAlignU(s,context=None): return readAlign(s,context=context).upper()
def readAlignL(s,context=None): return readAlign(s,context=context).lower()

def readvAlign(s,context=None):
    s=s.lower()
    if s in ('top','middle','bottom'): return s
    raise ValueError('Illegal vAlign attribute "%s"' % s)

def readvAlignU(s,context=None): return readvAlign(s).upper()

def readString(s,context=None): return s #identity
def readInt(s,context=None): return int(s)
def readFloat(s,context=None): return float(s)
def readIntOrString(s,context=None):
    try:
        return readInt(s,context)
    except:
        return readString(s,context)
def readIntDefault(s,context=None):
    x = readIntOrString(s,context)
    if x=='default': x = None
    return x

# the default aliases
DEFAULT_ALIASES = {
    "h1.defaultStyle": "style.Heading1",
    "h2.defaultStyle": "style.Heading2",
    "h3.defaultStyle": "style.Heading3",
    "h4.defaultStyle": "style.Heading4",
    "h5.defaultStyle": "style.Heading5",
    "h6.defaultStyle": "style.Heading6",
    "title.defaultStyle": "style.Title",
    "para.defaultStyle": "style.Normal",
    "pre.defaultStyle": "style.Code",
    "li.defaultStyle": "style.Definition"
    }

styles = getSampleStyleSheet()

class NamesArchive:
    "like a dictionary, but keeps record of defaults and updates to remember when to do a multipass build"
    # None is a forbidden value
    def __init__(self, maxResets=None):
        self.archive = {}
        self.maxResets = maxResets
        self.resetCount = -1 # for bootstrapping only
        self.touched = 1 # for bootstrapping only
        self.reset(0)
    def reset(self, abortOnNoProgress=1):
        if not self.touched and abortOnNoProgress:
            raise ValueError("no progress in resolving %s\n (count=%s)" % (repr(list(self.defaultEncountered.keys())), self.resetCount))
        self.touched = {}
        x = self.resetCount = self.resetCount+1
        if self.maxResets is not None and self.maxResets<=x:
            raise ValueError("too many resets %s resolving %s" % (x, repr(list(self.defaultEncountered.keys()))))
        self.defaultEncountered = {}
    def complete(self):
        if self.defaultEncountered:
            return 0
        else:
            return 1
    def __setitem__(self, key, value):
        if value is None:
            raise ValueError("None is forbidden for names archive setitem")
        a = self.archive
        if key not in a:
            self.touched[key] = value
        a[key] = value
    def get(self, key, default=None):
        a = self.archive
        if key in a:
            return a[key]
        else:
            self.defaultEncountered[key] = default
            return default
    def __getitem__(self, key):
        test = self.get(key)
        if test is None:
            raise KeyError("no entry  for %s" % repr(key))
        return test

class RMLContext:
    """Allow for aliases and redirection of aliases
    should colors be treated specially (like now)?
    eventually this should grow to include shadowing, etc..."""

    filename = None # should be set
    doc = None # the document being constructed...

    def __init__(self, namesarchive=None, permitEvaluations=1):
        self.permitEvaluations = permitEvaluations
        if namesarchive is None:
            namesarchive = NamesArchive()
        self.imageFileMap = {}
        self.pageDrawings = []
        self.canvasInfo = CanvasParameters()
        self.initialize = []
        self.document = None
        self.story = []
        self.firstPageTemplateName = None   #set this to select the first one
        self.compression = None
        self.invariant = None
        self.debug = None
        self.enforceColorSpace = None
        self.author = None
        self.title = None
        self.subject = None
        self.creator = None
        self.keywords = None
        self.lang = None
        self.displayDocTitle = None
        namedColors = reportlab.lib.colors.getAllNamedColors()
        self.colors = namedColors.copy() # for paranoia purposes...
        toColor.setExtraColorsNameSpace(self.colors)
        self.lengths = {}
        names = self.names = namesarchive # formerly {}
        for n in list(styles.byName.keys()):
            s = styles[n]
            names["style."+n] = s
            # change this?
            names[n] = s
        for n in list(styles.byAlias.keys()):
            s = styles[n]
            names["style." +n] = s
            names[n] = s
        self.aliases = {}
        # an example default (ultimatel
        #self.aliases["h1.defaultStyle"] = "style.Heading1"
        for k in list(DEFAULT_ALIASES.keys()):
            self.alias(k, DEFAULT_ALIASES[k])
    def destroy(self):
        "this should (I hope!) break all possible cycles leading from the context"
        d = self.__dict__
        for k in list(d.keys()):
            del d[k]
    def prepare(self):
        # execute delayed actions stored in initialize
        i = self.initialize
        self.initialize = []
        L = []
        for c in i:
            # converting to string will set off delayed actions
            L.append(asUnicodeEx(c))
    def __setitem__(self, item, value):
        if value is None:
            raise ValueError("None is forbidden for context setitem")
        self.names[item] = value
    def alias(self, alias, name):
        self.aliases[alias] = name
    def get(self, item, default=None):
        visited = {}
        aliases = self.aliases
        names = self.names
        item1 = item
        while 1:
            if item1 in visited:
                raise ValueError("infinite alias loop %s" % repr((item, item1)))
            visited[item1] = 1
            # always prefer an alias... (?)
            if item1 not in aliases:
                test = names.get(item1, default)
                if test is None:
                    raise KeyError("%s not found in context" % repr(item1))
                return test
            else:
                item1 = aliases[item1]
    def __getitem__(self, item):
        return self.get(item)

    def checkColor(self, stuff):
        "Wraps toColor but can check it's valid for colorSpace"
        if self.enforceColorSpace: #the default, anything goes
            c = self.enforceColorSpace(stuff)
        else:
            c = toColor(stuff)
        return c

def joinflatten(e):
    if isinstance(e,strTypes):
        return e
    if isinstance(e,(list,tuple)):
        stre = list(map(joinflatten, e))
        return LazyJoin(stre)
    return e # str conversion handled late by LazyJoin

class MapController:
    """Top level controller"""

    def __init__(self):
        self.nodemappers = {None: None} # default

    def __setitem__(self, item, value):
        self.nodemappers[item] = value

    def __getitem__(self, item):
        return self.nodemappers[item]

    def process(self, elts, context):
        """process preparsed xml text"""
        # the real result of the process are the side effects to context
        elts = self.clean_elts(elts)
        return joinflatten(self.processContent(elts, context, top_level=1))

    def processContent(self, elts, context, overrides=None, top_level=0):
        if overrides is None:
            overrides = {} # no overrides yet
        if isinstance(elts,strTypes):
            return self.processString(elts, context)
        if isinstance(elts,tuple):
            return self.processTuple(elts, context, overrides)
        else:
            L = []
            for e in elts:
                if isinstance(e,strTypes):
                    e2 = self.processString(e, context)
                else:
                    if not isinstance(e,tuple):
                        raise ValueError("bad content type %s" % type(e))
                    e2 = self.processTuple(e, context, overrides)
                L.append(e2)
            return L

    def processTuple(self, e, context, overrides):
        tagname = e[0]
        nodemappers = self.nodemappers
        if overrides:
            nodemappers = nodemappers.copy()
            # do overrides
            nodemappers.update(overrides)
        defaultmapper = nodemappers.get(None, None)
        processor = nodemappers.get(tagname, defaultmapper)
        if processor is None:
            raise NameError("no processor for %s" % repr(tagname))
        e2 = processor.translate(e, self, context, overrides)
        return e2
##
##    def joinTranslatedContent(self, L):
##        strL = map(str, L)
##        return ("".join(strL), L)

    def processString(self, elts, context):
        return elts # default, for now

    def clean_elts(self, elts):
        """optionally do stuff like dispose of all white content"""
        return elts

# the one and only controller
Controller = MapController()

class MapNode(MapController):

    def __init__(self, defaults=None, **kw):
        self.nodemappers = {}
        if defaults is None:
            defaults = {}
        self.defaults = defaults
        # transforms to apply per attribute to the content (eg make it have 2 digits and put a dollar in front)...
        self.transforms = {}
        self.init1(**kw) # for localization in subclasses

    def __str__(self):
        raise ValueError("%s instance has no string conversion method" % self.__class__)

    def init1(self, **kw):
        pass # only for use in subclasses

    def addTransform(self, name, t):
        self.transforms[name] = t
##
##    def transformContent(self, t):
##        self.transforms["__content__"] = t

    def translate(self, nodetuple, controller, context, overrides):
        # add own overrides if present
        # "translate", self
        if self.nodemappers:
            overrides = overrides.copy()
            overrides.update(self.nodemappers)
        (tagname, attdict, content, extra) = nodetuple
        #tagname = nodedict[0]
        #content = nodedict.get(1, None)
        if not attdict: attdict = {}
        sdict = attdict.copy() # for modification
        defaults = self.defaults
        for name in list(defaults.keys()):
            if name not in sdict:
                sdict[name] = defaults[name]
        pcontent = None
        if content is not None:
            pcontent = self.MyProcessContent(content, controller, context, overrides)
            #sdict["__content__"] = pcontent
        transforms = self.transforms
        for name in list(transforms.keys()):
            if name in sdict:
                t = transforms[name]
                sdict[name] = t(sdict[name])
        result = self.evaluate(tagname, sdict, pcontent, extra, context)
        return result

    def evaluate(self, tagname, sdict, pcontent, extra, context):
        """after all defaults and transformations, evaluate the tag.
        Maybe modify the content. return something to use higher up..."""
        # this superclass is a "pass thru", just returns the tag itself (with substitutions,etc)
        # no side effects to the context
        if tagname=="":
            return pcontent # top level
        L = ["<"+tagname]
        keys = list(sdict.keys())
        keys.sort()
        for k in keys:
            v = sdict[k] # XXXX maybe need to "escape" v???
            ss = LazySubst(' %s="%s"', (k, v))
            L.append(ss)
        if pcontent is not None:
            pcontent = joinflatten(pcontent)
            ss = LazySubst(">%s</%s>", (pcontent, tagname))
            L.append(ss)
        else:
            L.append("/>")
        return LazyJoin(L)

    def MyProcessContent(self, content, controller, context, overrides):
        """by default ask the global controller to do it"""
        return controller.processContent(content, context, overrides)

class NoWhiteContentMixin:
    def MyProcessContent(self, content, controller, context, overrides):
        """erase whitespace, then, ask the global controller to do it"""
        newcontent = []
        for c in content:
            if isinstance(c,strTypes) and not c.strip():
                pass # erase it
            else:
                newcontent.append(c)
        return controller.processContent(newcontent, context, overrides)

# the "top level" mapper (doesn't itself do anything)
Controller[""] = MapNode()

def _scanList(L,func,i=0):
    try:
        while not func(L[i]): i+=1
        return i
    except IndexError:
        return -1
### map nodes for each element
### should define init1 and evaluate where appropriate

class document(MapNode):

    def evaluate(self, tagname, sdict, pcontent, extra, context):
        # context
        context.filename = sdict["filename"]
        context.compression = readIntDefault(sdict.get("compression", 'default'))
        context.invariant = readIntDefault(sdict.get("invariant", 'default'))
        context.debug = readInt(sdict.get("debug", '0'))  #None means unknown

        # we do NOT parse the colorSpace attribute, because it was needed
        #long ago; document is the last thing parsed, being at the top of the tree.
        #It gets parsed and set where the RMLContext is created.
        return MapNode.evaluate(self, tagname, sdict, pcontent, extra, context)

    def translate(self, nodetuple, controller, context, overrides):
        #*HACK* ensure template,stylesheet,story --> stylesheet, template, story
        content = nodetuple[2]
        t = _scanList(content,lambda x: isinstance(x,tuple) and x[0]=='template')
        if t>=0:
            s = _scanList(content,lambda x: isinstance(x,tuple) and x[0]=='stylesheet',t+1)
            if s>=0:
                tmp = content[t]
                content[t] = content[s]
                content[s] = tmp
                del tmp, s, t, content
        return MapNode.translate(self,nodetuple, controller, context, overrides)
Controller["document"] = document()

class PassThru(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return "".join(pcontent)
Controller['<![CDATA['] = PassThru()

def flattenDeferred(pcontent):
    for c in flatten(pcontent):
        if isinstance(c,DeferredInitialization):
            c = c.initialize()
            if isinstance(c,(tuple,list)):
                for x in flattenDeferred(c):
                    yield x
            else:
                yield c
        else:
            yield c

#TOPLEVELCLASSES = (LazyParagraph, Table, xTable, Spacer, CondPageBreak, LazyPreformatted,
#                   NextPageTemplate, PageBreak, SlowPageBreak, ActionFlowable, IllustrationFlowable,
#                  LazyPlugInFlowable, OutlineEntry, FrameBreak.__class__, NextFrameFlowable,
#                  PTOContainer,KeepInFrame,FlowblesAndImage)
def _story_evaluate(tagname, sdict, pcontent, extra, context):
    story = context.story
    story_append = story.append
    for x in flattenDeferred(pcontent):
        if x is None or isinstance(x,strTypes):
            if x: raise ValueError("string %s in story content" % repr(x[min(100,len(x)):]))
        else:
            story_append(x)

    #remove unwanted nextPage.  We have to test if there's a story, because otherwise
    #the 'storylet' in empty td tags will barf.
    if len(story):
        while 1:
            f = story[0]
            if isinstance(f,(PageBreak,SlowPageBreak,CondPageBreak)) and getattr(f,'_suppressFirst',0):
                del story[0]
            else:
                break

class _LContext:
    def __init__(self):
        self.story = []

def get_local_story(tagname, sdict, pcontent, extra):
    lcontext = _LContext()
    _story_evaluate(tagname, sdict, pcontent, extra, lcontext)
    return lcontext.story

class story(NoWhiteContentMixin, MapNode):
    def evaluate(self,tagname, sdict, pcontent, extra, context):

        #we offer a "last chance" to specify the first template
        #when the story begins; this is much more natural than
        #having to specify before all the templates are defined.
        pt = sdict.get("firstPageTemplate",None)
        T = context.doc
        if pt:
            T.handle_nextPageTemplate(pt)
            T._firstPageTemplateIndex = T._nextPageTemplateIndex
            del T._nextPageTemplateIndex

        #now evaluate the story
        _story_evaluate(tagname, sdict, pcontent, extra, context)
Controller["story"] = story()

class setNextTemplate(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        name = sdict["name"]
        #they can pass in multiple sequences e.g. "left,right"
        templateNames = name.split(',')
        if len(templateNames) == 1:
            template = templateNames[0]
        else:
            template = templateNames #pass the list
        return NextPageTemplate(template)
Controller["setNextTemplate"] = setNextTemplate()

class switchTemplate(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        name = sdict["name"].strip()
        #they can pass in multiple sequences e.g. "left,right"
        if name:
            name = list(filter(None,(v.strip() for v in name.split(','))))
            if len(name)==1:
                name = name[0]
        else:
            raise ValueError('Illegal name attribute value for switchTemplate')
        return DocIf(
                "not doc._samePT(%s)" % repr(name),
                (NextPageTemplate(name),PageBreak()),
                )
Controller["switchTemplate"] = switchTemplate()

class nextFrame(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        name = sdict.get('name',None)
        if name:
            return [NextFrameFlowable(readIntOrString(name,context)),FrameBreak]
        return FrameBreak
Controller["nextFrame"] = nextFrame()

class setNextFrame(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return NextFrameFlowable(readIntOrString(sdict["name"],context))
Controller["setNextFrame"] = setNextFrame()

class nextPage(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        name = sdict.get('name',None)
        if name:
            name = list(filter(None,(v.strip() for v in name.split(','))))
            if len(name)==1:
                name = name[0]
        p = (readBool(sdict.get("slow",'0')) and SlowPageBreak or PageBreak)(nextTemplate=name)
        p._suppressFirst = readBool(sdict.get("suppressFirst",'0'))
        return p
Controller["nextPage"] = nextPage()

class nextPageIfNotEmpty(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        name = sdict.get('name',None)
        if name:
            name = list(filter(None,(v.strip() for v in name.split(','))))
            if len(name)==1:
                name = name[0]
        p = PageBreakIfNotEmpty(nextTemplate=name)
        p._suppressFirst = readBool(sdict.get("suppressFirst",'0'))
        return p
Controller["nextPageIfNotEmpty"] = nextPageIfNotEmpty()

class frameBackground(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        start = readBool(sdict.get("start",'0'))
        if start:
            left = readLengthOrNone(sdict.get("left",'0'),context)
            right = readLengthOrNone(sdict.get("right",'0'),context)
            color = readColor(sdict.get('color','white'),context)
        else:
            left = right = color = None
        return FrameBG(color=color,left=left,right=right,start=start)
Controller["frameBackground"] = frameBackground()

class initialize(NoWhiteContentMixin, MapNode):
    "initialize names (eg, for headers and footers)"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        # save delayed actions
        context.initialize = pcontent
        return "" # vanish
Controller["initialize"] = initialize()

class docinit(NoWhiteContentMixin, MapNode):
    """initialize anything - security, font setup etc.  Container for other tags"""
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        # save delayed actions
        context.canvasInfo.pageLayout = sdict.get('pageLayout',None)
        context.canvasInfo.pageMode = sdict.get('pageMode','UseNone')
        context.canvasInfo.useCropMarks = readBool(sdict.get("useCropMarks", '0'),context)
        context.docinit = pcontent
        return "" # vanish
Controller["docinit"] = docinit()

class alias(MapNode):
    "name a thing, for now just strings"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        id = sdict["id"]
        value = sdict["value"]
        context.alias(id, value)
        return "" # vanish
Controller["alias"] = alias()

class registerType1Face(MapNode):
    "name a thing, for now just strings"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        # if some glyphs are missing, suppress warnings
        import reportlab.rl_config
        reportlab.rl_config.warnOnMissingFontGlyphs = 0
        afmFile = sdict["afmFile"]
        pfbFile = sdict["pfbFile"]
        from reportlab.pdfbase import pdfmetrics
        theface = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(theface)
        return "" # vanish
Controller["registerType1Face"] = registerType1Face()

class registerFont(MapNode):
    "register an ordinary Type 1 Font"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        name = sdict["name"]
        faceName = sdict["faceName"]
        encName = sdict.get("encName", "utf8")  #AR 10 feb 2006 - not used yet but seems sensible
        from reportlab.pdfbase import pdfmetrics
        thefont = pdfmetrics.Font(name, faceName, encName)
        pdfmetrics.registerFont(thefont)
        return "" # vanish
Controller["registerFont"] = registerFont()

class registerCidFont(MapNode):
    "Register a CID (Asian) font"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        from reportlab.pdfbase.pdfmetrics import registerFont
        from reportlab.pdfbase.cidfonts import CIDFont, UnicodeCIDFont
        faceName = sdict["faceName"]
        encName = sdict.get("encName", None)
        if encName:
            registerFont(CIDFont(faceName, encName))
        else:  #assume utf8/unicode
            registerFont(UnicodeCIDFont(faceName))

        return ""
Controller["registerCidFont"] = registerCidFont()

class registerTTFont(MapNode):
    "Register a TTF font"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        faceName = sdict["faceName"]
        fileName = sdict["fileName"]
        from reportlab.pdfbase.pdfmetrics import registerFont
        from reportlab.pdfbase.ttfonts import TTFont
        registerFont(TTFont(faceName, fileName))
        return ""
Controller["registerTTFont"] = registerTTFont()

class registerFontFamily(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        normal = sdict["normal"].strip()
        if not normal:
            raise ValueError("registerFontFamily tag normal attribute must be non-empty")
        bold = sdict.get("bold","").strip()
        italic = sdict.get("italic","").strip()
        boldItalic = sdict.get("boldItalic","").strip()
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        registerFontFamily(normal,normal,bold,italic,boldItalic)
        return "" # vanish
Controller["registerFontFamily"] = registerFontFamily()

class getName(MapNode):
    "name a thing, for now just strings"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        id = sdict["id"]
        if "default" in sdict:
            default = sdict["default"]
        else:
            default = None
        #val = context[id]
        ### note: this may occur in a HEADER/FOOTER
        ### and the value may change every time!!!
        ### so it's done lazily!
        return LazyGetItem(context,id,default)
Controller["getName"] = getName()

class color(MapNode):
    """define a color in the context"""
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        i = sdict["id"]
        RGB = sdict.get("RGB", None)
        CMYK = sdict.get("CMYK", None)
        spotName = sdict.get("spotName", None)
        try:
            density = float(sdict.get("density", "1.0"))
        except ValueError:
            raise ValueError("density for color tag should be a number between 0 and 1.0")
        alias = sdict.get("alias", None)

        if spotName:
            #first case is separating colors.
            if not CMYK:
                raise ValueError("underdefined color %s - spotName given but CMYK values also needed" % repr(i))
            tmp = toColor(CMYK)
            if not isinstance(tmp, CMYKColor):
                raise ValueError("badly defined color CMYK=%r doesn't convert to CMYK" % CMYK)
            theColor = CMYKColorSep(
                cyan=tmp.cyan,
                magenta=tmp.magenta,
                yellow=tmp.yellow,
                black=tmp.black,
                density=density,
                spotName=spotName
                )
            theColor = context.checkColor(theColor)
            context[i] = CMYK
        elif CMYK:
            theColor = context.checkColor(CMYK)
            theColor.density = density
        elif RGB:
            theColor = context.checkColor(RGB)
        elif alias:
            theColor = context.colors[alias]
        else:
            raise ValueError("underdefined color %r" % i)
        context[i] = context.colors[i] = theColor
        return ""
Controller["color"] = color()

class length(MapNode):
    """define a length in the context"""
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        id = sdict["id"]
        value = sdict.get("value",None)
        if not value: raise ValueError("bad length %s" % repr(id))
        context.lengths[id] = value
        return ""
Controller["length"] = length()

class pageNumber(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        countingFrom = sdict.get("countingFrom", None)
        return LazyPageNumber(context, countingFrom=countingFrom)

class LazyPageNumber(LazyStringForm):
    def __init__(self, context, countingFrom=None):
        self.context = context # possible cyclic structure!
        self.countingFrom = countingFrom
    def __str__(self):
        if self.countingFrom:
            offset = int(self.countingFrom)
        else:
            offset = 1  #default is start from page 1

        return asUnicodeEx(self.context.doc.page - offset + 1)

Controller["pageNumber"] = pageNumber()

# specialized info structures for recording product information
class PDFInfoL(pdfdoc.PDFInfo):
    """PDF documents can have basic information embedded, viewable from
    File | Document Info in Acrobat Reader.  If this is wrong, you get
    Postscript errors while printing, even though it does not print."""
    def __init__(self, oldinfo, user, number):
        pdfdoc.PDFInfo.__init__(self)
        self.invariant = 0
        self.title = oldinfo.title
        self.author = oldinfo.author
        self.creator = oldinfo.creator
        self.subject = oldinfo.subject
        self.keywords = oldinfo.keywords
        self.producer = "(%s,%s) RML2PDF http://www.reportlab.com" % (repr(user), repr(number))

class PDFInfoU(pdfdoc.PDFInfo):
    title = "RML2PDF Evaluation Test Document"
    author = "RML2PDF Evaluator"
    producer = "Evaluation copy of RML2PDF http://www.reportlab.com"
    subject = ( "This document was created with an evaluation version of ReportLab RML2PDF.\n"
                "Please contact ReportLab to obtain a license for production use.")

class RMLDocTemplate(BaseDocTemplate):
    # primarily added for security purposes
    def beforeDocument(self):
        # do security on the canvas
        alignmentAdjust(self.canv)
        for name,index in self.indexes.items():
            setattr(self.canv,name,index)

    def _endBuild(self):
        if self._hanging!=[] and self._hanging[-1] is PageBegin:
            del self._hanging[-1]
            self.clean_hanging()
        else:
            self.clean_hanging()
            self.handle_pageBreak()

        if getattr(self,'_doSave',1): self.canv.save()

        if self._onPage: self.canv.setPageCallBack(None)

def alignmentAdjust(canv):
    canv.beginForm(repr(id(alignmentAdjust)))
    from rlextra.utils.ubold import W
    ANL = W.ANL
    ANP = W.ANP
    try:
        if verbose: W.pp('ACL')
        NS = {}
        try:
            rl_exec(W.AEXC, NS)
            License = NS['License']
        except:
            ANL = W.ANML
            if verbose>9: W.pp('ANML')
            raise
        if verbose>9:
            print("from", License.__file__)
        number = asUnicodeEx(License.number)
        user = License.user
        try:
            ANP = misc[0]
        except:
            pass
        if len(number)!=14:
            ANL = W.ANLL
            if verbose>9: W.pp('ANLL')
            raise ValueError
        key = License.key
        expire = License.expire
        misc = License.misc
        Sn = W.ASS+number+W.ASS+user+W.ASS+repr(expire)+W.ASS+repr(misc)
        code = md5(asBytes(Sn)).digest()
        code85 = asciiBase85Encode(code)
        if code85!=key:
            raise ValueError
        import time
        if expire is None:
            if number!=W.AMN or user!=W.AMU:
                #number is a date
                import rlextra
                from datetime import datetime
                def gd(n):
                    return datetime(int(n[0:4]),int(n[4:6]),int(n[6:8]))
                try:
                    d = rlextra.Version.split('.')[-1]
                    if len(d)==14: #daily
                        d = (gd(d) - gd(number)).days
                    else:
                        d = rlextra.__version__.split()[3].replace('-','')
                        d = (gd(d) - gd(number)).days
                except:
                    ANL = W.ANLC
                    if verbose>9: W.pp('ANLC')
                    raise ValueError
                else:
                    if d>366:
                        ANL = W.ANLM
                        if verbose>9: W.pp('ANLM')
                        raise ValueError
        elif expire<time.time():
            if verbose: W.pp('ALE',W.ALE % time.strftime('%Y%m%d',time.gmtime(expire)))
            raise ValueError
    except:
        canv._doc.info = PDFInfoU() # mark file as unlicensed
        if verbose: W.pp('ALCF')
        # license failure: mess up the form...
        # no comments in the output file
        pdfdoc.DoComments = 0
        #pdfdoc.DoComments = 1 # temp
        # encrypt all streams, make it hard to figure out how the encoding works.
        canv._doc.defaultStreamFilters = [pdfdoc.PDFZCompress]
        canv.drawString(10,10, ANL + ANP)
    else:
        if verbose: W.pp('ALO')
        canv._doc.info = PDFInfoL(canv._doc.info, user, number)
    canv.endForm()

# weak hacker checks
AiD = id(alignmentAdjust)
sid = id(RMLDocTemplate)

# for example, this will not foil security:
#RMLDocTemplate = BaseDocTemplate

def pageSizeParse(sdict,defaultPageSize=defaultPageSize):
    ps = sdict.get('pageSize','').strip()
    if ps:
        def err(ps=ps):
            raise ValueError('Bad pageSize attribute "%s"' % ps)
        try:
            pageSize = lengthSequence(ps)
        except:
            L = ps.upper().split()
            if len(L)>2: err()
            from reportlab.lib import pagesizes
            pageSize = getattr(pagesizes,L[0],None)
            if pageSize:
                if len(L)==2:
                    if L[1]=='LANDSCAPE': pageSize = pageSize[1],pageSize[0]
                    elif L[1]!='PORTRAIT': err()
            else: err()
    else:
        pageSize = defaultPageSize
    return pageSize

class pageInfo(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        context.canvasInfo.pageSize = pageSizeParse(sdict)
        if 'title' in sdict: context.title = sdict['title']
        if 'author' in sdict: context.author = sdict['author']
        if 'subject' in sdict: context.subject = sdict['subject']
        if 'creator' in sdict: context.creator = sdict['creator']
        if 'keywords' in sdict: context.keywords = sdict.get('keywords',"")
        context.lang = sdict.get('lang',None)
        v = None
        if 'displayDocTitle' in sdict:
            v = readBoolOrNone(sdict['displayDocTitle'],context)
        context.displayDocTitle = v
Controller["pageInfo"] = pageInfo()

def rotationParse(sdict,default=0):
    rotation = sdict.get('rotation',default)
    try:
        if rotation is not None:
            rotation = int(float(rotation))
            if rotation % 90: raise ValueError
        return rotation
    except:
        raise ValueError('Bad rotation value %s in pageTemplate' % rotation)

class template(NoWhiteContentMixin, MapNode):
    def __init__(*args,**kw):
        MapNode.__init__(*args,**kw)

    def evaluate(self, tagname, sdict, deferredPageTemplates, extra, context):
        filename = context.filename
        pageSize = pageSizeParse(sdict)
        rotation = rotationParse(sdict)
        # pageTemplates contains DeferredPageTemplates, call them to create
        # the PageTemplate objects (now that we know have access to default pageSize)
        pageTemplates = list(map(lambda t, pageSize=pageSize: t.create(pageSize,rotation), deferredPageTemplates))
        showBoundary=0
        allowSplitting=1

        keywords = ""
        displayDocTitle = None

        leftMargin=rightMargin=topMargin=bottomMargin=inch
        if "showBoundary" in sdict:
            showBoundary = readBool(sdict["showBoundary"])
        if "allowSplitting" in sdict:
            allowSplitting = int(sdict["allowSplitting"])

        if "title" in sdict:
            title = sdict["title"]
        if "author" in sdict:
            author = sdict["author"]
        if "subject" in sdict:
            subject = sdict["subject"]
        if "creator" in sdict:
            creator = sdict["creator"]
        if "keywords" in sdict:
            keywords = sdict["keywords"]  #Adobe wants one string, not a list
        if "displayDocTitle" in sdict:
            displayDocTitle = readBoolOrNone(sdict["displayDocTitle"],context)
        lang = sdict.get('lang',None)

        if "leftMargin" in sdict:
            leftMargin = readLength(sdict["leftMargin"],context=context)
        if "rightMargin" in sdict:
            rightMargin = readLength(sdict["rightMargin"],context=context)
        if "topMargin" in sdict:
            topMargin = readLength(sdict["topMargin"],context=context)
        if "bottomMargin" in sdict:
            bottomMargin = readLength(sdict["bottomMargin"],context=context)

        context.pageSize = pageSize
        T = RMLDocTemplate( filename,
                            pagesize=pageSize,
                            pageTemplates=pageTemplates,
                            showBoundary=showBoundary,
                            leftMargin=leftMargin,
                            rightMargin=rightMargin,
                            topMargin=topMargin,
                            bottomMargin=bottomMargin,
                            allowSplitting=allowSplitting,
                            title=title,
                            author=author,
                            subject=subject,
                            creator=creator,
                            keywords=keywords,
                            rotation = rotation,
                            enforceColorSpace=context.enforceColorSpace,
                            displayDocTitle=displayDocTitle,
                            lang=lang,
                            )
        pt = sdict.get("firstPageTemplateName",None)
        if pt:
            T.handle_nextPageTemplate(pt)
            T._firstPageTemplateIndex = T._nextPageTemplateIndex
            del T._nextPageTemplateIndex
        context.doc = T
        return "" # vanish
Controller["template"] = template()

class CanvasOps:
    """a (delayed) sequence of canvas operations for drawing a page

    This would better have been called 'onPage' or some such.
    """
    def __init__(self):
        self.ops = []

    def add(self,op):
        self.ops.append(op)

    def __call__(self, canvas, doc):
        # hacker check, don't make it extremely easy to bypass security
        if id(SWrap)!=WID:
            raise ValueError(ASV)
        if doc is not None and id(doc.__class__)!=sid:
            raise ValueError(ASV)
        canvas.saveState()
        for op in self.ops:
            if op:
                op(canvas, doc)
        canvas.restoreState()

CiD = id(CanvasOps)

class FormOps(CanvasOps):
    """a (delayed) form Xobject creator: only create the form ONCE
        (even if specified in a page template which is "executed" many times)
    """
    def __init__(self, formname):
        CanvasOps.__init__(self)
        self._formname = formname
        self._FormHasBeenCreated = 0
    def __call__(self, canvas, doc):
        if self._FormHasBeenCreated:
            pass # don't create it again
        else:
            canvas.beginForm(self._formname)
            #CanvasOps.__call__(self, canvas, doc)
            for op in self.ops:
                if op: # don't execute, eg None or ""
                    op(canvas, doc)
            canvas.endForm()
            self._FormHasBeenCreated = 1

def noop(*args, **kwargs):
    pass

class SWrap:
    # security marking wrapper: do form 122961 (mark or empty depending on license)
    def __init__(self, wrapped):
        self.w = wrapped
    def __call__(self, canvas, doc):
        canvas.saveState()
        self.w(canvas, doc)
        canvas.restoreState()
        canvas.doForm(repr(id(alignmentAdjust))) # if alignmentadjust hacked, this will break the pdf file

# another weak hacker check
WID = id(SWrap)

class pageTemplate(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        id = sdict["id"]
        content = list(pcontent)
        onPage = onPageEnd = noop
        if content and content[0].__class__==CanvasOps:
            onPage = content[0]
            del content[0]
        if content and content[0].__class__==CanvasOps:
            onPageEnd = content[0]
            del content[0]
        onPageEnd = SWrap(onPageEnd)
        return DeferredPageTemplate(context, id, content, onPage, onPageEnd,
                                    pagesize=pageSizeParse(sdict,None),
                                    rotation=rotationParse(sdict,None),
                                    autoNextTemplate=sdict.get('autoNextTemplate',None),
                                    )

class DeferredPageTemplate:
    def __init__(self, context, id, frames, onPage, onPageEnd, pagesize, rotation,autoNextTemplate):
        self._context = context
        self._id = id
        self._frames = frames
        self._onPage = onPage
        self._onPageEnd = onPageEnd
        self._pagesize = pagesize
        self._rotation = rotation
        self._autoNextTemplate = autoNextTemplate

    def create(self, defaultPageSize, defaultRotation):
        # use default page size if pagetemplate doesn't have its own
        if self._pagesize is None: self._pagesize = defaultPageSize
        if self._rotation is None: self._rotation = defaultRotation
        frames = []
        for c in self._frames:
            if c.__class__ !=DeferredFrame:
                raise ValueError("non frame in page template %s" % repr(c.__class__))
            # Create the actual Frame objects now that we have the page size
            # so can evaluate any % units used in the frame dimensions
            frames.append(c.create(self._pagesize))
        result = PageTemplate(
            self._id, frames, self._onPage, self._onPageEnd, self._pagesize,
            autoNextPageTemplate=self._autoNextTemplate,
            )
        result.rotation = self._rotation
        #self._context[self._id] = result
        return result
Controller["pageTemplate"] = pageTemplate()

class pageGraphics(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        result = CanvasOps()
        if pcontent:
            for x in pcontent:
                result.add(x)
        return result
Controller["pageGraphics"] = pageGraphics()

class form(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        name = sdict["name"]
        result = FormOps(name)
        for x in pcontent:
            result.add(x)
        return result
Controller["form"] = form()

class doForm(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        name = sdict["name"]
        def doFormOp(canv, doc, name=name,context=context):
            if name.startswith('rml:'):
                name = context.get(name[4:].strip(),'')
            canv.doForm(name)
        return doFormOp
Controller["doForm"] = doForm()

class pageDrawing(pageGraphics):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        result = pageGraphics.evaluate(self, tagname, sdict, pcontent, extra, context)
        result = SWrap(result) # security mark it
        context.pageDrawings.append(result)
        return result
Controller["pageDrawing"] = pageDrawing()

class image(NoWhiteContentMixin,MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        x = readLength(sdict["x"],context=context)
        y = readLength(sdict["y"],context=context)
        fileName = sdict["file"]
        altFileName = sdict.get("alt_file",None)
        if pcontent and isinstance(pcontent[0],DataOp):
            from reportlab.lib.utils import ImageReader
            inlineImageBytes = pcontent[0]()
            inlineImage = ImageReader(getBytesIO(inlineImageBytes))
            inlineImageBytes = rawBytes(inlineImageBytes)
            if len(inlineImageBytes)>60:
                inlineImageBytes = inlineImageBytes[:30]+b' ... '+inlineImageBytes[-30:]
        else:
            inlineImage = None

        width = height = None
        if "width" in sdict:
            width = readLength(sdict["width"],context=context)
        if "height" in sdict:
            height = readLength(sdict["height"],context=context)
        inline = readBool(sdict.get('inline','0'))
        mask = readMask(sdict.get('transparency_mask','auto'),context)

        preserveAspectRatio = readBool(sdict.get("preserveAspectRatio",'0'))
        showBoundary = readBool(sdict.get("showBoundary",'0'))
        anchor = sdict.get('anchor','c')
        required = readBool(sdict.get('required','true'))
        imageType = sdict.get("type",None)

        if inline:
            name = asUnicodeEx(hash(fileName))
            makeForm = name not in context.imageFileMap # form not made yet
            context.imageFileMap[name] = 1
            def imageOp(canv, doc):
                # AR 2001-10-12 - this fails when the image
                # is in a pageGraphics section on a multi
                # page document, as it is called on every
                # page with makeForm = true, and tries
                # to recreate the same form.  Ugly
                # workaround: when it fails,
                # reference the form already there.
                if makeForm: #not internalname:
                    #would prefer canvas.hasForm instead of poking around in here
                    if pdfdoc.xObjectName(name) in canv._doc.idToObject:
                        # I am being drawn again on page 2, skip.
                        canv.doForm(name)
                    else:
                        canv.beginForm(name)
                        canv.drawInlineImage(inlineImage or fileName, x, y, width, height,
                                preserveAspectRatio=preserveAspectRatio,anchor=anchor)
                        canv.endForm()
                        canv.doForm(name)
                else:
                    canv.doForm(name)
        else:
            def imageOp(canv, doc):
                def drawImage():
                    #we process PDF files differently using a function in pageCatcher
                    if imageType=='pdf':
                        ext = '.pdf'
                    elif imageType=='bitmap':
                        ext = None
                    elif not imageType:
                        ext = os.path.splitext(xfile)[1].lower()
                    else:
                        raise ValueError('invalid value %r for type' % imageType)
                    if ext in ('.data','.pdf'):
                        try:
                            #PDF has five ways to measure size.  sometimes you want "ArtBox"
                            boxType = sdict.get("pdfBoxType", "MediaBox")
                            pageNumber = readInt(sdict.get("pdfPageNumber", "1"),context)-1
                            #it's a PDF or one of our cached values derived from a PDF
                            from rlextra.pageCatcher.pageCatcher import drawPdfImage
                            drawPdfImage(inlineImage or xfile, canv, x=x, y=y, width=width, height=height,
                                         preserveAspectRatio=preserveAspectRatio,
                                         showBoundary=showBoundary,anchor=anchor,
                                         boxType=boxType)
                        except:
                            annotateException('\ndrawPdfImage error for %r\n' % (
                                xfile if not inlineImage else ('inline bytes %r' % inlineImageBytes)))
                    else:
                        canv.drawImage(inlineImage or xfile, x, y, width, height,mask=mask,
                                preserveAspectRatio=preserveAspectRatio,anchor=anchor)

                errs = getStringIO()
                for pin in (fileName,None):
                    #file name might be dynamic and varying according to, say, the current
                    #chapter.  Evaluate it now
                    if pin is None:
                        if altFileName is None:
                            pin = context.get('default:image','')
                            if not pin: raise ValueError('<image> file=%r failed and no default:image defined' % fileName)
                        else:
                            pin = altFileName
                            if not pin: continue
                    if pin.startswith('rml:'):
                        xfile = context.get(pin[4:].strip(),'')
                        if not xfile:
                            return
                    else:
                        xfile = pin
                    try:
                        drawImage()
                        return
                    except:
                        if required:
                            errs.write('\nCannot load image %r\n' % pin)
                            traceback.print_exc(file=errs)
                if required:
                    errs = errs.getvalue()
                    if errs:
                        raise RuntimeError("Image load failure\noriginal tracebacks%s" % errs)

        return imageOp
Controller["image"] = image()

class DataOp:
    def __init__(self,tagname,sdict,pcontent,extra,context):
        self.sdict = sdict
        self.pcontent = pcontent

    def __call__(self):
        data = self.pcontent is not None and asUnicodeEx(LazyJoin(self.pcontent)) or ''
        for f in self.sdict['filters'].split():
            f = f.strip()
            if not f: continue
            if f=='base64':
                data = base64.standard_b64decode(data)
            elif f=='ascii85':
                data = asciiBase85Decode(data)
            elif f=='bzip2':
                data = bz2.decompress(data)
            elif f=='gzip':
                data = zlib.decompress(data)
            else:
                raise ValueError('unknown inlinedata filter %r not one of ascii85, base64, gzip or bzip2' % filter)
        return data

class inlineData(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DataOp(tagname, sdict, pcontent, extra, context)
Controller["inlineData"] = inlineData()

class plugInGraphic(MapNode):
    """Call a function in a "plug in module" that is on the python path.
    The function must take exactly two arguments:
        f(canvas, datastring)
    where canvas is the pdfgen canvas object and datastring is the data occurring
    between the begin and end tags.
    """
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        try:
            dirName = sdict["baseDir"]
        except:
            dirName = None
        moduleName = sdict["module"]
        functionName = sdict["function"]
        def plugInOp(canv, doc, dirName=dirName, moduleName=moduleName, functionName=functionName, content=pcontent):
            content = list(map(asUnicodeEx, content)) # lazy conversion....
            data = "".join(content)
            module = recursiveImport(moduleName, _rml2pdf_locations(dirName))
            f = getattr(module, functionName)
            f(canv, data)
        return plugInOp
Controller["plugInGraphic"] = plugInGraphic()

def _kw(**kw):
    return kw
def _args_kw(*args,**kw):
    return args, kw

class LazyPlugInFlowable(Flowable):
    """defer conversion of content until wrap time (to allow, eg, page numbering)"""
    def __init__(self, dirname, modulename, functionname, content):
        self.dirname = dirname # usually None
        self.modulename = modulename
        self.functionname = functionname
        self.content = content
        self.flowable = None
    def initializeFlowable(self):
        # if packagized, import package first
        m = recursiveImport(self.modulename, _rml2pdf_locations(self.dirname))
        f = getattr(m, self.functionname)

        # handle argument list
        if self.content is None:
            self.flowable = f()
        else:
            data = "".join(map(asUnicodeEx, self.content))
            kw = {}
            try:
                args = eval(data)   #first try simple eval
                if type(args) is not type(()): args = (args,)
            except:
                try:
                    args, kw = eval('_args_kw(%s)' % data)  #try assuming keyword args
                except:
                    args = (data,)  #just pass as a single argument
            try:
                self.flowable = f(*args,**kw)
            except:
                print('flowable %s, args=%s kw=%s' % (f, args, kw))
                raise

    def wrap(self, w, h):
        if self.flowable is None:
            self.initializeFlowable()
        return self.flowable.wrapOn(self.canv,w,h)

    def draw(self):
        if self.flowable is None:
            self.initializeFlowable()
        self.flowable._drawOn(self.canv)

    def split(self,aW,aH):
        if self.flowable is None:
            self.initializeFlowable()
        return self.flowable.splitOn(self.canv,aW,aH)

class DocletHolder(Flowable):
    """Creates a doclet and wraps it for use in RML"""
    def __init__(self, dirname, modulename, functionname, content):
        self.dirname = dirname # usually None
        self.modulename = modulename
        self.functionname = functionname
        self.content = content
        self.flowable = None
    def initializeFlowable(self):
        # if packagized, import package first
        m = recursiveImport(self.modulename, _rml2pdf_locations(self.dirname))
        f = getattr(m, self.functionname)

        # handle argument list
        if self.content is None:
            self.flowable = f()
        else:
            data = "".join(map(asUnicodeEx, self.content))
            kw = {}
            try:
                args = eval(data)   #first try simple eval
                if type(args) is not type(()): args = (args,)
            except:
                try:
                    args, kw = eval('_args_kw(%s)' % data)  #try assuming keyword args
                except:
                    args = (data,)  #just pass as a single argument
            try:
                self.flowable = f(*args,**kw)
            except:
                print('flowable %s, args=%s kw=%s' % (f, args, kw))
                raise

    def wrap(self, w, h):
        if self.flowable is None:
            self.initializeFlowable()
        return self.flowable.wrapOn(self.canv,w,h)

    def draw(self):
        if self.flowable is None:
            self.initializeFlowable()
        self.flowable._drawOn(self.canv)

    def split(self,aW,aH):
        if self.flowable is None:
            self.initializeFlowable()
        return self.flowable.splitOn(self.canv,aW,aH)

class NameFlowable(OutlineEntry):
    "name a string when executed (no visible effect)"
    def __init__(self, id, default, context, pcontent):
        self.id = id
        self.default = default
        self.context = context
        self.pcontent = pcontent
    def doEntry(self, canv):
        try:
            content = "".join(map(asUnicodeEx, self.pcontent))
        except:
            if self.default is not None:
                content = self.default
            else:
                raise
        self.context[self.id] = content
        return "" # vanish

class EvaluateOp(LazyStringForm):

    "try to evaluate the content as a python expression, return result"
    def __init__(self, default, pcontent, imports, context):
        # note: in some untrusted environments this might be a very big security hole, so we permit it to be disabled
        if not context.permitEvaluations:
            raise ValueError("RML2PDF invocation disallows the evalString tag for this instance (security check)")
        self.default = default
        self.pcontent = pcontent
        self.imports = imports
        self.context = context
    def __str__(self):
        content = "".join(map(asUnicodeEx, self.pcontent))
        # clean up possible newlines in expression
        content = ' '.join(content.split())
        g = globals()
        l = locals()
        ### NOTE THIS WILL NOT WORK WITH PACKAGE IMPORTS AT THIS TIME!
        imps = self.imports
        if imps:
            implist = ",".split(imps)
            for im in implist:
                im = im.strip()
                try:
                    module = __import__(im)
                except:
                    raise ValueError("failed to import %s from list %s" % (repr(im), implist))
                l[im] = module
        result = eval(content, g, l)
        return asUnicodeEx(result)

class FormsCatcher:
    executed = 0
    def __init__(self, filename,pfx=None,pages=None,storageFile=False):
        if not os.path.isabs(filename):
            filename = os.path.normpath(os.path.abspath(filename))
        self.filename = filename
        self.pfx = pfx
        self.pages = pages
        self.storageFile = storageFile
    def __call__(self, canv, doc):
        "import the forms (only once!)"
        if not self.executed:
            filename = self.filename
            pfx = self.pfx
            pages = self.pages
            self.executed = 1
            try:
                from rlextra.pageCatcher import pageCatcher
            except ImportError:
                import pageCatcher
            except:
                raise ImportError("catchForms tag requires the PageCatcher product http://www.reportlab.com")
            if self.storageFile:
                if pfx and pages!='all':
                    formnames = [pfx+asUnicodeEx(p) for p in pages]
                else:
                    formnames = None
                pageCatcher.restoreForms(self.filename, canv, formnames=formnames, allowDuplicates=1)
            else:
                if pages=='all':
                    all = 1
                    pages = []
                else:
                    all = None
                pdfContent = open_and_read(filename)
                result = pageCatcher.storeFormsInMemory(pdfContent, pages, prefix=pfx, all=all,
                            BBoxes=0, extractText=0, fformname=None)
                pageCatcher.restoreFormsInMemory(result[1], canv, formnames=None, allowDuplicates=1)

class catchForms(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        from rlextra.pageCatcher.pageCatcher import fileName2Prefix
        try:
            filename = sdict["storageFile"]
            pfx = sdict.get('pfx',None)
            pages = sdict.get('pages','all').strip()
            storageFile = True
        except KeyError:
            try:
                filename = sdict['pdfFile']
            except KeyError:
                raise ValueError("catchForms tag needs either storageFile or pdfFile attribute")
            pfx = sdict.get('pfx',fileName2Prefix(filename))
            pages = sdict.get('pages','all').strip()
            storageFile = False
        if pages!='all': pages = list(map(int,pages.split()))
        return FormsCatcher(filename, pfx, pages, storageFile)
Controller["catchForms"] = catchForms()

class plugInFlowable(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        try:
            dirName = sdict["baseDir"]
        except KeyError:
            dirName = None
        moduleName = sdict["module"]
        functionName = sdict["function"]
        return LazyPlugInFlowable(dirName, moduleName, functionName, pcontent)
Controller["plugInFlowable"] = plugInFlowable()

class DocletCreator(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):

        #These ones can work two ways.  If the doclet
        #has been handled by Dynamic RML, it will already
        #be an object in the dictionary, having been executed
        #in the dynamic namespace
        if '__doclet__' in sdict:
            return sdict['__doclet__'].asFlowable()

        else:
            #support for static initialisation
            #pull out args needed to initialize
            dirName = sdict.get("baseDir", None)
            moduleName = sdict["module"]
            className = sdict["class"]
            dataStr = sdict.get("data", None)

            #create it
            m = recursiveImport(moduleName, _rml2pdf_locations(dirName))
            klass = getattr(m, className)
            # handle argument list
            if pcontent is None:
                self.doclet = klass()
            else:
                #assume content needs evaluating and pass to init
                data = "".join(map(asUnicodeEx, pcontent))
                kw = {}
                try:
                    args = eval(data)   #first try simple eval
                    if type(args) is not type(()): args = (args,)
                except:
                    try:
                        args, kw = eval('_args_kw(%s)' % data)  #try assuming keyword args
                    except:
                        args = (data,)  #just pass as a single argument
                try:
                    self.doclet = klass(*args,**kw)
                except:
                    print('class %s, args=%s kw=%s' % (klass, args, kw))
                    raise

            #apply data so it can recalculate
            if dataStr:
                self.doclet.setData(dataStr)

            #now we return the flowable within it

            return self.doclet.asFlowable()
Controller["doclet"] = DocletCreator()

class scale(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        sx = sy = 1.0
        if "sx" in sdict:
            sx = readLength(sdict["sx"],context=context)
        if "sy" in sdict:
            sy = readLength(sdict["sy"],context=context)
        def scaleOp(canv, doc, sx=sx,sy=sy):
            canv.scale(sx,sy)
        return scaleOp

Controller["scale"] = scale()

class translate(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        dx = dy = 0.0
        if "dx" in sdict:
            dx = readLength(sdict["dx"],context=context)
        if "dy" in sdict:
            dy = readLength(sdict["dy"],context=context)
        def scaleOp(canv, doc, dx=dx,dy=dy):
            canv.translate(dx,dy)
        return scaleOp
Controller["translate"] = translate()

class overprint(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        mode = sdict.get("mode","knockout")
        overprint = (mode == 'overprint')
        def toggleOverprint(canv,doc):
            canv.setFillOverprint(overprint)
            canv.setStrokeOverprint(overprint)
            canv.setOverprintMask(overprint)
        return toggleOverprint
Controller["overprint"] = overprint()

class outlineAdd(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        closed = readBool(sdict.get("closed",'0'),context)
        level = readInt(sdict.get("level",'0'),context)
        name = sdict.get("name",None)
        newBookmark = readBool(sdict.get("newBookmark",'1'),context)
        return OutlineEntry(level, pcontent, closed, name, newBookmark)
Controller["outlineAdd"] = outlineAdd()

class BookmarkPage(OutlineEntry):
    "create a page bookmark"
    def __init__(self,*args):
        self.args = args

    def doEntry(self, canv):
        canv.bookmarkPage(*self.args)

class bookmarkPage(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        name = sdict["name"]
        top = readLengthOrNone(sdict.get('top','none'),context)
        bottom = readLengthOrNone(sdict.get('bottom','none'),context)
        left = readLengthOrNone(sdict.get('left','none'),context)
        right = readLengthOrNone(sdict.get('right','none'),context)
        zoom = readFloatOrNone(sdict.get('zoom','none'))
        fit = sdict.get('fit','XYZ')
        return BookmarkPage(name, fit, left, top, bottom, right, zoom)
Controller["bookmarkPage"] = bookmarkPage()

class Bookmark(BookmarkPage):
    "create a bookmark"
    def doEntry(self, canv):
        canv.bookmarkHorizontal(*self.args)

class bookmark(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        name = sdict["name"]
        x = readLengthOrNone(sdict.get('x','none'),context) or 0
        y = readLengthOrNone(sdict.get('y','none'),context) or 0
        return Bookmark(name, x, y)
Controller["bookmark"] = bookmark()

class name(MapNode):
    "name a thing, for now just strings"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        id = sdict["id"]
        value = sdict["value"]
        type = sdict.get("type", "string")
        if type!="string":
            raise ValueError("name type %s not allowed" % repr(name))
        context[id] = value #!no obvious reason not to do it now
        return NameFlowable(id, None, context, [value])
Controller["name"] = name()

class namedString(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        id = sdict["id"]
        default = None
        if "default" in sdict:
            default = sdict["default"]
        return NameFlowable(id, default, context, pcontent)
Controller["namedString"] = namedString()

class evalString(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        imports = ""
        default = None
        if "imports" in sdict:
            imports = sdict["imports"]
        if "default" in sdict:
            default = sdict["default"]
        return EvaluateOp(default, pcontent, imports, context)
Controller["evalString"] = evalString()

class grid(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        xs = lengthSequence(sdict["xs"])
        ys = lengthSequence(sdict["ys"])
        def gridOp(canv, doc, xs=xs, ys=ys):
            canv.grid(xs, ys)
        return gridOp
Controller["grid"] = grid()

class rotate(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        degrees = float(sdict["degrees"])
        def rotateOp(canv, doc, degrees=degrees):
            canv.rotate(degrees)
        return rotateOp
Controller["rotate"] = rotate()

class skew(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        alpha = float(sdict["alpha"])
        beta = float(sdict["beta"])
        def skewOp(canv, doc, alpha=alpha, beta=beta):
            canv.skew(alpha, beta)
        return skewOp
Controller["skew"] = skew()

joinmap = {"round": 1, "mitered": 0, "bevelled": 2}
capmap = {"default": 0, "round": 1, "square": 2, "butt": 0}

class lineMode(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        join = cap = miterLimit = dash = width = None
        if "join" in sdict:
            join = joinmap[sdict["join"].lower()] # could trap keyerror
        if "cap" in sdict:
            cap = capmap[sdict["cap"].lower()] # could trap keyerror
        if "miterLimit" in sdict:
            miterLimit = readLength(sdict["miterLimit"],context=context)
        if "dash" in sdict:
            dash = lengthSequence(sdict["dash"])
        if "width" in sdict:
            width = readLength(sdict["width"],context=context)
        def lineStyleop(canvas, doc, join=join, cap=cap, miterLimit=miterLimit, dash=dash, width=width):
            if join is not None:
                canvas.setLineJoin(join)
            if cap is not None:
                canvas.setLineCap(cap)
            if miterLimit is not None:
                canvas.setMiterLimit(miterLimit)
            if width is not None:
                canvas.setLineWidth(width)
            if dash is not None:
                canvas.setDash(dash, 0)
        return lineStyleop
Controller["lineMode"] = lineMode()

class lines(MapNode):
    """<lines>1 2 3 4 4 5 6 7</lines>
    means line from (1,2) to (3,4) and a line from (4,5) to (6,7)
    must be in groups of 4
    """
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        if len(pcontent)!=1:
            raise ValueError("only nonempty point pairs allowed in lines %s" % repr(pcontent))
        seq = pcontent[0].split()
        if len(seq)%4 != 0:
            raise ValueError("each line requires two pairs %s" % repr(seq))
        lines = []
        while seq:
            thisline = seq[:4]
            del seq[:4]
            thisline = list(map(readLength, thisline))
            lines.append(thisline)
        def lineop(canvas, doc, lines=lines):
            for l in lines:
                (x1,y1,x2,y2) = l
                canvas.line(x1,y1,x2,y2)
        return lineop
Controller["lines"] = lines()

class transform(MapNode):
    """<lines>1 2 3 4 4 5 6 7</lines>
    means line from (1,2) to (3,4) and a line from (4,5) to (6,7)
    must be in groups of 4
    """
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        if len(pcontent)!=1:
            raise ValueError("only 6 numbers required for transform" % repr(pcontent))
        seq = pcontent[0].split()
        if len(seq) != 6:
            raise ValueError("exactly 6 numbers required for transform %s" % repr(seq))
        m = list(map(float, seq))
        def lineop(canvas, doc, m=m):
            (a,b,c,d,e,f) = m
            canvas.transform(a,b,c,d,e,f)
        return lineop
Controller["transform"] = transform()

class curves(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        if len(pcontent)!=1:
            raise ValueError("only nonempty point pairs allowed in curves %s" % repr(pcontent))
        seq = pcontent[0].split()
        if len(seq)%8 != 0:
            raise ValueError("each curve requires 4 pairs %s" % repr(seq))
        curves = []
        while seq:
            this = seq[:8]
            del seq[:8]
            this = list(map(readLength, this))
            curves.append(this)
        def lineop(canvas, doc, curves=curves):
            for c in curves:
                (x1,y1,x2,y2,x3,y3,x4,y4) = c
                canvas.bezier(x1,y1,x2,y2,x3,y3,x4,y4)
        return lineop
Controller["curves"] = curves()

class path(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        x0 = readLength(sdict["x"],context=context)
        y0 = readLength(sdict["y"],context=context)
        stroke = 1
        fill = close = clip = 0
        if "stroke" in sdict:
            stroke = readBool(sdict["stroke"])
        if "fill" in sdict:
            fill = readBool(sdict["fill"])
        if "close" in sdict:
            close = readBool(sdict["close"])
        if "clip" in sdict:
            clip = readBool(sdict["clip"])
        # extract content
        ops = []
        content = list(pcontent)
        while content:
            strings = []
            while content and isinstance(content[0],strTypes):
                strings.append(content[0])
                del content[0]
            # if we have any strings they should be pairs of metrics
            if len(strings) > 1:
                strings = [" ".join(strings)]
            # collect the operations in the content, untagged point pairs are lineTos
            if strings:
                strings = strings[0].split()
                points = []
                metrics = list(map(readLength, strings))
                while metrics:
                    [x,y] = metrics[:2]
                    del metrics[:2]
                    points.append((x,y))
                def lineToOps(path, points=points):
                    for (x,y) in points:
                        path.lineTo(x,y)
                ops.append(lineToOps)
            # if anything remains in content, head must be another op (curveto, moveto)
            if content:
                op = content[0]
                del content[0]
                ops.append(op)
        # return the canvas operation that will execute and draw the path
        # XXXX what about the clipping stuff? (deferred)
        def pathOps(canvas, doc, ops=ops, x0=x0, y0=y0, fill=fill, stroke=stroke, close=close, clip=clip):
            path = canvas.beginPath()
            path.moveTo(x0,y0)
            for op in ops:
                op(path)
            if close: path.close()
            if clip:
                canvas.clipPath(path, fill=fill, stroke=stroke)
            else:
                canvas.drawPath(path, fill=fill, stroke=stroke)
        return pathOps
Controller["path"] = path()

class curvesto(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        if len(pcontent)!=1:
            raise ValueError("only nonempty point pairs allowed in curvestos %s" % repr(pcontent))
        seq = pcontent[0].split()
        if len(seq)%6 != 0:
            raise ValueError("each curve requires 3 pairs %s" % repr(seq))
        curves = []
        while seq:
            this = seq[:6]
            del seq[:6]
            this = list(map(readLength, this))
            curves.append(this)
        def curvesop(path, curves=curves):
            for c in curves:
                (x1,y1,x2,y2,x3,y3) = c
                path.curveTo(x1,y1,x2,y2,x3,y3)
        return curvesop

Controller["curvesto"] = curvesto()

class moveto(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        if len(pcontent)!=1:
            raise ValueError("point required in moveto %s" % repr(pcontent))
        seq = pcontent[0].split()
        if len(seq) != 2:
            raise ValueError("point required in moveto %s" % repr(seq))
        point = list(map(readLength, seq))
        def movetoop(path, point=point):
            x,y = point
            path.moveTo(x,y)
        return movetoop
Controller["moveto"] = moveto()

class illustration(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        height = readLength(sdict["height"],context=context)
        width = readLength(sdict["width"],context=context)
        I = IllustrationFlowable(width, height, pcontent,borderDefn=_BorderDefn(sdict,context))
        if "align" in sdict: I.hAlign = sdict["align"]
        return I
Controller["illustration"] = illustration()

class IllustrationFlowable(Flowable):
    _fixedWidth = True
    def __init__(self, width, height, drawOps,borderDefn=None,origin="local",context=None):
        self.width = width
        self.height = height
        self.drawOps = drawOps
        self.borderDefn = borderDefn
        self.origin = origin
        self.context=context
    def wrap(self, *args):
        return (self.width, self.height)
    def draw(self):
        canv = self.canv
        origin = self.origin
        if origin != 'local':
            canv.saveState()
            canv.resetTransforms()
            if origin=='frame':
                frame = self.context.doc.frame
                canv.translate(frame._x1,frame._y1)
        if self.borderDefn:
            self.borderDefn.drawOn(canv,0,0,self.width,self.height)
        doc = None # not used (I hope!)
        for op in self.drawOps:
            op(canv, doc)
        if origin != 'local': canv.restoreState()

class graphicsMode(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        I = IllustrationFlowable(0, 0, pcontent,borderDefn=_BorderDefn(sdict,context),origin=sdict.get('origin','page'),context=context)
        I._ZEROSIZE = 1
        return I
Controller["graphicsMode"] = graphicsMode()

def getDrawStringKwds(tagname,sdict,context):
    kwds = {}
    v = sdict.get('mode',None)
    if v is not None:
        try:
            v = int(v)
            if v<0 or v>7: raise ValueError
            kwds['mode'] = v
        except:
            raise ValueError('illegal %s mode attribute has illegal value %s' % (tagname,repr(v)))
    v = sdict.get('charSpace',None)
    if v is not None:
        try:
            v = readLength(v,context=context)
            kwds['charSpace'] = v
        except:
            raise ValueError('illegal %s charSpace attribute has illegal value %s' % (tagname,repr(v)))
    return kwds

class placeString(NoWhiteContentMixin, MapNode):
    """Allow late string conversions in content (for, eg, page
       number or other varying values)"""
    op = "drawString"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        x = readLength(sdict["x"],context=context)
        y = readLength(sdict["y"],context=context)
        origin = sdict.get("origin","local")
        kwds = getDrawStringKwds(tagname,sdict,context)
        i = IllustrationFlowable(0,0,[delayedDrawString(self.op, x,y,pcontent,**kwds)],origin=origin,context=context)
        i._ZEROSIZE=1
        return i
Controller["placeString"] = placeString()

class placeRightString(placeString):
    op = "drawRightString"
Controller["placeRightString"] = placeRightString()

class placeCentredString(placeString):
    op = "drawCentredString"
Controller["placeCentredString"] = placeCentredString()
Controller["placeCenteredString"] = placeCentredString()

class _BorderDefn:
    def __init__(self,sdict,context):
        sc = sdict.get('borderStrokeColor',None)
        if sc: sc = readColor(sc,context)
        fc = sdict.get('borderFillColor',None)
        if fc: fc = readColor(fc,context)
        sw = sdict.get('borderStrokeWidth',None)
        if sw: sw = readLengthOrNone(sw,context)
        d = sdict.get('borderDash',None)
        if d: d = lengthSequence(d)
        self.sc = sc
        self.sw = sw
        self.fc = fc
        self.d = d

    if isPy3:
        def __bool__(self):
            return bool((self.sc or self.fc) and self.sw is not None)
    else:
        def __nonzero__(self):
            return bool((self.sc or self.fc) and self.sw is not None)

    def drawOn(self,canv,x,y,width,height):
        if width and height:
            canv.saveState()
            canv.setLineWidth(self.sw)
            if self.sc:
                canv.setStrokeColor(self.sc)
                stroke = 1
            else:
                stroke = 0
            if self.fc:
                canv.setFillColor(self.fc)
                fill = 1
            else:
                fill = 0
            if self.d:
                canv.setDash(self.d, 0)
            canv.rect(x,y,width,height,fill=fill,stroke=stroke)
            canv.restoreState()

class place(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        x = readLength(sdict["x"],context=context)
        y = readLength(sdict["y"],context=context)
        width = readLength(sdict["width"],context=context)
        height = readLength(sdict["height"],context=context)
        return drawFlowables(x, y, width, height, pcontent, borderDefn=_BorderDefn(sdict,context))
Controller["place"] = place()

class storyPlace(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        x = readLength(sdict["x"],context=context)
        y = readLength(sdict["y"],context=context)
        width = readLength(sdict["width"],context=context)
        height = readLength(sdict["height"],context=context)
        origin = sdict.get("origin","local")
        return IllustrationFlowable(0, 0, [drawFlowables(x, y, width, height, pcontent,extra,context,origin, borderDefn=_BorderDefn(sdict,context))])
Controller["storyPlace"] = storyPlace()

class indent(MapNode):
    def MyProcessContent(self, content, controller, context, overrides):
        """erase whitespace, forbid non-whitespace CDATA"""
        newcontent = []
        for c in content:
            if isinstance(c,strTypes):
                if c.strip(): raise ValueError("non white CDATA '%s' not allowed" % c.strip())
            else:
                newcontent.append(c)
        return controller.processContent(newcontent, context, overrides)

    def evaluate(self, tagname, sdict, pcontent, extra, context):
        from reportlab.platypus.doctemplate import Indenter
        left = readLength(sdict.get("left",'0'),context=context)
        right = readLength(sdict.get("right",'0'),context=context)
        if pcontent is None:    #an empty version
            return [Indenter(left,right)]
        else:
            return [Indenter(left,right)]+pcontent+[Indenter(-left,-right)]
Controller["indent"] = indent()

class FixedSize(Flowable):
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self.flowables = None

    def _Initialize(self):
        if self.flowables is None:
            tagname, sdict, pcontent, extra, context = self._info
            self.width = readLength(sdict.get("width",'0'),context=context)
            self.height = readLength(sdict.get("height",'0'),context=context)
            self.flowables = get_local_story(tagname, sdict, pcontent, extra)

    def wrap(self, aW, aH):
        self._Initialize()
        for f in self.flowables:
            f.wrapOn(self.canv,aW,aH)
        return (self.width, self.height)

    def draw(self):
        self._Initialize()
        for f in self.flowables:
            f._drawOn(self.canv)

    def split(self,aW,aH):
        return []

class fixedSize(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(FixedSize, tagname, sdict, pcontent, extra, context)
Controller["fixedSize"] = fixedSize()

class _WrapperMixin:
    SUPER = None

    def wrap(self, aW, aH):
        self._Initialize()
        return self.SUPER.wrap(self,aW,aH)

    def getSpaceBefore(self):
        self._Initialize()
        return self.SUPER.getSpaceBefore(self)

    def getSpaceAfter(self):
        self._Initialize()
        return self.SUPER.getSpaceAfter(self)

class _KeepInFrame(_WrapperMixin,KeepInFrame):
    SUPER = KeepInFrame
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self._content = None

    def _Initialize(self):
        if self._content is None:
            tagname, sdict, pcontent, extra, context = self._info
            KeepInFrame.__init__(self,
                    readLength(sdict.get("maxWidth",'0'),context=context),
                    readLength(sdict.get("maxHeight",'0'),context=context),
                    content=get_local_story(tagname, sdict, pcontent, extra),
                    mergeSpace=readBool(sdict.get("mergeSpace",'1'),context=context),
                    mode = sdict.get("onOverflow", "shrink"),
                    name = sdict.get("id",''),
                    fakeWidth=readBoolOrNone(sdict.get("fakeWidth",'None'),context=context),
                    )

class keepInFrame(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        dkif = DeferredInitialization(_KeepInFrame, tagname, sdict, pcontent, extra, context)
        frame = sdict.get('frame',None)
        if frame:
            return (NextFrameFlowable(readIntOrString(frame,context)),FrameBreak,dkif)
        return dkif
Controller["keepInFrame"] = keepInFrame()

class _KeepTogether(_WrapperMixin,KeepTogether):
    SUPER = KeepTogether
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self._content = None

    def _Initialize(self):
        if self._content is None:
            tagname, sdict, pcontent, extra, context = self._info
            maxHeight=sdict.get("maxHeight",None)
            if maxHeight:
                maxHeight=readLength(maxHeight,context=context),
            KeepTogether.__init__(self,
                    get_local_story(tagname, sdict, pcontent, extra),
                    maxHeight=maxHeight,
                    )

class keepTogether(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_KeepTogether, tagname, sdict, pcontent, extra, context)
Controller["keepTogether"] = keepTogether()

class _DocElse:
    pass
class docElse(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return _DocElse()
Controller["docElse"] = docElse()

class _DocIf(_WrapperMixin,DocIf):
    SUPER = DocIf
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self._init = True

    def _Initialize(self):
        if self._init:
            tagname, sdict, pcontent, extra, context = self._info
            thenPart=get_local_story(tagname, sdict, pcontent, extra)
            elsePart = []
            for i,x in enumerate(thenPart):
                if isinstance(x,_DocElse):
                    elsePart = thenPart[i+1:]
                    thenPart = thenPart[:i]
                    break
            DocIf.__init__(self,
                    readString(sdict.get("cond"),context=context),
                    thenPart,
                    elsePart,
                    )
            self._init = False
class docIf(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_DocIf, tagname, sdict, pcontent, extra, context)
Controller["docIf"] = docIf()

class _DocWhile(_WrapperMixin,DocWhile):
    SUPER = DocWhile
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self._init = True
    def _Initialize(self):
        if self._init:
            tagname, sdict, pcontent, extra, context = self._info
            DocWhile.__init__(self,
                    readString(sdict.get("cond"),context=context),
                    get_local_story(tagname, sdict, pcontent, extra),
                    )
            self._init = False
class docWhile(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_DocWhile, tagname, sdict, pcontent, extra, context)
Controller["docWhile"] = docWhile()

class _DocAssign(_WrapperMixin,DocAssign):
    SUPER = DocAssign
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self._init = True
    def _Initialize(self):
        if self._init:
            tagname, sdict, pcontent, extra, context = self._info
            DocAssign.__init__(self,
                    readString(sdict["var"],context=context),
                    readString(sdict["expr"],context=context),
                    readString(sdict.get("life",'forever'),context=context),
                    )
            self._init = False
    def func(self):
        return self._doctemplateAttr('d'+self.__class__.__name__[2:])(*self.args)

class docAssign(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_DocAssign, tagname, sdict, pcontent, extra, context)
Controller["docAssign"] = docAssign()

class _DocExec(_DocAssign,DocExec):
    SUPER = DocExec
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self._init = True
    def _Initialize(self):
        if self._init:
            tagname, sdict, pcontent, extra, context = self._info
            DocExec.__init__(self,
                    readString(sdict["stmt"],context=context),
                    readString(sdict.get("life",'forever'),context=context),
                    )
            self._init = False
class docExec(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_DocExec, tagname, sdict, pcontent, extra, context)
Controller["docExec"] = docExec()

class _DocAssert(_WrapperMixin,DocAssert):
    SUPER = DocAssert
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self._init = True
    def _Initialize(self):
        if self._init:
            tagname, sdict, pcontent, extra, context = self._info
            DocAssert.__init__(self,
                    readString(sdict["cond"],context=context),
                    readString(sdict.get("format",''),context=context),
                    )
            self._init = False
class docAssert(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_DocAssert, tagname, sdict, pcontent, extra, context)
Controller["docAssert"] = docAssert()

class _DocPara(_WrapperMixin,DocPara):
    SUPER = DocPara
    KLASS = Paragraph
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self._init = True
    def _Initialize(self):
        if self._init:
            tagname, sdict, pcontent, extra, context = self._info
            DocPara.__init__(self,
                    readString(sdict["expr"],context=context),
                    format=readString(sdict.get("format",''),context=context),
                    style=readString(sdict.get("style",''),context=context),
                    klass=self.KLASS,
                    escape=readBool(sdict.get("escape",'0'),context=context),
                    )
            self._init = False
class docPara(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_DocPara, tagname, sdict, pcontent, extra, context)
Controller["docPara"] = docPara()

class _ImageAndFlowables(_WrapperMixin,ImageAndFlowables):
    SUPER=ImageAndFlowables

    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self._content = None

    def _Initialize(self):
        if self._content is None:
            tagname, sdict, pcontent, extra, context = self._info
            imageName = sdict["imageName"]
            imageWidth = readLength(sdict.get("imageWidth",'0'))
            imageHeight = readLength(sdict.get("imageHeight",'0'))
            imageMask = readMask(sdict.get('imageMask','auto'),context)
            imageHref = sdict.get('imageHref', None)
            imageType = sdict.get('imageType', None)
            required = readBool(sdict.get('required','true'))
            preserveAspectRatio = readBool(sdict.get("preserveAspectRatio",'0'))

            from rlextra.pageCatcher.pageCatcher import pdfImageFormDetails, _getAdjustedDimensions

            def findImg(imgfn):
                #bitmap or PDF?
                if imageType=='pdf':
                    ext = '.pdf'
                elif imageType=='bitmap':
                    ext = None
                elif not imageType:
                    ext = os.path.splitext(imgfn)[1].lower()
                else:
                    raise ValueError('invalid value %r for type' % imageType)
                if ext in ('.data','.pdf'):
                    #PDF has five ways to measure size.  sometimes you want "ArtBox"
                    boxType = sdict.get("pdfBoxType", "MediaBox")
                    pageNumber = readInt(sdict.get("pdfPageNumber", "1"),context)-1
                    #it's a PDF or one of our cached values derived from a PDF
                    kind = 'pdf'
                    formName, (mediaX, mediaY,
                            mediaWidth, mediaHeight) = pdfImageFormDetails(self.canv,
                                    imgfn,pageNumber,boxType)
                    from rlextra.pageCatcher.pageCatcher import PDFImageFlowable
                else:
                    from reportlab.lib.utils import ImageReader
                    im = ImageReader(imgfn)
                    mediaWidth, mediaHeight = im.getSize()
                    kind = 'bitmap'

                adjustedX, adjustedY, adjustedWidth, adjustedHeight = _getAdjustedDimensions(
                        0, 0, mediaWidth, mediaHeight,
                        x=0, y=0, width=imageWidth, height=imageHeight,
                        preserveAspectRatio=preserveAspectRatio,
                        anchor='c',
                        )

                return (PDFImageFlowable(imgfn, adjustedWidth, adjustedHeight) if kind=='pdf'
                        else Image(imgfn, adjustedWidth, adjustedHeight, mask=imageMask))
            errs = getStringIO()
            img = None
            for pin in (imageName,None):
                if pin is None:
                    imageType = None    #force reliance on the extension
                    altFileName = sdict.get("alt_file",None)
                    if altFileName is None:
                        pin = context.get('default:image','')
                        if not pin: raise ValueError('<image> file=%r failed and no alt_file or default:image defined' % fileName)
                    else:
                        pin = altFileName
                    if pin.startswith('rml:'):
                        imgfn = context.get(pin[4:].strip(),'')
                        if not imgfn:
                            break
                    else:
                        imgfn = pin
                else:
                    imgfn = pin
                try:
                    img = findImg(imgfn)
                    break
                except:
                    if required:
                        errs.write('\nCannot load image %r\n' % pin)
                        traceback.print_exc(file=errs)
            if not img:
                if required:
                    errs = errs.getvalue()
                    if errs:
                        raise RuntimeError("Image load failure\noriginal tracebacks%s" % errs)
            ImageAndFlowables.__init__(self,
                    img,
                    get_local_story(tagname, sdict, pcontent, extra),
                    imageRightPadding=readLength(sdict.get("imageRightPadding",'3'),context=context),
                    imageLeftPadding=readLength(sdict.get("imageLeftPadding",'0'),context=context),
                    imageTopPadding=readLength(sdict.get("imageTopPadding",'0'),context=context),
                    imageBottomPadding=readLength(sdict.get("imageBottomPadding",'3'),context=context),
                    imageSide=sdict.get("imageSide",'right'),
                    imageHref=imageHref,
                    )

class imageAndFlowables(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_ImageAndFlowables, tagname, sdict, pcontent, extra, context)
Controller["imageAndFlowables"] = imageAndFlowables()

def _safe_issubclass(ob,K):
    try:
        return issubclass(ob,K)
    except TypeError:
        return False

class _ImageFigure(FlexFigure):
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self.kind = None

    def _Initialize(self):
        if self.kind is None:
            tagname, sdict, pcontent, extra, context = self._info
            imageName = sdict["imageName"]
            if imageName.startswith('rml:'):
                imageName = context.get(imageName[4:].strip(),'')
                if not imageName: return
            self.imageName = imageName
            imageWidth = readLength(sdict.get("imageWidth",'0'))
            imageHeight = readLength(sdict.get("imageHeight",'0'))
            #imageMask = readMask(sdict.get('imageMask','auto'),context)
            imageType = sdict.get('imageType', None)
            preserveAspectRatio = readBool(sdict.get("preserveAspectRatio",'0'))
            #showBoundary = readBool(sdict.get("showBoundary",'0'))
            #bitmap or PDF?
            if imageType=='pdf':
                ext = '.pdf'
            elif imageType=='bitmap':
                ext = None
            elif not imageType:
                ext = os.path.splitext(imageName)[1].lower()
            else:
                raise ValueError('invalid value %r for type' % imageType)
            from rlextra.pageCatcher.pageCatcher import pdfImageFormDetails, _getAdjustedDimensions
            if ext in ['.data','.pdf']:
                #PDF has five ways to measure size.  sometimes you want "ArtBox"
                boxType = sdict.get("pdfBoxType", "MediaBox")
                pageNumber = readInt(sdict.get("pdfPageNumber", "1"),context) - 1
                #it's a PDF or one of our cached values derived from a PDF
                self.kind = 'pdf'
                self.formName, (self.mediaX, self.mediaY,
                        self.mediaWidth, self.mediaHeight) = pdfImageFormDetails(self.canv,
                                imageName,pageNumber,boxType)
            else:
                self.kind = 'image'
                from reportlab.lib.utils import ImageReader
                self.im = ImageReader(self.imageName)
                self.mediaWidth, self.mediaHeight = self.im.getSize()
                self.mediaX = self.mediaY = 0
                self.mask = readMask(sdict.get('transparency_mask','auto'),context)
            if not imageWidth: imageWidth=self.mediaWidth
            if not imageHeight: imageHeight=self.mediaHeight
            self.adjustedX, self.adjustedY, self.adjustedWidth, self.adjustedHeight = _getAdjustedDimensions(
                                self.mediaX, self.mediaY, self.mediaWidth, self.mediaHeight,
                                x=0, y=0, width=imageWidth, height=imageHeight,
                                preserveAspectRatio=preserveAspectRatio,
                                anchor='c',
                                )
            shrinkToFit = readBool(sdict.get("shrinkToFit",'0'))
            growToFit = readBool(sdict.get("growToFit",'0'))
            caption = sdict.get('caption','')
            P = pcontent.pop(0) if pcontent and (isinstance(pcontent[0],Paragraph)
                            or _safe_issubclass(getattr(pcontent[0],'klass',None),Paragraph)) else None
            if P:
                if caption:
                    raise ValueError("caption attribute %r specified at same time as a caption paragraph" % caption)
                caption = P.initialize()
            captionColor = readColor(sdict.get('captionColor','black'),context)
            captionFont = sdict.get('captionFont','Helvetica')
            captionSize = readLength(sdict.get('captionSize','10'),context)
            captionGap = readLength(sdict.get('captionGap','9'),context)
            captionAlign = sdict.get('captionAlign','center').lower()
            captionPosition = sdict.get('captionPosition','bottom').lower()
            spaceBefore = readLength(sdict.get('spaceBefore','0'),context)
            spaceAfter = readLength(sdict.get('spaceAfter','0'),context)
            border = sdict.get('showBoundary',None)
            if border: border = readBorder(border,context)
            FlexFigure.__init__(self,
                        self.adjustedWidth, self.adjustedHeight,
                        caption,
                        background=None,
                        captionFont=captionFont,
                        captionSize=captionSize,
                        captionTextColor=captionColor,
                        captionAlign=captionAlign,
                        captionPosition=captionPosition,
                        shrinkToFit=shrinkToFit,
                        growToFit=growToFit,
                        spaceBefore=spaceBefore,
                        spaceAfter=spaceAfter,
                        captionGap=captionGap,
                        hAlign = sdict.get('align','CENTER').upper(),
                        border = border,
                        )

    def getSpaceBefore(self):
        return readLength(self._info[1].get('spaceBefore','0'),self._info[4])

    def getSpaceAfter(self):
        return readLength(self._info[1].get('spaceAfter','0'),self._info[4])

    def wrap(self, aW, aH):
        self._Initialize()
        w,h = FlexFigure.wrap(self,aW,aH)
        self.dx = 0
        return w,h

    def split(self,aW,aH):
        self._Initialize()
        return FlexFigure.split(self,aW,aH)

    def drawFigure(self):
        if self.kind=='image':
            self.canv.drawImage(self.im, 0, 0, self.width, self.figureHeight,mask=self.mask)
        else:
            self.canv.saveState()
            self.canv.translate(self.adjustedX,self.adjustedY)
            self.canv.scale(self.adjustedWidth/float(self.mediaWidth),self.adjustedHeight/float(self.mediaHeight))
            self.canv.doForm(self.formName)
            self.canv.restoreState()

class imageFigure(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_ImageFigure, tagname, sdict, pcontent, extra, context)
Controller["imageFigure"] = imageFigure()

class _Figure(_ImageFigure):
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self.caption = None

    def _Initialize(self):
        if self.caption is None:
            tagname, sdict, pcontent, extra, context = self._info
            caption = sdict.get('caption','')
            P = pcontent.pop(0) if pcontent and (isinstance(pcontent[0],Paragraph)
                            or _safe_issubclass(getattr(pcontent[0],'klass',None),Paragraph)) else None
            if P:
                if caption:
                    raise ValueError("caption attribute %r specified at same time as a caption paragraph" % caption)
                caption = P.initialize()
            D = self._drawing = pcontent.pop(0) if pcontent else None
            shrinkToFit = readBool(sdict.get("shrinkToFit",'0'))
            growToFit = readBool(sdict.get("growToFit",'0'))
            captionColor = readColor(sdict.get('captionColor','black'),context)
            captionFont = sdict.get('captionFont','Helvetica')
            captionSize = readLength(sdict.get('captionSize','10'),context)
            captionGap = readLength(sdict.get('captionGap','9'),context)
            captionAlign = sdict.get('captionAlign','center').lower()
            captionPosition = sdict.get('captionPosition','bottom').lower()
            spaceBefore = readLength(sdict.get('spaceBefore','0'),context)
            spaceAfter = readLength(sdict.get('spaceAfter','0'),context)
            border = sdict.get('showBoundary',None)
            if border: border = readBorder(border,context)
            FlexFigure.__init__(self,
                        D.width, D.height,
                        caption,
                        background=None,
                        captionFont=captionFont,
                        captionSize=captionSize,
                        captionTextColor=captionColor,
                        captionAlign=captionAlign,
                        captionPosition=captionPosition,
                        shrinkToFit=shrinkToFit,
                        growToFit=growToFit,
                        spaceBefore=spaceBefore,
                        spaceAfter=spaceAfter,
                        captionGap=captionGap,
                        hAlign = sdict.get('align','CENTER').upper(),
                        border = border,
                        )

    def drawFigure(self):
        from reportlab.graphics import renderPDF
        renderPDF.draw(self._drawing, self.canv, 0, 0, showBoundary=False)

class Figure(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_Figure, tagname, sdict, pcontent, extra, context)
Controller["figure"] = Figure()

class _BarcodeFlowable(Flowable):
    _fixedWidth = _fixedHeight = True
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self._code = None

    def _Initialize(self):
        if self._code is None:
            tagname, sdict, pcontent, extra, context = self._info
            d = self._d = _getBarcodeDrawing(sdict,context,value=None)
            self.width = d.width
            self.height = d.height

    def wrap(self,aW,aH):
        self._Initialize()
        return self._d.wrap(aW,aH)

    def draw(self):
        self._Initialize()
        self._d.canv = self.canv
        try:
            self._d.draw()
        finally:
            del self._d.canv

    def getSpaceBefore(self):
        return 0

    def getSpaceAfter(self):
        return 0

class BarcodeFlowable(story):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_BarcodeFlowable, tagname, sdict, pcontent, extra, context)
Controller["barCodeFlowable"] = BarcodeFlowable()

class _pto_child(Flowable):
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self.flowables = get_local_story(tagname, sdict, pcontent, extra)
        self.kind = tagname[4:]

class pto_child(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_pto_child, tagname, sdict, pcontent, extra, context)
Controller["pto_trailer"] = pto_child()
Controller["pto_header"] = pto_child()

class _PTO(PTOContainer):
    def __init__(self, tagname, sdict, pcontent, extra, context):
        F = get_local_story(tagname, sdict, pcontent, extra)
        H = T = None
        C = [_ for _ in F if isinstance(_,_pto_child)]
        F = [_ for _ in F if not isinstance(_,_pto_child)]
        for _ in C:
            if _.kind=='trailer': T = _.flowables
            elif _.kind=='header': H = _.flowables
        PTOContainer.__init__(self,F,T,H)

class pto(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return DeferredInitialization(_PTO, tagname, sdict, pcontent, extra, context)
Controller["pto"] = pto()

class drawFlowables:
    def __init__(self, x, y, width, height, pcontent, extra=None, context=None, origin='local', borderDefn=None):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.pcontent, self.extra, self.context, self.origin = pcontent, extra, context, origin
        self.borderDefn = borderDefn
    def __call__(self, canvas, doc):
        origin = self.origin
        if origin != 'local':
            canvas.saveState()
            canvas.resetTransforms()
            if origin=='frame':
                frame = self.context.doc.frame
                canvas.translate(frame._x1,frame._y1)

        if self.borderDefn:
            self.borderDefn.drawOn(canvas,self.x,self.y,self.width,self.height)

        (aW, aH) = (self.width, self.height)
        for flowable in self.pcontent:
            if isinstance(flowable, DeferredInitialization):
                flowable = flowable.initialize() # create the flowable now and get the correct bindings
            (w, h) = flowable.wrapOn(canvas,aW, aH)
            if w<=aW and h<=aH:
                aH = aH-h # room left for next ones
                flowable.drawOn(canvas, self.x, self.y+aH)
            else:
                #content too big for place.  Strictness can be varies
                from reportlab.rl_config import allowTableBoundsErrors
                if allowTableBoundsErrors:
                    pass # we just don't draw the extra stuff
                else:  #fail, telling them which paragraph or whatever bombed and why
                    raise ValueError("not enough room in 'place' for %s. \n (place size: x=%s y=%s width=%s height=%s;  \n offending flowable %s size (%s, %s)" % (
                        repr(self.pcontent),
                        self.x, self.y, self.width, self.height,
                        flowable.identity(), w, h))
        if origin != 'local': canvas.restoreState()

def _saveStateOp(canv,*args):
    canv.saveState()
class saveState(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return _saveStateOp
Controller["saveState"] = saveState()

def _restoreStateOp(canv,*args):
    canv.restoreState()
class restoreState(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return _restoreStateOp
Controller["restoreState"] = restoreState()

class drawString(MapNode):
    """Allow late string conversions in content (for, eg, page
       number or other varying values)"""
    op = "drawString"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        x = readLength(sdict["x"],context=context)
        y = readLength(sdict["y"],context=context)
        kwds = getDrawStringKwds(tagname,sdict,context)
        return delayedDrawString(self.op, x,y,pcontent,**kwds)

class delayedDrawString:
    def __init__(self, op, x, y, stringseq, **kwds):
        self.op = op
        self.x = x
        self.y = y
        self.stringseq = stringseq
        self.kwds = kwds
    def __call__(self, canvas, doc):
        s = "".join(map(asUnicodeEx, self.stringseq))
        #remove tab and newline characters if present; these may have got into someone's
        #RML file through pretty indentation, and will produce an ugly blob.
        s = s.replace("\t","")
        s = s.replace("\r","")
        s = s.replace("\n","")
        getattr(canvas, self.op)(self.x, self.y, s,**self.kwds)
Controller["drawString"] = drawString()

class drawRightString(drawString):
    op = "drawRightString"
Controller["drawRightString"] = drawRightString()

class drawCentredString(drawString):
    op = "drawCentredString"
Controller["drawCentredString"] = drawCentredString()
Controller["drawCenteredString"] = drawCentredString()

class setFont(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        name = sdict["name"]
        size = readLength(sdict["size"],context=context)
        if 'leading' in sdict:
            leading = readLength(sdict["leading"],context=context)
        else:
            leading = None
        def setFontOp(canv, doc, name=name, size=size, leading=leading):
            canv.setFont(name, size, leading)
        return setFontOp
Controller["setFont"] = setFont()

class setFontSize(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        if 'size' in sdict:
            size = readLength(sdict["size"],context=context)
        else:
            size = None
        if 'leading' in sdict:
            leading = readLength(sdict["leading"],context=context)
        else:
            leading = None
        def setFontSizeOp(canv, doc, size=size, leading=leading):
            canv.setFontSize(size, leading)
        return setFontSizeOp
Controller["setFontSize"] = setFontSize()

class stroke(MapNode):
    op = "setStrokeColor"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        width = sdict.get("width",None)
        if width is not None:
            width = readLength(width,context=context)
        def setStrokeOp(canv, doc, colorName=sdict["color"], width=width, context=context, op=self.op):
            color = readColor(colorName,context)
            getattr(canv, op)(color)
            if width is not None:
                getattr(canv,'setLineWidth')(width)
        return setStrokeOp
Controller["stroke"] = stroke()

class fill(stroke):
    op = "setFillColor"
Controller["fill"] = fill()

class rect(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        x = readLength(sdict["x"],context=context)
        y = readLength(sdict["y"],context=context)
        width = readLength(sdict["width"],context=context)
        height = readLength(sdict["height"],context=context)

        destination = sdict.get("destination", None)  #allows internal links
        href = sdict.get("href", None)  #allows external links
        if destination and href:
            raise ValueError("rect cannot have both 'href' and 'destination' set at once!")

        fill = 0
        if "fill" in sdict:
            fill = readBool(sdict["fill"])
        round = 0
        if "round" in sdict:
            round = readLength(sdict["round"],context=context)
        stroke = 1
        if "stroke" in sdict:
            stroke = readBool(sdict["stroke"])

        def rectOp(canv, doc, x=x, y=y,
                   width=width, height=height,
                   fill=fill,
                   stroke=stroke,
                   round=round,
                   context=context,
                   destination=destination,
                   href=href):

            if destination:
                #internal hyperlink
                if destination.startswith('rml:'):
                    destination = context.get(destination[4:].strip(), '')
                canv.linkRect("", destination, Rect=(x,y,x+width,y+height))

            if href:
                if href.startswith('rml:'):
                    href = context.get(href[4:].strip(), '')
                canv.linkURL(href, (x,y,x+width,y+height), relative=1)

            if round:
                canv.roundRect(x,y,width,height,round, fill=fill,stroke=stroke)
            else:
                canv.rect(x,y,width,height,fill=fill,stroke=stroke)

        return rectOp
Controller["rect"] = rect()

class circle(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        x = readLength(sdict["x"],context=context)
        y = readLength(sdict["y"],context=context)
        radius = readLength(sdict["radius"],context=context)
        fill = 0
        if "fill" in sdict:
            fill = readBool(sdict["fill"])
        stroke = 1
        if "stroke" in sdict:
            stroke = readBool(sdict["stroke"])
        def circleOp(canv, doc, x=x, y=y,
                   radius=radius, fill=fill, stroke=stroke):
            canv.circle(x,y,radius,fill=fill, stroke=stroke)
        return circleOp

Controller["circle"] = circle()

class ellipse(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        x = readLength(sdict["x"],context=context)
        y = readLength(sdict["y"],context=context)
        width = readLength(sdict["width"],context=context)
        height = readLength(sdict["height"],context=context)
        fill = 0
        if "fill" in sdict:
            fill = readBool(sdict["fill"])
        stroke = 1
        if "stroke" in sdict:
            stroke = readBool(sdict["stroke"])
        def ellipseOp(canv, doc, x=x, y=y,
                   width=width, height=height, fill=fill, stroke=stroke):
            canv.ellipse(x,y,width,height,fill=fill, stroke=stroke)
        return ellipseOp
Controller["ellipse"] = ellipse()

class textAnnotation(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        content = []
        kw = {}
        for p in pcontent:
            if isinstance(p,tuple):
                if p[0] == 'setParam':
                    _, key, value = p
                    kw[key] = value
                    continue
            content.append(p)
        def taOp(canv,doc):
            canv.textAnnotation(''.join(map(asUnicodeEx,content)),**kw)
        return taOp
Controller["textAnnotation"] = textAnnotation()

class textField(MapNode):
    aMap = {
        'id':(readString,''),
        'value': (readString,''),
        'x': (readLength,'0'),
        'y': (readLength,'0'),
        'width': (readLength,'0'),
        'height': (readLength,'0'),
        'maxlen': (readInt,'100000'),
        'multiline': (readBool,'0'),
        }

    def evaluate(self, tagname, sdict, pcontent, extra, context):
        content = []
        A = {}
        for p in pcontent or []:
            if isinstance(p,tuple):
                if p[0] == 'setParam':
                    _, key, value = p
                    if key in sdict:
                        raise ValueError('textField atttribute %s extra value "%s"' % (key,asUnicodeEx(value)))
                    A[key] = value
                    continue
            content.append(p)
        content = ''.join(map(asUnicodeEx,content))
        if 'value' in A or 'value' in sdict:
            if content.strip():
                raise ValueError('textField atttribute content ambiguous')
        else:
            A['value'] = content

        for key,value in list(self.aMap.items()):
            A[key] = value[0](asUnicodeEx(A.setdefault(key,sdict.setdefault(key,value[1]))),context=context)

        def Op(canv,doc):
            from reportlab.pdfbase.pdfform import textFieldRelative
            textFieldRelative(canv, A['id'],
                    A['x'], A['y'], A['width'], A['height'],
                    A['value'], A['maxlen'], A['multiline'])
        return Op
Controller["textField"] = textField()

class frame(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        id = sdict["id"]
        x1 = sdict["x1"]
        y1 = sdict["y1"]
        width = sdict["width"]
        height = sdict["height"]
        overlapAttachedSpace = sdict.get('overlapAttachedSpace',None)
        if overlapAttachedSpace is not None:
            overlapAttachedSpace = int(overlapAttachedSpace)
        else:
            from reportlab.rl_config import overlapAttachedSpace
        # Wait until we have access to our container's size before creating Frame
        # object so that we can allow percent (%) units for frame dimensions
        return DeferredFrame(id, x1, y1, width, height, overlapAttachedSpace,context)

class DeferredFrame:
    def __init__(self, id, x1, y1, width, height, overlapAttachedSpace,context):
        self._id = id
        self._x1 = x1
        self._y1 = y1
        self._width = width
        self._height = height
        self._oASpace = overlapAttachedSpace
        self._context = context

    def create(self, parentSize):
        x1 = readLength(self._x1, parentSize[0],context=self._context)
        y1 = readLength(self._y1, parentSize[1],context=self._context)
        width = readLength(self._width, parentSize[0],context=self._context)
        height = readLength(self._height, parentSize[1],context=self._context)
        return Frame(x1, y1, width, height, id=self._id,
                     #AR 2000-12-10 - should do this in Platypus?? makes life
                     #much easier positioning frames without boundaries.
                     leftPadding=0, rightPadding=0, topPadding=0,bottomPadding=0, overlapAttachedSpace=self._oASpace)
Controller["frame"] = frame()

#these classes are implemented as do nothings ie they utilize the base MapNode class
for _ in ("stylesheet", "b", "i", "u", "font", "span", "greek",
        "super", "sub", "seq", "seqDefault", "seqReset",
        "seqChain", "seqFormat", "bullet",
        ):
    Controller[_] = Controller[""]
del _

class blockTableStyle(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        id = sdict["id"]
        parentName = sdict.get("parent", None)
        if parentName:
            parent = context[parentName]
        else:
            parent = None

        st = TableStyle(pcontent,parent=parent,keepWithNext=_checkBool(sdict,"keepWithNext",0))
        st.spaceBefore = readLength(sdict.get("spaceBefore", "0"))
        st.spaceAfter = readLength(sdict.get("spaceAfter", "0"))

        context[id] = st
        return st
Controller["blockTableStyle"] = blockTableStyle()

class lineStyle(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        localdict = sdict.copy()
        kind = localdict["kind"]
        thickness = 1
        if "thickness" in localdict:
            thickness = readLength(localdict["thickness"],context=context)
        color = readColor(localdict["colorName"],context)
        (start, stop) = startstop(localdict)
        if "cap" in localdict: cap = capmap[localdict["cap"].lower()]
        else: cap = 'round'
        dash = "dash" in localdict and lengthSequence(localdict["dash"]) or None

        count = int(localdict.get("count","1"))
        if 'space' in localdict:
            space = readLength(localdict["space"],context=context)
        else:
            space = thickness
        return (kind, start, stop, thickness, color, cap, dash, None, count, space)

def _int_or_split(x):
    try:
        return int(x)
    except ValueError:
        if x in ('splitfirst','splitlast'): return x
        raise

def startstop(dict):
    if "start" in dict:
        start = dict["start"]
        start = lengthSequence(start, converter=_int_or_split)
    else:
        start = (0,0)
    if "stop" in dict:
        stop = dict["stop"]
        stop = lengthSequence(stop, converter=_int_or_split)
    else:
        stop = (-1,-1)
    return (start, stop)
Controller["lineStyle"] = lineStyle()

class blockFont(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        fontname = sdict["name"]
        (start, stop) = startstop(sdict)
        result = ["FONT", start, stop, fontname]
        if "size" in sdict:
            result.append(readLength(sdict["size"],context=context))
            if "leading" in sdict:
                result.append(readLength(sdict["leading"],context=context))
        return tuple(result)

Controller["blockFont"] = blockFont()

class blockTextColor(MapNode):
    id = "TEXTCOLOR"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        (start, stop) = startstop(sdict)
        color = readColor(sdict["colorName"],context)
        return (self.id, start, stop, color)

Controller["blockTextColor"] = blockTextColor()

class blockSpan(MapNode):
    id = "SPAN"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        (start, stop) = startstop(sdict)
        return (self.id, start, stop)

Controller["blockSpan"] = blockSpan()

class blockLeading(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        (start, stop) = startstop(sdict)
        length = sdict["length"]
        length = readLength(length,context=context)
        return ("LEADING", start, stop, length)

Controller["blockLeading"] = blockLeading()

class blockAlignment(MapNode):
    # note: if value checking is added need to modify valign too!
    id = "ALIGNMENT"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        (start, stop) = startstop(sdict)
        return (self.id, start, stop, sdict["value"].upper())

Controller["blockAlignment"] = blockAlignment()

class blockValign(blockAlignment):
    id = "VALIGN"

Controller["blockValign"] = blockValign()

class blockLeftPadding(MapNode):
    id = "LEFTPADDING"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        (start, stop) = startstop(sdict)
        length = sdict["length"]
        length = readLength(length,context=context)
        return (self.id, start, stop, length)

Controller["blockLeftPadding"] = blockLeftPadding()

class blockRightPadding(blockLeftPadding):
    id = "RIGHTPADDING"

Controller["blockRightPadding"] = blockRightPadding()

class blockBottomPadding(blockLeftPadding):
    id = "BOTTOMPADDING"

Controller["blockBottomPadding"] = blockBottomPadding()

class blockTopPadding(blockLeftPadding):
    id = "TOPPADDING"

Controller["blockTopPadding"] = blockTopPadding()

#class blockBackground(blockTextColor):
#    id = "BACKGROUND"
#
#
class blockBackground(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        (start, stop) = startstop(sdict)
        if 'colorsByRow' in sdict:
            self.id = 'ROWBACKGROUNDS'
            color = readColorSequence(sdict["colorsByRow"],context)
        elif 'colorsByCol' in sdict:
            self.id = 'COLBACKGROUNDS'
            color = readColorSequence(sdict["colorsByCol"],context)
        else:
            self.id = 'BACKGROUND'
            color = readColor(sdict["colorName"],context)
        return (self.id, start, stop, color)

Controller["blockBackground"] = blockBackground()

def _checkBool(dict,a,d=None):
    if d is not None:
        v = dict.get(a,asUnicodeEx(d))
    else:
        v = dict[a]
    vl = v.lower()
    if vl in ['1','yes','true','on', 'y']: v = 1
    elif vl in ['0','no','false','off', 'n']: v = 0
    else: raise ValueError('Attribute "%s" given invalid value "%s"' % (a,v))
    return v

class paraStyle(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        localdict = {}
        for k,v in list(sdict.items()):
            localdict[asUnicodeEx(k)] = v
        if "parent" in localdict:
            style = context[localdict["parent"]]
            localdict["parent"] = style
        if "name" not in localdict:
            raise ValueError("name required for styles")
        name = localdict["name"]
        # fix attribute types
        for numericatt in ("fontSize", "leading",
                           "leftIndent", "rightIndent",
                           "firstLineIndent", "spaceBefore",
                           "spaceAfter", "bulletFontSize",
                           "bulletIndent", "bulletOffsetY",
                           "borderWidth","borderRadius","borderPadding","endDotsFontSize","endDotsDy"):
            if numericatt in localdict:
                value = localdict[numericatt]
                value = readLength(value,context=context)
                localdict[numericatt] = value
        for a in ['pageBreakBefore','frameBreakBefore','keepWithNext', 'allowWidows', 'allowOrphans']:
            if a in localdict:
                localdict[a] = _checkBool(localdict,a)
        # test
        #localdict["spaceBefore"] = "invalid"
        for colatt in ("textColor","borderColor","backColor","bulletColor","endDotsColor"):
            if colatt in localdict:
                localdict[colatt] = readColor(localdict[colatt],context)
        if "alignment" in localdict:
            localdict["alignment"] = readAlignment(localdict["alignment"])
        if "endDots" in localdict:
            edd = dict([(k,v) for k,v in localdict.items() if k.startswith("endDots")])
            list(map(localdict.pop,iter(edd.keys())))
            t = edd.pop("endDots")
            if edd:
                edd['text'] = t
                t = ABag(**edd)
            localdict["endDots"] = t
        context[name] = ParagraphStyle(**localdict)
        return "" # vanish
Controller["paraStyle"] =  paraStyle()

class pre(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        stylename = "pre.defaultStyle"
        if "style" in sdict:
            stylename = sdict["style"]
        maxLineLength = None
        if "maxLineLength" in sdict:
            ll = sdict["maxLineLength"].lower()
            if ll == 'none':
                maxLineLength = None
            else:
                try:
                    maxLineLength = int(ll)
                except ValueError:
                    pass
        splitChars = None
        if "splitChars" in sdict:
            splitChars = sdict["splitChars"]
        newLineChars = None
        if "newLineChars" in sdict:
            newLineChars = sdict["newLineChars"]
        text = LazyJoin(pcontent)
        style = context[stylename]
        P = LazyPreformatted(text, style, maxLineLength=maxLineLength, splitChars=splitChars, newLineChars=newLineChars)
        return P
Controller["pre"] = pre()

class _LazyMixin:
    """don't do any initialization until wrap time! (allow lazy string conversion)"""
    def __init__(self, text, style, bulletText = None, frags=None):
        self._args = (text, style, bulletText, frags)
        self._initialized = 0

    def __setstate__(self,state):
        self.__dict__.update(state)

    def __getattr__(self,a):
        #Curing excessive laziness...the object may not exist
        #yet, but the packer needs some attributes to pack it right.
        if not self._initialized:
            self._Initialize()
            if a in ('spaceBefore','spaceAfter','keepWithNext'):
                self.__dict__[a] = v = getattr(self,'get'+a.capitalize())()
                return v
            return getattr(self,a)
        raise AttributeError("No attribute '%s'" % a)

    def __str__(self):
        raise ValueError("%s instance has no string conversion method" % self.__class__)

    def _Initialize(self):
        if not self._initialized:
            self.SUPER.__init__(*((self,)+self._args))
            self._initialized = 1
            del self._args

    def wrap(self, availWidth, availHeight):
        self._Initialize()
        return self.SUPER.wrap(self, availWidth, availHeight)

    def split(self,availWidth, availHeight):
        self._Initialize()
        return self.SUPER.split(self, availWidth, availHeight)

from reportlab.platypus.paraparser import ParaParser
_space_re=re.compile(r'\s+')
class TTParser(ParaParser):
    _handle_getName = Controller['getName'].evaluate
    _handle_evalString = Controller['evalString'].evaluate
    _handle_name = Controller['name'].evaluate
    _UNI = 0

    def __init__(self):
        ParaParser.__init__(self)
        self._evs = []

    def start_getName(self,attr):
        self.handle_data(asUnicodeEx(self._handle_getName('getName',attr,[],None,self._rml_context)))
    def start_name(self,attr):
        self.handle_data(asUnicodeEx(self._handle_name('name',attr,[],None,self._rml_context)))
    def start_pageNumber(self,attr):
        self.handle_data(asUnicodeEx(self._rml_context.doc.page))

    def end_getName(self): pass
    end_pageNumber = end_getName
    end_name = end_getName

    def start_evalString(self,attr):
        F = hasattr(self._stack[-1],'isBullet') and self.bFragList or self.fragList
        self._evs.append((attr,len(F),F))

    def end_evalString(self):
        attr, n, F = self._evs.pop()
        content = [x.text for x in F[n:]]
        del F[n:]
        self.handle_data(asUnicodeEx(self._handle_evalString('evalString',attr,content,None,self._rml_context)))

    def handle_data(self,data):
        if self._clean_space:
            data = _space_re.sub(' ',data)
        ParaParser.handle_data(self,data)

    def findSpanStyle(self,style):
        return self._rml_context[style]

def cleanTT(tt):
    return list(tt)

class TTParagraphMixin:
    _CLEAN_SPACE=0
    _parser = TTParser()
    def __init__(self, tt, style, bulletText=None, frags=None, caseSensitive=1, encoding='utf8'):
        self.caseSensitive = caseSensitive
        self.encoding = encoding
        self._setup(tt, style, bulletText or getattr(style,'bulletText',None), frags, cleanTT)

    def _setup(self, tt, style, bulletText, frags, cleaner):
        if frags is None:
            tt = cleaner(tt)
            self._parser.caseSensitive = self.caseSensitive
            self._parser._rml_context = tt[3]
            clean_space = self._parser._clean_space = self._CLEAN_SPACE
            style, frags, bulletTextFrags = self._parser.tt_parse(tt,style)
            textTransformFrags(frags,style)
            if clean_space:
                for f in frags:
                    if f.text or getattr(getattr(f,'cbDefn',None),'width',0):
                        f.text = f.text.lstrip()
                        break
                for i in range(len(frags)-1,-1,-1):
                    f = frags[i]
                    if f.text or getattr(getattr(f,'cbDefn',None),'width',0):
                        f.text = f.text.rstrip()
                        break
            del self._parser._rml_context
            tt[3] = None
            if bulletTextFrags: bulletText = bulletTextFrags
            elif bulletText is not None: bulletText = asUnicodeEx(bulletText).strip()
        self.text = tt
        self.frags = frags
        self.style = style
        self.bulletText = bulletText
        self.debug = 0  #turn this on to see a pretty one with all the margins etc.

    def getPlainText(self,identify=None):
        """Convenience function for templates which want access
        to the raw text, without XML tags. """
        frags = getattr(self,'frags',None)
        if frags:
            plains = []
            for frag in frags:
                if hasattr(frag, 'text'):
                    plains.append(frag.text)
            return ''.join(plains)
        elif identify:
            text = getattr(self,'text',None)
            if text: return text
        return repr(self)

class TTParagraph(TTParagraphMixin,Paragraph):
    pass

class TTXPreformatted(TTParagraphMixin,XPreformatted):
    pass

class LazyParagraph(_LazyMixin,TTParagraph):
    SUPER=TTParagraph
    _CLEAN_SPACE=1

class LazyXPreformatted(_LazyMixin,TTXPreformatted):
    SUPER=TTXPreformatted

def _processPreText(s):
    return u'\n'.join([_.rstrip() for _ in asUnicodeEx(s).split(u'\n')])

class LazyPreformatted(_LazyMixin,Preformatted):
    SUPER=Preformatted
    def __init__(self, text, style, bulletText=None, dedent=0, maxLineLength=None, splitChars=None, newLineChars=None):
        self._initialized = 0
        self._args = (text, style, bulletText, dedent, maxLineLength, splitChars, newLineChars)

    def _Initialize(self):
        if not self._initialized:
            args = list(self._args)
            for i in (0,5): #text & bulletText
                if args[i] is not None: args[i] = _processPreText(args[i])
            # store it, (in case of rewrap
            self._args = args = tuple(args)
            self.SUPER.__init__(*((self,)+args))
            self._initialized = 1

class para(MapNode):
    SUPER = LazyParagraph
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        localdict = sdict.copy()
        stylename = "para.defaultStyle"
        if "style" in localdict:
            stylename = localdict["style"]
            del localdict["style"]
        bulletText = None
        if "bulletText" in localdict:
            bulletText = localdict["bulletText"]
            del localdict["bulletText"]
        return DeferredInitialization(self.SUPER, ('para',localdict,pcontent,context), context[stylename], bulletText=bulletText)

    def MyProcessContent(self, content, controller, context, overrides):
        return content  #tuple tree parser now in place
Controller["para"] = para()

class xpre(para):
    SUPER = LazyXPreformatted
Controller["xpre"] = xpre()

class PlaceFlowableMixin:
    _ZEROSIZE=1
    def drawOn(self,canv,x,y,_sW=0):
        px = self.placeX
        py = self.placeY
        anchor = self.placeAnchor
        if anchor in ('nw','n','ne'):       #top of first line
            py -= self.height
        elif anchor in ('nwl','nl','nel'):  #base of first line
            py -= self.height
        elif anchor in ('nwb','nb','neb'):  #bottom of first line
            py -= self.height
        elif anchor in ('w','c','e'):
            py -= 0.5*self.height
        elif anchor in ('swt','st','set'):  #top of last line
            py -= self.getDescent(-1)
        elif anchor in ('swb','sb','seb'):  #base of last line
            py -= self.getDescent(-1)
        elif anchor in ('sw','s','se'):
            pass
        if anchor in ('n','nl','nb','c','s','st','sb'):
            px -= 0.5*self.width
        elif anchor in ('ne','nel','neb','e','eb','set','seb','se'):
            px -= self.width
        origin = self.placeOrigin

        if origin != 'local':
            canv.saveState()
            canv.resetTransforms()
            if origin=='frame':
                frame = self.placeContext.doc.frame
                canv.translate(frame._x1,frame._y1)
        self.SUPER.drawOn(self,canv,px,py,_sW=0)
        if origin != 'local': canv.restoreState()

    def wrap(self,*args,**kwds):
        self.wrappedWidth, self.wrappedHeight = self.SUPER.wrap(self,self.placeWidth,0x7fffffff)
        return 0,0

class LazyPlaceParagraph(PlaceFlowableMixin,LazyParagraph):
    pass

class LazyPlaceXPreformatted(PlaceFlowableMixin,LazyXPreformatted):
    pass

class DeferredInitializationEx(DeferredInitialization):
    """DeferredInitialization with extra attributes set on instance after creation"""
    def __init__(self, klass, extraAttrs, *args, **kw):
        DeferredInitialization.__init__(self,klass,*args,**kw)
        self.extraAttrs = extraAttrs

    def initialize(self):
        i = DeferredInitialization.initialize(self)
        i.__dict__.update(self.extraAttrs)
        return i

class placePara(MapNode):
    SUPER = LazyPlaceParagraph
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        localdict = sdict.copy()
        stylename = "para.defaultStyle"
        if "style" in localdict:
            stylename = localdict["style"]
            del localdict["style"]
        bulletText = None
        if "bulletText" in localdict:
            bulletText = localdict["bulletText"]
            del localdict["bulletText"]
        extraAttrs = dict(
                        placeX = readLength(localdict.pop('x'),context),
                        placeY = readLength(localdict.pop('y'),context),
                        placeWidth = readLength(localdict.pop('width','0'),context),
                        placeOrigin = localdict.pop('origin','page'),
                        placeAnchor = localdict.pop('anchor','sw'),
                        placeContext = context,
                        )
        return DeferredInitializationEx(self.SUPER, extraAttrs, ('para',localdict,pcontent,context), context[stylename], bulletText=bulletText)

    def MyProcessContent(self, content, controller, context, overrides):
        return content  #tuple tree parser now in place
Controller["placePara"] = placePara()

class placeXPre(placePara):
    SUPER = LazyPlaceXPreformatted
Controller["placeXPre"] = placeXPre()

class codesnippet(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        stylename = "pre.defaultStyle"
        if "style" in sdict:
            stylename = sdict["style"]
        language = sdict.get("language", None)

        maxLineLength = None
        if "maxLineLength" in sdict:
            ll = sdict["maxLineLength"].lower()
            if ll == 'none':
                maxLineLength = None
            else:
                maxLineLength = int(ll)

        splitChars = None
        if "splitChars" in sdict:
            splitChars = sdict["splitChars"]

        newLineChars = None
        if "newLineChars" in sdict:
            newLineChars = sdict["newLineChars"]

        #clean up the block of code prior to display.

        src = ''.join(map(asUnicodeEx, pcontent))
        #split line ends, strip trailing space

        lines = [x.rstrip() for x in src.split('\n')]
        #generally we trim off up to one leading and trailing blank lines
        #that's probably from indenting the XML
        if lines[0] == '':
            lines = lines[1:]
        if lines[-1] == '':
            lines = lines[:-1]

        if maxLineLength is not None and not src == '':
            lines = reportlab.platypus.flowables.splitLines(lines, maxLineLength, splitChars, newLineChars)

        #strip off consistent whitespace on the left
        dedent = None
        for line in lines:
            spaces = len(line) - len(line.lstrip())
            if dedent is None:
                dedent = spaces
            else:
                dedent = min(dedent, spaces)
        if dedent:
            for i in range(len(lines)):
                lines[i] = lines[i][dedent:]

        text = '\n'.join(lines)

        #this uses Pygments if available
        from xml.sax.saxutils import escape
        if language:
            from reportlab.lib.pygments2xpre import pygments2xpre
            coloured = pygments2xpre(text, language=language)
            if coloured is text:
                coloured = escape(text)
        else:
            coloured = escape(text)

        style = context[stylename]
        return XPreformatted(coloured, style) #, maximumLineLength=maxLineLength, splitCharacters=splitChars, newLineCharacter=newLineChars)
Controller["codesnippet"] = codesnippet()

class hr(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        dash = sdict.get('dash',None)
        if dash: dash = lengthSequence(dash)
        return HRFlowable(
                        width=readLength(sdict.get('width','80%'),"%",context=context),
                        thickness=readLength(sdict.get('thickness','1'),context=context),
                        lineCap=sdict.get('lineCap','round'),
                        color=readColor(sdict.get('color','lightgrey'),context=context),
                        hAlign=readAlignment(sdict.get('align','centre')),
                        spaceBefore=readLength(sdict.get('spaceBefore','1'),context=context),
                        spaceAfter=readLength(sdict.get('spaceAfter','1'),context=context),
                        dash = dash,
                        )
Controller["hr"] = hr()

class h1(para):
    def __init__(self, defaultStyle="h1.defaultStyle"):
        para.__init__(self)
        self.defaultStyle = defaultStyle
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        # sdict should be empty: reset it
        sdict = {"style": self.defaultStyle }
        return para.evaluate(self, tagname, sdict, pcontent, extra, context)

Controller["h1"] = h1()
Controller["h2"] = h1("h2.defaultStyle")
Controller["h3"] = h1("h3.defaultStyle")
Controller["h4"] = h1("h4.defaultStyle")
Controller["h5"] = h1("h5.defaultStyle")
Controller["h6"] = h1("h6.defaultStyle")
Controller["title"] = h1("title.defaultStyle")

class listStyle(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        D = sdict.copy()
        if "parent" in D:
            D["parent"] = context[D["parent"]]
        if "name" not in D:
            raise ValueError("name required for styles")
        name = D["name"]
        D['leftIndent'] = readLength(D.get('leftIndent','18pt'), percentTotal=None, context=context)
        D['rightIndent'] = readLength(D.get('rightIndent','0'), percentTotal=None, context=context)
        if 'spaceBefore' in D:
            D['spaceBefore'] = readLength(D['spaceBefore'], percentTotal=None, context=context)
        if 'spaceAfter' in D:
            D['spaceAfter'] = readLength(D['spaceAfter'], percentTotal=None, context=context)
        D['bulletColor'] = readColor(D.get('bulletColor','black'), context=context)
        D['bulletFontSize'] = readLength(D.get('bulletFontSize','12'), percentTotal=None, context=context)
        bd = D.get('bulletDedent','auto')
        if bd!='auto':
            bd = readLength(bd, percentTotal=None, context=context)
        D['bulletDedent'] = bd
        D['bulletOffsetY'] = readLength(D.get('bulletOffsetY','0'), percentTotal=None, context=context)
        D['bulletAlign'] = readAlignL(D.get('bulletAlign','left'),context=context)
        D['bulletFormat'] = D.get('bulletFormat',None)
        D['bulletDir'] = D.get('bulletDir','ltr')
        D['bulletType'] = D.get('bulletType','1')
        D['bulletFontName'] = D.get('bulletFontName','Helvetica')
        D['start'] = D.get('start',None)
        context[name] = ListStyle(**D)
        return "" # vanish
Controller["listStyle"] =  listStyle()

def readBulletDir(a,context=None):
    s = readString(a,context=context)
    if s not in ('ltr','rtl'):
        raise ValueError('bulletDir, %r is not ltr or rtl' % s)
    return s

_listMA=[
    ('style',readString),
    ('leftIndent',readLength),
    ('rightIndent',readLength),
    ('spaceBefore',readLength),
    ('spaceAfter',readLength),
    ('bulletAlign',readAlignL),
    ('bulletType',readString),
    ('bulletColor',readColor),
    ('bulletFontName',readString),
    ('bulletFontSize',readLength),
    ('bulletOffsetY',readLength),
    ('bulletDedent',readLength),
    ('bulletDir',readBulletDir),
    ('bulletFormat',readString)
    ]
def _getListMAD(sdict,context,notAllowed=[],thing='ol',defaults={}):
    D = {}
    for k,func in _listMA:
        if k in sdict:
            if k in notAllowed:
                raise ValueError('attribute %s not allowed in %s' % (k,thing))
            v = sdict[k]
        elif k in defaults:
            v = defaults[k]
        else:
            continue
        D[k] = func(v,context=context)
    return D

class DeferredList(DeferredInitialization):
    def __init__(self, kind, data, params, context):
        self.kind = kind
        self.data = data
        self.params = params
        style = params.pop('style',None)
        if style:
            style = context[style]
        self.style = style

    def initialize(self):
        params = self.params
        start = params.pop('start',1)
        F = []
        Fextend = F.extend
        for f in self.data:
            if isinstance(f, DeferredInitialization):
                d = f.initialize()
            else:
                d = f
            if not isinstance(d,list):
                d = [d]
            Fextend(d)
        return ListFlowable(F,start,self.style,**params)

class ol(NoWhiteContentMixin,MapNode):
    @staticmethod
    def _getStart(sdict,context):
        bv = sdict.get('start',None)
        if bv:
            bv = readString(bv,context=context)
        else:
            bv = None
        return bv
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        D = _getListMAD(sdict,context)
        D.setdefault('bulletType','1')
        if D.get('bulletType',None)=="bullet":
            raise ValueError('ol disallows bulletType="bullet"')
        D['start'] = self._getStart(sdict,context)
        return DeferredList('ol',pcontent,D,context)
Controller["ol"] = ol()

class ul(ol):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        D = _getListMAD(sdict,context)
        D.setdefault('bulletType','bullet')
        if D['bulletType']!='bullet':
            raise ValueError('ul requires bulletType="bullet"')
        D['start'] = self._getStart(sdict,context)
        return DeferredList('ul',pcontent,D,context)
Controller["ul"] = ul()

class DeferredLI(DeferredInitialization):
    def __init__(self, data, params):
        self.data = data
        self.params = params

    def initialize(self):
        return ListItem(flatten([isinstance(f, DeferredInitialization) and f.initialize() or f for f in self.data]),**self.params)

class li(NoWhiteContentMixin,MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        D = _getListMAD(sdict,context,thing='li')
        if 'value' in sdict:
            D['value'] = sdict.get('value',None)
        style = D.pop('style',None)
        if style:
            D['style'] = context[style]
        return DeferredLI(pcontent,D)
Controller["li"] = li()

class DeferredDL(DeferredInitialization):
    def __init__(self,indents,data):
        self.indents = indents
        self.data = data

    def initialize(self):
        R = [].extend
        left, right = self.indents
        for tag, C in self.data:
            if not C: continue
            C = flatten([isinstance(c, DeferredInitialization) and c.initialize() or c for c in C])
            if tag=='dd':
                C = [DDIndenter(c,left,right) for c in C]
            R(C)
        R = R.__self__
        return R

class dl(NoWhiteContentMixin,MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        ddLeftIndent = readLength(sdict.get('ddLeftIndent','12'),context=context)
        ddRightIndent = readLength(sdict.get('ddRightIndent','0'),context=context)
        return DeferredDL((ddLeftIndent,ddRightIndent),pcontent)
Controller["dl"] = dl()

class dt(NoWhiteContentMixin,MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return (tagname,pcontent)
Controller["dt"] = dt()
Controller["dd"] = dt()

class blockTable(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        #first content element MIGHT be a style; is so we
        #use it, if not we may look for a style in the context.
        if len(pcontent) > 0 and isinstance(pcontent[0], TableStyle):
            data = pcontent[1:]
            style = pcontent[0]
        elif "style" in sdict:
            data = pcontent
            stylename = sdict["style"]
            style = context[stylename]
        else:
            style = None
            data = pcontent

        #if the new first element is bulkData, grab its output as the
        #data; otherwise pcontent is just the data - a collection of
        #rows and cells which have done parsing themselves already.
        if len(pcontent) > 0 and isinstance(pcontent[0], BulkDataHolder):
            data = pcontent[0].value

        colWidths = None
        rowHeights = None
        splitByRow = 1
        repeatRows = 0
        repeatCols = 0
        # ... now change the defaults
        if "colWidths" in sdict:
            colWidths = sdict["colWidths"]
            colWidths = lengthSequence(colWidths,converter=lambda x,context=context: readLengthOrNone(x,percentTotal='%',context=context))
        if "rowHeights" in sdict:
            rowHeights = sdict["rowHeights"]
            rowHeights = lengthSequence(rowHeights,converter=lambda x,context=context: readLengthOrNone(x,percentTotal='%',context=context))
        if "splitByRow" in sdict:
            splitByRow = int(sdict["splitByRow"])
        if "repeatRows" in sdict:
            repeatRows = sdict["repeatRows"]
            try:
                repeatRows = int(repeatRows)
            except ValueError:
                try:
                    repeatRows = eval(repeatRows,{},context)
                except:
                    raise ValueError('invalid repeatRows=%r' % repeatRows)
        if "repeatCols" in sdict:
            repeatCols = int(sdict["repeatCols"])
        xkw = {}
        if "spaceBefore" in sdict:
            xkw['spaceBefore'] = readLength(sdict.get("spaceBefore", "0"))
        if "spaceAfter" in sdict:
            xkw['spaceAfter'] = readLength(sdict.get("spaceAfter", "0"))
        if "rowSplitRange" in sdict:
            def rowSplitRangeError():
                raise ValueError("invalid value %r for rowSplitRange" % sdict["rowSplitRange"])
            try:
                v = lengthSequence(sdict["rowSplitRange"],int)
            except:
                rowSplitRangeError()
            if len(v)==1:
                v.append(-1)
            elif len(v)>2:
                rowSplitRangeError()
            xkw['rowSplitRange'] = v
        htmlSpans = readBool(sdict.get('htmlSpans','0'),context)
        ident = sdict.get('ident',None)
        # XXXXXXX
        # make a default widths, if none specified # THIS IS HACKED BIGTIME!!! MUST BE DONE LAZILY!!!
        if 0 and data and style is None:
            ncols = len(data[0])
            pagewidth = context.pageSize[0]
            # TOTAL HACK!
            usewidth = pagewidth/2.0
            eachwidth = usewidth/ncols
            colWidths = [eachwidth]*ncols
        T = DeferredTable(data=data,htmlSpans=htmlSpans,
                    colWidths=colWidths, rowHeights=rowHeights,
                    style=style, splitByRow=splitByRow,
                    repeatRows=repeatRows, repeatCols=repeatCols,
                    hAlign=sdict.get('align',None),
                    vAlign=sdict.get('vAlign',None),
                    ident=ident,
                    **xkw)
        #context.story.append(T)
        return T

class StyledTD:
    def __init__(self,value,style_cmds,span_cmds):
        self.value = value
        self.style_cmds = style_cmds
        self.span_cmds = span_cmds

class DeferredTable(DeferredInitialization):
    klass = [xTable] # for debugging
    def __init__(self, data, htmlSpans, *args, **kw):
        self.data = data
        self.htmlSpans = htmlSpans
        self.args = args
        self.kw = kw

    def initialize(self):
        data = self.data
        htmlSpans = self.htmlSpans
        dataout = []
        dataout_append = dataout.append
        cmds = []
        cmds_append = cmds.append
        for i,row in enumerate(data):
            rowout = []
            rowout_append = rowout.append
            noSplitRowCount = getattr(row,'noSplitRowCount',0)
            if noSplitRowCount>1:
                cmds_append(('NOSPLIT',(0,i),(0,i+noSplitRowCount-1)))
            j = 0
            while j<len(row):
                datum = row[j]
                if isinstance(datum,StyledTD):
                    ij = (j,i)
                    IJ = ij, ij
                    for cmd in datum.style_cmds:
                        cmds_append((cmd[0],)+IJ+tuple(cmd[1:]))
                    sc = 0
                    sr = 0
                    for cmd in datum.span_cmds:
                        sc=max(cmd[1],sc)
                        sr=max(cmd[2],sr)
                        cmds_append((cmd[0],)+(ij,(j+cmd[1],i+cmd[2])))
                    if htmlSpans and (sr or sc):
                        sr += 1
                        sc += 1
                        for si in range(sr):
                            srow = data[i+si]
                            sj = int(not si)
                            srow[j+sj:j+sj] = (sc-sj)*['']
                    datum = datum.value
                if isinstance(datum,list):
                    #list of flowables
                    outdatum = []
                    for thing in datum:
                        if isinstance(thing, DeferredInitialization):
                            thing = thing.initialize()
                        outdatum.append(thing)
                    datum = outdatum
                elif isinstance(datum, DeferredInitialization):
                    #single deferred flowable
                    datum = datum.initialize()
                #else simple string
                rowout_append(datum)
                j += 1
            dataout_append(rowout)
        kw = self.kw
        if cmds:
            S = kw.get('style',None)
            kw['style'] = TableStyle(cmds,parent=S)
        T = xTable(*((dataout,)+tuple(self.args)), **kw)
        return T
Controller["blockTable"] = blockTable()

class _TR(list):
    def __init__(self,pcontent,sdict,context):
        list.__init__(self,pcontent)
        s = sdict.get('noSplitRowCount',0)
        try:
            i = int(s)
            if i<0: raise ValueError
        except:
            raise ValueError('Illegal value %r for noSplitRows' % i)
        self.noSplitRowCount = i
class tr(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        # just return the row itself
        return _TR(pcontent,sdict,context)
Controller["tr"] = tr()

def readCap(s,context):
    return capmap[s.lower()]
_tdAMap = {
    'fontName': ('FACE',readString),
    'fontSize': ('SIZE',readLength),
    'fontColor': ('TEXTCOLOR',readColor),
    'leading': ('LEADING',readLength),
    'leftPadding': ('LEFTPADDING',readLength),
    'rightPadding': ('RIGHTPADDING',readLength),
    'topPadding': ('TOPPADDING',readLength),
    'bottomPadding': ('BOTTOMPADDING',readLength),
    'background': ('BACKGROUND',readColor),
    'align': ('ALIGN',readAlignU),
    'vAlign': ('VALIGN',readvAlignU),
    'noSplitRows': ('NOSPLIT',readInt),
    'lineBelowThickness': ('LINEBELOW',(readLength,3)),
    'lineBelowColor': ('LINEBELOW',(readColor,4)),
    'lineBelowCap': ('LINEBELOW',(readCap,5)),
    'lineBelowCount': ('LINEBELOW',(readInt,8)),
    'lineBelowSpace': ('LINEBELOW',(readLength,9)),
    'lineAboveThickness': ('LINEABOVE',(readLength,3)),
    'lineAboveColor': ('LINEABOVE',(readColor,4)),
    'lineAboveCap': ('LINEABOVE',(readCap,5)),
    'lineAboveCount': ('LINEABOVE',(readInt,8)),
    'lineAboveSpace': ('LINEABOVE',(readLength,9)),
    'lineLeftThickness': ('LINEBEFORE',(readLength,3)),
    'lineLeftColor': ('LINEBEFORE',(readColor,4)),
    'lineLeftCap': ('LINEBEFORE',(readCap,5)),
    'lineLeftCount': ('LINEBEFORE',(readInt,8)),
    'lineLeftSpace': ('LINEBEFORE',(readLength,9)),
    'lineRightThickness': ('LINEAFTER',(readLength,3)),
    'lineRightColor': ('LINEAFTER',(readColor,4)),
    'lineRightCap': ('LINEAFTER',(readCap,5)),
    'lineRightCount': ('LINEAFTER',(readInt,8)),
    'lineRightSpace': ('LINEAFTER',(readLength,9)),
    'href': ('HREF',readString),
    'destination': ('DESTINATION',readString),
    'colspan': ('SPAN',readInt),
    'rowspan': ('SPAN',readInt),
    }

class td(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        # clean out the pcontent
        # STRIP ANY STRINGS

        L = []
        #for now only support either a sequence of (lazy) strings or a single flowable
        hasFlowable = hasLazyString = None
        if pcontent is not None:  #can happen with <td/>
            for x in flatten(pcontent):
                if isinstance(x, Flowable) or isinstance(x, DeferredInitialization): hasFlowable = 1
                elif isinstance(x, LazyStringForm): hasLazyString = 1
                elif isinstance(x,strTypes):
                    hasLazyString = 1
                    x = x.strip()
                L.append(x)
        lenL = len(L)
        if lenL==1: L = L[0]
        elif lenL==0: L = ""
        if hasLazyString:
            if hasFlowable: raise ValueError("<td>cell tag cannot include both strings and flowables: "+repr(L))
            #strings only
            if lenL>1: L = LazyJoin(L)
        if sdict:
            #we have local attributes
            cmds = []
            a = cmds.append
            span_cmds = []
            b = span_cmds.append
            lc = {}
            for k, v in list(sdict.items()):
                K, f = _tdAMap[k]
                if K.startswith('LINE'):
                    x = f[1]
                    f = f[0]
                    lc.setdefault(K,10*[None])[x] = f(v,context=context)
                elif K.startswith('SPAN'):
                    n = f(v,context=context)-1
                    if k.startswith('col'):
                        b((K,n,0))
                    else:
                        b((K,0,n))
                else:
                    a((K,f(v,context=context)))
            for K,v in list(lc.items()):
                a((K,)+tuple(v[3:]))
            L = StyledTD(L,cmds,span_cmds)
        return L
Controller["td"] = td()

class topPadder(NoWhiteContentMixin, MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        if pcontent is None:
            raise ValueError('topPadder with no content is not allowed')
        if len(pcontent)>1:
            raise ValueError('topPadder can only have one element')
        x = pcontent[0]
        if isinstance(x, Flowable) or isinstance(x, DeferredInitialization):
            if isinstance(x, DeferredInitialization): x = x.initialize()
        else:
            raise ValueError('topPadder can only have one flowable element')
        return TopPadder(x)
Controller["topPadder"] = topPadder()

class BulkDataHolder:
    def __init__(self, value):
        self.value = value

class bulkDataParser(MapNode):
    "This holds field and row separated data to save tr/td tags"
    def evaluate(self, tagname, sdict, pcontent, extra, context):

        stripBlock = (sdict.get("stripBlock","yes") != "no")
        stripRows = (sdict.get("stripRows","yes") != "no")
        stripFields = (sdict.get("stripFields","no") != "no")

        fieldDelim = sdict.get("fieldDelim", ",")
        #allow escaped tabs
        if fieldDelim == '\\t':
            fieldDelim = '\t'

        rowDelim = sdict.get("rowDelim", "\n")

        if stripBlock:
            raw = pcontent[0].strip()
        else:
            raw = pcontent[0]
        lines = raw.split(rowDelim)
        output = []
        for line in lines:
            if stripRows:
                line = line.strip()
            row = line.split(fieldDelim)
            if stripFields:
                row = [x.strip() for x in row]
            output.append(row)
        #we return the data wrapper, so that the enclosing table can
        #look for a bulkData object and not a list, which is a bit
        #ambiguous.
        return BulkDataHolder(output)
Controller["bulkData"] = bulkDataParser()

class ExcelDataHolder(BulkDataHolder): pass

class excelDataParser(MapNode):
    "This holds field and row separated data to save tr/td tags"
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        from rlextra.rml2pdf import readxls

        fileName = sdict["fileName"]
        sheetName = sdict["sheetName"]
        rangeSpec = sdict.get("range")
        rangeName = sdict.get("rangeName")

        output = readxls.extract(fileName, sheetName, rangeSpec, rangeName)
        #we return the data wrapper, so that the enclosing table can
        #look for a bulkData object and not a list, which is a bit
        #ambiguous.
        return ExcelDataHolder(output)
Controller["excelData"] = excelDataParser()

class spacer(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        length = readLength(sdict["length"],context=context)
        width = 1
        if "width" in sdict:
            width = readLength(sdict["width"],context=context)
        return Spacer(width, length, isGlue = readLength(sdict.get("isGlue","0"),context=context))
Controller["spacer"] = spacer()

class condPageBreak(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        length = readLength(sdict["height"],context=context)
        p = CondPageBreak(length)
        p._suppressFirst = readBool(sdict.get("suppressFirst",'0'))
        return p
Controller["condPageBreak"] = condPageBreak()

###########################################################################
# Form and bar code widgets and support
###########################################################################

def _parseBorderSpecValue(spec,v,context=None):
    v = v.strip()
    if not v: return 0,0
    s = v.split('%')
    def error(v=v,spec=spec):
        raise ValueError('Bad value "%s" in borderSpec "%s"' % (v, spec))
    if len(s)>2: error()
    if len(s)>1:
        m = readLength(s[0]+'%',percentTotal=1.)
    else:
        s = v.split('*')
        if len(s)>2: error()
        if len(s)>1:
            m = readLength(s[0])
        else:
            m = 0
    a = readLength(s[-1])
    return m,a

def _parseBorderSpec(s,specs=('under','over','left','right'),context=None):
    '''Parser for border spec
    We allow
    none/normal --> None
    else {} containing key value pairs
    under[=low,hi]
    over[=low,hi]
    left[=low,hi]
    right[=low,hi]
    '''
    if not s: return None
    s = asUnicode(s).lower().strip()
    if s in ('none','normal'): return None
    D = {}
    for spec in s.split():
        V = spec.split('=')
        K = V[0]
        if K not in specs: raise ValueError('bad borderSpec key "%s" not in %s' % (spec,specs))
        if len(V)>2: raise ValueError('bad borderSpec "%s"' % spec)
        if len(V)==1: v = ((0,0),(0,0))
        else:
            lohi = [_.strip() for _ in asUnicodeEx(V[1]).split(u',')]
            if len(lohi)!=2: raise ValueError('bad borderSpec "%s" value "%s" needs two items' % (spec,V[1]))
            v = _parseBorderSpecValue(spec,lohi[0]), _parseBorderSpecValue(spec,lohi[1],context=context)
        D[K] = v
    return D

def _renderBorderSpec(canv, stroke, fill, x, y, boxWidth, boxHeight, borderSpec=None):
    if not (stroke or fill): return
    if not borderSpec:
        canv.rect(x, y, boxWidth, boxHeight, stroke=stroke, fill=fill)
    else:
        if fill: canv.rect(x, y, boxWidth, boxHeight, stroke=0, fill=fill)
        if not stroke: return
        for k, v in list(borderSpec.items()):
            if k in ('under', 'over'):
                x0 = v[0][0]*boxWidth+v[0][1]+x
                x1 = v[1][0]*boxWidth+v[1][1]+x+boxWidth
                if k=='under': y0 = y1 = y
                else: y0 = y1 = y+boxHeight
            elif k in ('left', 'right'):
                y0 = v[0][0]*boxHeight+v[0][1]+y
                y1 = v[1][0]*boxHeight+v[1][1]+y+boxHeight
                if k=='left': x0 = x1 = x
                else: x0 = x1 = x+boxWidth
            else:
                raise ValueError('Bad borderSpec '+repr(borderSpec))
            canv.line(x0, y0, x1, y1)

class BoxStyle(PropertySet):
    "Attribute collection used in form elements like checkboxes etc."

    defaults = {
        'fontName':'Courier-Bold',
        'fontSize':10,
        'alignment':TA_LEFT,
        'textColor':black,
        'labelFontName':'Times-Roman',
        'labelFontSize':8,
        'labelAlignment':TA_LEFT,
        'labelTextColor':black,
        'labelOffsetX':0,
        'labelOffsetY':0.2*cm,
        'fillColor':white,
        'strokeColor':black,
        'cellWidth':0.5*cm,
        'cellHeight':0.5*cm,
        'borderSpec': None,
        }

    def fromStringDict(self, strDict, context):
        "converts string data to numbers, colors etc."
        # a big help when parsing...
        # not that if propertySet had some of th behavior
        # of the validators in graphics, we would
        # not even need this and propertySet could infer
        # it from a type catalog.

        # if it is not a string, assume parsed already and pass
        # through; RML handles color names separately
        for (key, strValue) in list(strDict.items()):
            if key in ("name", "parent"):
                # we already have those two form construction
                continue
            elif not isinstance(key,strTypes):
                value = strValue
            elif key in ("fontSize",
                        "labelFontSize",
                        "cellWidth",
                        "cellHeight",
                        "labelOffsetX",
                        "labelOffsetY",
                        ):
                value = readLength(strValue,context=context)
            elif key in ("textColor","labelTextColor", "boxFillColor", "boxStrokeColor"):
                value = readColor(strValue,context)
            elif key in ("alignment",):
                value = readAlignment(strValue,context)
            elif key in ("borderSpec",):
                value = _parseBorderSpec(strValue,context)
            else:
                value = strValue
            setattr(self, key, value)

class boxStyle(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        # need the parent if there is one
        if "parent" in sdict:
            parentStyle = context[sdict["parent"]]
        else:
            parentStyle = None

        if "name" not in sdict:
            raise ValueError("name required for styles")
        styleName = sdict["name"]

        newstyle = BoxStyle(name=styleName, parent=parentStyle)
        newstyle.fromStringDict(sdict, context)

        context[styleName] = newstyle
        return "" # vanish
Controller["boxStyle"] =  boxStyle()

def _getBarcodeDrawing(sdict,context, value=None):
    code = sdict["code"]
    from reportlab.graphics.shapes import Drawing
    params = {}
    for k,func in dict(
                value=readString,
                fontName=readString,
                tracking=readString,
                routing=readString,
                barStrokeColor=readColor,
                barFillColor=readColor,
                textColor=readColor,
                ratio = readFloat,
                barStrokeWidth=readLength,
                gap=readLength,
                bearers=readLength,
                barHeight=readLength,
                barWidth=readLength,
                fontSize=readLength,
                spaceWidth=readLength,
                widthSize=readLength,
                heightSize=readLength,
                checksum=readInt,
                quiet=readBool,
                lquiet=readBool,
                rquiet=readBool,
                humanReadable=readBool,
                stop=readBool,
                ).items():
        if k in sdict:
            params[k] = func(sdict[k],context)
    if value:
        if params.get('value'):
            raise ValueError("Barcodes must use either the attribute or content, nit both!")
        else:
            params['value'] = value

    #find the correct widget to draw it with
    #from reportlab.graphics.barcode import widgets as BCW
    #w = getattr(BCW,'Barcode'+code)(**params)
    from reportlab.graphics import barcode
    barcodes = barcode.getCodes()  #code to class mapping
    w = barcodes[code](**params)  #create the widget
    b = w.getBounds()
    w.x = -b[0]
    w.y = -b[1]
    d = Drawing(b[2]-b[0],b[3]-b[1])
    d.add(w)
    return d

class barCode(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):

        def barCodeOp(canv, doc, sdict=sdict, pcontent=pcontent, context=context):
            x = readLength(sdict["x"],context=context)
            y = readLength(sdict["y"],context=context)
            d = _getBarcodeDrawing(sdict,context,asUnicodeEx(joinflatten(pcontent)))
            d.drawOn(canv, x, y)

        return barCodeOp
Controller['barCode'] = barCode()

def extractStyledAttributes(sdict, attrMap, context):
    """Helper for the three box objects.

    The attribute map defines type conversions
    and defaults.  It first sees if the object
    has a 'style' attribute, and if so it looks
    up the style object.  All properties are
    then gathered in a new dictionary which
    gives priority to (1) the tag, (2) the
    associated style if any, and (3) attrMap
    defaults."""

    #is there a style name? if so, get the style object.
    if "style" in sdict:
        styleName = sdict["style"]
        if styleName == '':
            style = None
        else:
            try:
                style = context[styleName]
                assert isinstance(style, BoxStyle), "LetterBox object has a style '%s' which is not a BoxStyle" % style.name
            except KeyError:
                style = None
    else:
        style = None

    # gather up the data into a dictionary.
    # try object, then style, then default.  This
    # could be in a subroutine.
    d = {}
    for (attrName, readerFunc, default) in attrMap:
        try:
            value = readerFunc(sdict[attrName],context=context)
        except TypeError:
            print(readerFunc)
            raise
        except KeyError:
            if style is None:
                value = default
            else:
                try:
                    value = getattr(style, attrName)
                except AttributeError:
                    value = default

        d[attrName] = value

    return d

class textBox(MapNode):
    """A textbox with multi-line text, possibly shrinked to fit."""
    def evaluate(self, tagname, sdict, pcontent, extra, context):
##  style CDATA ""
##  x CDATA #REQUIRED
##  y CDATA #REQUIRED
##  boxWidth CDATA #REQUIRED
##  boxHeight CDATA #REQUIRED
##  boxStrokeColor CDATA #IMPLIED
##  boxFillColor CDATA #IMPLIED
##  lineWidth CDATA #IMPLIED
##  fontName CDATA #IMPLIED
##  fontSize CDATA #IMPLIED
##  align CDATA #IMPLIED
##  shrinkToFit CDATA #IMPLIED
##  label CDATA #IMPLIED
##>

        attrMap = [ ('x', readLength, 0.0),
                    ('y', readLength, 0.0),
                    ('count', readInt, 10),
                    ('boxWidth', readLength, 0.5*cm),
                    ('boxHeight', readLength, 0.6*cm),
                    ('boxStrokeColor', readColor, colors.black),
                    ('boxFillColor', readColor,colors.white),
                    ('textColor', readColor,colors.black),
                    ('lineWidth', readLength, 1) ,
                    ('fontName', readString, 'Courier-Bold'),
                    ('fontSize', readLength, 10),
                    ('align', readAlign, 'left'),
                    ('vAlign', readvAlign, 'top'),
                    ('shrinkToFit', readBool, 11),
                    ('label', readString, ''),
                    ('labelFontName', readString, 'Helvetica'),
                    ('labelFontSize', readLength, 8),
                    ('labelTextColor', readColor,colors.black),
                    ('labelOffsetX', readLength,0),
                    ('labelOffsetY', readLength,0.2*cm),
                    ('borderSpec',_parseBorderSpec,None),
                    ]

        d = extractStyledAttributes(sdict, attrMap, context)
        d['data'] = LazyJoin(pcontent)

        def textBoxOp(canv, doc,
                      x=d['x'],
                      y=d['y'],
                      boxWidth=d['boxWidth'],
                      boxHeight=d['boxHeight'],
                      boxStrokeColor=d['boxStrokeColor'],
                      boxFillColor=d['boxFillColor'],
                      textColor=d['textColor'],
                      lineWidth=d['lineWidth'],
                      fontName=d['fontName'],
                      fontSize=d['fontSize'],
                      align=d['align'],
                      vAlign=d['vAlign'],
                      shrinkToFit=d['shrinkToFit'],
                      label=d['label'],
                      labelFontName=d['labelFontName'],
                      labelFontSize=d['labelFontSize'],
                      labelTextColor=d['labelTextColor'],
                      labelOffsetX=d['labelOffsetX'],
                      labelOffsetY=d['labelOffsetY'],
                      borderSpec=d['borderSpec'],
                      text=d['data']):
            #raise "death", text

            text = asUnicodeEx(text)

            # box
            canv.saveState()
            fill = boxFillColor is not None
            if fill: canv.setFillColor(boxFillColor)
            stroke = boxStrokeColor is not None
            if stroke:
                canv.setStrokeColor(boxStrokeColor)
                canv.setLineWidth(lineWidth)
            _renderBorderSpec(canv, stroke, fill, x, y, boxWidth, boxHeight, borderSpec)

            # label
            if label:
                canv.setFillColor(labelTextColor)
                canv.setStrokeColor(colors.black)
                canv.setFont(labelFontName, labelFontSize)
                canv.drawString(x+labelOffsetX, y + boxHeight + labelOffsetY, label)

            # Split into lines and find longest one.
            from reportlab.pdfbase.pdfmetrics import stringWidth
            lines = asUnicodeEx(text).split('\n')
            numLines = len(lines)
            maxStringWidth = 0
            for line in lines:
                m = stringWidth(line, fontName, fontSize)
                if maxStringWidth < m:
                    maxStringWidth = m

            distanceToBorder = 1 + lineWidth/2.0
            if shrinkToFit:
                # Shrink fontsize such that text fits in box.
                dtb2 = 2*distanceToBorder
                sw = maxStringWidth
                if sw > boxWidth - dtb2:
                    fontSize = fontSize * (boxWidth-dtb2)/sw
                if numLines > 1 and 1.2*fontSize*numLines > boxHeight - dtb2:
                    fontSize = fontSize * (boxHeight-dtb2)/(1.2*fontSize*numLines)

            # Draw text.
            canv.setStrokeColor(colors.black)
            canv.setFillColor(textColor)
            canv.setFont(fontName, fontSize)
            from reportlab.pdfbase import pdfmetrics
            n = len(lines)
            if vAlign=='bottom':
                font = pdfmetrics._fonts[fontName]
                descent = font.face.descent*fontSize/1000.
                yt0 = y - descent + (0.2+(n-1)*1.2)*fontSize
            elif vAlign=='middle':
                font = pdfmetrics._fonts[fontName]
                descent = font.face.descent*fontSize/1000.
                ascent = font.face.ascent*fontSize/1000.
                yt0 = y+boxHeight/2.+int(n/2)*fontSize*1.2 -((ascent-descent)/2.+descent)
            else:   #top
                yt0 = y + boxHeight - fontSize
            for i in range(n):
                line = lines[i]
                yt = yt0 - 1.2*fontSize*i
                if align == 'left':
                    xt = x + distanceToBorder
                    canv.drawString(xt, yt, line)
                elif align == 'right':
                    xt = x + boxWidth - distanceToBorder
                    canv.drawRightString(xt, yt, line)
                elif align == 'center':
                    xt = x + boxWidth/2.0
                    canv.drawCentredString(xt, yt, line)

            canv.restoreState()

        return textBoxOp
Controller['textBox'] = textBox()

class checkBox(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):

        # (name, reader, default)
        attrMap = [('x', readLength, 0.0),
                   ('y', readLength, 0.0),
                   ('label', readString, ''),
                   ('labelFontName', readString, 'Helvetica'),
                   ('labelFontSize', readLength, 8),
                   ('labelTextColor', readColor,colors.black),
                   ('labelOffsetX', readLength,0),
                   ('labelOffsetY', readLength,0.2*cm),
                   ('boxWidth', readLength, 0.5*cm),
                   ('boxHeight', readLength, 0.6*cm),
                   ('checkStrokeColor', readColor, colors.black),
                   ('boxStrokeColor', readColor, colors.black),
                   ('boxFillColor', readColor,colors.white),
                   ('lineWidth', readLength, 1) ,
                   ('line1', readString, ''),
                   ('line2', readString, ''),
                   ('line3', readString, ''),
                   ('checked', readBool, 0),
                   ('bold', readBool, 0),
                   ('graphicOn', readString, None),
                   ('graphicOff', readString, None),
                   ]
        # this gives us the attributes to actually use,
        # after any style lookups and default substitutions
        d = extractStyledAttributes(sdict, attrMap, context)

        def checkBoxOp(canv, doc,
                       x=d['x'],
                       y=d['y'],
                       label=d['label'],
                       labelFontName=d['labelFontName'],
                       labelFontSize=d['labelFontSize'],
                       labelTextColor=d['labelTextColor'],
                       labelOffsetX=d['labelOffsetX'],
                       labelOffsetY=d['labelOffsetY'],
                       boxWidth=d['boxWidth'],
                       boxHeight=d['boxHeight'],
                       checkStrokeColor=d['checkStrokeColor'],
                       boxStrokeColor=d['boxStrokeColor'],
                       boxFillColor=d['boxFillColor'],
                       lineWidth=d['lineWidth'],
                       line1=d['line1'],
                       line2=d['line2'],
                       line3=d['line3'],
                       checked=d['checked'],
                       bold=d['bold'],
                       graphicOn=d['graphicOn'],
                       graphicOff=d['graphicOff'],
                       ):

            canv.saveState()

            # either we draw the box, or use the provided
            # pair of bitmaps
            if (graphicOn is not None or graphicOff is not None):
                assert (graphicOn and graphicOff), "a pair of graphics/bitmaps must be provided even if you only want to use one of them!"
                doGraphic = 1
            else:
                doGraphic = 0

            if doGraphic:
                if checked:
                    canv.drawImage(graphicOn, x, y, boxWidth, boxHeight)
                else:
                    canv.drawImage(graphicOff, x, y, boxWidth, boxHeight)
            else:  #draw a simple box ourselves
                fill = boxFillColor is not None
                stroke = boxStrokeColor is not None
                if stroke: canv.setStrokeColor(boxStrokeColor)
                if fill: canv.setFillColor(boxFillColor)
                canv.setLineWidth(lineWidth)
                if stroke or fill: canv.rect(x, y, boxWidth, boxHeight, stroke=stroke, fill=fill)
                if checked:
                    if checkStrokeColor:
                        canv.setStrokeColor(checkStrokeColor)
                    else:
                        canv.setStrokeColor(boxStrokeColor)
                    canv.line(x+1, y+1, x+boxWidth-1, y+boxHeight-1)
                    canv.line(x+1, y+boxHeight-1, x+boxWidth-1, y+1)

            # text - up to three lines right to check box
            linesUsed = 0
            if line1: linesUsed = linesUsed + 1
            if line2: linesUsed = linesUsed + 1
            if line3: linesUsed = linesUsed + 1
            #manually specify line positions
            canv.setFillColor(labelTextColor)
            fs = 8
            if bold:
                canv.setFont(labelFontName, labelFontSize)
            else:
                canv.setFont("Helvetica", fs)
            x1 = x + boxWidth + 0.1*cm
            ds = canv.drawString
            if linesUsed:
                lines = [_x for _x in [line1, line2, line3] if _x != '']
                lines.reverse()
                for i in range(len(lines)):
                    line = lines[i]
                    yt = y + boxWidth/2.0 - (fs*linesUsed + fs*0.2*(linesUsed-1))/2.0 + i*fs*1.2
                    ds(x1, yt, line)

            # label
            if label:
                canv.setFillColor(labelTextColor)
                canv.setFont(labelFontName, labelFontSize)
                canv.drawString(x+labelOffsetX, y + boxHeight + labelOffsetY, label)

            canv.restoreState()    #accidentaly deleted at rev 34110

        return checkBoxOp
Controller['checkBox'] = checkBox()

def _innerLetterBoxesOp(canv, doc,
                  x=None,
                  y=None,
                  count=None,
                  label=None,
                  labelFontName =None,
                  labelFontSize =None,
                  labelTextColor =None,
                  labelOffsetX=None,
                  labelOffsetY=None,
                  boxWidth=None,
                  boxHeight=None,
                  boxGap=None,
                  boxExtraGaps=None,
                  combHeight=None,
                  boxStrokeColor=None,
                  boxFillColor=None,
                  textColor=None,
                  lineWidth=None,
                  fontName=None,
                  fontSize=None,
                  alignment=None,
                  data=None,
                  ):

    fill = boxFillColor is not None
    stroke = boxStrokeColor is not None
    if stroke:
        canv.setStrokeColor(boxStrokeColor)
        canv.setLineWidth(lineWidth)
    if fill: canv.setFillColor(boxFillColor)

    xpoints = [x]

    extraGapDict = {}
    for offset, length in boxExtraGaps:
        extraGapDict[offset] = length

    y1 = y+combHeight*boxHeight
    if boxGap>0:
        nudged = 0.0
        y2 = y+boxHeight
        for i in range(count):
            if i+1 in extraGapDict:
                nudged = nudged + extraGapDict[i+1]
            thisX = x+(i+1)*(boxWidth+boxGap) + nudged
            x0 = xpoints[-1]
            x1 = thisX - boxGap
            xpoints.append(thisX)
            if combHeight==1:
                if fill or stroke:
                    canv.rect(x0, y, boxWidth, boxHeight, fill=fill, stroke=stroke)
            else:
                if fill: canv.rect(x0, y, boxWidth, boxHeight, fill=fill, stroke=0)
                if stroke:
                    canv.line(x0, y, x0, y1)
                    canv.line(x1, y, x1, y1)
                    canv.line(x0, y, x1, y)
                    canv.line(x0, y2, x1, y2)
    else:
        #what on earth do gaps mean here? at least get width right
        totalNudge = 0.0
        for (off, wid) in list(extraGapDict.items()):
            totalNudge += wid
        # rectangle
        if stroke or fill: canv.rect(x, y, boxWidth*count + totalNudge, boxHeight, fill=fill, stroke=stroke)

        # blue grid
        nudged = 0.0
        for i in range(count):
            if i+1 in extraGapDict:
                extraGap = extraGapDict[i+1]
            else:
                extraGap = 0.0
            nudged = nudged + extraGap
            thisX = x+(i+1)*(boxWidth+boxGap) + nudged
            xpoints.append(thisX)
            if stroke:
                canv.line(thisX, y, thisX, y1)
                if extraGap:  #draw the other line
                    canv.line(thisX - extraGap, y, thisX - extraGap, y1)

    # label
    if label:
        canv.setFillColor(labelTextColor)
        canv.setFont(labelFontName, labelFontSize)
        canv.drawString(x+labelOffsetX, y + boxHeight + labelOffsetY, label)

    # data
    if data:
        # Shrink fontsize such that text fits in box.
        from reportlab.pdfbase.pdfmetrics import stringWidth
        maxStringWidth = 0
        uniData = asUnicode(data,'utf-8')
        for d in uniData:
            m = stringWidth(d, fontName, fontSize)
            if maxStringWidth < m:
                maxStringWidth = m

        # correct fontSize
        dtb = 1 + lineWidth/2.0
        dtb2 = 2*dtb
        sw = maxStringWidth
        avw = boxWidth-dtb2
        if avw<0: avw = boxWidth
        if sw>avw: fontSize = fontSize*avw/float(sw)

        # fill in text in boxes
        canv.setFillColor(textColor)
        uniData = uniData[0:count]  # data might be too long

        #text data may need to be right aligned for numeric fields.
        #we cannot trust whitespace as it might come from lining tags
        #up neatly.
        if alignment == TA_RIGHT:
            while len(uniData) < count:
                uniData = ' ' + uniData

        canv.setFont(fontName, fontSize)
        yt = y + boxHeight - fontSize
        for i in range(len(uniData)):
            xt = xpoints[i] + boxWidth*0.5
            canv.drawCentredString(xt, yt, uniData[i])

class letterBoxes(MapNode):
    "Box grid with one letter per box"
    def evaluate(self, tagname, sdict, pcontent, extra, context):

        # (name, reader, default)
        # should correspond to the DTD.
        attrMap = [('x', readLengths, 0.0),
                   ('y', readLengths, 0.0),
                   ('count', readInt, 10),
                   ('label', readString, ''),
                   ('labelFontName', readString, 'Helvetica'),
                   ('labelFontSize', readLength, 8),
                   ('labelTextColor', readColor,colors.black),
                   ('labelOffsetX', readLength,0),
                   ('labelOffsetY', readLength,0.2*cm),
                   ('boxWidth', readLengths, 0.5*cm),
                   ('boxGap',readLength, 0),
                   ('boxExtraGaps',readGapSequence, []),
                   ('boxHeight', readLengths, 0.6*cm),
                   ('combHeight',readFloat, 1),
                   ('boxStrokeColor', readColor, colors.black),
                   ('boxFillColor', readColor,colors.white),
                   ('textColor', readColor, colors.black),
                   ('lineWidth', readLength, 1) ,
                   ('fontName', readString, 'Courier-Bold'),
                   ('fontSize', readLength, 10),
                   ('alignment', readAlignment, 'LEFT'),
                   ]

        d = extractStyledAttributes(sdict, attrMap, context)
        try:
            d['data'] = pcontent[0]
        except:
            d['data'] = ''

        # embedded drawing function specific to this
        # text box.
        def letterBoxesOp(canv, doc,
                          x=d['x'],
                          y=d['y'],
                          count=d['count'],
                          label=d['label'],
                          labelFontName = d['labelFontName'],
                          labelFontSize = d['labelFontSize'],
                          labelTextColor = d['labelTextColor'],
                          labelOffsetX=d['labelOffsetX'],
                          labelOffsetY=d['labelOffsetY'],
                          boxWidth=d['boxWidth'],
                          boxHeight=d['boxHeight'],
                          boxGap=d['boxGap'],
                          boxExtraGaps=d['boxExtraGaps'],
                          combHeight=d['combHeight'],
                          boxStrokeColor=d['boxStrokeColor'],
                          boxFillColor=d['boxFillColor'],
                          textColor=d['textColor'],
                          lineWidth=d['lineWidth'],
                          fontName=d['fontName'],
                          fontSize=d['fontSize'],
                          alignment=d['alignment'],
                          data=d['data']
                          ):

            canv.saveState()
            if isinstance(x,list):
                data = asUnicode(data)
                for i,_x in enumerate(x):
                    if i<len(data):
                        c = data[i].encode('utf8')
                    else:
                        c = ''
                    _innerLetterBoxesOp(canv, doc,
                      x=x[i],
                      y=y[i],
                      boxWidth=boxWidth[i],
                      boxHeight=boxHeight[i],
                      data=c,
                      count=1,
                      label=label,
                      labelFontName = labelFontName,
                      labelFontSize = labelFontSize,
                      labelTextColor = labelTextColor,
                      labelOffsetX=labelOffsetX,
                      labelOffsetY=labelOffsetY,
                      boxGap=boxGap,
                      boxExtraGaps=boxExtraGaps,
                      combHeight=combHeight,
                      boxStrokeColor=boxStrokeColor,
                      boxFillColor=boxFillColor,
                      textColor=textColor,
                      lineWidth=lineWidth,
                      fontName=fontName,
                      fontSize=fontSize,
                      alignment=alignment,
                      )
            else:
                _innerLetterBoxesOp(canv, doc,
                  x=x,
                  y=y,
                  count=count,
                  label=label,
                  labelFontName = labelFontName,
                  labelFontSize = labelFontSize,
                  labelTextColor = labelTextColor,
                  labelOffsetX=labelOffsetX,
                  labelOffsetY=labelOffsetY,
                  boxWidth=boxWidth,
                  boxHeight=boxHeight,
                  boxGap=boxGap,
                  boxExtraGaps=boxExtraGaps,
                  combHeight=combHeight,
                  boxStrokeColor=boxStrokeColor,
                  boxFillColor=boxFillColor,
                  textColor=textColor,
                  lineWidth=lineWidth,
                  fontName=fontName,
                  fontSize=fontSize,
                  alignment=alignment,
                  data=data,
                  )

            canv.restoreState()

        return letterBoxesOp
Controller['letterBoxes'] = letterBoxes()
###########################################################################
# End of... form stuff
###########################################################################

###########################################################################
# easier way to hook up to graphics....
###########################################################################
class Param(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        key = sdict['name']
        value = pcontent[0]
        try:
            value = eval(value)
        except:
            value = value.strip()
        return ("setParam", key, value)
Controller["param"] = Param()

class DiagraWidgetFactory(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        moduleName = sdict["module"]
        funcName = sdict["function"]
        alias = sdict["name"]
        # the path for the imports should include:
        # 1. document directory
        # 2. python path if baseDir not given, or
        # 3. baseDir if given
        try:
            dirName = sdict["baseDir"]
        except:
            dirName = None
        importPath = _rml2pdf_locations()
        if dirName is None:
            importPath.extend(sys.path)
        else:
            importPath.insert(0, dirName)

        modul = recursiveImport(moduleName, baseDir=importPath)
        initArgs = eval(sdict.get("initargs", '[]'))
        widget = getattr(modul, funcName)(*initArgs)
        return ("addWidget", widget, alias)

Controller["widget"] = DiagraWidgetFactory()

class DiagraFlowableWrapper(MapNode):
    """Call a standard drawing module"""
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        moduleName = sdict["module"]
        funcName = sdict["function"]

        showBoundary = int(sdict.get("showBoundary", "0"))

        hAlign = sdict.get("hAlign", "CENTER")

        # the path for the imports should include:
        # 1. document directory
        # 2. python path if baseDir not given, or
        # 3. baseDir if given
        try:
            dirName = sdict["baseDir"]
        except:
            dirName = None
        importPath = _rml2pdf_locations()
        if dirName is None:
            importPath.extend(sys.path)
        else:
            importPath.insert(0, dirName)

        modul = recursiveImport(moduleName, baseDir=importPath)
        func = getattr(modul, funcName)
        drawing = func()

        drawing.hAlign = hAlign
        if showBoundary:
            drawing._showBoundary = 1

        #pcontent is the children, but they have been
        #traversed into already
        if pcontent is not None:
            for thing in pcontent:
                if isinstance(thing,tuple):
                    if thing[0] == 'setParam':
                        (command, key, value) = thing
                        recursiveSetAttr(drawing, key, value)
                    elif thing[0] == 'addWidget':
                        (command, widget, alias) = thing
                        drawing.add(widget, alias)
                    else:
                        raise ValueError("unknown Diagra command verb %s" % thing[0])
        # as a high-level convenience, it can also return one of
        # our figure objects, which wrap up drawings and let you shrink/scale
        # them and add captions
        return drawing
Controller["drawing"] = DiagraFlowableWrapper()

#######################################################################
#
#  PageCatcher flowable support. Need a flowable which does all
#  the storyplace stuff.
#
########################################################################
class IncludePdfPages(MapNode):
    """PDF Pages to be included inline within the story"""

    def evaluate(self, tagname, sdict, pcontent, extra, context):
        fileName = sdict["filename"]
        sx = sy = 1
        if "sx" in sdict:
            sx = readLength(sdict["sx"],context=context)
        if "sy" in sdict:
            sy = readLength(sdict["sy"],context=context)
        dx = dy = 0.0
        if "dx" in sdict:
            dx = readLength(sdict["dx"],context=context)
        if "dy" in sdict:
            dy = readLength(sdict["dy"],context=context)
        degrees = 0
        if "degrees" in sdict:
            degrees = float(sdict["degrees"])
        pages = sdict.get("pages", None)
        template = sdict.get("template", None)

        outlineText = sdict.get("outlineText", None)
        outlineLevel = int(sdict.get("outlineLevel", 0))
        outlineClosed= int(sdict.get("outlineClosed", 0))
        leadingFrame = sdict.get('leadingFrame','1').lower()
        if leadingFrame!='notattop':
            leadingFrame = readBool(leadingFrame)
        isdata = readBool(sdict.get('isdata','0'))
        orientation = sdict.get('orientation',None)
        t = sdict.get('pageSize',None)
        pageSize = None
        if t is not None:
            if t and '(' in t or '[' in t or ',' in t:
                pageSize = t.replace('[','').replace(']','').replace('(','').replace(')').split(',')
                if len(pageSize)==4:
                    try:
                        pageSize = [readLength(x,context=context) for x in pageSize]
                    except:
                        pageSize = None
                else:
                    pageSize = None
            elif t.lower() in ('1','yes','true','on', 'y'):
                pageSize = True
            elif t.lower() in ('0','no','false','off', 'n'):
                pageSize=False
            elif t.lower() in ('set','fit','orthofit','center','centre'):
                pageSize = t
            if pageSize is None:
                raise ValueError('pageSize=%r cannot be evaluated' % t)
        t = sdict.get('autoCrop',None)
        autoCrop = None
        if t is not None:
            if t and '(' in t or '[' in t or ',' in t:
                autoCrop = t.replace('[','').replace(']','').replace('(','').replace(')').split(',')
                if len(autoCrop)==4:
                    try:
                        autoCrop = [readLength(x,context=context) for x in autoCrop]
                    except:
                        autoCrop = None
                else:
                    autoCrop = None
            elif t.lower() in ('1','yes','true','on', 'y'):
                autoCrop = True
            elif t.lower() in ('0','no','false','off', 'n'):
                autoCrop=False
            elif t.lower() in ('mediabox','cropbox', 'trimbox','bleedbox','artbox'):
                autoCrop = t
            if autoCrop is None:
                raise ValueError('autoCrop=%r cannot be evaluated' % t)
        t = sdict.get('pdfBoxType',None)
        pdfBoxType = None
        if t is not None:
            if t and '(' in t or '[' in t or ',' in t:
                pdfBoxType = t.replace('[','').replace(']','').replace('(','').replace(')').split(',')
                if len(pdfBoxType)==4:
                    try:
                        pdfBoxType = [readLength(x,context=context) for x in pdfBoxType]
                    except:
                        pdfBoxType = None
                else:
                    pdfBoxType = None
            elif t.lower() in ('mediabox','cropbox', 'trimbox','bleedbox','artbox'):
                pdfBoxType = t
            if pdfBoxType is None:
                raise ValueError('pdfBoxType=%r cannot be evaluated' % t)
        return includePdfFlowables(fileName,
                        pages=pages,
                        dx=dx, dy=dy, sx=sx, sy=sy, degrees=degrees,
                        orientation=orientation,
                        isdata=isdata,
                        leadingBreak=leadingFrame,
                        template=template,
                        outlineText=outlineText,
                        outlineLevel=outlineLevel,
                        outlineClosed=outlineClosed,
                        pageSize=pageSize,
                        autoCrop=autoCrop,
                        pdfBoxType=pdfBoxType,
                        )
Controller["includePdfPages"] = IncludePdfPages()

###########################################################################
# dynamic behaviour
###########################################################################
def loseText(content):
    out = []
    for elem in content:
        if not isinstance(elem,strTypes):
            out.append(elem)
    return out

class ConditionalFlowable(MapNode, Flowable):
    """This wraps up and selects conditional content."""
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        """This returns a conditional flowable object - itself, actually -
        which when drawn decides what content it is."""
        print('conditional tag arrived')
        self.cases = []
        self.elseCase = None
        for elem in pcontent:
            if type(elem) == type(''):
                continue
            elif isinstance(elem, Case):
                print('found a case object')
                self.cases.append(elem)
            elif isinstance(elem, Else):
                print('found an else object')
                self.elseCase = elem
        return self

##        print 'evaluating cases...'
##        nameSpace = {
##            'pageNumber':context.doc.page
##            }
##        nameSpace.update(context.names)
##
##        #skip out and return first true one
##        for case in cases:
##            if eval(case.expr):
##                print 'case %s evaluated true' % case.expr
##                return case.content
##            else:
##                print 'case %s evaluated false' % case.expr
##                print 'case %s evaluated false' % case.expr
##
##        if elseCase:
##            print 'else case present'
##            return elseCase.content
##
##        #still here
##        return None
Controller["condFlowable"] = ConditionalFlowable()

class Case(MapNode):
    """This wraps up and selects conditional content."""
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        self.expr = sdict["expr"]
        self.content = loseText(pcontent)
        return self
Controller["case"] = Case()

class Else(MapNode):
    """Returns its content if called."""
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        self.content = loseText(pcontent)
        return self
Controller["else"] = Else()

class CropMarks(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        cM=ABag()
        cM.borderWidth = readLength(sdict.get('borderWidth','36'),context=context)
        cM.markWidth = readLength(sdict.get('markWidth','0.5'),context=context)
        cM.markLength = readLength(sdict.get('markLength','18'),context=context)
        cM.markColor = readColor(sdict.get('markColor','black'),context=context)
        cM.bleedWidth = readLength(sdict.get('bleedWidth','0'),context=context)
        cM.markLast = readBool(sdict.get('markLast','1'),context=context)
        context.canvasInfo.cropMarks = cM
        return "" # vanish
Controller["cropMarks"] = CropMarks()

def _getIndexName(sdict):
    from reportlab.platypus.paraparser import DEFAULT_INDEX_NAME
    name = sdict.get('name',DEFAULT_INDEX_NAME)
    return name

class StartIndex(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        from reportlab.platypus.tableofcontents import SimpleIndex
        name=_getIndexName(sdict)
        offset = readInt(sdict.get('offset','0'),context)
        format = sdict.get('format','123')
        cI = context.canvasInfo
        if not hasattr(cI,'indexes'): cI.indexes = {}
        cI.indexes[name] = SimpleIndex(name=name, format=format, offset=offset)
        return "" # vanish
Controller["startIndex"] = StartIndex()

class ShowIndex(Flowable):
    """defer conversion of content until wrap time (to allow, eg, page numbering)"""
    def __init__(self, tagname, sdict, pcontent, extra, context):
        self._info =  tagname, sdict, pcontent, extra, context
        self.index = None

    def initializeFlowable(self):
        if self.index is None:
            tagname, sdict, pcontent, extra, context = self._info
            name=_getIndexName(sdict)
            try:
                ix = self.index = context.canvasInfo.indexes[name]
            except KeyError:
                raise KeyError('Index with name %r not found' % name)
            headers = readBool(sdict.get('headers','1'),context)
            style = sdict.get('style',None)
            tableStyle = sdict.get('tableStyle',None)
            dot = sdict.get('dot',None)
            rmlcontext = self._doctemplateAttr('_nameSpace')['rmlcontext']
            if rmlcontext:
                def checkStyle(s):
                    if s is None: return
                    try:
                        return rmlcontext.names[s]
                    except KeyError:
                        raise KeyError('Style %r not found in showIndex' % s)
                tableStyle = checkStyle(tableStyle)
                if style is not None:
                    style = list(map(checkStyle,style.split()))
            ix._index_name= name
            ix.setup(**dict(tableStyle=tableStyle,style=style,headers=headers,dot=dot))

    def wrap(self, aW, aH):
        self.initializeFlowable()
        self.width,self.height = self.index.wrapOn(self.canv,aW,aH)
        return self.width, self.height

    def draw(self):
        self.initializeFlowable()
        self.index._drawOn(self.canv)

    def split(self,aW,aH):
        self.initializeFlowable()
        return self.index.splitOn(self.canv,aW,aH)

class showIndex(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):
        return ShowIndex(tagname, sdict, pcontent, extra, context)
Controller["showIndex"] = showIndex()

#################################################################################
#
#  support for logging
#
#################################################################################
class LogConfig(MapNode):
    def evaluate(self, tagname, sdict, pcontent, extra, context):

        levelName = sdict.get('level','WARNING')
        level = getattr(logging, levelName)

        filename = sdict.get('filename',None)
        filemode = sdict.get('filemode','APPEND').lower()[0]   #'a' or 'w'
        format = sdict.get('format',None)
        datefmt = sdict.get('datefmt',None)

        logging.basicConfig(level=level,
                            filename=filename,
                            filemode=filemode,
                            format=format,
                            datefmt=datefmt)

        return "" # vanish
Controller["logConfig"] = LogConfig()

class LogWriter(MapNode):
    def init1(self, **kw):
        level = kw.get('level',None)
        if level is None:
            level = logging.debug
        self.defaultLevel = level

    def evaluate(self, tagname, sdict, pcontent, extra, context):
        levelName = sdict.get('level',None)
        if levelName:
            level = getattr(logging, levelName)
        else:
            level = self.defaultLevel
        message = u"".join(map(asUnicodeEx, pcontent))

        return LogFlowable('reportlab.rml2pdf.user', level, message)

class LogFlowable(Flowable):
    """This writes to a logger when drawn."""
    def __init__(self, name, level, message):
        Flowable.__init__(self)
        self.name = name
        self.level = level
        self.message = message

    def draw(self):
        logger = logging.getLogger(self.name)
        msg = 'Page %d: %s' % (self.canv.getPageNumber(), self.message)
        logger.log(self.level, msg)
Controller["log"] = LogWriter()
Controller["debug"] = LogWriter(level=logging.debug)
Controller["info"] = LogWriter(level=logging.info)
Controller["warning"] = LogWriter(level=logging.warning)
Controller["error"] = LogWriter(logging.error)
Controller["critical"] = LogWriter(logging.critical)

def getoutfile(parsedtext):
    if isinstance(parsedtext,strTypes):
        return None
    (name, atts, content, misc) = parsedtext
    if name=="document":
        return atts["filename"]
    else:
        if content is None:
            return None
        for e in content:
            t = getoutfile(e)
            if t is not None:
                return t
        return None

def getColorSpace(parsedtext):
    "Called by main loop so we know it before instantiating all objects"
    #iterates until document tag found
    if isinstance(parsedtext,strTypes):
        return None
    (name, atts, content, misc) = parsedtext
    if name=="document":
        return atts.get("colorSpace", None)
    else:
        if content is None:
            return None
        for e in content:
            t = getColorSpace(e)
            if t is not None:
                return t
        return None

def getEncryption(parsedtext):
    if isinstance(parsedtext,strTypes):
        return None
    (name, atts, content, misc) = parsedtext
    if name=="document":
        userPass = atts.get("userPass",None)
        ownerPass = atts.get("ownerPass",None)
        if userPass is None and ownerPass is None: return
        if userPass is None:
            raise ValueError("Document attribute userPass required for encryption")
        permissions = atts.get("permissions","print").split()
        strength = atts.get("encryptionStrength","128")
        if strength in ("128","40"):
            strength = int(strength)
        else:
            raise ValueError("Document attribute strength not 40|128")
        kwds = dict(strength=strength)
        for p in permissions:
            if p in ('print','copy','modify','annotate'):
                kwds['can'+p.capitalize()] = 1
            else:
                raise ValueError("Document attribute permissions contains invalid value %r" % p)
        return StandardEncryption(userPass,ownerPassword=ownerPass,**kwds)
    else:
        if content is None:
            return None
        for e in content:
            t = getEncryption(e)
            if t is not None:
                return t
        return None

def _vStr2DTDName(s):
    '''Map a version string to an rmldtd filename'''
    return 'rml_%s.dtd' % s.replace('.','_')
DTDName='rml.dtd'
CompatibleDTDNames = ['dynamic_rml.dtd','rml.dtd']+list(map(_vStr2DTDName,compatible_versions))

def _checkDone(done,canv):
    if done: canv.save()
    else:
        f = getattr(canv._doc,'File',None)
        if f: f.closeOrReset()

def _setPageLayoutAndMode(cI,canv):
    canv._doc._catalog.setPageLayout(getattr(cI,'pageLayout',None))
    canv._doc._catalog.setPageMode(getattr(cI,'pageMode',None))

def go(xmlInputText, outputFileName=None, outDir=None, dtdDir=None,
       passLimit=2, permitEvaluations=1, ignoreDefaults=0,
       pageCallBack=None,
       progressCallBack=None,
       dynamicRml=0, dynamicRmlNameSpace={},   #!--this is how dynamic RML gets stuff in
       encryption=None,
       saveRml=None,
       parseOnly=False, #if we're only calling the parse
       ):

    logger.debug("rmlpdf.go starting run")
    # passLimit of None means "keep trying until done"
    #   of 3 means, "try 3 times then quit"
    # permitEvaluations when false disallows the evalString tag for security (web apps, eg)
    # ignoreDefaults=1 means "do one pass and use the default values where values are not found"
    # pageCallBack is a callback to execute on final formatting of each page.
    # progressCallBack is a cleverer callback; see the progressCB function
    # in reportlab\platypus\doctemplate
    # preppyDictionary if set to a dictionary indicates that the xmlInputText should be
    #  preprocessed using preppy with the preppyDictionary as argument.
    # if preppyDictionary is not None and preppyIterations is >1 then the preppy preprocessing will
    #  be repeated preppyIterations times (max of 3) with the same dict,
    #  to generate, eg, table of contents...
    # If encryption is set it must be an encryption object.
    # For example
    # reportlab.lib.pdfencrypt.StandardEncryption("User", "Owner", canPrint=0, canModify=0, canCopy=0, canAnnotate=0)

    if progressCallBack:
        progressCallBack('STARTED', 0)

    if saveRml:
        f = open(saveRml,'w')
        f.write(xmlInputText)
        f.close()
        del f
    if progressCallBack:
        progressCallBack('BEFORE_PARSE_XML', 0)

    # PARSE THE XML
    if verbose:
        print("parsing XML")
    def warnCB(s):
        print(s)
    import pyRXPU
    parsexml = pyRXPU.Parser(
        ErrorOnValidityErrors=1,
        NoNoDTDWarning=1,
        ExpandCharacterEntities=1,
        ExpandGeneralEntities=1,
        warnCB = warnCB,
        srcName='string input',
        ).parse

    if dtdDir is None: dtdDir = _rml_dtd_dirs()
    else:
        if not isinstance(dtdDir, collections.Callable): dtdDir = _FS_Checker(dtdDir)
        if type(dtdDir) not in (type(()),type([])): dtdDir = [dtdDir]
    dtd_list = []
    def _eoDTD(s,possibles=CompatibleDTDNames,target=DTDName,dtdDir=dtdDir,dtd_list=dtd_list,path_basename=os.path.basename):
        if path_basename(s) in possibles:
            t =  target if not s.endswith('dynamic_rml.dtd') else 'dynamic_rml.dtd'
            if dtdDir:
                for d in dtdDir:
                    s = d(t)
                    if s:
                        dtd_list.append(t)
                        return s
            else:
                if s!=t: s = t
        return s

    # need to extract the filename by tricky methods
    # because we need the document defined *before* processing
    parsed = parsexml(xmlInputText,eoCB=_eoDTD)
    logger.debug("parsed XML")

    if progressCallBack:
        progressCallBack('AFTER_PARSE_XML', 0)

    if dynamicRml or 'dynamic_rml.dtd' in dtd_list:
        #do a preprocessing pass on tuple tree.
        from rlextra.radxml import xpreppy
        parsed = xpreppy.preProcess(parsed, dynamicRmlNameSpace, caller='rml')
        logger.debug("dynamic RML preprocessing done")
        if progressCallBack:
            progressCallBack('AFTER_PRE_PROCESS', 0)

    if parseOnly: return

    # DETERMINE THE OUTPUT FILE (xxxx IS THIS HISTORICAL?)
    if not outputFileName:
        outputFileName = getoutfile(parsed)
    # outputFileName must be allowed to be a file-like object or a string!
    if outDir and (isinstance(outputFileName,strTypes)) and (not os.path.isabs(outputFileName)):
        outputFileName = os.path.join(outDir, outputFileName)

    if not encryption:
        encryption = getEncryption(parsed)

    # NOW PROCESS THE PARSED XML
    # create a names archive (to allow multipass crossreferencing
    namearchive = NamesArchive(passLimit)
    # repeat until done
    done = 0
    count = 1
    enforceColorSpace = _chooseEnforceColorSpace(getColorSpace(parsed)) #surely we only need do this once

    while not done:
        if verbose:
            print("Generating PDF...", count)
        #reset all counters for numbering
        sequencer.setSequencer(sequencer.Sequencer())
        count += 1
        if progressCallBack:
            progressCallBack('BEFORE_RML_CONTEXT', 0)
        context = RMLContext(namearchive, permitEvaluations)
        context.enforceColorSpace = enforceColorSpace

        #we need to know this early, before other parsing,
        #as it is used to check colour attribute parsing
        if progressCallBack:
            progressCallBack('AFTER_RML_CONTEXT', 0)
        #context.doc = doc
        context.filename = outputFileName
        if progressCallBack:
            progressCallBack('BEFORE_CONTROLLER_PROCESS', 0)

        #formatted = \
        Controller.process(parsed, context)
        if progressCallBack:
            progressCallBack('AFTER_CONTROLLER_PROCESS', 0)
        context.filename = outputFileName
        # hacker check
        if CiD != id(CanvasOps):
            raise ValueError(ASV)
        if AiD != id(alignmentAdjust):
            raise ValueError(ASV)
        # if it is a simple document, just render the pages
        pDs = context.pageDrawings
        cI = context.canvasInfo
        if getattr(cI,'useCropMarks',False):
            cropMarks = getattr(cI,'cropMarks',True)
        else:
            cropMarks = None
        if pDs:
            if progressCallBack:
                progressCallBack('BEGIN_FORMAT', 0)
                progressCallBack('SIZE_EST', len(pDs))
            if verbose:
                print("Gen: pageDrawing style document")
            cI.filename = context.filename
            from reportlab.pdfgen import canvas
            canv = canvas.Canvas(cI.filename, cI.pageSize, pageCompression=context.compression,
                                 invariant=context.invariant,cropMarks=cropMarks,enforceColorSpace=enforceColorSpace)
            canv.setAuthor(context.author)
            canv.setTitle(context.title)
            canv.setSubject(context.subject)
            canv.setCreator(context.creator)
            canv.setKeywords(context.keywords)
            if context.displayDocTitle is not None:
                canv.setViewerPreference('DisplayDocTitle',['false','true'][context.displayDocTitle])
            canv.setCatalogEntry('Lang',context.lang)
            _setPageLayoutAndMode(cI,canv)
            if encryption:
                canv._doc.encrypt = encryption
            canv.setPageCallBack(pageCallBack)
            canv.imageCaching = cI.imageCaching
            # security
            alignmentAdjust(canv)
            doc = None # not used (?)

            for pD in pDs:
                pD(canv, doc)
                canv.showPage()
                if progressCallBack:
                    progressCallBack('PROGRESS', canv.getPageNumber())
                    progressCallBack('PAGE', canv.getPageNumber())
            done = namearchive.complete()
            _setPageLayoutAndMode(cI,canv)
            _checkDone(done,canv)
            # destroy the context object (break possible cycles)
            context.destroy()
            # return the canvas info object, with last canvas attached
            cI.canv = canv
            outputDevice = canv._filename
            result = cI
        else:
            if verbose:
                print("Gen: page template style document")
            doc = context.doc
            doc.cropMarks = cropMarks
            doc.indexes = getattr(cI,'indexes',{})
            doc.invariant = context.invariant
            doc.pageCompression = context.compression
            doc._debug = context.debug
            doc.setPageCallBack(pageCallBack)
            doc.setProgressCallBack(progressCallBack)
            Story = context.story
            # prepare the context
            context.prepare()
            doc._doSave = 0
            doc._nameSpace['rmlcontext'] = context
            doc.build(Story)
            try:
                del doc._nameSpace['rmlcontext']
            except KeyError:
                pass
            doc._doSave = done = namearchive.complete()
            if encryption:
                doc.canv._doc.encrypt = encryption
            _setPageLayoutAndMode(cI,doc.canv)
            _checkDone(done,doc.canv)
            context.destroy()
            result = doc
            outputDevice = doc.canv._filename
        if not done:
            done = ignoreDefaults # if set this overrides, forces early termination
        if not done:
            namearchive.reset() # raises error on no progress or if too many passes are executed
            if verbose:
                print("Gen: namearchive not completely defined: trying again...")
    #... go to top and try again (unless limit reached)

    # the progress callback should be told the size of the output if possible
    if hasattr(outputDevice, 'tell'): # stream
        size = outputDevice.tell()
    elif os.path.isfile(outputDevice): #file on disk
        size = os.stat(outputDevice)[6]
    else:
        size = 0    # we won't guarantee all cases yet

    logger.debug("go() finished")
    if progressCallBack:
        progressCallBack('PDF_SIZE', size)
        progressCallBack('FINISHED', 0)
    return result

class ProgressMonitor:
    "Callback for logging. Gives main events and every 10th page."
    def __init__(self):
        self.started = time.clock()

    def __call__(self, typ, value):
        if typ == 'PROGRESS':
            return
        elif typ == 'PAGE' and value % 10 != 0:
            return
        else:
            elapsed = time.clock() - self.started
            print("%0.4f seconds:  %s     %s" % (elapsed, typ, value))

def _saveLastestRml(fn,rml,dfn='lastest.rml'):
    if fn:
        if not isinstance(fn,strTypes): fn=dfn
        f = open(asUnicode(fn),'w')
        f.write(rml)
        f.close()

def invalid_rml(text, paragraph=True, stylesheet='', saveAs=None):
    '''test para text for errors and return tuple of stuff if bad'''
    if isUnicode(text):
        text = text.encode('utf8')
    else:
        text = asUnicodeEx(text)
        try:
            text = text.decode('utf8').encode('utf8')
        except UnicodeDecodeError as e:
            i,j = e.args[2:4]
            return (e.args[:4]+('%s\n%s-->%s<--%s' % (e.args[4],text[max(i-10,0):i],text[i:j],text[j:j+10]),))
    text=text.strip()
    rml = _invalid_rml_template % (stylesheet, text)
    parts = _invalid_rml_template.split('%s')
    if paragraph:
        text = _spara_re.sub('',text)
        text = _epara_re.sub('',text)
        parts[1] = parts[1] + '<para>\n'
        parts[2] = '\n<para>' + parts[2]
    ss_offset = parts[0].count('\n') + 1
    text_offset = ss_offset + (stylesheet + parts[1]).count('\n')
    rml = parts[0] + stylesheet + parts[1] + text + parts[2]
    try:
        go(rml,saveAs,parseOnly=bool(not saveAs))
    except Exception as e:
        errs = ''.join(list(e.args))
        print(errs)
        poserrs = errs.replace('Error: ','').replace('\nParse Failed!\n','')
        poserrs = poserrs.split('\n')
        poserrs = '\n'.join([poserrs[0]]+[_e for _e in poserrs[1:] if _e.strip()!=poserrs[0].strip()])
        poserrs = poserrs.replace(' in unnamed entity','')
        p = re.compile(r'\s+at\s+line\s+(?P<l>\d+)\s+char\s+(?P<c>\d+)\s+of\s+string\s+input',re.M)
        m = p.search(poserrs)
        if m:
            l = int(m.group('l')) - text_offset
            L = text.split('\n')
            if l >= 0 and l < len(L):
                c = int(m.group('c'))
                ctxt = L[l][max(c-10,0):c+10]
                if c+10 > len(L[l]) and l < len(L)-1:
                    ctxt += '\n'+L[l+1][:10]
                if c-10 < 0 and l > 0:
                    ctxt = L[l-1][-10:]+'\n'+ctxt
                errs = p.sub(' near line %d char %d of input. "-->%s<--"'%(l,c,ctxt),poserrs,1)
        if isUnicode(errs): errs=errs.encode('utf8')
        return (errs.replace(b' ',b' '),)
invalid_rml_para = invalid_rml

def invalid_rml_image(file,width='1in',height='1in',inline="1",
        transparency_mask="auto",preserveAspectRatio="1",showBoundary="0",
        anchor="c",pdfBoxType='MediaBox',x="0",y="0"):
    if not os.path.isfile(file):
        return 'no such image file "%s"' % file
    A=' '.join(['%s=%r' % (a,locals()[a]) for a in ('file','width','height','inline','transparency_mask',
            'preserveAspectRatio','showBoundary','anchor','pdfBoxType','x','y')])
    rml = _invalid_rml_template % ('<illustration width="%(width)s" height="%(height)s"><image %(A)s/></illustration>' % locals())
    io = getBytesIO()
    try:
        go(rml,io)
    except Exception as e:
        errs = ''.join(list(e.args))
        return '%s(%s)' % (e.__class__.__name__,errs)
    return None

_invalid_rml_template='''<!DOCTYPE document SYSTEM "rml_1_0.dtd">
<document filename="/tmp/sample.pdf" invariant="1">
<template>
<pageTemplate id="main">
<pageGraphics>
</pageGraphics>
<frame id="first" x1="1in" y1="1in" width="6.27in" height="9.69in"/>
</pageTemplate>
</template>
<stylesheet>
%s
</stylesheet>
<story>
%s
</story>
</document>'''

_spara_re=re.compile(r'^<\s*para[^>]*>',re.I+re.M)
_epara_re=re.compile(r'\s*<\s*/\s*para\s*>\s*$',re.I+re.M)

def oldmain(quiet=0,exe=0,fn=[],outDir=None):
    '''use exe=1 if this is the exe'''
    global verbose
    cwd = os.getcwd()
    if outDir and not os.path.isabs(outDir):
        outDir = os.path.join(cwd,outDir)
    try:
        if len(fn):
            # extract options
            if '-v' in fn:
                verbose = 1
                fn.remove('-v')

            for inputPath in fn:
                if not os.path.isabs(inputPath):
                    inputPath = os.path.join(cwd,inputPath)
                targetDir=os.path.dirname(inputPath)
                InputFile = open(inputPath,'rb')
                os.chdir(targetDir)
                if verbose:
                    progressCB = ProgressMonitor()
                else:
                    progressCB = None

                test = go(InputFile.read(),outDir=outDir, progressCallBack=progressCB,
                          dynamicRml=1)
                os.chdir(cwd)
                if not quiet: print(test.filename)
        else:
            test = go(sys.stdin.read(),outDir=outDir)
            if not quiet: print(test.filename)
    finally:
        os.chdir(cwd)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert Report Markup Language (RML) files to PDF")
    parser.add_argument("--version", help="print version number and then exit", action="store_true")
    parser.add_argument("-v", "--verbosity", help="control verbosity", type=int, default=1)
    parser.add_argument("-o", "--outdir", help="create PDFs in given directory")
    parser.add_argument("files", help="File(s) to convert to PDF", nargs="*")
    parser.add_argument("-p", "--pipe", help="run as a pipe - read stdin and write stdout", action="store_true")

    args = parser.parse_args()

    if args.version:
        import rlextra
        print(rlextra.Version)
        return

    if args.pipe:
        input_rml = sys.stdin.read()
        buf = io.BytesIO()
        go(input_rml, buf)
        sys.stdout.write(buf.getvalue())
        return

    if not args.files:
        print("No files to process. Either use --pipe mode, or list rml files on command line")

    cwd = os.getcwd()

    outdir = args.outdir
    if outdir and not os.path.isabs(outdir):
        outdir = os.path.join(cwd, outdir)

    for inputPath in args.files:
        if not os.path.isabs(inputPath):
            inputPath = os.path.join(cwd,inputPath)
        targetDir = outdir or os.path.dirname(inputPath)
        inputFile = open(inputPath,'rb')
        os.chdir(targetDir)
        if args.verbosity > 1:
            progressCB = ProgressMonitor()
        else:
            progressCB = None

        test = go(
                    inputFile.read(),
                    outDir=outdir,
                    progressCallBack=progressCB,
                    dynamicRml=1
                    )
        os.chdir(cwd)
        if args.verbosity > 0:
            print(test.filename)

if __name__=="__main__":
    #oldmain(exe=1,fn=sys.argv[1:])
    main()
