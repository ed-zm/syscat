"""
pageCatcher demo script:
   This version of "append" uses a specialized copy feature of pageCatcher
   which does not permit the modification of pages.  However, all pages of
   the copied document will be put into the output document together with
   annotations, bookmarks and outlines.
"""

try:
    from rlextra.pageCatcher.pageCatcher import copyPages
except ImportError:
    pass # running inside pageCatcher module?

from reportlab.pdfgen import canvas

def doappend(topdffile, frompdffilelist):
    canv = canvas.Canvas(topdffile)
    for frompdffile in frompdffilelist:
        print("copying", frompdffile)
        copyPages(frompdffile, canv)
    print("\n\nnow writing", topdffile)
    canv.save()

if __name__=="__main__":
    # edit this
    doappend("out8_directcopy.pdf", ["sample1.pdf", "sample2.pdf", "sample3.pdf"])