#copyright ReportLab Inc. 2001-2012
#see license.txt for license details
"""<i>Invoice generation example</i>"""
import sys
import os

from rlextra.radxml import xmlutils
import preppy
from rlextra.rml2pdf import rml2pdf

def go(dictionary):
    """This provides support for the web framework.  Ignore it
    if you want to learn the basic concepts, instead use the command
    line routine below."""
    from rlextra.ers.framework import TemplateSelectingWrappedXMLProcessor
    return TemplateSelectingWrappedXMLProcessor().go(dictionary)


def runCommandLine(xmlFileName):

    #read into memory
    xmlText = open(xmlFileName, 'r').read()

    import pyRXPU
    tagTree = pyRXPU.Parser(ReturnUTF8=1).parse(xmlText)

    #use our 'TagWrapper' to get an object with friendly
    #syntax for referring to XML nodes
    wrappedTagTree = xmlutils.TagWrapper(tagTree)

    #make a dictionary to pass into preppy as its namespace.
    #you could pass in any Python objects or variables,
    #as long as the template expressions evaluate
    nameSpace = {'data':wrappedTagTree}

    template = preppy.getModule('rmltemplate.prep')
    rmlText = template.getOutput(nameSpace)

    #convert to PDF
    pdfFileName = os.path.splitext(xmlFileName)[0] + '.pdf'

    rml2pdf.go(rmlText, outputFileName=pdfFileName)
    print('saved %s' % pdfFileName)
    
        
if __name__=='__main__':
    if len(sys.argv) != 2:
        print('usage:  invoice.py myinvoice.xml > myinvoice.pdf')
    else:
        xmlFileName = sys.argv[1]
        runCommandLine(xmlFileName)        
