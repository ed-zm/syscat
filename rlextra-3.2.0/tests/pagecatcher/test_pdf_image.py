#tests pdf image
from rlextra.pageCatcher import pageCatcher
from reportlab.pdfgen.canvas import Canvas
def run():
    c = Canvas('test_pdf_image.pdf')
    c.drawString(72, 720, "Testing PDFs as images....")
    c.drawString(72, 700, "These all use a blue-ish vector icon of a PC")

    imageName = "internet_access.pdf"

    #natural size
    c.drawString(72, 680, "Huge image off the right edge ---->")
    pageCatcher.drawPdfImage(imageName, c),


    c.drawString(5, 25, "little 25x25 point image at page corner")

    pageCatcher.drawPdfImage(imageName, c,
                             width=25, height=25,
                             showBoundary=True)

    #move it a bit
    c.drawString(100, 630, "50x25 image below me, origin (600,100)...")
    pageCatcher.drawPdfImage(imageName, c,
                             x=100, y=600,
                             width=50, height=25,
                             showBoundary=True)


    #preserve aspect 
    c.drawString(100, 530, "zoomed to fit at west and east edges of 50x25 box")
    pageCatcher.drawPdfImage(imageName, c,
                             x=100, y=500,
                             width=50, height=25,
                             showBoundary=True,
                             preserveAspectRatio=True
                             )
    pageCatcher.drawPdfImage(imageName, c,
                             x=200, y=500,
                             width=50, height=25,
                             showBoundary=True,
                             preserveAspectRatio=True,
                             anchor="e"
                             )
    c.drawString(100, 460, "zoomed to fit at north and south edges of 25x50 box")

    pageCatcher.drawPdfImage(imageName, c,
                             x=100, y=400,
                             width=25, height=50,
                             showBoundary=True,
                             preserveAspectRatio=True,
                             anchor='n'
                             )
    pageCatcher.drawPdfImage(imageName, c,
                             x=200, y=400,
                             width=25, height=50,
                             showBoundary=True,
                             preserveAspectRatio=True,
                             anchor='s'
                             )


    #aspect ratio should be kept if shrinking...


##def drawPdfImage(fileName, canv, x=0, y=0, width=None, height=None,
##                 preserveAspectRatio=False, pageNumber=0):


    c.save()
    print('saved test_pdf_image.pdf')

if __name__=='__main__':
    run()
