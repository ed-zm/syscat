import os
from rlextra.radxml import rltext
from rlextra.rml2pdf import rml2pdf
from types import UnicodeType

def getHtmlSamples(ext=('.html','.htm'), dir='.'):
    # return a list of files with a . html or .htm ext
    return [file for file in os.listdir(dir) if os.path.splitext(file)[1] in ext]

def runTestCases(samples):
    # process each html file
    if not samples: print("No test cases found"); return
    for sample in samples:
        f = open(sample)
        xhtml = f.read()
        filename = os.path.splitext(sample)[0]
        print()
        process(xhtml, filename, saveRml=True, generatePdf=True, verbose=True, saveNormalized=True)
        f.close()

def escu(txt):
    if txt == None:
        return ""
    """Use this for quoting text fields (which might contain non-ascii
    such as pound symbols, and '&' signs.  If they are unicode, it
    converts to UTF8 first."""
    if type(txt) is UnicodeType:
        bytes = txt.encode('utf8')
    else:
        bytes = txt
    return bytes

def process(xhtml, filename, saveRml=True, generatePdf=True, verbose=True, saveNormalized=True):
    # Entry method. Pass the xhtml and the filename to save the result to.
    # function Validates, Convert into RML, Save this rml or create a pdf.

    #check if it's UTF8 - if not, assume latin-1 and convert for them.   This would not be appropriate
    #for non-western clients.
    try:
        uText = xhtml.decode('utf8', 'strict')
    except UnicodeDecodeError:
        uText = xhtml.decode('cp1252', 'strict')
        xhtml = uText.encode('utf8')
    xhtml = escu(xhtml) # we have to make this unicode for pyRXPU
    
    # Validate xhtml
    rltext.validate(xhtml)
    
    # convert xhtml to rml
    rml = rltext.toRML(xhtml)
    rml = rml.encode('utf-8') # now we have to convert back to utf-8 for rml
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    filename = output_dir + '/' + filename
    
    # Test normalization code.
    # Normalization does clean up. In simple terms, gets xhtml, removes unsupported tags and returns a 
    # clean xhtml ready to be stored up somewhere.
    
    normalized_xhtml = rltext.normalize(xhtml)
    if saveNormalized:
        f = open('%s.nhtml' %filename, 'w')
        f.write(normalized_xhtml)
        f.close()
        if verbose: print("saved normalized xhtml in %s.nhtml" %filename)
    
    # Should we save this rml?
    if saveRml and filename:
        f = open('%s.rml' % filename, 'w')
        f.write(rml)
        f.close()
        if verbose: print("saved > %s.rml" % filename)
        
    # Should we generated pdf?
    if generatePdf and filename:        
        rml = getCannedRML(rml)
        toPDF(rml, '%s.pdf' % filename)
        if verbose: print("saved > %s.pdf" % filename)
    return
    
def getCannedRML(raw_rml, filename='test.pdf'):
    # Returns a proper RML ready to be converted into a pdf
    rml_template = """<?xml version="1.0" encoding="iso-8859-1" standalone="no"?>"""
    rml_template += """
    <!DOCTYPE document SYSTEM "rml_1_0.dtd">
    <document filename="%(filename)s" invariant="1">
        <docinit>
            <registerFont name="Frutiger-Roman"  faceName="Frutiger-Roman" encName="WinAnsiEncoding"/>   
            <registerType1Face afmFile="fonts/LT_50333.afm" pfbFile="fonts/LT_50333.pfb"/>
            <registerFont name="Frutiger-Black" faceName="Frutiger-Black" encName="WinAnsiEncoding"/> 
            <registerType1Face afmFile="fonts/LT_50331.afm" pfbFile="fonts/LT_50331.pfb"/>    
            <registerFontFamily normal="Frutiger-Roman" bold="Frutiger-Black"/>
        </docinit>
        <template>
            <pageTemplate id="titlePage" pageSize="210mm,297mm">
                <frame id="main" x1="25mm" y1="25mm" width="160mm" height="247mm"/>
            </pageTemplate>
        </template>
        <stylesheet>
            <paraStyle name="h1" fontName="Frutiger-Black" fontSize="38pt" leading="0.3in" spaceBefore="20"/>
            <paraStyle name="h2" fontName="Frutiger-Black" fontSize="10pt" leading="20" spaceBefore="20"/>
            <paraStyle name="normal" fontName="Frutiger-Roman" fontSize="8" leading="10" spaceBefore="10" spaceAfter="10"/>
            <paraStyle name="spaced" fontName="Frutiger-Roman" fontSize="8" leading="10" spaceBefore="10" spaceAfter="10"/>
            <blockTableStyle id="tableStyle">
                <lineStyle kind="grid" colorName="black"/>
            </blockTableStyle>
        </stylesheet>
        <story>
            %(raw_rml)s
        </story>
    </document>
    """
    return rml_template % dict(filename=filename, raw_rml=raw_rml)
    
def toPDF(rml, filename=None):
    # Method to convert rml to pdf. RML should be of proper format.
    if not filename:
        filename = getRandString() + ".pdf"
    rml2pdf.go(rml, outputFileName=filename)
        
if __name__ == "__main__":
    # start the tests
    samples = getHtmlSamples()
    runTestCases(samples)