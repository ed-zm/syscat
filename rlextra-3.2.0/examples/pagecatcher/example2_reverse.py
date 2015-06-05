"""
pageCatcher demo script:
   reverse the pages in a pdf file.   
"""
from reportlab.pdfgen import canvas
inputFileName = "sample2.pdf"
outputFileName = "out2_reversed.pdf"
storageFile = "sample2.data"


try:
    from rlextra.pageCatcher.pageCatcher import storeForms, restoreForms
except ImportError:
    pass # running inside pageCatcher module?

def run(inputFileName=inputFileName, outputFileName=outputFileName, storageFile=storageFile):
    print("reversing", inputFileName, "into", outputFileName)
    storeForms(inputFileName, storageFile, all=1)
    print("stored all pages to", storageFile)
    canv = canvas.Canvas(outputFileName)
    formNames = restoreForms(storageFile, canv)

    # write out the pages in reversed order
    formNames.reverse()
    for f in formNames:
        canv.doForm(f)
        canv.showPage()
    canv.save()
    print("wrote", outputFileName)

if __name__=='__main__':
    run(inputFileName=inputFileName, outputFileName=outputFileName, storageFile=storageFile)

    
