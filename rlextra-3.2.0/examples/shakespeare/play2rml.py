
"convert play.dtd format into RML"

USEILLUSTRATIONS = 0
from rlextra.radxml.xmlmap import MapController, MapNode
from rlextra.rml2pdf import rml2pdf
import string

def annotation0(n, x1, y1, xn):
    L = ['<path x="%scm" y="%scm"> <curvesto>' %(x1, y1)]
    dx = (xn-x1)*1.0/n
    for i in range(n):
        for x in [(0,1), (0.5,1), (0.5,1),
                      (1,1), (1,0), (1,0),
                      (1, -1), (1.5, -1), (1.5, -1),
                      (2, -1), (2, 0), (2, 0)]:
            #print x
            (k,j) = x
            L.append("%scm %scm" % (x1+dx*(i+k/2.0), y1+(j/2.0)))
    L.append("</curvesto></path>")
    return string.join(L, "\n")

def annotationC(n, xc, yc, r, d):
    from math import pi, sin, cos
    angle = 2*pi/n
    L = ['<path x="%scm" y="%scm"> <curvesto>' % (xc+r, yc)]
    for i in range(n):
        baseangle = i*angle
        for (deltaangle, scale) in [(0, d), (1, d), (1, 1)]:
            anglen = baseangle + deltaangle*angle
            radius = r*scale
            x = cos(anglen)*radius + xc
            y = sin(anglen)*radius + yc
            L.append("%scm %scm" % (x,y))
    L.append("</curvesto></path>")
    return string.join(L, "\n")

def annotation1():
    xmin = ymin = 2
    xmax = 19
    ymax = 27
    L = [annotation0(xmax-xmin, xmin, ymin, xmax),
         annotation0(xmax-xmin, xmin, ymax, xmax),
         '<rotate degrees="90"/>',
         annotation0(ymax-ymin, ymin, -xmax, ymax),
         annotation0(ymax-ymin, ymin, -xmin, ymax),
         ]
    return string.join(L, "\n")

def annotation():
    return """
    <form name="annotation">
    %s
    </form>
    <lineMode width="3"/>
    %s
    <lineMode width="10"/>
    <stroke color="cyan"/>
    <doForm name="annotation"/>
    <translate dx="21cm" dy="29.7cm"/>
    <rotate degrees="180"/>
    <stroke color="lightcyan"/>
    <doForm name="annotation"/>
    <lineMode width="5"/>
    <translate dx="3" dy="3"/>
    <stroke color="blue"/>
    <doForm name="annotation"/>
    <translate dx="21cm" dy="29.7cm"/>
    <rotate degrees="180"/>
    <stroke color="black"/>
    <doForm name="annotation"/>
    """ % (annotation1(), annotationC(n=17, xc=10.5, yc=29.7/2, r=2, d=0.4))

TOPLEVELRML = """<?xml version="1.0" encoding="utf-8" standalone="no" ?>
<!DOCTYPE document SYSTEM "rml.dtd">

<document filename="[[PDFFILENAME]]">

<template pageSize="(21cm, 29.7cm)"
        leftMargin="1.5cm"
        rightMargin="1.5cm"
        topMargin="1.5cm"
        bottomMargin="1.5cm"
        title="Shakespeare"
        author="Reportlab Inc"
        allowSplitting = "20"
        >

	<pageTemplate id="titlepage">
	    <pageGraphics>
	    [[ANNOTATION]]
        </pageGraphics>

        <frame id="main" x1="5cm" y1="2cm" width="11cm" height="21.7cm"/>

	</pageTemplate>
	
	<pageTemplate id="main">
        <pageGraphics></pageGraphics>
        <pageGraphics>
        <fill color="crimson"/>
        <setFont name="Times-Roman" size="7"/>
        <drawRightString x="20cm" y="28cm"><getName id="header" default="???"/></drawRightString>
        <drawString x="1cm" y="28.5cm">http://www.reportlab.com</drawString>
        <!-- uncomment lastpage below to slow down generation 2x (but get page count) -->
        <drawString x="1cm" y="1cm"><getName id="playtitle" default="???"/>, page <pageNumber/><!-- of <getName id="lastpage" default="???"/> -->
        </drawString>
        </pageGraphics>
        <frame id="main" x1="3.5cm" y1="3.5cm" width="14cm" height="22.7cm"/>

	</pageTemplate>
</template>

<stylesheet>
	<initialize>
	</initialize>
	
	<paraStyle name="playtitle"
        fontSize="40"
        leading="50"
        alignment="center"
        spaceBefore="5cm"
        spaceAfter="3cm"
        textColor="darkslateblue"
	/>
	
	<paraStyle name="title"
        fontSize="20"
        leading="25"
        alignment="center"
        spaceBefore="2cm"
        spaceAfter="1cm"
        textColor="darkgreen"
	/>

	<paraStyle name="fm"
        fontSize="10"
        leading="12"
        alignment="center"
        spaceBefore="0"
        spaceAfter="0"
        textColor="darkmagenta"
	/>
	
	<paraStyle name="persona"
        fontSize="14"
        leading="18"
        alignment="center"
        spaceBefore="0"
        spaceAfter="0"
        textColor="darkmagenta"
	/>
	
	<paraStyle name="grpdescr"
        fontSize="14"
        leading="18"
        alignment="right"
        spaceBefore="0"
        spaceAfter="0"
        textColor="darkgreen"
	/>

	<paraStyle name="speaker"
        fontSize="14"
        fontName="Times-Bold"        
        leading="18"
        alignment="left"
        spaceBefore="0"
        spaceAfter="0"
        textColor="darkgreen"
	/>
	
	<paraStyle name="line"
        fontSize="12"
        leading="18"
        alignment="left"
        spaceBefore="0"
        spaceAfter="0"
        leftIndent="1in"
	/>
	
	<paraStyle name="stagedir"
        fontName="Times-Italic"
        fontSize="12"
        leading="18"
        alignment="left"
        spaceBefore="10"
        spaceAfter="10"
        leftIndent="2in"
        textColor="darkmagenta"
	/>

</stylesheet>
<story>
<setNextTemplate name="main"/>
%(__content__)s

<spacer length="2cm"/>
<h3>END OF <getName id="playtitle" default="???"/></h3>
<namedString id="lastpage"><pageNumber/></namedString>
</story>
</document>
"""

def translateFiles(inputfilename="policytext.xml", rmlfilename="shakespeare.rml", pdffilename="shakespeare.pdf"):
    fn = inputfilename
    ofn = rmlfilename
    text = open(fn).read()
    otext = translateText(text, outputfilename=pdffilename)
    open(ofn, "w").write(otext)
    print("wrote", ofn)

def translateText(text, outputfilename="shakespearetest.pdf"):
    # fix toplevel
    toplevel = string.replace(TOPLEVELRML, "[[PDFFILENAME]]", outputfilename)
    toplevel = string.replace(toplevel, "[[ANNOTATION]]", annotation())
    # now define the mapper
    M = MapController()
    M.joinSeparator = ""
    M[""] = """%(__content__)s"""
    M["PLAY"] = toplevel
    M["TITLE"] = """<para style="playtitle">
    <name id="playtitle" value="%(__content__)s"/>
    <name id="header" value="%(__content__)s"/>
    %(__content__)s</para>
    <spacer length="2in"/><para style="title">by William Shakespeare</para>"""
    M["SUBTITLE"] = """<h1>%(__content__)s</h1>"""
    M["SUBHEAD"] = """<h1>%(__content__)s</h1>"""
    M["FM"] = """<spacer length="0.2in"/>%(__content__)s"""
    M["FM"]["P"] = """<para style="fm">%(__content__)s</para>"""
    M["P"] = """<para>%(__content__)s</para>"""
    M["PERSONAE"] = """<nextFrame/>%(__content__)s"""
    M["PERSONAE"]["TITLE"] = """<para style="title">%(__content__)s</para>"""
    M["PERSONA"] = """<para style="persona">%(__content__)s</para>"""
    M["PGROUP"] = """<spacer length="1cm"/>%(__content__)s<spacer length="1cm"/>"""
    M["GRPDESCR"] = """<para style="grpdescr"><i>%(__content__)s</i></para>"""
    M["SCNDESCR"] = """<para style="title"><i>%(__content__)s</i></para>"""
    M["PLAYSUBT"] = """<para style="title">%(__content__)s</para>"""
    M["PROLOGUE"] = """<nextFrame/>%(__content__)s"""
    M["PROLOGUE"]["TITLE"] = """<para style="title">%(__content__)s</para>"""
    M["SPEECH"] = """<condPageBreak height="4cm"/><spacer length="1cm"/>%(__content__)s"""
    if not USEILLUSTRATIONS and 0:
        # non optimized
        print("using paragraphs for lines and speakers")
        M["SPEAKER"] = """<para style="speaker"><b>%(__content__)s</b></para>"""
        M["LINE"] = """<para style="line">%(__content__)s</para>"""
        M["LINE"]["STAGEDIR"] = """<font color="darkmagenta"><i>[%(__content__)s]</i></font>"""
    elif USEILLUSTRATIONS: # non optimized, we don't need paragraphs, preformatted is faster
        print("using illustrations for lines and speakers")
        M["SPEAKER"] = """<para style="speaker"><b>%(__content__)s</b></para>"""
        M["LINE"] = """<illustration width="0" height="14">
        <setFont name="Times-Roman" size="12"/>
        <fill color="black"/>
        <drawString x="1in" y="2">%(__content__)s</drawString>
        </illustration>
        """
        M["LINE"]["STAGEDIR"] = """</drawString></illustration>
    
        <illustration width="0" height="14">
        <setFont name="Times-Italic" size="12"/>
        <fill color="darkmagenta"/>
        <drawString x="2in" y="2">%(__content__)s</drawString>
        </illustration>
    
        <illustration width="0" height="14">
        <setFont name="Times-Roman" size="12"/>
        <fill color="black"/>
        <drawString x="1in" y="2">"""
    else:
        # optimized with preformatted text (30%+ faster) (slight format changes)
        print("using preformatted for lines and speakers")
        M["LINE"] = """<pre style="line">%(__content__)s</pre>"""
        M["LINE"]["STAGEDIR"] = """</pre><pre style="stagedir">
        [%(__content__)s]</pre> <pre style="line">"""
        M["SPEAKER"] = """<pre style="speaker">%(__content__)s</pre>"""
    M["STAGEDIR"] = """<para style="stagedir">%(__content__)s</para>"""
    M["ACT"] = """<nextFrame/>%(__content__)s"""
    M["ACT"]["TITLE"] = """<para style="title">%(__content__)s
    <name id="act" value="%(__content__)s"/>
    <name id="header" value="%(__content__)s"/></para>"""
    M["INDUCT"] = """<nextFrame/>%(__content__)s"""
    M["INDUCT"]["TITLE"] = """<para style="title">%(__content__)s
    <name id="act" value="%(__content__)s"/>
    <name id="header" value="%(__content__)s"/></para>"""
    M["EPILOGUE"] = """<nextFrame/>%(__content__)s"""
    M["EPILOGUE"]["TITLE"] = """<para style="title">%(__content__)s
    <name id="act" value="%(__content__)s"/>
    <name id="header" value="%(__content__)s"/></para>"""
    M["SCENE"] = """<spacer length="4cm"/><condPageBreak height="15cm"/>%(__content__)s"""
    M["SCENE"]["TITLE"] = """<para style="title">%(__content__)s
    <name id="scene" value="%(__content__)s"/></para>
    <namedString id="header"><getName id="act" default="???"/>, %(__content__)s</namedString>"""
    import pyRXPU
    from rlextra.radxml import xmlutils
    tree=pyRXPU.Parser().parse(text,ReturnUTF8=1)
    print('after tree parsed')
    tree = xmlutils.escapeTree(tree)
    print('after re entitising')
    otext = M.processParsed(tree)
    print('after processParsed')
    return otext

def test():
    from time import time
    from glob import glob
    files = glob("shakespeare.1.10.xml/*.xml")
    for file in files:
        now = time()
        rmlfile = file[:-4] + ".rml"
        pdffile = file[:-4] + ".pdf"
        print(); print("########## now processing", file, "into", rmlfile, "into", pdffile)
        translateFiles(inputfilename=file,
                       rmlfilename=rmlfile,
                       pdffilename=pdffile)
        text = open(rmlfile).read()
        rml2pdf.go(text)
        print("wrote", pdffile)

if __name__=="__main__":
    import sys
    from glob import glob
    def getFlag(name,nextVal=0):
        r = name in sys.argv
        if r:
            x = sys.argv.index(name)
            del sys.argv[x]
            if nextVal:
                r = sys.argv[x]
                del sys.argv[x]
        return r
    prof = getFlag('-prof')
    timing = getFlag('-timing')
    if timing:
        from time import time
        t0 = time()
        test()
        print('play2rml took %.2f seconds' % (time()-t0))
    elif prof:
        import profile
        profile.run('test()','play2rml.stats')
    else:
        test()
