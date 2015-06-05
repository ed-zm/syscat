
"make preppy for a form"

formdatafile = "f1040fields.py"
storagefile = "f1040.storage"

def emitString(name, x, y, font="Courier", size=10, op="drawString", sx=1):
    D = {"name": name, "x": x, "y": y, 
         "font": font, "size": size, "op": op, "sx": sx,
        }
    return """
    <pageGraphics>
    <translate dx="%(x)s" dy="%(y)s"/>
    <scale sx="%(sx)s" sy="1"/>
    <setFont name="%(font)s" size="%(size)s"/>
    <%(op)s x="0" y="0">{{%(name)s}}</%(op)s>
    </pageGraphics>""" % D

def emit(name, alignment, description, xmin, xmax, y):
    if not description:
        if alignment==2:
            return emitString(name, xmax-6, y+1, op="drawRightString")
        else:
            return emitString(name, xmin+2, y+1, size=8)
    elif description=="phone":
        return emitString(name, xmin-1, y+1, size=12)
    elif description=="PIN":
        return emitString(name, xmin, y+1, size=12, sx=2) # formerly 2.1
    elif description=="bigssn":
        return emitString(name, xmin+10, y+1, size=12, sx=1)
    elif description=="ssn":
        return emitString(name, xmin+2, y+1, size=12)
    elif description=="account":
        return emitString(name, xmin, y+1, size=12, sx=2) # formerly 1.65
    else:
        raise ValueError("unknown description: "+repr((description,name)))

def genpreppy(formdatafile=formdatafile, storagefile=storagefile):
    print("""<!DOCTYPE document SYSTEM "rml_1_0.dtd"> 
<document filename="test.pdf">

<stylesheet>
</stylesheet>
""")
    formdata = eval( open(formdatafile).read() )
    starting = 1
    count = 0
    for page in formdata:
        print("<pageDrawing>")
        print('<fill color="red"/>')
        if starting:
            print('<catchForms storageFile="%s"/>' % storagefile)
        print('<doForm name="PF%s"/>' % count)
        starting = 0
        for descriptor in page:
            name = descriptor["T"]
            # ignore names that begin "c" or "f"
            if name[0] in "cf":
                continue
            alignment = descriptor.get("Q", 0)
            description = descriptor.get("TU", None)
            [xmin,ymin,xmax,ymax] = descriptor["Rect"]
            print(emit(name, alignment, description, xmin, xmax, ymin))
        count = count+1
        print("</pageDrawing>")
    print("</document>\n\n")
    return ""

if __name__=="__main__":
    import sys
    args = sys.argv[1:]
    if not args:
        stdout = sys.stdout
        sys.stdout = sys.stderr
        print("usage: makeprep.py formname")
        print("defaulting to formname='f1040'")
        sys.stdout = stdout
        formname = "f1040"
    else:
        formname = args[0]
    formdatafile = "%sfields.py" % formname
    storagefile = "%s.storage" % formname
    print(genpreppy(formdatafile, storagefile))