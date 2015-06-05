# example3_append.py
"""
pageCatcher demo script:
   Concatenates pdf files together, using the in-memory APIs.
   Use this if you are working with PDF files read from file like
   objects, rather than on the disk.  Otherwise, it's exactly like
   example3_append.py
"""
from io import StringIO

from reportlab.pdfgen import canvas
try:
    from rlextra.pageCatcher.pageCatcher import storeFormsInMemory, restoreFormsInMemory
except ImportError:
    pass # running inside pageCatcher module?

def run():
    outputFileName = "out3_combined.pdf"
    inputFileNames = ["sample1.pdf", "sample2.pdf"]
    tempfile = "combined.data"
    print("concatenating", inputFileNames, "into", outputFileName)
    
    
    #we will write out output to a memory buffer.  You could
    #just as easily write to any file like object
    
    outbuf = StringIO()
    canv = canvas.Canvas(outbuf)
    count = 0
    for pdfFileName in inputFileNames:
        count = count+1
        prefix = "prefix"+str(count)
        print("storing pages from", pdfFileName)
        
        #get your input PDF ready as one big string
        inputPDF = open(pdfFileName, 'rb').read()
        
        (formnames, content) = storeFormsInMemory(inputPDF, prefix=prefix, all=1)
        
        print("now restoring", pdfFileName, "into", outputFileName)
        
        pageforms = restoreFormsInMemory(content, canv)
        
        for n in pageforms:
            canv.doForm(n)
            canv.showPage()


    #canvas writes to file like object
    canv.save()
    outputPDF = outbuf.getvalue()   #your PDF as a string
    open(outputFileName, 'wb').write(outputPDF)
    
    print("stored", outputFileName)
    



if __name__=="__main__":
    run()
