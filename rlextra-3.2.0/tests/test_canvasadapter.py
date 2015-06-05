import os
import unittest
from reportlab.lib.testutils import makeSuiteForClasses
from rlextra.graphics.canvasadapter import PMCanvasAdapter, PSCanvasAdapter
from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics.renderPM import PMCanvas
from rlextra.graphics.renderPS_SEP import PSCanvas_SEP
def getExemplar(n):
    if n==1:
        from rlextra.graphics.chargestable import ChargesTable
        F = ChargesTable().asFlowable()
    elif n==2:
        from rlextra.graphics.chargestable import JumboChargesTable
        F = JumboChargesTable().asFlowable()
    else:
        from reportlab.platypus.tables import Table, TableStyle
        from reportlab.platypus.paragraph import Paragraph
        from reportlab.platypus.flowables import CallerMacro
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.colors import blue, lightgrey, red
        from reportlab.rl_config import verbose
        class callMacroAction:
            def __init__(self,msg):
                self._msg = msg
            def __call__(self,macro,*args):
                canv = macro.canv
                ctm = getattr(canv,'ctm',None) or getattr(canv,'_currentMatrix')
                print(self._msg, ctm)
        P0 = Paragraph('<b>Hello</b><font color="green">World</font>! This is the end! This is a<sub><font color="red">i</font></sub> subscript.',
                style = getSampleStyleSheet()['Normal'])
        T0 = Table([ ['','Hello World'],
                    ['1','2'],
                    ],
                    style=TableStyle([
                        ('GRID',(0,0),(-1,-1),1,blue),
                        ('BACKGROUND',(0,0),(-1,0),lightgrey),
                        ('ALIGN',(0,1),(-1,1),'RIGHT'),
                        ]),
                    )
        c0 = [CallerMacro(callMacroAction('before drawing P0'))] if verbose else []
        c1 = [CallerMacro(callMacroAction('after  drawing P0'))] if verbose else []
        F = Table([ ['ABCDEF','GHIJKL'],
                    ['next to a Para',[c0, P0, c1]],
                    ['next to a TABLE',T0],
                    ['1','2'],
                    ],
                    colWidths = (None,144),
                    style=TableStyle([
                        ('GRID',(0,0),(-1,-1),0.6,red),
                        ]),
                    )
    return F

class CanvasAdapterTestCase(unittest.TestCase):

    @staticmethod
    def runtest(kind,n):
        fn = 'test_canvasadapter-%d.%s'%(n,kind)
        if os.path.isfile(fn):
            os.remove(fn)
        if kind=='eps':
            F = getExemplar(n)
            w, h = F.wrap(240,10000)
            c = PSCanvasAdapter(PSCanvas_SEP((w+2,h+2)))
            F.drawOn(c,1,1)
            c.save(fn)
        elif kind=='gif':
            F = getExemplar(n)
            w, h = F.wrap(240,10000)
            canv = PMCanvasAdapter(PMCanvas(w+2,h+2,dpi=96))
            F.drawOn(canv,1,1)
            canv.saveToFile(fn)
        elif kind=='pdf':
            F = getExemplar(n)
            w, h = F.wrap(240,10000)
            c = Canvas(fn)
            F.drawOn(c,0,0)
            c.save()
        return fn

    def test_eps_0(self):
        fn = self.runtest('eps',0)
        self.assertTrue(os.path.isfile(fn))

    def test_eps_1(self):
        fn = self.runtest('eps',1)
        self.assertTrue(os.path.isfile(fn))

    def test_eps_2(self):
        fn = self.runtest('eps',2)
        self.assertTrue(os.path.isfile(fn))

    def test_gif_0(self):
        fn = self.runtest('gif',0)
        self.assertTrue(os.path.isfile(fn))

    def test_gif_1(self):
        fn = self.runtest('gif',1)
        self.assertTrue(os.path.isfile(fn))

    def test_gif_2(self):
        fn = self.runtest('gif',2)
        self.assertTrue(os.path.isfile(fn))

    def test_pdf_0(self):
        fn = self.runtest('pdf',0)
        self.assertTrue(os.path.isfile(fn))

    def test_pdf_1(self):
        fn = self.runtest('pdf',1)
        self.assertTrue(os.path.isfile(fn))

    def test_pdf_2(self):
        fn = self.runtest('pdf',2)
        self.assertTrue(os.path.isfile(fn))

def makeSuite():
    return makeSuiteForClasses(CanvasAdapterTestCase)

#noruntests
if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
