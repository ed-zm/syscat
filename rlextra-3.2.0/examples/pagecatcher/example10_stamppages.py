#example9_barcode
"""
pageCatcher demo script:
   adds a message to each page of a document
"""

import sys
from reportlab.pdfgen import canvas
from reportlab.lib import colors
#this bit looks strange; it's possible for this script to be
#run from a pagecatcher .exe which already has storeForms + restoreForms
#in the namespace.  Normal programmers don't need try/except.
try:
    from rlextra.pageCatcher.pageCatcher import storeForms, restoreForms #, fourPage
except ImportError:
    pass # running inside pageCatcher module?



def run():
    inputFileName = "sample2.pdf"
    outputFileName = "out10_stamppages.pdf"

    #one could do it all in memory, but if there is one input file to
    #be marked up many times, it's easier to store the parsed input
    #PDF in our input PDF file.
    tempStorageFile = "out10_intermediate.data"

    print("placing barcodes on pages of", inputFileName)
    print("storing to", outputFileName)


    print("storing all pages of", inputFileName, "in", tempStorageFile)
    storeForms(inputFileName, tempStorageFile, prefix="foreground", all=1)


    #start a blank document
    canv = canvas.Canvas(outputFileName)
    print("now restoring the pages as forms to be available in a new Canvas")
    formNames = restoreForms(tempStorageFile, canv)
    pagenum = 0

    print("now writing out the pages with barcodes")
    for f in formNames:
        pagenum += 1

        #lay down the input page
        canv.doForm(f)  

        #now draw what you want to...
        canv.setFont('Helvetica-BoldOblique', 24)
        canv.setFillColor(colors.red)
        canv.drawCentredString(297, 800, 'Document watermarked by ReportLab')


        canv.showPage()
        print('.', end=' ')   #progress indicator
    canv.save()
    print("wrote", outputFileName)
    

if __name__=='__main__':
    run()

    
