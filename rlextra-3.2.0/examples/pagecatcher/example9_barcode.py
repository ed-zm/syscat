#example9_barcode
"""
pageCatcher demo script:
   Adds a barcode onto scaled pages of another PDF file.
   Very simplistic use of barcodes for demo purposes only.
"""

import sys
from reportlab.pdfgen import canvas
try:
    from rlextra.pageCatcher.pageCatcher import storeForms, restoreForms #, fourPage
except ImportError:
    pass # running inside pageCatcher module?

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.widgets import BarcodeStandard93


def run():
    inputFileName = "sample2.pdf"
    outputFileName = "out9_barcodes.pdf"
    ForegroundStorageFile = "foreground.data"

    print("placing barcodes on pages of", inputFileName)
    print("storing to", outputFileName)


    print("storing all pages of", inputFileName, "in", ForegroundStorageFile)
    storeForms(inputFileName, ForegroundStorageFile, prefix="foreground", all=1)
    print("now restoring the pages as forms")
    canv = canvas.Canvas(outputFileName)
    ForeGroundFormNames = restoreForms(ForegroundStorageFile, canv)
    pagenum = 0

    print("now writing out the pages with barcodes")
    for f in ForeGroundFormNames:
        print(f)
        pagenum += 1
        # display foreground scaled at 75%
        canv.saveState()
        canv.scale(0.75, 0.75)
        canv.doForm(f)
        canv.restoreState()

        #Create a blank Drawing.  This would commonly be
        #used for charts, but BarCode widgest can be added too
        d= Drawing(100,50)
        #create and set up the widget
        bc = BarcodeStandard93()
        bc.value = 'DEM-%06d' % (pagenum+1)
        d.add(bc) 
        d.drawOn(canv, 25, 720)

        canv.showPage()
    canv.save()
    print("wrote", outputFileName)
    

if __name__=='__main__':
    run()

    
