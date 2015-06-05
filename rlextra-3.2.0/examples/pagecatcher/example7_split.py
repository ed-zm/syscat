"""
pageCatcher demo script:
   Split one file into many PDFs, one page each.
"""

import sys
from reportlab.pdfgen import canvas
try:
    from rlextra.pageCatcher.pageCatcher import storeForms, restoreForms, fourPage
except ImportError:
    pass # running inside pageCatcher module?

def run():
    inputFileName = "sample2.pdf"
    StorageFile = "out7_split.data"
    page = 0
    done = 0
    while not done:
        try:
            print("from", inputFileName, "storing page", page, "to", StorageFile)
            storeForms(inputFileName, StorageFile, [page])
        except IndexError:
            print("stopping at page count", page)
            done = 1
        else:
            outputFileName = "out7_page"+str(page)+".pdf"
            print("restoring page into", outputFileName)
            canv = canvas.Canvas(outputFileName)
            names = restoreForms(StorageFile, canv)
            canv.doForm(names[0])
            canv.showPage()
            canv.save()
            print("   done with page", page)
            page = page+1

if __name__=='__main__':
    run()

    