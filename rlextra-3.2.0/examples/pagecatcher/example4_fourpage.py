#example4_fourpage.py
#prints PDF four to a page.  Works best with A4 portrait files;
from reportlab.pdfgen import canvas
try:
    from rlextra.pageCatcher.pageCatcher import storeForms, restoreForms, fourPage
except ImportError:
    pass # running inside pageCatcher module?

def run():
    inputFileName = "sample2.pdf"
    outputFileName = "out4_fourpage.pdf"
    storageFile = "sample2.data"

    print("reversing", inputFileName, "into", outputFileName)

    storeForms(inputFileName, storageFile, all=1)
    print("stored all pages to", storageFile)
    #canv = canvas.Canvas(outputFileName)
    #formNames = restoreForms(storageFile, canv)

    fourPage(storageFile, outputFileName)

if __name__=='__main__':
    run()

    
