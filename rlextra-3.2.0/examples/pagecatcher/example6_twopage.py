#example6_twopage.py
#prints PDF two to a page.  Works best with A4 portrait files;

from reportlab.pdfgen import canvas
try:
    from rlextra.pageCatcher.pageCatcher import storeForms, restoreForms, twoPage
except ImportError:
    pass # running inside pageCatcher module?

def run():
    inputFileName = "sample2.pdf"
    outputFileName = "out6_twopage.pdf"
    storageFile = "sample2.data"

    print("2 up", inputFileName, "into", outputFileName)

    storeForms(inputFileName, storageFile, all=1)
    print("stored all pages to", storageFile)
    #canv = canvas.Canvas(outputFileName)
    #formNames = restoreForms(storageFile, canv)

    def twoPage(storagefile, testfile, scalefactor = 0.75):
        print("placing forms from", storagefile, "into", testfile, "two to a page")
        from reportlab.pdfgen import canvas
        canv = canvas.Canvas(testfile)
        (width, height) = canv._pagesize
        names = restoreForms(storagefile, canv, verbose=1)
        while names:
            for (xoff, yoff) in [ (0,2), (0,1) ]:
                thisname = names[0]
                print(thisname, end=' ')
                canv.saveState()
                (x,y) = (0, yoff*height/2.0)
                canv.translate(x,y)
                canv.rotate(-90)
                canv.scale(scalefactor, scalefactor)
                canv.doForm(thisname)
                canv.restoreState()
                del names[0]
                if not names: break
            canv.showPage()
            print()
        canv.save()
        print("wrote", testfile)

    twoPage(storageFile, outputFileName)

if __name__=='__main__':
    run()

    