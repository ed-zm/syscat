
"make form f1040ez from xml input"

def main(xmlinput, rmlfilename="f1040last.rml", pdffilename="f1040last.pdf"):
    # parse the input
    from reportlab.lib.rparsexml import parsexml
    parsed = parsexml(xmlinput)
    #print parsed
    tags = parsed[2]
    firsttag = tags[0]
    while isinstance(firsttag,str):
        del tags[0]
        firsttag = tags[0]
    attributes = firsttag[1]
    # now generate the rml from the attributes
    import preppy
    template = preppy.getModule("f1040ezTemplate")
    rmlfile = open(rmlfilename, "w")
    template.run(attributes, outputfile=rmlfile)
    rmlfile.close()
    print("wrote", rmlfilename)
    rml = open(rmlfilename, "r").read()
    import string
    rml = string.replace(rml, '"test.pdf"', '"%s"' % pdffilename)
    # now process the rml into pdf
    from rlextra.rml2pdf import rml2pdf
    rml2pdf.go(rml)
    print("wrote", pdffilename)

if __name__=="__main__":
    import sys
    args = sys.argv[1:]
    if args:
        xmlfilename = args[1]
    else:
        print("usage: makef1040ez.py InputFileName.xml")
        print("defaulting to f1040ez_example.xml")
        xmlfilename = "f1040ez_example.xml"
    xmlinput = open(xmlfilename).read()
    main(xmlinput)

    
