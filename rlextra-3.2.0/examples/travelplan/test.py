# simple program to generate a PDF document. data comes from a preppy file and is generated into a PDF
import os
import preppy
from rlextra.rml2pdf import rml2pdf
from rlextra.radxml.xmlutils import xml2doctree


def generatePDF(xml='''<doc><a>AAAAA</a></doc>'''):
    # 1 - get the prep file
    module = preppy.getModule('travel_template.prep')
    preppydict =  dict( doc = xml2doctree(xml),)  #this is the preppy dictionary
    #print "doc: %s" % doc
    rml = module.getOutput(preppydict)
    outputFileName='myPDFfile.pdf'
    saveRml='latest.rml'
    rml2pdf.go(rml, outputFileName=outputFileName, outDir='.',saveRml=saveRml)
    print("generated %s and %s" % (outputFileName, saveRml))

def parseCommmandLine():
    from optparse import OptionParser
    parser = OptionParser('test [options]')
    parser.set_defaults(dirName=os.getcwd())
    parser.add_option("--xml", help='retrieve data from an XML document') 
    return parser.parse_args()

def main():
    options, args = parseCommmandLine()

    # check whether we have a xml document for reading      
    if options.xml:
        xmlFile = options.xml
        f = open(xmlFile, 'r')
        xmlDoc = f.read()
        f.close()
    generatePDF(xml=xmlDoc)
    
if __name__=="__main__":
    main()

