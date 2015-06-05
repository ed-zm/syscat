
"test extracting info from pdf-forms"

pdfsource = "f1040ez.pdf"
storagefile = "f1040ez.storage"
formdump = "f1040ez.py"
pdfoutfile="f1040annotated.pdf"
import string, sys
from reportlab.pdfgen.canvas import Canvas

def annotate(pdfoutfile=pdfoutfile, pdfsource=pdfsource, formdump=formdump, storagefile=storagefile):
    canvas = Canvas(pdfoutfile)
    print("first get the formdata")
    formdatatext = string.strip(open(formdump).read())
    formdata = eval(formdatatext)
    print("now catch the form pages")
    from rlextra.pageCatcher import pageCatcher
    formnames = pageCatcher.storeForms(pdfsource, storagefile, all=1, verbose=1)
    pageCatcher.restoreForms(storagefile, canvas)
    npages = len(formnames)
    print(formnames)
    if len(formdata)!=npages:
        raise ValueError("number of forms and pages should match")
    # now annotate the form pages with the field info
    for pagenumber in range(npages):
        formname = formnames[pagenumber]
        canvas.doForm(formname)
        canvas.setStrokeColorRGB(0, 0.5, 1)
        canvas.setFillColorRGB(1, 1, 0)
        canvas.setFont("Courier", 5)
        formdatum = formdata[pagenumber]
        for field in formdatum:
            if field is None:
                print("Warning, field repeats!")
            elif "Rect" in field:
                # draw the rectangle
                rect = field["Rect"]
                #print rect
                (x1, y1, x2, y2) = rect
                canvas.rect(x1, y1, x2-x1, y2-y1, fill=1)
        canvas.setFillColorRGB(0.5, 0, 0)
        count = 0
        for field in formdatum:
            if field and "Rect" in field:
                rect = field["Rect"]
                (x1, y1, x2, y2) = rect
                canvas.saveState()
                canvas.translate(x1+1, y1+1)
                canvas.rotate(20)
                T = FT = None
                if "T" in field:
                    T = field["T"]
                if "FT" in field:
                    FT = field["FT"]
                canvas.setFillColorRGB(1,1,1)
                canvas.rect(0,0,25,3,fill=1,stroke=0)
                canvas.setFillColorRGB(0.5, 0, 0)
                canvas.drawString(0,0, "[%s][%s] %s:%s" %(pagenumber, count, T, FT))
                canvas.restoreState()
                count = count+1
        canvas.showPage()
    canvas.save()
    print("wrote", pdfoutfile)

if __name__=="__main__":
    annotate()

    