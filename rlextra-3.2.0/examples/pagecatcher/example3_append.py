# example3_append.py
"""
pageCatcher demo script:
   Concatenates pdf files together.
"""
from reportlab.pdfgen import canvas
try:
    from rlextra.pageCatcher.pageCatcher import storeForms, restoreForms
except ImportError:
    pass # running inside pageCatcher module?

def run():
    outputFileName = "out3_combined.pdf"
    inputFileNames = ["sample1.pdf", "sample2.pdf"]
    tempfile = "combined.data"
    print("concatenating", inputFileNames, "into", outputFileName)
    canv = canvas.Canvas(outputFileName)
    count = 0
    for pdfFileName in inputFileNames:
        count = count+1
        prefix = "prefix"+str(count)
        print("storing pages from", pdfFileName)
        storeForms(pdfFileName, tempfile, prefix=prefix, all=1)
        print("now restoring", pdfFileName, "into", outputFileName)
        pageforms = restoreForms(tempfile, canv)
        for n in pageforms:
            canv.doForm(n)
            canv.showPage()
    print("storing", outputFileName)
    canv.save()


if __name__=="__main__":
    run()