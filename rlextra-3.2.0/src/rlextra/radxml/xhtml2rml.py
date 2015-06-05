from __future__ import unicode_literals
import os, sys
import pyRXPU
from rlextra.radxml.xmlmap import LazyAttrs, MapController, MapNode, SpecialTransform
from rlextra.radxml.xmlutils import TupleTreeWalker
from reportlab.lib.utils import asUnicode
import collections

def xhtmlDocFromXhtmlFragment(xhtmlFrag,enc='utf8'):
    r = []
    #r.append('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
    r.append('<html><head><title></title></head><body>')
    xhtmlFrag=xhtmlFrag.replace('<p><table>','<table>').replace('</table></p>','</table>')
    r.append(asUnicode(xhtmlFrag,enc=enc))
    r.append('</body></html>')
    r = ''.join(r)
    return r

def curry(func, *args, **kwargs):
    class C:
        def __init__(self, func, args, kw):
            self.func = func
            self.args = args
            self.kw = kw
        def __call__(self, *args, **kw):
            nkw = self.kw
            nkw.update(kw)
            return self.func(*(self.args + args), **nkw)
    return C(func, args, kwargs)

def pTransform(c, paraStyle='normal'):
    "take image out of p and put p in imageAndFlowables"
    if '<imageAndFlowables' not in c:
        return '<para style="%s">%s</para>' % (paraStyle, c)
    f = []
    #b = []
    s = '%s' % c
    while '<imageAndFlowables' in s:
        im = s[s.index('<imageAndFlowables'):s.index('</imageAndFlowables>') + 20]
        s = s.replace(im, '')
        im = im.split('><')
        f.append(im[0] + '>')
        #b.append('<' + im[1])
    f[-1] = f[-1] + '<para style="%s">%s</para>' % (paraStyle, s)
    f = [a + '</imageAndFlowables>' for a in f]
    f = ''.join(f) #+ ''.join(b)
    return f

def aTransform(sdict, name):
    href = sdict.get('href', '')
    if href.startswith('http://') or href.startswith('https://'):
        return '<a href="%s">%s</a>' % (href, sdict['__content__'])
    else:
        return sdict['__content__']

def aTransformMailto(sdict, name):
    """Transform of <a> which allows mailto links."""
    href = sdict.get('href', '')
    if href.startswith('http://') or href.startswith('https://')\
        or href.startswith('mailto:'):
        return '<a href="%s">%s</a>' % (href, sdict['__content__'])
    else:
        return sdict['__content__']

class ImageTransform(SpecialTransform):
    """Transforms XHTML 'img' tag to 'imageAndFlowables', but only if it's there.
    
    If not, we transform to '' so that missing images on the server don't cause
    RML to choke when creating the guide.
    """
    amap=dict(src='imageName',
              width='imageWidth',
              height='imageHeight',
              )

    def __init__(self, pathTransform=None,allowMissing=False, imageWidth=None, imageHeight=None):
        self.pathTransform = pathTransform
        self.allowMissing = allowMissing
        self.imageWidth = imageWidth
        self.imageHeight = imageHeight

    def __call__(self, sdict, name):
        D = sdict[name]._D
        src = D['src']
        if self.pathTransform:
            src = D['src'] = self.pathTransform(src)
        allowMissing = self.allowMissing
        if allowMissing:
            if isinstance(allowMissing, collections.Callable) and not allowMissing(src):
                return ''
        elif not os.path.isfile(src) and not src.startswith('rml:'):
            #image not found, so exclude it from the RML.  
            return ''

        ND = {}
        amap=self.amap
        K=list(amap.keys())
        for k,v in D.items():
            if k in K:
                ND[amap[k]] = v
        for a in ('imageWidth','imageHeight'):
            v = getattr(self,a,None)
            if v:
                ND[a] = v
        return '<imageAndFlowables %s imageSide="left"></imageAndFlowables>' % str(LazyAttrs(ND))

def xhtml2rml(xml, paraStyle='normal', tableStyle='noPaddingStyle', bulletStyle='bullet', pathTransform=None, imageTransformKwds={}, allowMailtoLinks=False):
    """Convert chunk of our mini-html to RML.
    
    >>> xhtml2rml('text')=='text'               #avoid spurious whitespace
    True
    >>> xhtml2rml('2m * 2m = 4m<sup>2</sup>')=='2m * 2m = 4m<sup>2</sup>'   #why it matters - space appears!
    True
    >>> xhtml2rml('<p>test</p>')=='<para style="normal">test</para>'
    True
    >>> xhtml2rml('<p>test</p>', paraStyle='custom')=='<para style="custom">test</para>'
    True
    >>> from rlextra.radxml.html_cleaner import cleanBlocks
    >>> xhtml2rml(cleanBlocks('<p>aaaa <img src="rml:img1">bbbb<p>cccc<img src="rml:img2"> dddd</p> eeeee</p>'))=='<imageAndFlowables  imageName="rml:img1" imageSide="left"><para style="normal">aaaa bbbb</para></imageAndFlowables><imageAndFlowables  imageName="rml:img2" imageSide="left"><para style="normal">cccc dddd</para></imageAndFlowables><para style="normal"> eeeee</para>'
    True
    """
    xml = xhtmlDocFromXhtmlFragment(xml)
    M = MapController()
    
    M[""] = '%(__content__)s'
    M["html"] = '%(__content__)s'
    M["body"] = '%(__content__)s'
    M["head"] = '%(__content__)s'
    M["title"] = '%(__content__)s'
    M["p"] = '%(__content__)s'
    M["p"].transformContent(curry(pTransform, paraStyle=paraStyle))
    M["img"] = MapNode(None, '%(__attrs__)s')
    if pathTransform: imageTransformKwds['pathTransform'] = pathTransform
    M["img"].addTransform('__attrs__', ImageTransform(**imageTransformKwds))
    M["table"] = '<blockTable style="' + tableStyle + '">%(__content__)s</blockTable>'
    M["tr"] = '<tr>%(__content__)s</tr>'
    M["td"] = '<td><para style="' + paraStyle + '">%(__content__)s</para></td>'
    M["th"] = '<td><para style="' + paraStyle + '">%(__content__)s</para></td>'
    M["b"] = '<b>%(__content__)s</b>'
    M["i"] = '<i>%(__content__)s</i>'
    M["u"] = '<u>%(__content__)s</u>'
    M["sup"] = '<sup>%(__content__)s</sup>'
    M["sub"] = '<sub>%(__content__)s</sub>'
    M["strong"] = MapNode('<b>%(__content__)s</b>','')
    M["em"] = '<i>%(__content__)s</i>'
    M["br"] = MapNode(None, '<br/>')
    M["h1"] = '<para style="h1">%(__content__)s</para>'
    M["h2"] = '<para style="h2">%(__content__)s</para>'
    M["h3"] = '<para style="h3">%(__content__)s</para>'
    M["h4"] = '<para style="h4">%(__content__)s</para>'
    M["h5"] = '<para style="h5">%(__content__)s</para>'
    M["h6"] = '<para style="h6">%(__content__)s</para>'
    M["ul"] = '%(__content__)s'
    M["ol"] = '%(__content__)s'
    M["li"] = '<para style="' + bulletStyle + '"><bullet>&bull;</bullet>%(__content__)s</para>'
    M["address"] = '<para style="' + paraStyle + '">%(__content__)s</para>'
    M["span"] = '%(__content__)s'
    M["a"] = MapNode('%(__attrs__)s', None)
    if allowMailtoLinks:
        M["a"].addTransform('__attrs__', aTransformMailto)
    else:
        M["a"].addTransform('__attrs__', aTransform)
    parser = pyRXPU.Parser(ExpandCharacterEntities=0, ExpandGeneralEntities=0)
    xml = parser.parse(xml)
    return M.process(xml, isTupleTree=True)

class ImageFinder(TupleTreeWalker):
    def __init__(self, tree):
        TupleTreeWalker.__init__(self, tree)
        self.images = []
    def startElement(self, tagName, attrs):
        if tagName == 'img':
            if 'src' in attrs:
                path = attrs['src']
                self.images.append(path)

def findImages(xml):
    "Returns lists of all images referred to in markup"
    xml = asUnicode(xml)
    validDoc = xhtmlDocFromXhtmlFragment(xml)  #adds 'html','head etc. to our fragment
    parser = pyRXPU.Parser(ReturnUTF8=1, ExpandCharacterEntities=0, ExpandGeneralEntities=0)
    tree = parser.parse(validDoc)
    walker = ImageFinder(tree)
    walker.go()
    return walker.images

# Testing

stylesheet = '''<initialize>
<alias id="style.normal" value="style.Normal"/>
</initialize>
<paraStyle name="h1" fontName="Courier-Bold" fontSize="15" spaceBefore = "0.5 cm" />
<paraStyle name="h2" fontName="Courier-Bold" fontSize="14" spaceBefore = "0.5 cm" />
<paraStyle name="h3" fontName="Courier-Bold" fontSize="13" spaceBefore = "0.5 cm" />
<paraStyle name="h4" fontName="Courier-Bold" fontSize="12" spaceBefore = "0.5 cm" />
<paraStyle name="normal" fontName="Helvetica" fontSize="10" leading="12"/>
<paraStyle name="bullet" parent="normal" leftIndent = "0.5cm"/>
<blockTableStyle id="noPaddingStyle" spaceAfter="0.5 cm">
    <blockAlignment value="left"/>
    <blockFont name="Helvetica-Oblique"/>
    <lineStyle kind="GRID" colorName="black"/>
    <lineStyle kind="OUTLINE" colorName="black" thickness="2"/>
    <blockBackground colorName="pink" start="0,0" stop="-1,0"/>
    <blockBackground colorName="yellow" start="0,0" stop="-1,0"/>
    <blockBackground colorName="yellow" start="0,0" stop="-1,0"/>
</blockTableStyle>'''

def indent(str):
    return '\n'.join(['\t%s' % l for l in str.split('\n')])

def testfile(path):
    from rlextra.radxml.html_cleaner import cleanBlocks
    from rlextra.rml2pdf.rml2pdf import invalid_rml
    import time
    import traceback

    f = open(path, 'r')
    try:
        html = cleanBlocks(f.read(), aHrefTr='http://reportlab.com')
        open(path+'.cleaned', 'w').write(html)
        print('Created ' + path+'.cleaned')
        b = float(len(html))/1024.0
        print('Testing %s (%d kB)' % (path, int(b)))
        try:
            start = time.time()
            rml = xhtml2rml(html)
            d = time.time() - start
        except:
            print(indent(traceback.format_exc()))
            print()
            sys.exit()
        else:
            open(path+'.rml', 'w').write(rml)
            print('Generated %s | Speed: %f kB/s' % (path+'.rml', b/d))
            errs = invalid_rml(rml, paragraph=False, stylesheet=stylesheet, saveAs=path+'.pdf')
            if not errs:
                print('Created ' + path+'.pdf')
            else:
                print('Error:', errs)
                sys.exit()
    finally:
        f.close()

def testdir(path):
    'Recursively looks for .html or .xml files in path and tries to convert them to rml and pdf.'
    for d in os.listdir(path):
        p = os.path.join(path, d)
        if os.path.isdir(p):
            testdir(p)
        elif os.path.isfile(p) and (p.endswith('.html') or p.endswith('.xml')):
            testfile(p)

if __name__=='__main__':
    # Runs doc tests and if a list of paths are passed, recursively converts .html and .xml files in there
    import doctest
    doctest.testmod()
    
    for path in sys.argv[1:]:
        testdir(path)
