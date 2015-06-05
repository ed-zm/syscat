import sys

# generator for tag reference

# XXXX ultimately this should be somehow automated.

debug = 0

if not debug:
	outfile = "tagref.rml"
	#print "redirecting stdout to", outfile
	#sys.stdout = open(outfile, "w")

def doProlog(standalone=1):
	# print the prolog
	o = ""
	if standalone:
		o = "%s%s" % (o, """\
		<!DOCTYPE document SYSTEM "rml_1_0.dtd"> 
		<document filename="tagref.pdf"><template>
			<pageTemplate id="main">
			<frame id="first" x1="72" y1="72" width="451" height="698"/> 
			</pageTemplate>
		</template>
		<stylesheet>
		</stylesheet>

		<story>
		<h1>RML Tag Quick Reference</h1>
		""")
	o = "%s%s" % (o, """\
	<para>
	All attributes are optional unless otherwise specified.
	</para>
	""")
	return o

def doEpilogue(standalone=1):
	# print the epilogue
	o = ""
	if standalone:
		o = "%s%s" % (o, """
		</story>
		</document>
		""")
	return o

class tag:
	fontsize = 10
	extra = 5
	# tagname attr=value type comment
	fonts = ("Courier", "Courier", "Helvetica", "Helvetica-Oblique", )
	columns = ("0", "1in", "3.6in", "5.2in")
	colors = ("black", "blue", "green", "red")
	def __init__(self, name, attributeLines=(), contentLines=(), reqHeight="2in"):
		self.name = name
		self.attributeLines = attributeLines
		self.contentLines = contentLines
		self.reqHeight = reqHeight
	def __repr__(self):
		n = self.name
		a = self.attributeLines
		c = self.contentLines
		stringOps = []
		add = stringOps.append
		nLines = 1
		#yoffset = self.fontsize + self.extra
		yoffset = 0
		delta = self.fontsize + self.extra
		if a:
			add((yoffset, "&lt;"+self.name))
		elif c:
			add((yoffset, "&lt;"+self.name+"&gt;"))
		else:
			add((yoffset, "&lt;"+self.name+"/&gt;"))
		yoffset = yoffset+delta
		for al in self.attributeLines:
			add((yoffset, None,)+al)
			yoffset = yoffset+delta
		if c and a:
			add((yoffset, "&gt;"))
			yoffset = yoffset+delta
		elif a:
			add((yoffset, "/&gt;"))
			yoffset = yoffset+delta
		for c in self.contentLines:
			tc = type(c)
			if tc is bytes:
				add((yoffset, c,))
			elif tc is tuple:
				add((yoffset, c[0], None, None)+c[1:])
			yoffset = yoffset+delta
		if c:
			add((yoffset, "&lt;/%s&gt;" % self.name))
		else:
			# a bit hacky, for some reason the yoffset goes to far in this case
			yoffset = yoffset-delta
		outLines = []
		maxY = yoffset + delta
		nlines = 1
		Ops = []
		addop = Ops.append
		for s in stringOps:
			yoffset = maxY-s[0]
			s = s[1:]
			for i in range(len(s)):
				si = s[i]
				#print i, si
				if si is not None:
					si = e(si)
					addop('<setFont name="%s" size="%s"/>' % (self.fonts[i], self.fontsize))
					addop('<fill color="%s"/>'% self.colors[i])
					addop('<stroke color="%s"/>' %(self.colors[i],))
					addop('<drawString x="%s" y="%s">%s</drawString>'%(self.columns[i],yoffset,si))
		addop('<fill color="plum"/>')
		addop('<stroke color="plum"/>')
		addop('<rect x="-10" y="0" height="%s" width="%s" fill="true"/>' %(maxY+delta, -5))
		allOps = "\n".join(Ops)
		return """
		<condPageBreak height="%s"/>
			<h3>%s</h3>
		<illustration height="%s" width="%s">
		%s
		</illustration>\n\n""" % (self.reqHeight, n, maxY+delta, 1, allOps)

def e(s):
	s = s.replace("<", "&lt;")
	s = s.replace(">", "&gt;")
	return s

def d(**kw):
	return kw

def t(*args,**kw):
	return tag(*args,**kw)

def p(s):
	return """<para>%s</para>\n""" % (s,)

def h1(s):
	return """\n<condPageBreak height="2in"/>
	<spacer length="0.2in"/>
	<h1>%s</h1>\n\n""" % s

def h2(s):
	return """\n\n
	<h2>%s</h2>\n""" % s


##def test1():
##	  print tag("name", [('attr="val"', "type", "comment")], ["line1","line2"])
##
##test1()


# would be better as a dict, but need to preserve the order - can't just sort the keys
contentlist = [
	"document",
	t("document", [
			('filename="myfile.pdf"', "string", "required"),
			('compression="0|1|default"','PDF compression (default)'),
			('invariant="0|1|default"','PDF invariance (default)'),
			('debug="0|1"','Debug document production (0)'),
			('userPass="uuserpw"','Encryption user password'),
			('ownerPass="ownerpw"','Encryption owner password'),
			('encryptionStrength="128|40"','Encryption strength','optional'),
			('','defaults to 128'),
			('permissions="print annotate..."','Encryption permissions','optional'),
			('','allowed are print copy modify annotate'),
			('','default is print'),
			],
		  ["<template...>...</template>",
		   "<stylesheet...>...</stylesheet>",
		   "<story...>...</story>",
		   ]),

	"",
	p("Above is the story based form for the document tag.<br/>Encryption will only take place if a userPass is specified."),

	"document",
	t("document", [('filename="myfile.pdf"', "string", "required")],
			  [
			   "<stylesheet>...</stylesheet>",
			   ("<pageInfo>...</pageInfo>", "optional"),
			   ("<pageDrawing>...</pageDrawing>", "one or more"),
			   ]),

	"",
	p("Above is the PageDrawing based form for the document tag."),
	"",
	p("""The document tag is the root tag for RML docuoments.  Every RML document must contain on and
	only one document tag.	There are two forms for a document: the story form and the pageDrawing form."""),

	"docinit",
	t("docinit",
		[
		("pageMode", "UseNone|UseOutlines|UseThumbs|FullScreen"),
		("pageLayout", "SinglePage|OneColumn|TwoColumnLeft|TwoColumnRight"),
		("useCropMarks", "(yes | no | 0 | 1 | true | false)"),
		],
		[
		("	  <alias ... />"),
		("	  <color ... />"),
		("	  <name ... />"),
		("	  <namedString> ... </namedString>"),
		("	  <outlineAdd> ... </outlineAdd>"),
		("	  <registerType1Face ... />"),
		("	  <registerFont ... />"),
		("	  <registerCidFont ... />"),
		("	  <registerTTFont ... />"),
		("	  <registerFontFamily ... />"),
		("	  <logConfig ... />"),
		("	  <cropMarks ... />"),
		("	  <startIndex ... />"),
	   ]
	  ),

	"template",
	t("template",
		[ ('pageSize="(8.5in, 11in)"', "pair of lengths"),
		('rotation="270"', "page angular orientation (multiple of 90, default 0)"),
		('firstPageTemplate="main"', "page template id"),
		('leftMargin="1in"', "length"),
		('rightMargin="1in"', "length"),
		('topMargin="1.5in"', "length"),
		('bottomMargin="1.5in"', "length"),
		('showBoundary="false"', "truth value"),
		('allowSplitting="true"', "truth value"),
	   ('title="my title"', "string"),
	   ('author="yours truly"', "string"),
		],
		[("<pageTemplate...> ...</pageTemplate>", "1 or more"),
	   ]),

	"stylesheet",
	t("stylesheet",
		[],
		[("<initialize>...</initialize>", "optional"),
	   ("<paraStyle ... />", "(any number"),
	   ("<blockTableStyle>...</blockTableStyle>", "of styles)")
	   ]),

	"story",
	t("story", [],
		[("<para>...</para>", "(Sequence of"),
	   ("...", "top level"),
	   ("<illustration>...</illustration>", "flowables)")]),

	"pageInfo",
	t("pageInfo", [('pageSize="(8.5in,11in)"', "pair of lengths", "required")]),

	"pageDrawing",
	t("pageDrawing", [],
		[("<drawString ...> ...</drawString>", "(Sequence of"),
	   ("...", "graphical"),
	   ("<place ...>...</place>", "operations)")]),

	"pageGraphicsFletterbox",
	t("pageGraphics", [],
		[("<drawString ...> ...</drawString>", "(Sequence of"),
	   ("...", "graphical"),
	   ("<place>...</place>", "operations)")]),


	"",
	h1("Generic Flowables (Story Elements)"),

	"spacer",
	t("spacer", [('length="1.2in"', "measurement", "required"),
				 ('width="5in"', "measurement"),
				  ]),

	"graphicsMode",
	t("graphicsMode", [('origin="page|local|frame"',"drawing origin"),
				  ],
		[("<drawString ...> ...</drawString>", "(Sequence of"),
	   ("...", "graphical"),
	   ("<place ...>...</place>", "operations)")]),

	"illustration",
	t("illustration", [('height="1.2in"', "measurement", "required"),
				 ('width="5in"', "measurement", "required"),
				  ],
		[("<drawString ...> ...</drawString>", "(Sequence of"),
	   ("...", "graphical"),
	   ("<place ...>...</place>", "operations)")]),

	"pre",
	t("pre", [('style="myfavoritestyle"', "string paragraph style name")],
		[("Preformatted Text", "also string forms (getname)")]),

	"xpre",
	t("xpre", [('style="myfavoritestyle"', "string paragraph style name")],
		[("Paragraph text which may contain", "intraparagraph markup")]),

	"plugInFlowable",
	t("plugInFlowable", [('module="mymodule"', "string", "required"),
						 ('function="myfunction"', "string", "required")],
		[("string data for plug in", "unformatted data")]),

	"",
	h2("Table Elements"),

	"blockTable",
	t("blockTable", [
		('style="mytablestyle"', "string style name"),
		('rowHeights="(23, 20, 30, 10)"', "sequence of measurement"),
		('colWidths="50, 90, 35, 11"', "sequence of measurement"),
		('repeatRows="2"', "repeat two rows when split (or tuple of zero based rows to repeat)"),
		],
		[ ("<tr>...</tr>", "(rows of"),
		("<tr>...</tr>", "same length)"),
		"..."
		  ]),

	"tr",
	t("tr", [],
		["<td>...</td>", "<td>...</td>", "..."
		  ]),

	'<condPageBreak height="5in"/>','',
	"td",
	t("td", [
	('fontName="Helvetica"','stringform font name'),
	('fontSize="12"','stringform font size'),
	('fontColor="red"','stringform font color'),
	('leading="12"','stringform line spacing'),
	('leftPadding="3"','cell left padding'),
	('rightPadding="3"','cell right padding'),
	('topPadding="3"','cell top padding'),
	('bottomPadding="3"','cell bottom padding'),
	('background="pink"','background color'),
	('align="right"','cell horizontal alignment'),
	('vAlign="bottom"','vertical alignment'),
	('lineBelowThickness','bottom line thickness'),
	('lineBelowColor','bottom line color'),
	('lineBelowCap','bottom cap (butt | round | square)'),
	('lineBelowCount','bottom line count'),
	('lineBelowSpace','bottom line spacing'),
	('lineAboveThickness','topline thickness'),
	('lineAboveColor','top line colour'),
	('lineAboveCap','top cap (butt | round | square)'),
	('lineAboveCount','top line count'),
	('lineAboveSpace','top line spacing'),
	('lineLeftThickness','left line thickness'),
	('lineLeftColor','left line color'),
	('lineLeftCap','left line cap (butt | round | square)'),
	('lineLeftCount','left line count'),
	('lineLeftSpace','left line spacing'),
	('lineRightThickness','right line thickness'),
	('lineRightColor','right line color'),
	('lineRightCap','right line cap (butt | round | square)'),
	('lineRightCount','right line count'),
	('lineRightSpace','right line spacing'),
],
		[  "string of string form", "or sequence of flowable"
		  ],reqHeight="3in"),

	"docAssert",
	t("docAssert",[
		('cond="i==3"', "condition string", "required"),
		('format="The value of i is %(__expr__)"', "format string"),
		]),

	"docAssign",
	t("docAssign",[
		('var="i"', "string"),
		('expr="availableWidth"', "expression string"),
		]),

	"docElse",
	t("docElse",[
		]),

	"docIf",
	t("docIf",[
		('cond="i==3"', "condition string"),
		]),

	"docExec",
	t("docExec",[
		('stmt="i-=1"', "statement string"),
		]),

	"docPara",
	t("docPara",[
		('expr="availableWidth"', "expression string"),
		('format="The value of i is %(__expr__)"', "format string"),
		('style=""', "string"),
		('escape="yes"', "(yes | no | 0 | 1)"),
		]),

	"docWhile",
	t("docWhile",[
		('cond="i==3"', "condition string"),
		]),

	"drawing",
	t("drawing",[
		('baseDir="../"', "path string"),
		('module="python_module"', "string"),
		('function="module_function"', "string"),
		('hAlign="CENTER"', "center|centre|left|right|CENTER|CENTRE|LEFT|RIGHT"),
		('showBoundary="no"', "(0|1|yes|no)"),
		],),

	"widget",
	t("widget",[
		('baseDir="../"', "path string"),
		('module="python_module"', "string"),
		('function="module_function"', "string"),
		('name="somename"', "string"),
		('initargs="someinitargs"', "string"),
		]),

	"",
	
	h2("Paragraph-like Elements"),

	"para",
	t("para",
		[('style="myfavoritstyle"', "string paragraph style name")],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"title",
	t("title",
		[('style="myfavoritstyle"', "string paragraph style name")],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"h1",
	t("h1",
		[('style="myfavoritstyle"', "string paragraph style name")],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"h2",
	t("h2",
		[('style="myfavoritstyle"', "string paragraph style name")],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"h3",
	t("h3",
		[('style="myfavoritstyle"', "string paragraph style name")],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"h4",
	t("h4",
		[('style="myfavoritstyle"', "string paragraph style name")],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"h5",
	t("h5",
		[('style="myfavoritstyle"', "string paragraph style name")],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"h6",
	t("h6",
		[('style="myfavoritstyle"', "string paragraph style name")],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"a",
	t("a",[
		('color="blue"', "string color name"),
		('fontSize="12"','stringform font size'),
		('fontName="Helvetica"', "string font name"),
		('name="somename"', "string"),
		('backColor="cyan"', "string color string"),
		('href="someurl"', "string"),
		],["Link name"]),
	
	"evalString",
	t("evalString",[
		('imports="someimports"', "string"),
		('default="somedefault"', "string"),
		]),

	"",
	h2("Intra-Paragraph Markup"),

	"i",
	t("i",
		[],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"b",
	t("b",
		[],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"font",
	t("font",
		[('face="Helvetica"', "string font name"),
	   ('color="blue"', "string color name"),
	   ('size="34"', "fontsize measurement"),
		  ],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"greek",
	t("greek",
		[],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"sub",
	t("sub",
		[],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"super",
	t("super",
		[],
		["Paragraph text which may contain", "intraparagraph markup"]),

	"strike",
	t("strike",[
		]),

	"sup",
	t("sup",[
		]),

	"seq",
	t("seq",
		[('id="SecNum"', "string"),
	   ('template="%(Ch)s.%(SecNum)s"', "string"),
		  ]
	  ),

	"seqDefault",
	t("seqDefault",
		[('id="SecNum"', "string"),
		  ]),

	"seqReset",
	t("seqReset",
		[('id="SecNum"', "string"),
		  ]),

	"seqChain",
	t("seqChain",
		[('order="id id id id"', "string"),
		  ]),

	"seqFormat",
	t("seqFormat",
		[('id="seqId"', "string"),('value="format char"','(1|i|I|a|A)'),
		  ]),

	"onDraw",
	t("onDraw", [
		('name="somename"', "string"),
		('label="somelabel"','string'),
		  ]),

	"br",
	t("br",[
		]),

	"bullet",
	t("bullet",[
		('bulletColor="blue"', "string color name"),
		('bulletFontName=""', "string"),
		('bulletFontSize="1in"', "measurement"),
		('bulletIndent="1in"', "measurement"),
		('bulletOffsetY="1in"', "measurement"),
		]),

	"link",
	t("link",[
		('destination="somedestination"', "string"),
		('color="blue"', "string color name"),
		]),

	"setLink",
	t("setLink",[
		('destination="somedestination"', "string"),
		('color="blue"', "string color name"),
		]),

	"unichar",
	t("unichar",[
		('name="somename"', "string"),
		('code="somecode"', "string"),
		]),


	"",



	h2("Page Level Flowables"),

	"nextFrame",
	t("nextFrame",
		[('name="frameindex"','int or string frame index'),
		]),

	"setNextFrame",
	t("setNextFrame",
		[('name="frameindex"','int or string frame index',"required"),
		]),

	"nextPage",
	t("nextPage"),

	"setNextTemplate",
	t("setNextTemplate",
		[('name="indextemplate"', "string template name", "required"),
		  ]),

	"condPageBreak",
	t("condPageBreak",
		[('height="10cm"', "measurement", "required"),
		  ]),

	"storyPlace",
	t("storyPlace", [('x="1in"', "measurement", "required"),
	   ('y="7in"', "measurement", "required"),
	   ('width="5in"', "measurement", "required"),
	   ('height="3in"', "measurement", "required"),
	   ('origin="page"', '"page", "frame", or "local"', "optional"),
	   ],
		[("<para>...</para>", "(Sequence of"),
	   ("...", "top level"),
	   ("<table>...</table>", "flowables)")]),
	"keepInFrame",
	t("keepInFrame",
		[
		('maxWidth="int"','maximum width or 0'),
		('maxHeight="int"','maximum height or 0'),
		('frame="frameindex"','optional frameindex to start in'),
		('mergeSpace="1|0"','whether padding space is merged'),
		('onOverflow="error|overflow|"',''),
		(' ......	 |shrink|truncate"','over flow behaviour'),
		('id="name"','name for identification purposes'),
		],
		[
		("<para>...</para>", "(Sequence of"),
		("...", "top level"),
		("<table>...</table>", "flowables)")]),
	"imageAndFlowables",
	t("imageAndFlowables",
		[
		('imageName="path"','path to image file or url'),
		('imageWidth="float"','image width or 0'),
		('imageHeight="float"','image height or 0'),
		('imageMask="color"','image transparency color or "auto"'),
		('imageLeftPadding="float"','space on left of image'),
		('imageRightPadding="float"','space on right of image'),
		('imageTopPadding="float"','space on top of image'),
		('imageBottomPadding="float"','space on bottom of image'),
		('imageSide="left"','hrizontal image location left|right'),
		],
		[
		("<para>...</para>", "(Sequence of"),
		("...", "top level"),
		("<table>...</table>", "flowables)")]),
	"pto",
	t("pto", [],
		[ ('<pto_trailer>...</pto_trailer>', 'optional'),
		('<pto_header>...</pto_header>', 'optional'),
		("<para>...</para>", "(Sequence of"),
		("...", "top level"),
		("<table>...</table>", "flowables)")]),
	"pto_trailer",
	t("pto_trailer", [],
		[ ('', 'Only in PTO'),
		("<para>...</para>", "(Sequence of"),
		("...", "top level"),
		("<table>...</table>", "flowables)")]),
	"pto_header",
	t("pto_header", [],
		[ ('', 'Only in PTO'),
		("<para>...</para>", "(Sequence of"),
		("...", "top level"),
		("<table>...</table>", "flowables)")]),
	"indent",
	t("indent", [('left="1in"', "measurement", "optional"),
	   ('right="1cm"', "measurement", "optional"),
	   ],
		[("<para>...</para>", "(Sequence of"),
	   ("...", "top level"),
	   ("<table>...</table>", "flowables)")]),
	"frameBackground",
	t("frameBackground", [('color="pink"',"color","optional"),
		('left="1in"', "measurement", "optional"),
	   ('right="1cm"', "measurement", "optional"),
	   ('start="1"', "boolean", "optional"),
	   ],
		[]),
	"fixedSize",
	t("fixedSize", [('width="1in"', "measurement", "optional"),
	   ('height="1cm"', "measurement", "optional"),
	   ],
		[("<para>...</para>", "(Sequence of"),
	   ("...", "top level"),
	   ("<table>...</table>", "flowables)")]),

	"",
	h1("Graphical Drawing Operations"),

	"drawString",
	t("drawString",
		[('x="1in"', "measurement", "required"),
	   ('y="7in"', "measurement", "required"),
		  ],
		["text to draw or string forms"]),

	"drawRightString",
	t("drawRightString",
		[('x="1in"', "measurement", "required"),
	   ('y="7in"', "measurement", "required"),
		  ],
		["text to draw or string forms"]),

	"drawCentredString",
	t("drawCentredString",
		[('x="1in"', "measurement", "required"),
	   ('y="7in"', "measurement", "required"),
		  ],
		["text to draw or string forms"]),

	"drawCenteredString",
	t("drawCenteredString",
		[('x="1in"', "measurement", "required"),
	   ('y="7in"', "measurement", "required"),
		  ],
		["synonym for drawCentredString"]),

	"ellipse",
	t("ellipse",
		[('x="1in"', "measurement", "required"),
	   ('y="7in"', "measurement", "required"),
	   ('width="5cm"', "measurement", "required"),
	   ('height="3cm"', "measurement", "required"),
	   ('fill="true"', "truth value"),
	   ('stroke="false"', "truth value"),
		  ],),

	"circle",
	t("circle",
		[('x="1in"', "measurement", "required"),
	   ('y="7in"', "measurement", "required"),
	   ('radius="3cm"', "measurement", "required"),
	   ('fill="true"', "truth value"),
	   ('stroke="false"', "truth value"),
		  ],),

	"rect",
	t("rect",
		[('x="1in"', "measurement", "required"),
	   ('y="7in"', "measurement", "required"),
	   ('width="5cm"', "measurement", "required"),
	   ('height="3cm"', "measurement", "required"),
	   ('round="1.2cm"', "measurement"),
	   ('fill="true"', "truth value"),
	   ('stroke="false"', "truth value"),
		  ],),

	"grid",
	t("grid", 
		[('xs="1in 2in 3in"', "measurements", "required"),
	   ('ys="7in 7.2in 7.4in"', "measurements", "required"),
	   ]),

	"lines",
	t("lines", [],
		[("1in 1in 2in 2in", "quadruples of"),
	   ("1in 2in 2in 3in", "measurements"),
	   ("1in 3in 2in 4in", "representing"),
	   ("...", "line segments")]),

	"curves",
	t("curves", [],
		[("1in 1in 2in 2in 2in 3in 1in 3in", "octtuples of"),
	   ("1in 2in 2in 3in 2in 4in 1in 4in", "measurements"),
	   ("1in 3in 2in 4in 2in 5in 1in 5in", "representing"),
	   ("...", "Bezier curves")]),

	"image",
	t("image",
		[('file="cute.jpg"', "string", "required"),
		  ('x="1in"', "measurement", "required"),
	   ('y="7in"', "measurement", "required"),
	   ('width="5cm"', "measurement"),
	   ('height="3cm"', "measurement"),
		  ],),

	"place",
	t("place", [('x="1in"', "measurement", "required"),
	   ('y="7in"', "measurement", "required"),
	   ('width="5in"', "measurement", "required"),
	   ('height="3in"', "measurement", "required"),],
		[("<para>...</para>", "(Sequence of"),
	   ("...", "top level"),
	   ("<illustration>...</illustration>", "flowables)")]),

	"doForm",
	t("doForm", [('name="logo"', "string", "required"),]),
	
	"includePdfPages",
	t("includePdfPages",[
		('filename="path"','string','required: path to included file'),
		('pages="1-3,6"','string','optional: , separated page list'),
		('template="name"','string','optional: pagetemplate name'),
		('outlineText="text"','string','optional: text for outline entry'),
		('outlineLevel="1"','int','optional: outline level default 0'),
		('outlineClose="0"','int','optional: 0 for closed outline entry'),
		('leadingFrame="no"','bool','optional: no if you don\'t want a page throw use notAtTop for special conditional behaviour.'),
		('isdata="yes"','bool','optional: true if filename is a pageCatcher .data file'),
		('orientation="auto"','string','optional: 0 90 180 270 auto landscape portrait'),
		('sx="0.9"','float'),
		('sy="0.9"','float'),
		('dx="2in"','measurement'),
		('dy="2in"','measurement'),
		('degrees="45"', "angle in degrees")
		]),

	"textField",
	t("textField",
		[('id="name"', "name of field","required"),
	   ('value="initial"', "field initial value","optional"),
	   ('x="34"', "x coord"),
	   ('y="500"', "y coord"),
	   ('width="72"', "width"),
	   ('height="12"', "height"),
	   ('maxlen="1200"', "maximum #chars"),
	   ('multiline="0/1"', "1 for multiline text"),
		  ],
		["value text or <param> tags", "param value or attributes allowed not both"]),
	"textAnnotation",
	t("textAnnotation",
		[],
		["annotaion text or <param> tags", "params may adjust the annotation"]),

	"plugInGraphic",
	t("plugInGraphic", [('module="mymodule"', "string", "required"),
						 ('function="myfunction"', "string", "required")],
		[("string data for plug in", "unformatted data")]),

	"path",
	t("path",
		[('x="1in"', "measurement", "required"),
	   ('y="7in"', "measurement", "required"),
	   ('close="true"', "truth value"),
	   ('fill="true"', "truth value"),
	   ('stroke="false"', "truth value"),
		  ],
		[ ("1in 6in", "measurement pairs"),
		("1in 7in", "representing points"),
		("...", "or path operations"),
		  ]),


	"barCodeFlowable",
	t("barCodeFlowable",[
		('code="Code11"', "(I2of5 | Code128 | Standard93 | Extended93 | Standard39 | Extended39 | MSI | Codabar |  Code11 | FIM | POSTNET | USPS_4State)", "required"),
		('value="somevalue"', "string", "required"),
		('fontName="Helvetica"', "string font name"),
		('tracking="sometracking"', "string"),
		('routing="somerouting"', "string"),
		('barStrokeColor="blue"', "string color name"),
		('barFillColor="blue"', "string color name"),
		('textColor="blue"', "string color name"),
		('barStrokeWidth="1in"', "measurement"),
		('gap="1in"', "measurement"),
		('ratio="I2of5"', "string"),
		('bearers=""', "string"),
		('barHeight="1in"', "measurement"),
		('barWidth="1in"', "measurement"),
		('fontSize="12"','stringform font size'),
		('spaceWidth="1in"', "measurement"),
		('spaceHeight="1in"', "measurement"),
		('widthSize="1in"', "measurement"),
		('heightSize="1in"', "measurement"),
		('checksum="-1"', "(-1 | 0 | 1 | 2)"),
		('quiet="yes"', "(yes | no | 0 | 1)"),
		('lquiet="yes"', "(yes | no | 0 | 1)"),
		('rquiet="yes"', "(yes | no | 0 | 1)"),
		('humanReadable="yes"', "(yes | no | 0 | 1)"),
		('stop="yes"', "(yes | no | 0 | 1)"),
		]),

	"figure",
	t("figure",[
		('showBoundary="no"', "(0|1|yes|no)"),
		('shrinkToFit="no"', "(0|1|yes|no)"),
		('growToFit="no"', "(0|1|yes|no)"),
		('scaleFactor="somescaleFactor"', "string"),
		]),

	"imageFigure",
	t("imageFigure",[
		('imageName="someimageName"', "string"),
		('imageWidth="1in"', "measurement"),
		('imageHeight="1in"', "measurement"),
		('imageMask="someimageMask"', "string"),
		('preserveAspectRatio="yes"', "(yes | no | 0 | 1)"),
		('showBoundary="yes"', "(yes | no | 0 | 1)"),
		('pdfBoxType="MediaBox"', "(MediaBox | CropBox | TrimBox | BleedBox | ArtBox)"),
		('pdfPageNumber="4"', "integer"),
		('showBoundary="no"', "(0|1|yes|no)"),
		('shrinkToFit="no"', "(0|1|yes|no)"),
		('growToFit="no"', "(0|1|yes|no)"),
		('caption="somecaption"', "string"),
		('captionFont="12"', "stringform font name"),
		('captionSize="1in"', "measurement"),
		('captionGap="somecaptionGap"', "string"),
		('captionColor="blue"', "string color name"),
		('spaceAfter="4"', "integer"),
		('spaceBefore="4"', "integer"),
		('align="center|centre|left|right|CENTER|CENTRE|LEFT|RIGHT)"', "(center|centre|left|right|CENTER|CENTRE|LEFT|RIGHT)"),
		]),

	"img",
	t("img",[
		('src="somesrc"', "string"),
		('width="1in"', "measurement"),
		('height="1in"', "measurement"),
		('valign="top"', "(top|middle|bottom))"),
		]),

	"",
	h2("Path Operations"),

	"moveto",
	t("moveto", [], [("5in 3in", "measurement pair")]),

	"curvesto",
	t("curvesto", [],
		[("1in 1in 1in 4in 4in 4in", "sextuples of"),
	   ("2in 2in 2in 5in 5in 5in", "measurements for"),
	   ("...", "bezier curves"),
		  ]),

	"",
	h2("Form Field Elements"),

	"barCode",
	t("barCode", [
		('x="1in"', "measurement", "required"),
		('y="1in"', "measurement", "required"),
		('code="Code 11"', '"Codabar", "Code11",', "required"),
		('', '"Code128", "I2of5"'),
		('', '"Standard39", Standard93", '),
		('', '"Extended39", "Extended93"'),
		('', '"MSI", "FIM", "POSTNET"'),
		],
		[ ("01234545634563", "unformatted barcode data")
		  ]),

	"checkBox",
	t("checkBox", [
		('style="myboxstyle"', "string box style name"),
		('x="1in"', "measurement", "required"),
		('y="1in"', "measurement", "required"),
		('labelFontName="Helvetica"', "string font name"),
		('labelFontSize="12"', "fontsize measurement"),
		('labelTextColor="blue"', "string color name"),
		('boxWidth="1in"', "measurement"),
		('boxHeight="1in"', "measurement"),
		('checkStrokeColor="blue"', "string color name"),
		('boxStrokeColor="blue"', "string color name"),
		('boxFillColor="blue"', "string color name"),
		('lineWidth="1"', "measurement"),
		('line1="label text 1"', "string"),
		('line2="label text 2"', "string"),
		('line3="label text 3"', "string"),
		('checked="false"', "truth value"),
		('bold="false"', "truth value"),
		('graphicOn="cute_on.jpg"', "string file name"),
		('graphicOff="cute_off.jpg"', "string file name"),
		  ]),

	"letterBoxes",
	t("letterBoxes", [
		('style="myboxstyle"', "string box style name"),
		('x="1in"', "measurement", "required"),
		('y="1in"', "measurement", "required"),
		('count="10"', "integer", "required"),
		('label="label text"', "string"),
		('labelFontName="Helvetica"', "string font name"),
		('labelFontSize="12"', "fontsize measurement"),
		('labelTextColor="blue"', "string color name"),
		('labelOffsetX="1in"', "measurement"),
		('labelOffsetY="1in"', "measurement"),
		('boxWidth="1in"', "measurement"),
		('boxHeight="1in"', "measurement"),
		('combHeight="0.25"', "float"),
		('boxStrokeColor="blue"', "string color name"),
		('boxFillColor="blue"', "string color name"),
		('textColor="blue"', "string color name"),
		('lineWidth="1in"', "measurement"),
		('fontName="Helvetica"', "string font name"),
		('fontSize="12"', "fontsize measurement"),
		],
		[ ("box contents goes here", "unformatted data")
		  ]),

	"textBox",
	t("textBox", [
		('style="myboxstyle"', "string box style name"),
		('x="1in"', "measurement", "required"),
		('y="1in"', "measurement", "required"),
		('boxWidth="1in"', "measurement", "required"),
		('boxHeight="1in"', "measurement", "required"),
		('labelFontName="Helvetica"', "string font name"),
		('labelFontSize="12"', "fontsize measurement"),
		('labelTextColor="blue"', "string color name"),
		('labelOffsetX="1in"', "measurement"),
		('labelOffsetY="1in"', "measurement"),
		('boxStrokeColor="blue"', "string color name"),
		('boxFillColor="blue"', "string color name"),
		('textColor="blue"', "string color name"),
		('lineWidth="1in"', "measurement"),
		('fontName="Helvetica"', "string font name"),
		('fontSize="12"', "fontsize measurement"),
		('align="left"', '"left", "right" or "center"'),
		('shrinkToFit="false"', "truth value"),
		('label="label text"', "string"),
		],
		[ ("box contents goes here", "unformatted data")
		  ]),


	"",
	h1("Graphical State Change Operations"),

	"fill",
	t("fill", [('color="blue"', "string name", "required")]),

	"stroke",
	t("stroke", [('color="blue"', "string name", "required")]),

	"setFont",
	t("setFont",
		[('name="Helvetica"', "string name", "required"),
	   ('size="1cm"', "measurement", "required"),
	   ]),

	"form",
	t("form", [('name="logo"', "string name", "required"),],
		[("<drawString ...> ...</drawString>", "(Sequence of"),
	   ("...", "graphical"),
	   ("<place ...>...</place>", "operations)")]),

	"catchForms",
	t("catchForms", [('storageFile="storage.data"', "string name", "required"),],),

	"scale",
	t("scale",
		[('sx="0.8"', "scale factor", "required"),
	   ('sy="1.3"', "scale factor", "required"),]),

	"translate",
	t("translate",
		[('dx="0.8in"', "measurement", "required"),
	   ('dy="1.3in"', "measurement", "required"),]),

	"rotate",
	t("rotate", [('degrees="45"', "angle in degrees", "required")]),

	"skew",
	t("skew", [('alpha="15"', "angle in degrees", "required"),
			   ('beta="5"', "angle in degrees", "required"),
			   ]),

	"transform",
	t("transform", [],
		[("1.0 0.3","six number affine"),
	   ("-0.2 1.1", "transformation"),
	   ("10.1 15", "matrix")
		  ]),

	"lineMode",
	t("lineMode", [
		('width="0.2cm"', "measurement"),
		('dash=".1cm .2cm"', "measurements"),
		('join="round"', '"round", "mitered", or "bevelled"'),
		('cap="square"', '"default", "round", or "square"'),
		]),

	"",
	h1("Style Elements"),

	"initialize",
	t("initialize", [],
		[ ("<alias.../>", "sequence of"),
		("<name.../>", "alias, name"),
		("<color.../>", "or color tags")
		  ]),

	"paraStyle",
	t("paraStyle",
		[ ('name="mystyle"', "string"),
		('alias="pretty"', "string"),
		('parent="oldstyle"', "string"),
		('fontname="Courier-Oblique"', "string"),
		('fontsize="13"', "measurement"),
		('leading="20"', "measurement"),
		('leftIndent="1.25in"', "measurement"),
		('rightIndent="2.5in"', "measurement"),
		('firstLineIndent="0.5in"', "measurement"),
		('spaceBefore="0.2in"', "measurement"),
		('spaceAfter="3cm"', "measurement"),
		('alignment="justify"', '"left", "right", "center" or "justify"'),
		('bulletFontname="Courier"', "string"),
		('bulletFontsize="13"', "measurement"),
		('bulletIndent="0.2in"', "measurement"),
		('textColor="red"', "string"),
		('backColor="cyan"', "string"),
		  ],),

	"boxStyle",
	t("boxStyle",
		[ ('name="mystyle"', "string", "required"),
		('alias="pretty"', "string"),
		('parent="oldstyle"', "string"),
		('fontname="Courier-Oblique"', "string"),
		('fontsize="13"', "measurement"),
		('alignment="left"', '"left", "right" or "center"'),
		('textColor="blue"', "string color name"),
		('labelFontName="Courier"', "string"),
		('labelFontSize="13"', "measurement"),
		('labelAlignment="left"', '"left", "right" or "center"'),
		('labelTextColor="blue"', "string color name"),
		('boxFillColor="blue"', "string color name"),
		('boxStrokeColor="blue"', "string color name"),
		('cellWidth="1in"', "measurement"),
		('cellHeight="1in"', "measurement"),
		  ],),

	"blockTableStyle",
	t("blockTableStyle",
		[ ('id="mytablestyle"', "string"),],
		[ ('<blockFont.../>', "table style"),
		('<blockLeading.../>', "block descriptors"),
		"...",
		  ]),

	"",
	h2("Table Style Block Descriptors"),

	"blockFont",
	t("blockFont",
		[ ('name="TimesRoman"', "string", "required"),
		('size="8"', "measurement"),
		('leading="10"', "measurement"),
		('start="4"', "integer"),
		('stop="11"', "integer"),
		],),

	"blockLeading",
	t("blockLeading",
		[ 
		('length="10"', "measurement", "required"),
		('start="4"', "integer"),
		('stop="11"', "integer"),
		],),

	"blockTextColor",
	t("blockTextColor",
		[ ('colorName="pink"', "string", "required"),
		  ('start="4"', "integer"),
		('stop="11"', "integer"),
		],),

	"blockAlignment",
	t("blockAlignment",
		[ ('value="left"', '"left", "right", or "center"'),
		('start="4"', "integer"),
		('stop="11"', "integer"),
		],),

	"blockLeftPadding",
	t("blockLeftPadding",
		[ ('length="0.2in"', "measurement", "required"),
		('start="4"', "integer"),
		('stop="11"', "integer"),
		],),

	"blockRightPadding",
	t("blockRightPadding",
		[ ('length="0.2in"', "measurement", "required"),
		('start="4"', "integer"),
		('stop="11"', "integer"),
		],),

	"blockBottomPadding",
	t("blockBottomPadding",
		[ ('length="0.2in"', "measurement", "required"),
		('start="4"', "integer"),
		('stop="11"', "integer"),
		],),

	"blockTopPadding",
	t("blockTopPadding",
		[ ('length="0.2in"', "measurement", "required"),
		('start="4"', "integer"),
		('stop="11"', "integer"),
		],),

	"blockBackground",
	t("blockBackground",
		[ ('colorName="indigo"', "string", "required"),
		 ('start="4"', "integer"),
		('stop="11"', "integer"),
		],),

	"blockValign",
	t("blockValign",
		[ ('value="left"', '"top", "middle", or "bottom"'),
		('start="4"', "integer"),
		('stop="11"', "integer"),
		],),

	"blockSpan",
	t("blockSpan",[
		('start="4"', "integer"),
		('stop="4"', "integer"),
		]),


	"lineStyle",
	t("lineStyle",
		[ ('kind="BOX"', "line command", "required"),
		('thickness="4"', "measurement", "required"),
		('colorName="magenta"', "string", "required"),
		('start="4"', "integer"),
		('stop="11"', "integer"),
		('count="2"', "integer"),
		('space="2"', "integer"),
		('dash="2,2"', "integer,integer"),
		],),

	"",
	p("""
	The line command names are: GRID, BOX,
	OUTLINE, INNERGRID, LINEBELOW, LINEABOVE, LINEBEFORE and LINEAFTER. BOX and
	OUTLINE are equivalent, and GRID is the equivalent of applying both BOX and INNERGRID.
	"""),

	"bulkData",
	t("bulkData",[
		('stripBlock="yes"', "(yes | no)"),
		('stripLines="yes"', "(yes | no)"),
		('stripFields="yes"', "(yes | no)"),
		('fieldDelim=","', "string"),
		('recordDelim=","', "string"),
		]),

	"excelData",
	t("excelData",[
		('fileName="somefileName"', "string"),
		('sheetName="somesheetName"', "string"),
		('range="A1:B7"', "string"),
		('rangeName="somerangeName"', "string"),
		]),

	"",
	h1("Page Layout Tags"),

	"pageTemplate",
	t("pageTemplate",
		[ ('id="frontpage"', "string", "required"),
		('pageSize="(8.5in, 11in)"', "override template page size"),
		('rotation="270"', "override template page angular orientation"),
		],
		[ ('<pageGraphics>...</pageGraphics>...', "optional 1 or 2"),
		('<frame.../>', "one or more"),
		"...",
		]),

	"frame",
	t("frame",
		[ ('id="left"', "string", "required"),
		('x1="1in"', "measurement", "required"),
	 	('y1="1in"', "measurement", "required"),
	 	('width="50cm"', "measurement", "required"),
	 	('height="90cm"', "measurement", "required"),],),

	"pageGraphics",
	t("pageGraphics",[
		]),

	"",
	h1("Special Tags"),

	"name",
	t("name",
		[ ('id="chapterName"', "string", "required"),
		('value="Introduction"', "string", "required"),]),

	"alias",
	t("alias",
		[ ('id="footerString"', "string", "required"),
		('value="chapterName"', "string", "required"),]),

	"getName",
	t("getName",
		[ ('id="footerString"', "string", "required"),]),

	"color",
	t("color",
		[ ('id="footerString"', "string", "required"),
		('RGB="77aa00"', "hexidecimal red/green/blue values"),
		]),

	"pageNumber",
	t("pageNumber",[
		('countingFrom="2"', "integer"),
		]
	 ),
	"outlineAdd",
	t("outlineAdd", [
		('level="1"', "integer"),
		('closed="true"', "truth value"),
		],
		[ ("Chapter 1, section 2", "outline entry text")
		 ]),
		  
	"cropMarks",
	t("cropMarks",[
		('borderWidth="36"', "integer"),
		('markWidth="0.5"', "float"),
		('markColor="green"', 'color'),
		('markLength="18"', 'integer'),
		],

	 	),

	"startIndex",
	t("startIndex",[
		('name="somename"', "string"),
		('offset="0"', "integer"),
		('format="ABC"', '123|I|i|ABC|abc'),
		],
	  ),
	"index",
	t("index",[
		('name="somename"', "string"),
		('offset="0"', "integer"),
		('format="ABC"', '123|I|i|ABC|abc'),
		],

	  ),

	"showIndex",
	t("showIndex",[
		('name="somename"', "string"),
		('dot="-"', "string"),
		('style="somestyle"', 'string'),
		('tableStyle="sometablestyle"', 'string'),
		],

	  ),

	"bookmark",
	t("bookmark",[
		('name="somename"', "string"),
		('x="1in"', "measurement"),
		('y="1in"', "measurement"),
		]),

	"bookmarkPage",
	t("bookmarkPage",[
		('name="somename"', "string"),
		('fit="XYZ|Fit|FitH|FitV|FitR)"', "(XYZ|Fit|FitH|FitV|FitR)"),
		('top="1in"', "measurement"),
		('bottom="1in"', "measurement"),
		('left="1in"', "measurement"),
		('right="1in"', "measurement"),
		('zoom="somezoom"', "string"),
		]),

	"join",
	t("join",[
		('type="sometype"', "string"),
		]),

	"length",
	t("length",[
		('id="someid"', "string"),
		('value="4"', "integer"),
		]),

	"namedString",
	t("namedString",[
		('id="someid"', "string"),
		('type="sometype"', "string"),
		('default="somedefault"', "string"),
		]),

	"param",
	t("param",[
		('name="somename"', "string"),
		]),

	"registerCidFont",
	t("registerCidFont",[
		('faceName="VeraBold"', "font name string"),
		('encName="WinAnsiEncoding"', "string"),
		]),

	"registerFont",
	t("registerFont",[
		('name="somename"', "string"),
		('faceName="VeraBold"', "font name string"),
		('encName="WinAnsiEncoding"', "string"),
		]),

	"registerFontFamily",
	t("registerFontFamily",[
		('normal="VeraBold"', "font name string"),
		('bold="VeraBold"', "font name string"),
		('italic="VeraBold"', "font name string"),
		('boldItalic="VeraBold"', "font name string"),
		]),

	"registerTTFont",
	t("registerTTFont",[
		('faceName="VeraBold"', "font name string"),
		('fileName="somefileName"', "string"),
		]),

	"registerType1Face",
	t("registerType1Face",[
		('afmFile="DarkGardenMK.afm"', "string"),
		('pfbFile="DarkGardenMK.pfb"', "string"),
		]),

	"restoreState",
	t("restoreState",[
		]),

	"saveState",
	t("saveState",[
		]),

	"setFont",
	t("setFont",[
		('name="somename"', "font name string"),
		('size="1in"', "measurement"),
		('leading="4"', "integer"),
		]),

	"setFontSize",
	t("setFontSize",[
		('size="1in"', "measurement"),
		('leading="4"', "integer"),
		]),


	"",
	h1("Log tags"),

	"log",
	t("log",[
		('log="evel"', "(DEBUG | INFO | WARNING | ERROR | CRITICAL)"),
		],['log message']),

	"debug",
	t("debug",[
		],['debug message']),

	"info",
	t("info",[
		],['info message']),

	"warning",
	t("warning",[
		],['warning message']),

	"error",
	t("error",[
		],['error message']),

	"critical",
	t("critical",[
		],['critical message']),

	"logConfig",
	t("logConfig",[
		('level="DEBUG"', "(DEBUG | INFO | WARNING | ERROR | CRITICAL)"),
		('format="The value of i is %(__expr__)"', "format string"),
		('filename="somefilename"', "string"),
		('filemode="WRITE"', "(WRITE | APPEND)"),
		('datefmt="somedatefmt"', "string"),
		]),

	"",

	
	h1("Not implemented"),

	"",
	p("The following tags are allowed for in the DTD but are not implemented by the current version of RML2PDF:"),
	"",
	p("li, ol, u, ul, dd, dl, dt")

]

# the following tags appear in the DTD but are not implemented yet:
# li, ol, u, ul 

def makeTagRef():
	"""makes the middle section - the actual tag reference (without and prolog or epilogue"""
	o = ""
	if len(contentlist) % 2:
		raise ValueError("contentlist is corrupt!")
	for f in range(1, len(contentlist), 2):
		#print contentlist[f]
		o = "%s\n%s" % (o, contentlist[f])
	return o

def returnFullTagRef(standalone=1):
	o1 = doProlog(standalone)
	o2 = makeTagRef()
	o3 = doEpilogue(standalone)
	output = "%s%s%s" % (o1, o2, o3)
	return output

def testTags():
	# use the latest DTD... or at least the one with the highest number.
	# in case we have multiple DTDs in the directory.
	import glob, os.path, string
	poss = glob.glob(os.path.join('..', '*.dtd'))
	poss.sort()
	#print poss[-1]
	dtd = open(poss[-1], 'r').readlines()

	#can't get list of tags using pyRXP, pull from the DTD manually
	unknownTags = []
	allTags = []
	knownTags = []
	for f in range(0, len(contentlist), 2):
		if contentlist[f] != "":
			knownTags.append(contentlist[f])
	#import pprint;pprint.pprint(knownTags)

	for line in dtd:
		l = line.split()
		try:
			if l[0] == "<!ELEMENT":
				allTags.append(l[1])
				if l[1] not in knownTags:
					unknownTags.append(l[1])
		except IndexError:
			if l == []: pass
			else: print("!!!", l)
	if unknownTags != []:
		unknownTags.sort()
		print("the following tags do not appear in the tag reference:")
		for f in unknownTags: print("\t%s" % f)

		pofile = 'unknown_tags.txt'
		po = open(pofile, 'w')
		po.write("TAGS APPEARING IN THE RML DTD BUT NOT IN THE TAG REFERENCE\n")
		po.write("==========================================================\n")
		for f in unknownTags:
			po.write("\n\t%s"%f)
		po.close()
		print("\nwrote %s" % pofile)
	else:
		print("all tags appear in the tag reference")

if __name__ == "__main__":
	#sys.stdout = open(outfile, "w")
	tmparg = sys.argv[1:]
	if "--test" in tmparg:
		print("testing tags...\n");testTags()
	elif "-t" in tmparg:
		print("testing tags...\n");testTags()
	else:
		print("redirecting stdout to", outfile)
		standalone=1
		output = returnFullTagRef(standalone)
		out = open(outfile, "w")
		out.write(output)
		out.close()
		print("wrote %s" % outfile)
