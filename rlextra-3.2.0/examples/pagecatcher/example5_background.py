#example5_background
"""
pageCatcher demo script:
   Add a background from one PDF file behind all pages of another PDF file
"""

import sys
from reportlab.pdfgen import canvas
try:
    from rlextra.pageCatcher.pageCatcher import storeForms, restoreForms, fourPage
except ImportError:
    pass # running inside pageCatcher module?

def run():
    inputFileName = "sample2.pdf"
    backgroundFileName = "sample3.pdf"
    outputFileName = "out5_background.pdf"
    BackgroundStorageFile = "background.data"
    ForegroundStorageFile = "foreground.data"

    print("placing background from", backgroundFileName, "behind pages of", inputFileName)
    print("storing to", outputFileName)


    print("storing all pages of", inputFileName, "in", ForegroundStorageFile)
    storeForms(inputFileName, ForegroundStorageFile, prefix="foreground", all=1)
    print("storing first page of", backgroundFileName,"in",BackgroundStorageFile)
    storeForms(backgroundFileName, BackgroundStorageFile, prefix="background", all=1)
    print("now restoring the pages as forms")
    canv = canvas.Canvas(outputFileName)
    ForeGroundFormNames = restoreForms(ForegroundStorageFile, canv)
    BackGroundFormNames = restoreForms(BackgroundStorageFile, canv)

    print("now writing out the pages with backgrounds")
    backgroundFormName = BackGroundFormNames[0]
    for f in ForeGroundFormNames:
        print(f)
        # background first
        canv.doForm(backgroundFormName)
        # now foreground
        canv.doForm(f)
        canv.showPage()
    canv.save()
    print("wrote", outputFileName)

if __name__=='__main__':
    run()

    