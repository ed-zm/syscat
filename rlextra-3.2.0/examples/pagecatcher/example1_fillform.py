#example1_fillform
# uses a PDF as a form and fills in first page


try:
    from rlextra.pageCatcher.pageCatcher import storeForms, restoreForms
except ImportError:
    pass # running inside pageCatcher module?


data = """
1.7     24.5    Mr. Bond T. Owner
8.5     24.5    11-222-3344
11.5    24.5    Ms. With H. Agent
16.7    24.5    99-88-7777
1.7     23.4    10 Main St., Podunk OH 667788
11.5    23.4    1 Big Building, New York, NY 10011
9       22.5    Bernum & Runn, Inc 1999
15.3    22.5    10 Jan 2000
17.8    22.5    10 Dec 2000
1.7     21.7    (X)
1.7     20.8    F. Agent, Esquire
1.7     20.4    15 Central Av., Newark, NJ 11989
15.5    20.3    1999.90
18      20.3    0.00
15.5    19.5    1666.00
"""

def preprocess_form(pdffile,
                    storagefile):
    storeForms(pdffile, storagefile)
    print('preprocessed %s -> %s' % (pdffile, storagefile))
        

def do_test_form(storagefile, 
                 testfile, 
                 data=data):
    # make a canvas to draw on
    from reportlab.pdfgen import canvas
    canv = canvas.Canvas(testfile)
    # get the stored form layout
    names = restoreForms(storagefile, canv)
    # put the form layout on the current page
    canv.doForm(names[0])
    # fill the form in...
    canv.setFont("Helvetica", 10)
    from reportlab.lib.units import cm
    from reportlab.lib.colors import green
    canv.setFillColor(green)
    import string
    lines = string.split(string.strip(data), "\n")
    for l in lines:
        sline = string.split(l)
        x, y = float(sline[0]), float(sline[1])
        entry = string.join(sline[2:], " ")
        canv.drawString(x*cm, y*cm, entry)
    canv.showPage()
    canv.save()
    print('wrote filled form as %s' % testfile)

def run(preprocess_form=preprocess_form, do_test_form=do_test_form):
    preprocess_form('sample1.pdf','sample1.data')
    do_test_form('sample1.data','out1_fillform.pdf')
    

if __name__=="__main__":
    #print dir()
    run(preprocess_form, do_test_form)