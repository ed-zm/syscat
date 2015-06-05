
"make preppy for a form, with matching xml example"

formname = "f1040"
formdatafile = "f1040fields.py"
dtdout = "f1040.dtd"
xmlout = "f1040_example.xml"

import string

def emitString(name, example, dtdfile, xmlfile):
    dtdfile.write("""
	%s CDATA #REQUIRED""" % name)
    xmlfile.write("""
	%s="%s" """ % (name, example))

count = 1000.99
def emit(name, alignment, description, fieldtype, dtdfile, xmlfile):
    global count
    count = count+1
    example = str(name)[:15]
    if fieldtype=="/Btn":
        example = "X"
    if not description:
        if alignment==2:
            return emitString(name, count, dtdfile, xmlfile)
        else:
            return emitString(name, example, dtdfile, xmlfile)
    elif description=="phone":
        example = "111 222 %s" % int(count)
    elif description=="PIN":
        example = int(count)
    elif description=="bigssn":
        example = "999 22 %s" % int(count)
    elif description=="ssn":
        example = "333 44 %s" % int(count)
    elif description=="account":
        example = "9999%s" % int(count)
    else:
        raise ValueError("unknown description: "+repr((description,name)))
    return emitString(name, example, dtdfile, xmlfile)

def gendtd(formname=formname, formdatafile=formdatafile, dtdout=dtdout, xmlout=xmlout):
    dtdfile = open(dtdout, "w")
    xmlfile = open(xmlout, "w")
    #formname = string.split(dtdout, ".")[0]
    xmlfile.write("""<!DOCTYPE %s SYSTEM "%s">\n\n<%s\n""" % (formname, dtdout, formname))
    dtdfile.write("""\n<!ELEMENT %s EMPTY>\n\n<!ATTLIST %s\n""" % (formname, formname))
    formdata = eval( open(formdatafile).read() )
    starting = 1
    count = 0
    seen = {}
    for page in formdata:
        for descriptor in page:
            name = descriptor["T"]
            if name in seen:
                # don't do it again
                continue
            seen[name] = name
            # ignore names that begin "c" or "f"
            if name[0] in "cf":
                continue
            fieldtype = descriptor["FT"]
            alignment = descriptor.get("Q", 0)
            description = descriptor.get("TU", None)
            [xmin,ymin,xmax,ymax] = descriptor["Rect"]
            dummy = emit(name, alignment, description, fieldtype, dtdfile, xmlfile)
        count = count+1
    dtdfile.write("\n>\n\n")
    dtdfile.close()
    xmlfile.write("\n /> <!-- end of %s -->" % formname)
    xmlfile.close()
    print("wrote", dtdout, "and", xmlout)
    return ""

if __name__=="__main__":
    import sys
    args = sys.argv[1:]
    if not args:
        print("usage: makedtd.py formname")
        print("defaulting to formname='f1040'")
        formname = "f1040"
    else:
        formname = args[0]
    formdatafile = "%sfields.py" % formname
    storagefile = "%s.storage" % formname
    dtdout = "%s.dtd" % formname
    xmlout = "%s_example.xml" % formname
    print(gendtd(formname=formname, formdatafile=formdatafile, dtdout=dtdout, xmlout=xmlout))