
"make form f1040ez from xml input"

import string

def main(xmlinput, formname, fileprefix):
    # parse the input
    from reportlab.lib.rparsexml import parsexml
    parsed = parsexml(xmlinput)
    tags = parsed[2]
    firsttag = tags[0]
    while isinstance(firsttag,str):
        del tags[0]
        firsttag = tags[0]
    attributes = firsttag[1]
    # now generate the rml from the attributes
    import preppy
    template = preppy.getModule("%sTemplate" % formname)
    rmlfilename = fileprefix + ".rml"
    rmlfile = open(rmlfilename, "w")
    template.run(attributes, outputfile=rmlfile)
    rmlfile.close()
    print("wrote", rmlfilename)
    rml = open(rmlfilename, "r").read()
    import string
    pdffilename = fileprefix + ".pdf"
    rml = string.replace(rml, '"test.pdf"', '"%s"' % pdffilename)
    # now process the rml into pdf
    from rlextra.rml2pdf import rml2pdf
    rml2pdf.go(rml)
    print("wrote", pdffilename)

if __name__=="__main__":
    import sys
    args = sys.argv[1:]
    if len(args)==2:
        xmlfilename = args[1]
        formname = args[0]
    else:
        print("usage: makeform.py formname InputFileName.xml")
        print("defaulting to f1040 f1040_example.xml")
        formname = "f1040"
        xmlfilename = "f1040_example.xml"
    xmlinput = open(xmlfilename).read()
    fileprefix = string.split(xmlfilename, ".")[0]
    main(xmlinput, formname, fileprefix)

    
