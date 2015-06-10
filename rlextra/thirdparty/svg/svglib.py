#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""An experimental library for reading and converting SVG.

This is an experimental converter from SVG to RLG (ReportLab Graphics)
drawings. It converts mainly basic shapes, paths and simple text. 
The current intended usage is either as module within other projects:

    from svglib.svglib import svg2rlg
    drawing = svg2rlg("foo.svg")
  
or from the command-line where right now it is usable as an SVG to PDF
converting tool named sv2pdf (which should also handle SVG files com-
pressed with gzip and extension .svgz).
"""

import sys
import os
import glob
import copy
import types
import re
import operator
import gzip
import xml.dom.minidom 
from functools import reduce
try:
    import tinycss
except:
    tinycss=None

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.graphics.shapes import *
from reportlab.lib import colors
from reportlab.lib.units import cm, inch, mm, pica, toLength

__version__ = "0.6.3"
__license__ = "LGPL 3"
__author__ = "Dinu Gherman"
__date__ = "2010-03-01"

pt = 1
### helpers ###

def convertToFloats(aList):
    "Convert number strings in list to floats (leave rest untouched)."

    for i in range(len(aList)):
        try:
            aList[i] = float(aList[i])
        except ValueError:
            try:
                aList[i] = aList[i].encode("ASCII")
            except:
                pass
    return aList

def convertQuadraticToCubicPath(Q0, Q1, Q2):
    "Convert a quadratic Bezier curve through Q0, Q1, Q2 to a cubic one."
    C0 = Q0
    C1 = (Q0[0]+2./3*(Q1[0]-Q0[0]), Q0[1]+2./3*(Q1[1]-Q0[1]))
    C2 = (C1[0]+1./3*(Q2[0]-Q0[0]), C1[1]+1./3*(Q2[1]-Q0[1]))
    C3 = Q2
    return C0, C1, C2, C3

from math import cos, sin, pi, sqrt, acos, ceil, copysign, fabs, hypot, degrees, radians
def vectorAngle(u,v):
    d = hypot(*u)*hypot(*v)
    c = (u[0]*v[0]+u[1]*v[1])/d
    if c<-1: c = -1
    elif c>1: c = 1
    s = u[0]*v[1]-u[1]*v[0]
    return degrees(copysign(acos(c),s))

def endPointToCenterParameters(x1,y1,x2,y2,fA,fS,rx,ry,phi=0):
    '''
    see http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes F.6.5
    note that we reduce phi to zero outside this routine 
    '''
    rx = fabs(rx)
    ry = fabs(ry)

    #step 1
    if phi:
        phiRad = radians(phi)
        sinPhi = sin(phiRad)
        cosPhi = cos(phiRad)
        tx = 0.5*(x1-x2)
        ty = 0.5*(y1-y2)
        x1d = cosPhi*tx - sinPhi*ty
        y1d = sinPhi*tx + cosPhi*ty
    else:
        x1d = 0.5*(x1-x2)
        y1d = 0.5*(y1-y2)

    #step 2
    #we need to calculate
    # (rx*rx*ry*ry-rx*rx*y1d*y1d-ry*ry*x1d*x1d)
    # -----------------------------------------
    #     (rx*rx*y1d*y1d+ry*ry*x1d*x1d)
    #
    # that is equivalent to
    # 
    #          rx*rx*ry*ry 
    # = -----------------------------  -    1
    #   (rx*rx*y1d*y1d+ry*ry*x1d*x1d)
    #
    #              1
    # = -------------------------------- - 1
    #   x1d*x1d/(rx*rx) + y1d*y1d/(ry*ry)
    #
    # = 1/r - 1
    #
    # it turns out r is what they recommend checking
    # for the negative radicand case
    r = x1d*x1d/(rx*rx) + y1d*y1d/(ry*ry)
    if r>1:
        rr = sqrt(r)
        rx *= rr
        ry *= rr
        r = x1d*x1d/(rx*rx) + y1d*y1d/(ry*ry)
    r = 1/r - 1
    if -1e-10<r<0: r = 0
    r = sqrt(r)
    if fA==fS: r = -r
    cxd = (r*rx*y1d)/ry
    cyd = -(r*ry*x1d)/rx

    #step3
    if phi:
        cx = cosPhi*cxd - sinPhi*cyd + 0.5*(x1+x2)
        cy = sinPhi*cxd + cosPhi*cyd + 0.5*(y1+y2)
    else:
        cx = cxd + 0.5*(x1+x2)
        cy = cyd + 0.5*(y1+y2)

    #step 4
    theta1 = vectorAngle((1,0),((x1d-cxd)/rx,(y1d-cyd)/ry))
    dtheta = vectorAngle(((x1d-cxd)/rx,(y1d-cyd)/ry),((-x1d-cxd)/rx,(-y1d-cyd)/ry)) % 360
    if fS==0 and dtheta>0: dtheta -= 360
    elif fS==1 and dtheta<0: dtheta += 360
    return cx, cy, rx, ry, -theta1, -dtheta

def bezierArcFromCentre(cx,cy, rx, ry, startAng=0, extent=90):
    if abs(extent) <= 90:
        arcList = [startAng]
        fragAngle = float(extent)
        Nfrag = 1
    else:
        arcList = []
        Nfrag = int(ceil(abs(extent)/90.))
        fragAngle = float(extent) / Nfrag

    fragRad = radians(fragAngle)
    halfRad = fragRad * 0.5
    kappa = abs(4. / 3. * (1. - cos(halfRad)) / sin(halfRad))

    if fragAngle < 0:
        kappa = -kappa

    pointList = []
    pointList_append = pointList.append
    theta1 = radians(startAng)
    startRad = theta1 + fragRad

    c1 = cos(theta1)
    s1 = sin(theta1)
    for i in range(Nfrag):
        c0 = c1
        s0 = s1
        theta1 = startRad + i*fragRad
        c1 = cos(theta1)
        s1 = sin(theta1)
        pointList_append((cx + rx * c0,
                          cy - ry * s0,
                          cx + rx * (c0 - kappa * s0),
                          cy - ry * (s0 + kappa * c0),
                          cx + rx * (c1 + kappa * s1),
                          cy - ry * (s1 - kappa * c1),
                          cx + rx * c1,
                          cy - ry * s1))
    return pointList

def bezierArcFromBox(x1,y1, x2,y2, startAng=0, extent=90):
    """bezierArcFromBox(x1,y1, x2,y2, startAng=0, extent=90) --> List of Bezier
curve control points.

(x1, y1) and (x2, y2) are the corners of the enclosing rectangle.  The
coordinate system has coordinates that increase to the right and down.
Angles, measured in degress, start with 0 to the right (the positive X
axis) and increase counter-clockwise.  The arc extends from startAng
to startAng+extent.  I.e. startAng=0 and extent=180 yields an openside-down
semi-circle.

The resulting coordinates are of the form (x1,y1, x2,y2, x3,y3, x4,y4)
such that the curve goes from (x1, y1) to (x4, y4) with (x2, y2) and
(x3, y3) as their respective Bezier control points.

Contributed by Robert Kern.

The algorithm is an elliptical generalization of the formulae in
Jim Fitzsimmon's TeX tutorial <URL: http://www.tinaja.com/bezarc1.pdf>.
"""
    cx, cy, rx,ry = _bd2cr(x1,y1,x2,y2)
    return bezierArcFromCentre(cx,cy, rx, ry, startAng, extent)

def bezierArcFromEndPoints(x1,y1,rx,ry,phi,fA,fS,x2,y2):
    if phi:
        #our box bezier arcs can't handle rotations directly
        #move to a well known point, eliminate phi and transform the other point
        mx = mmult(rotate(-phi),translate(-x1,-y1))
        tx2,ty2 = transformPoint(mx,(x2,y2))
        #convert to box form in unrotated coords
        cx, cy, rx, ry, startAng, extent = endPointToCenterParameters(0,0,tx2,ty2,fA,fS,rx,ry)
        bp = bezierArcFromCentre(cx,cy, rx, ry, startAng, extent)
        #re-rotate by the desired angle and add back the translation
        mx = mmult(translate(x1,y1),rotate(phi))
        res = []
        for x1,y1,x2,y2,x3,y3,x4,y4 in bp:
            res.append(transformPoint(mx,(x1,y1))+transformPoint(mx,(x2,y2))+transformPoint(mx,(x3,y3))+transformPoint(mx,(x4,y4)))
        return res
    else:
        cx, cy, rx, ry, startAng, extent = endPointToCenterParameters(x1,y1,x2,y2,fA,fS,rx,ry)
        return bezierArcFromCentre(cx,cy, rx, ry, startAng, extent)

def fixSvgPath(aList):
    """Normalise certain "abnormalities" in SVG paths.

    Basically, this reduces adjacent number values for h and v
    operators to the sum of these numbers and those for H and V
    operators to the last number only.

    Returns a slightly more compact list if such reductions
    were applied or a copy of the same list, otherwise.
    """

    # this could also modify the path to contain an op code
    # for each coord. tuple of a tuple sequence... 

    hPos, vPos, HPos, VPos, numPos = [], [], [], [], []
    for i in range(len(aList)):
        hPos.append(aList[i]=='h')
        vPos.append(aList[i]=='v')
        HPos.append(aList[i]=='H')
        VPos.append(aList[i]=='V')
        numPos.append(type(aList[i])==type(1.0))

    fixedList = []
    fixedList_append = fixedList.append

    i = 0
    while i < len(aList):
        if hPos[i] + vPos[i] + HPos[i] + VPos[i] == 0:
            fixedList_append(aList[i])
        elif hPos[i] == 1 or vPos[i] == 1:
            fixedList_append(aList[i])
            s = 0
            j = i+1
            while j < len(aList) and numPos[j] == 1:
                s += aList[j]
                j += 1
            fixedList_append(s)
            i = j-1
        elif HPos[i] == 1 or VPos[i] == 1:
            fixedList_append(aList[i])
            last = 0
            j = i+1
            while j < len(aList) and numPos[j] == 1:
                last = aList[j]
                j += 1
            fixedList_append(last)
            i = j-1
        i += 1
    return fixedList

def normaliseSvgPath(attr):
    """Normalise SVG path.

    This basically introduces operator codes for multi-argument
    parameters. Also, it fixes sequences of consecutive M or m
    operators to MLLL... and mlll... operators. It adds an empty
    list as argument for Z and z only in order to make the resul-
    ting list easier to iterate over.

    E.g. "M 10 20, M 20 20, L 30 40, 40 40, Z" 
      -> ['M', [10, 20], 'L', [20, 20], 'L', [30, 40], 'L', [40, 40], 'Z', []]
    """

    # operator codes mapped to the minimum number of expected arguments 
    ops = {'A':7, 'a':7,
      'Q':4, 'q':4, 'T':2, 't':2, 'S':4, 's':4, 
      'M':2, 'L':2, 'm':2, 'l':2, 'H':1, 'V':1,  
      'h':1, 'v':1, 'C':6, 'c':6, 'Z':0, 'z':0}

    # do some preprocessing
    opKeys = list(ops.keys())
    a = attr
    a = a.replace(',', ' ')
    a = string.replace(a, 'e-', 'ee')
    a = string.replace(a, '-', ' -')
    a = string.replace(a, 'ee', 'e-')
    for op in opKeys:
        a = a.replace(op, " %s " % op)
    a = a.strip()
    a = a.split()
    a = convertToFloats(a)
    a = fixSvgPath(a)

    # insert op codes for each argument of an op with multiple arguments
    res = []
    res_append = res.append
    i = 0
    while i < len(a):
        el = a[i]
        if el in opKeys:
            if el in 'zZ':
                res_append(el)
                res_append([])
            else:
                n = ops[el]
                if el in 'mM':
                    if not i:
                        #first element
                        eln = 'l'
                        el = 'M'
                    else:
                        eln = 'l' if el=='m' else 'L'
                else:
                    eln = el
                while i < len(a)-1:
                    if a[i+1] not in opKeys:
                        res_append(el)
                        res_append(a[i+1:i+1+n])
                        el = eln
                        i += n
                    else:
                        break
        i += 1

    return res

### attribute converters (from SVG to RLG)

class AttributeConverter:
    "An abstract class to locate and convert attributes in a DOM instance."

    def __init__(self,verbose=0):
        self.verbose = verbose

    def parseMultiAttributes(self, line):
        """Try parsing compound attribute string.

        Return a dictionary with single attributes in 'line'.
        """
    
        try:
            line = line.encode("ASCII")
        except:
            pass

        attrs = [_f for _f in [x.strip() for x in line.split(';')] if _f]

        newAttrs = {}
        for a in attrs:
            k, v = a.split(':')
            k, v = [s.strip() for s in (k, v)]
            newAttrs[k] = v
        return newAttrs

    def findAttr(self, svgNode, name):
        """Search an attribute with some name in some node or above.

        First the node is searched, then its style attribute, then
        the search continues in the node's parent node. If no such
        attribute is found, '' is returned. 
        """

        # This needs also to lookup values like "url(#SomeName)"...    

        try:
            attrValue = svgNode.getAttribute(name)
        except:
            return ''

        if attrValue and attrValue != "inherit":
            return attrValue
        elif svgNode.getAttribute("style"):
            dict = self.parseMultiAttributes(svgNode.getAttribute("style"))
            if name in dict:
                return dict[name]
        else:
            if svgNode.parentNode:
                return self.findAttr(svgNode.parentNode, name)
        return ''

    def getAllAttributes(self, svgNode):
        "Return a dictionary of all attributes of svgNode or those inherited by it."

        dict = {}

        if svgNode.parentNode and svgNode.parentNode == 'g':
            dict.update(self.getAllAttributes(svgNode.parentNode))

        if svgNode.nodeType == svgNode.ELEMENT_NODE:
            style = svgNode.getAttribute("style")
            if style:
                d = self.parseMultiAttributes(style)
                dict.update(d)

        attrs = svgNode.attributes
        for i in range(attrs.length):
            a = attrs.item(i)
            if a.name != "style":
                dict[a.name.encode("ASCII")] = a.value
        return dict

    def id(self, svgAttr):
        "Return attribute as is."
        return svgAttr

    def convertTransform(self, svgAttr):
        """Parse transform attribute string.

        E.g. "scale(2) translate(10,20)" 
             -> [("scale", 2), ("translate", (10,20))]
        """

        line = svgAttr

        try:
            line = line.encode("ASCII")
        except:
            pass

        line = line.strip()
        ops = line[:]
        brackets = []
        indices = []
        for i in range(len(line)):
           if line[i] in "()": brackets.append(i)
        for i in range(0, len(brackets), 2):
            bi, bj = brackets[i], brackets[i+1]
            subline = line[bi+1:bj]
            subline = subline.strip()
            subline = subline.replace(',', ' ')
            subline = re.sub("[ ]+", ',', subline)
            indices.append(eval(subline))
            ops = ops[:bi] + ' '*(bj-bi+1) + ops[bj+1:]
        ops = ops.split()

        assert len(ops) == len(indices)
        result = []
        for i in range(len(ops)):
            result.append((ops[i], indices[i]))
        return result

class Svg2RlgAttributeConverter(AttributeConverter):
    "A concrete SVG to RLG attribute converter."

    def convertLength(self, svgAttr, percentOf=100):
        "Convert length to points."

        text = svgAttr
        if not text:
            return 0.0

        if text[-1] == '%':
            if self.verbose:
                print("Fiddling length unit: %")
            return float(text[:-1]) / 100 * percentOf
        elif text[-2:] == "pc":
            return float(text[:-2]) * pica

        newSize = text[:]
        for u in "em ex px".split():
            if newSize.find(u) >= 0:
                if self.verbose:
                    print("Ignoring unit: %s" % u)
                newSize = newSize.replace(u, '')

        newSize = newSize.strip()
        length = toLength(newSize)
        return length

    def convertLengthList(self, svgAttr):
        "Convert a list of lengths."

        t = svgAttr.replace(',', ' ')
        t = t.strip()
        t = re.sub("[ ]+", ' ', t)
        a = t.split(' ')
        a = list(map(self.convertLength, a))
        return a

    def convertColor(self, svgAttr):
        "Convert string to a RL color object."

        # fix it: most likely all "web colors" are allowed
        predefined = "aqua black blue fuchsia gray green lime maroon navy "
        predefined = predefined + "olive orange purple red silver teal white yellow "
        predefined = predefined + "lawngreen indianred aquamarine lightgreen brown"

        # This needs also to lookup values like "url(#SomeName)"...    

        text = svgAttr
        if not text or text == "none":
            return None

        try:
            text = text.encode("ASCII")
        except:
            pass

        if text in predefined.split():
            return getattr(colors, text)
        elif text == "currentColor":
            return "currentColor"
        elif len(text) == 7 and text[0] == '#':
            return colors.HexColor(text)
        elif len(text) == 4 and text[0] == '#':
            return colors.HexColor('#' + 2*text[1] + 2*text[2] + 2*text[3])
        elif text[:3] == "rgb" and text.find('%') < 0:
            t = text[:][3:]
            t = t.replace('%', '')
            tup = eval(t)
            tup = [h[2:] for h in list(map(hex, tup))]
            tup = [(2-len(h))*'0'+h for h in tup]
            col = "#%s%s%s" % tuple(tup)
            return colors.HexColor(col)
        elif text[:3] == 'rgb' and text.find('%') >= 0:
            t = text[:][3:]
            t = t.replace('%', '')
            tup = eval(t)
            tup = [c/100.0 for c in tup]
            col = colors.Color(*tup)
            return col

        if self.verbose:
            print("Can't handle color:", text)
        return None

    def convertLineJoin(self, svgAttr):
        return {"miter":0, "round":1, "bevel":2}[svgAttr]

    def convertLineCap(self, svgAttr):
        return {"butt":0, "round":1, "square":2}[svgAttr]

    def convertDashArray(self, svgAttr):
        strokeDashArray = self.convertLengthList(svgAttr)
        return strokeDashArray

    def convertDashOffset(self, svgAttr):
        strokeDashOffset = self.convertLength(svgAttr)
        return strokeDashOffset

    def convertFontFamily(self, svgAttr):
        # very hackish
        fontMapping = {"sans-serif":"Helvetica", 
                       "serif":"Times-Roman", 
                       "monospace":"Courier"}
        fontName = svgAttr
        if not fontName:
            return ''
        try:
            fontName = fontMapping[fontName]
        except KeyError:
            pass
        if fontName not in ("Helvetica", "Times-Roman", "Courier"):
            fontName = "Helvetica"
        return fontName

class NodeTracker:
    """An object wrapper keeping track of arguments to certain method calls.

    Instances wrap an object and store all arguments to one special
    method, getAttribute(name), in a list of unique elements, usedAttrs.
    """

    def __init__(self, anObject):
        self.object = anObject
        self.usedAttrs = []

    def getAttribute(self, name):
        # add argument to the history, if not already present
        if name not in self.usedAttrs:
            self.usedAttrs.append(name)
        # forward call to wrapped object
        return self.object.getAttribute(name)

    # also getAttributeNS(uri, name)?

    def __getattr__(self, name):
        # forward attribute access to wrapped object 
        return getattr(self.object, name)


class Definitions(dict):
    '''dict that performs an action when pending definitions are set'''
    def __new__(cls,renderer,*args):
        self = dict.__new__(cls,*args)
        self.pending = {}
        self.renderer = renderer
        return self

    def __init__(self,renderer,*args):
        dict.__init__(self,*args)

    def addPending(self,key,g,node):
        self.pending.setdefault(key,[]).append((g,node))

    def __setitem__(self,key,value):
        dict.__setitem__(self,key,value)
        if key in self.pending:
            P = self.pending.pop(key)
            renderer = self.renderer
            for gr, node in P:
                x = renderer.attrConverter.convertLength(renderer.attrConverter.findAttr(node,'x'))
                y = renderer.attrConverter.convertLength(renderer.attrConverter.findAttr(node,'y'))
                transform = n.getAttribute('transform')
                if x or y:
                    transform += 'translate(%s,%s)' % (x,y)
                if transform:
                    renderer.shapeConverter.applyTransformOnGroup(transform, gr)
                gr.add(copy.deepcopy(value))

### the main meat ###
class SvgRenderer:
    """Renderer that renders an SVG file on a ReportLab Drawing instance.

    This is the base class for walking over an SVG DOM document and
    transforming it into a ReportLab Drawing instance.
    """

    def __init__(self, path=None, verbose=0):
        self.attrConverter = Svg2RlgAttributeConverter(verbose=verbose)
        self.shapeConverter = Svg2RlgShapeConverter(verbose=verbose)
        self.shapeConverter.svgSourceFile = path
        self.handledShapes = self.shapeConverter.getHandledShapes()
        self.drawing = None
        self.mainGroup = Group()
        self.definitions = Definitions(self)
        self.doesProcessDefinitions = 0
        self.verbose = verbose
        self.level = 0
        self.path = path
        self.logFile = None
        #if self.path:
        #    logPath = os.path.splitext(self.path)[0] + ".log"
        #    self.logFile = open(logPath, 'w')

    def render(self, node, parent=None):
        if parent == None:
            parent = self.mainGroup
        name = node.nodeName
        if self.verbose:
            format = "%s%s"
            args = ('  '*self.level, name)
            #if not self.logFile:
            #    print format % args
            #else:
            #    self.logFile.write((format+"\n") % args)

        if name == "svg":
            self.level += 1
            n = NodeTracker(node)
            drawing = self.renderSvg(n)
            children = n.childNodes
            for child in children:
                if child.nodeType != 1:
                    continue
                self.render(child, self.mainGroup)
            self.level -= 1
            self.printUnusedAttributes(node, n)
        elif name == "defs":
            self.doesProcessDefinitions = 1
            n = NodeTracker(node)
            self.level += 1
            self.renderG(n)
            self.level -= 1
            self.doesProcessDefinitions = 0
            self.printUnusedAttributes(node, n)
        elif name == 'a':
            self.level += 1
            n = NodeTracker(node)
            item = self.renderA(n)
            parent.add(item)
            self.level -= 1
            self.printUnusedAttributes(node, n)
        elif name == 'g':
            self.level += 1
            n = NodeTracker(node)
            display = n.getAttribute("display")
            if display != "none":
                item = self.renderG(n)
                parent.add(item)
            if self.doesProcessDefinitions:
                id = n.getAttribute("id")
                if id:
                    self.definitions[id] = item
            self.level -= 1
            self.printUnusedAttributes(node, n)
        elif name == "symbol":
            self.level += 1
            n = NodeTracker(node)
            item = self.renderSymbol(n)
            # parent.add(item)
            if self.doesProcessDefinitions:
                id = n.getAttribute("id")
                if id:
                    self.definitions[id] = item
            self.level -= 1
            self.printUnusedAttributes(node, n)
        elif name == 'use':
            self.level += 1
            n = NodeTracker(node)
            xlink_href = n.getAttribute('xlink:href').lstrip('#')
            gr = Group()
            if xlink_href in self.definitions:
                x = self.attrConverter.convertLength(self.attrConverter.findAttr(n,'x'))
                y = self.attrConverter.convertLength(self.attrConverter.findAttr(n,'y'))
                transform = n.getAttribute('transform')
                if x or y:
                    transform += 'translate(%s,%s)' % (x,y)
                if transform:
                    self.shapeConverter.applyTransformOnGroup(transform, gr)
                gr.add(copy.deepcopy(self.definitions[xlink_href]))
                parent.add(gr)
                self.level -= 1
                self.printUnusedAttributes(node, n)
            else:
                parent.add(gr)
                self.level -= 1
                self.definitions.addPending(xlink_href,gr,node)
        elif name in self.handledShapes:
            methodName = "convert"+name.capitalize()
            n = NodeTracker(node)
            shape = getattr(self.shapeConverter, methodName)(n)
            if shape:
                self.shapeConverter.applyStyleOnShape(shape, n)
                transform = n.getAttribute("transform")
                display = n.getAttribute("display")
                if transform and display != "none":
                    gr = Group()
                    self.shapeConverter.applyTransformOnGroup(transform, gr)
                    gr.add(shape)
                    parent.add(gr)
                elif display != "none":
                    if self.doesProcessDefinitions:
                        id = n.getAttribute("id")
                        if id:
                            self.definitions[id] = shape
                    parent.add(shape)
                self.printUnusedAttributes(node, n)
        else:
            if self.verbose:
                print("Ignoring node: %s" % name)

    def printUnusedAttributes(self, node, n):
        allAttrs = list(self.attrConverter.getAllAttributes(node).keys())
        unusedAttrs = []

        for a in allAttrs:
            if a not in n.usedAttrs:
                unusedAttrs.append(a)

        if self.verbose and unusedAttrs:
            format = "%s-Unused: %s"
            args = ("  "*(self.level+1), ', '.join(unusedAttrs))
            #if not self.logFile:
            #    print format % args
            #else:
            #    self.logFile.write((format+"\n") % args)

        if self.verbose and unusedAttrs:
            #print "Used attrs:", n.nodeName, n.usedAttrs
            #print "All attrs:", n.nodeName, allAttrs
            print("Unused attrs:", n.nodeName, unusedAttrs)

    def renderTitle_(self, node):
        # Main SVG title attr. could be used in the PDF document info field.
        pass

    def renderDesc_(self, node):
        # Main SVG desc. attr. could be used in the PDF document info field.
        pass

    def renderSvg(self, node):
        getAttr = node.getAttribute
        width, height = list(map(getAttr, ("width", "height")))
        width, height = list(map(self.attrConverter.convertLength, (width, height)))
        viewBox = getAttr("viewBox")
        if viewBox:
            viewBox = self.attrConverter.convertLengthList(viewBox)
            width, height = viewBox[2:4]
        self.drawing = Drawing(width, height)
        return self.drawing

    def renderG(self, node, display=1):
        getAttr = node.getAttribute
        id, style, transform = list(map(getAttr, ("id", "style", "transform")))
        #sw = map(getAttr, ("stroke-width",))
        self.attrs = self.attrConverter.parseMultiAttributes(style)
        gr = Group()
        children = node.childNodes
        for child in children:
            if child.nodeType != 1:
                continue
            item = self.render(child, parent=gr)
            if item and display: 
                gr.add(item)

        if transform:
            self.shapeConverter.applyTransformOnGroup(transform, gr)
        return gr

    def renderSymbol(self, node):
        return self.renderG(node, display=0)

    def renderA(self, node):
        # currently nothing but a group...
        # there is no linking info stored in shapes, maybe a group should?
        return self.renderG(node)

    def renderUse(self, node):
        xlink_href = node.getAttributeNS("http://www.w3.org/1999/xlink", "href")
        grp = Group()
        try:
            item = self.definitions[xlink_href[1:]]
            grp.add(item)
            transform = node.getAttribute("transform")
            if self.verbose>2:
                print('renderUse: transform=%r'%transform)
            if transform:
                self.shapeConverter.applyTransformOnGroup(transform, grp)
        except KeyError:
            if self.verbose:
                print("Ignoring unavailable object width ID '%s'." % xlink_href)
        return grp

    def finish(self):
        height = self.drawing.height
        self.mainGroup.scale(1, -1)
        self.mainGroup.translate(0, -height)
        self.drawing.add(self.mainGroup)
        return self.drawing

class SvgShapeConverter:
    """An abstract SVG shape converter.

    Implement subclasses with methods named 'renderX(node)', where
    'X' should be the capitalised name of an SVG node element for 
    shapes, like 'Rect', 'Circle', 'Line', etc.

    Each of these methods should return a shape object appropriate
    for the target format.
    """

    def __init__(self,verbose=0,attrConverter=AttributeConverter):
        self.verbose = verbose
        self.attrConverter = attrConverter(verbose=verbose)
        self.svgSourceFile = ''

    def getHandledShapes(self):
        "Determine a list of handled shape elements."

        items = dir(self)
        items = list(self.__class__.__dict__.keys())
        keys = []
        for i in items:
            keys.append(getattr(self, i))
        keys = [k for k in keys if type(k) == types.MethodType]
        keys = [k.__name__ for k in keys]
        keys = [k for k in keys if k[:7] == "convert"]
        keys = [k for k in keys if k != "convert"]
        keys = [k[7:] for k in keys]
        shapeNames = [k.lower() for k in keys]
        return shapeNames

def svgPath2RL(path,verbose=False):
    pts = []
    ops = []
    ops_append = ops.append
    lastM = 0,0
    wasz = False
    prevOp = None

    for i in range(0, len(path), 2):
        op, nums = path[i:i+2]
        if ops and op in 'mM' and not wasz:
            #special check to see if we should 'close' previous sub-path
            if pts[-2]==lastM[0] and pts[-1]==lastM[1]:
                ops_append(3)
        wasz = False

        # moveto, lineto absolute
        if op in ('M', 'L'):
            xn, yn = nums
            pts += [xn, yn]
            if op == 'M': 
                ops_append(0)
                lastM = xn, yn
            elif op == 'L': 
                ops_append(1)

        # moveto, lineto relative
        elif op == 'm':
            xn, yn = nums
            xn += pts[-2]
            yn += pts[-1]
            pts += [xn,yn]
            ops_append(0)
            lastM = xn, yn
        elif op == 'l':
            xn, yn = nums
            pts += [pts[-2]+xn, pts[-1]+yn]
            ops_append(1)
        elif op in 'aA':
            rx,ry,phi,fA,fS,x2,y2 = nums
            x1, y1 = pts[-2:]
            if op=='a':
                x2 += x1
                y2 += y1
            if abs(rx)<=1e-10 or abs(ry)<=1e-10:
                ops_append(1)
                pts += [x2,y2]
            else:
                bp = bezierArcFromEndPoints(x1,y1,rx,ry,phi,fA,fS,x2,y2)
                for x1,y1,x2,y2,x3,y3,x4,y4 in bp:
                    ops_append(2)
                    pts += [x2,y2,x3,y3,x4,y4]
        # horizontal/vertical line absolute
        elif op in ('H', 'V'):
            k = nums[0]
            if op == 'H':
                pts += [k, pts[-1]]
            elif op == 'V':
                pts += [pts[-2], k]
            ops_append(1)

        # horizontal/vertical line relative
        elif op in ('h', 'v'):
            k = nums[0]
            if op == 'h':
                pts += [pts[-2]+k, pts[-1]]
            elif op == 'v':
                pts += [pts[-2], pts[-1]+k]
            ops_append(1)

        # cubic bezier, absolute
        elif op == 'C':
            x1, y1, x2, y2, xn, yn = nums
            pts += [x1, y1, x2, y2, xn, yn]
            ops_append(2)
        elif op == 'S':
            x2, y2, xn, yn = nums
            if ops:
                x0, y0 = pts[-2:]
                if prevOp in 'CcSs':
                    xp, yp, = pts[-4:-2]
                else:
                    xp = x0
                    yp = y0
            else:
                xp = x0 = x2
                yp = y0 = y2
            xi, yi = x0+(x0-xp), y0+(y0-yp)
            pts += [xi, yi, x2, y2, xn, yn]
            ops_append(2)

        # cubic bezier, relative
        elif op == 'c':
            xp, yp = pts[-2:]
            x1, y1, x2, y2, xn, yn = nums
            pts += [xp+x1, yp+y1, xp+x2, yp+y2, xp+xn, yp+yn]
            ops_append(2)
        elif op == 's':
            x2, y2, xn, yn = nums
            if ops:
                x0, y0 = pts[-2:]
                if prevOp in 'CcSs':
                    xp, yp = pts[-4:-2]
                else:
                    xp = x0
                    yp = y0
            else:
                xp = x0 = x2
                yp = y0 = y2
            xi, yi = x0+(x0-xp), y0+(y0-yp)
            pts += [xi, yi, x0+x2, y0+y2, x0+xn, y0+yn]
            ops_append(2)

        # quadratic bezier, absolute
        elif op == 'Q':
            x0, y0 = pts[-2:]
            x1, y1, xn, yn = nums
            (x0,y0), (x1,y1), (x2,y2), (xn,yn) = \
                convertQuadraticToCubicPath((x0,y0), (x1,y1), (xn,yn))
            pts += [x1,y1, x2,y2, xn,yn]
            ops_append(2)
        elif op == 'T':
            xn, yn = nums
            if ops:
                x0, y0 = pts[-2:]
                if prevOp in 'QqTt':
                    xp, yp = pts[-4:-2]
                else:
                    xp = x0
                    yp = y0
            xi, yi = x0+(x0-xp), y0+(y0-yp)
            (x0,y0), (x1,y1), (x2,y2), (xn,yn) = \
                convertQuadraticToCubicPath((x0,y0), (xi,yi), (xn,yn))
            pts += [x1,y1, x2,y2, xn,yn]
            ops_append(2)

        # quadratic bezier, relative
        elif op == 'q':
            x1, y1, xn, yn = nums
            if ops:
                x0, y0 = pts[-2:]
            else:
                x0 = x1
                y0 = y1
            x1, y1, xn, yn = x0+x1, y0+y1, x0+xn, y0+yn
            (x0,y0), (x1,y1), (x2,y2), (xn,yn) = \
                convertQuadraticToCubicPath((x0,y0), (x1,y1), (xn,yn))
            pts += [x1,y1, x2,y2, xn,yn]
            ops_append(2)
        elif op == 't':
            xn, yn = nums
            if ops:
                x0, y0 = pts[-2:]
                xn += x0
                yn += y0
                if prevOp in 'QqTt':
                    xp, yp = pts[-4:-2]
                else:
                    xp = x0
                    yp = y0
            else:
                xp = x0 = xn
                yp = y0 = yn
            xi, yi = x0+(x0-xp), y0+(y0-yp)
            (x0,y0), (x1,y1), (x2,y2), (xn,yn) = \
                convertQuadraticToCubicPath((x0,y0), (xi,yi), (xn,yn))
            pts += [x1,y1, x2,y2, xn,yn]
            ops_append(2)

        # close path
        elif op in ('Z', 'z'):
            ops_append(3)
            wasz = True
            try:
                nextOp = path[i+1]
                if nextOp!='M':
                    pts += list(lastM)
                    ops_append(0)
            except:
                pass

        # arcs
        else: #if op in unhandledOps.keys():
            if verbose:
                print("Suspicious path operator:", op)
        prevOp = op

    return ops, pts

class Svg2RlgShapeConverter(SvgShapeConverter):
    "Converte from SVG shapes to RLG (ReportLab Graphics) shapes."

    def __init__(self,verbose=0):
        SvgShapeConverter.__init__(self,verbose=verbose,attrConverter=Svg2RlgAttributeConverter)

    def convertLine(self, node):
        getAttr = node.getAttribute
        x1, y1, x2, y2 = list(map(getAttr, ("x1", "y1", "x2", "y2")))
        x1, y1, x2, y2 = list(map(self.attrConverter.convertLength, (x1, y1, x2, y2)))
        shape = Line(x1, y1, x2, y2)
        return shape

    def convertRect(self, node):
        getAttr = node.getAttribute
        x, y, width, height = list(map(getAttr, ('x', 'y', "width", "height")))
        x, y, width, height = list(map(self.attrConverter.convertLength, (x, y, width, height)))
        rx, ry = list(map(getAttr, ("rx", "ry")))
        rx, ry = list(map(self.attrConverter.convertLength, (rx, ry)))
        shape = Rect(x, y, width, height, rx=rx, ry=ry)
        return shape

    def convertCircle(self, node):
        # not rendered if r == 0, error if r < 0.
        getAttr = node.getAttribute
        cx, cy, r = list(map(getAttr, ("cx", "cy", 'r')))
        cx, cy, r = list(map(self.attrConverter.convertLength, (cx, cy, r)))
        shape = Circle(cx, cy, r)
        return shape

    def convertEllipse(self, node):
        getAttr = node.getAttribute
        cx, cy, rx, ry = list(map(getAttr, ("cx", "cy", "rx", "ry")))
        cx, cy, rx, ry = list(map(self.attrConverter.convertLength, (cx, cy, rx, ry)))
        width, height = rx, ry
        shape = Ellipse(cx, cy, width, height)
        return shape

    def convertPolyline(self, node):
        getAttr = node.getAttribute
        points = getAttr("points")
        points = points.replace(',', ' ')
        points = points.split()
        points = list(map(self.attrConverter.convertLength, points))

        # Need to use two shapes, because standard RLG polylines
        # do not support filling...
        gr = Group()
        shape = Polygon(points)
        self.applyStyleOnShape(shape, node)
        shape.strokeColor = None
        gr.add(shape)
        shape = PolyLine(points)
        self.applyStyleOnShape(shape, node)
        gr.add(shape)
        return gr

    def convertPolygon(self, node):
        getAttr = node.getAttribute
        points = getAttr("points")
        points = points.replace(',', ' ')
        points = points.split()
        points = list(map(self.attrConverter.convertLength, points))
        shape = Polygon(points)
        return shape

    def convertText0(self, node):
        getAttr = node.getAttribute
        x, y = list(map(getAttr, ('x', 'y')))
        if not x: x = '0'
        if not y: y = '0'
        text = ''
        if node.firstChild.nodeValue:
            try:
                text = node.firstChild.nodeValue.encode("ASCII")
            except:
                text = "Unicode"
        x, y = list(map(self.attrConv.convertLength, (x, y)))
        shape = String(x, y, text)
        self.applyStyleOnShape(shape, node)
        gr = Group()
        gr.add(shape)
        gr.scale(1, -1)
        gr.translate(0, -2*y)
        return gr

    def convertText(self, node):
        attrConv = self.attrConverter
        getAttr = node.getAttribute
        x, y = list(map(getAttr, ('x', 'y')))
        x, y = list(map(attrConv.convertLength, (x, y)))

        gr = Group()

        text = ''
        chNum = len(node.childNodes)
        frags = []
        fragLengths = []

        dx0, dy0 = 0, 0
        x1, y1 = 0, 0
        ff = attrConv.findAttr(node, "font-family") or "Helvetica"
        ff = ff.encode("ASCII")
        ff = attrConv.convertFontFamily(ff)
        fs = attrConv.findAttr(node, "font-size") or "12"
        fs = fs.encode("ASCII")
        fs = attrConv.convertLength(fs)
        for c in node.childNodes:
            dx, dy = 0, 0
            baseLineShift = 0
            if c.nodeType == c.TEXT_NODE:
                frags.append(c.nodeValue)
                try:
                    tx = ''.join([chr(ord(f)) for f in frags[-1]])
                except ValueError:
                    tx = "Unicode"
            elif c.nodeType == c.ELEMENT_NODE and c.nodeName == "tspan":
                frags.append(c.firstChild.nodeValue)
                tx = ''.join([chr(ord(f)) for f in frags[-1]])
                getAttr = c.getAttribute
                y1 = getAttr('y')
                y1 = attrConv.convertLength(y1)
                dx, dy = list(map(getAttr, ("dx", "dy")))
                dx, dy = list(map(attrConv.convertLength, (dx, dy)))
                dx0 += dx
                dy0 += dy
                baseLineShift = getAttr("baseline-shift") or '0'
                if baseLineShift in ("sub", "super", "baseline"):
                    baseLineShift = {"sub":-fs/2, "super":fs/2, "baseline":0}[baseLineShift]
                else:
                    baseLineShift = attrConv.convertLength(baseLineShift, fs)
            elif c.nodeType == c.ELEMENT_NODE and c.nodeName != "tspan":
                continue

            fragLengths.append(stringWidth(tx, ff, fs))
            rl = reduce(operator.__add__, fragLengths[:-1], 0)
            try:
                text = ''.join([chr(ord(f)) for f in frags[-1]])
            except ValueError:
                text = "Unicode"
            shape = String(x+rl, y-y1-dy0+baseLineShift, text)
            self.applyStyleOnShape(shape, node)
            if c.nodeType == c.ELEMENT_NODE and c.nodeName == "tspan":
                self.applyStyleOnShape(shape, c)

            gr.add(shape)

        gr.scale(1, -1)
        gr.translate(0, -2*y)
        return gr

    def convertPath(self, node):
        d = node.getAttribute('d')
        path = normaliseSvgPath(d)
        if self.verbose: print(repr(path))
        ops, pts = svgPath2RL(path,self.verbose)

        if not ops: return

        # hack because RLG has no "semi-closed" paths...
        gr = Group()
        if ops[-1] == 3:
            p = Path(pts, ops)
            self.applyStyleOnShape(p, node)
            fc = self.attrConverter.findAttr(node, "fill")
            if not fc:
                p.fillColor = colors.black
            sc = self.attrConverter.findAttr(node, "stroke")
            if not sc:
                p.strokeColor = None
            gr.add(p)
        else:
            fc = self.attrConverter.findAttr(node, "fill")
            if fc:
                p = Path(pts, ops+[3])
                self.applyStyleOnShape(p, node)
                p.strokeColor = None
                gr.add(p)
            else:
                sc = self.attrConverter.findAttr(node, "stroke")
                if sc:
                    p = Path(pts, ops)
                    self.applyStyleOnShape(p, node)
                    gr.add(p)
        return gr

    def convertImage(self, node):
        if self.verbose:
            print("Adding box instead image.")
        getAttr = node.getAttribute
        x, y, width, height = list(map(getAttr, ('x', 'y', "width", "height")))
        x, y, width, height = list(map(self.attrConverter.convertLength, (x, y, width, height)))
        xlink_href = node.getAttributeNS("http://www.w3.org/1999/xlink", "href")
        try:
            xlink_href = xlink_href.encode("ASCII")
        except:
            pass
        xlink_href = os.path.join(os.path.dirname(self.svgSourceFile), xlink_href)
        # print "***", x, y, width, height, xlink_href[:30]

        magic = "data:image/jpeg;base64"
        if xlink_href[:len(magic)] == magic:
            pat = "data:image/(\w+?);base64"
            ext = re.match(pat, magic).groups()[0]
            import base64, md5
            jpegData = base64.decodestring(xlink_href[len(magic):])
            hashVal = md5.new(jpegData).hexdigest()
            name = "images/img%s.%s" % (hashVal, ext)
            path = os.path.join(dirname(self.svgSourceFile), name)
            open(path, "wb").write(jpegData)
            img = Image(x, y+height, width, -height, path)
            # this needs to be removed later, not here...
            # if exists(path): os.remove(path)
        else:
            xlink_href = os.path.join(os.path.dirname(self.svgSourceFile), xlink_href)
            img = Image(x, y+height, width, -height, xlink_href)
        return img

    def applyTransformOnGroup(self, transform, group):
        """Apply an SVG transformation to a RL Group shape.

        The transformation is the value of an SVG transform attribute
        like transform="scale(1, -1) translate(10, 30)".

        rotate(<angle> [<cx> <cy>]) is equivalent to:
          translate(<cx> <cy>) rotate(<angle>) translate(-<cx> -<cy>)
        """

        tr = self.attrConverter.convertTransform(transform)
        for op, values in tr:
            if op == "scale":
                if type(values) != tuple:
                    values = (values, values)
                group.scale(*values)
            elif op == "translate":
                try: # HOTFIX
                    values = values[0], values[1]
                except TypeError:
                    return
                group.translate(*values)
            elif op == "rotate":
                if type(values) != tuple or len(values) == 1:
                    group.rotate(values)
                elif len(values) == 3:
                    angle, cx, cy = values
                    group.translate(cx, cy)
                    group.rotate(angle)
                    group.translate(-cx, -cy)
            elif op == "skewX":
                group.skew(values, 0)
            elif op == "skewY":
                group.skew(0, values)
            elif op == "matrix":
                group.transform = values
            else:
                if self.verbose:
                    print("Ignoring transform:", op, values)

    def applyStyleOnShape(self, shape, *nodes):
        "Apply styles from SVG elements to an RLG shape."

        # RLG-specific: all RLG shapes
        "Apply style attributes of a sequence of nodes to an RL shape."

        # tuple format: (svgAttr, rlgAttr, converter, default)
        mappingN = (
            ("fill", "fillColor", "convertColor", "none"), 
            ("stroke", "strokeColor", "convertColor", "none"),
            ("stroke-width", "strokeWidth", "convertLength", "0"),
            ("stroke-linejoin", "strokeLineJoin", "convertLineJoin", "0"),
            ("stroke-linecap", "strokeLineCap", "convertLineCap", "0"),
            ("stroke-dasharray", "strokeDashArray", "convertDashArray", "none"),
        )
        mappingF = (
            ("font-family", "fontName", "convertFontFamily", "Helvetica"),
            ("font-size", "fontSize", "convertLength", "12"),
            ("text-anchor", "textAnchor", "id", "start"),
        )

        ac = self.attrConverter
        for node in nodes:
            for mapping in (mappingN, mappingF):
                if shape.__class__ != String and mapping == mappingF:
                    continue
                for (svgAttrName, rlgAttr, func, default) in mapping:
                    try:
                        svgAttrValue = ac.findAttr(node, svgAttrName) or default
                        if svgAttrValue == "currentColor":
                            svgAttrValue = ac.findAttr(node.parentNode, "color") or default
                        meth = getattr(ac, func)
                        setattr(shape, rlgAttr, meth(svgAttrValue))
                    except:
                        pass

            if shape.__class__ == String:
                svgAttr = ac.findAttr(node, "fill") or "black"
                setattr(shape, "fillColor", ac.convertColor(svgAttr))

def svg2rlg(path,verbose=0):
    "Convert an SVG file to an RLG Drawing object."
    
    # unzip .svgz file into .svg
    unzipped = False
    if os.path.splitext(path)[1].lower() == ".svgz":
        data = gzip.GzipFile(path, "rb").read()
        open(path[:-1], 'w').write(data)
        path = path[:-1]
        unzipped = True


    # load SVG file
    try:
        doc = xml.dom.minidom.parse(path)
        svg = doc.documentElement
    except:
        print("!!!!! Failed to load input file!")
        return

    # convert to a RLG drawing
    svgRenderer = SvgRenderer(path,verbose=verbose)
    svgRenderer.render(svg)
    drawing = svgRenderer.finish()

    # remove unzipped .svgz file (.svg)
    if unzipped:
        os.remove(path)
        
    return drawing

if __name__=='__main__':
    import glob, traceback
    argv = sys.argv[1:]
    outDir = os.getcwd()
    formats = ['pdf']
    verbose = 0
    i = 0
    while i < len(argv):
        arg = argv[i]
        i += 1
        if arg.startswith('--outdir='):
            outDir = arg[9:]
            continue
        if arg.startswith('--formats='):
            formats = list(map(str.strip,arg[10:].split(',')))
            continue
        if arg.startswith('--verbose='):
            verbose = int(arg[10:])
            continue
        for fn in glob.glob(arg):
            try:
                d = svg2rlg(fn,verbose=verbose)
                if d:
                    d.save(formats=formats,verbose=verbose,fnRoot=os.path.splitext(os.path.basename(fn))[0],outDir=outDir)
            except:
                traceback.print_exc()
