#tests ability to parse a PDF and extract info
"""
Tests for ability to parse and extract info from PDF files.

Started Jan 2008, while adding recursive text extraction from subforms
"""
import os, sys, io, unittest
from pprint import pformat, pprint

class PdfExplorer(unittest.TestCase):

    def setUp(self):
        #check we're in the pagecatcher directory
        self.startDir = os.getcwd()
        cwd = os.getcwd()
        if not cwd.endswith('pagecatcher'):
            #probably running in 'tests'
            if os.path.isdir('pagecatcher'):
                os.chdir('pagecatcher')

    def tearDown(self):
        os.chdir(self.startDir)

    def test_can_open_ir684(self):
        "British Inland Revenue pdf included in distro"

        from rlextra.pageCatcher.pdfexplorer import PdfExplorer
        with open('ir684.pdf','rb') as f:
            exp = PdfExplorer(f.read())

        self.assertEqual(exp.pageCount, 2)
        page_1_text = exp.getText(0)  #zero based
        assert "BMSD10/99" in page_1_text
        assert "Data Protection Act" in exp.getText(1)

        #print exp.getText(1)

    def test_nested_forms(self):
        from rlextra.pageCatcher.pdfexplorer import PdfExplorer
        from reportlab.pdfgen.canvas import Canvas
        c = Canvas('temp_nested_forms.pdf', pageCompression=0)
        c.drawString(100,700,'this is top level text')

        c.beginForm('subsubsubform3')
        c.drawString(100,400,'buried deep in subsubsubform3 and called in subsubform2')
        c.endForm()

        c.beginForm('subsubform2')
        c.drawString(100,500,'this is written in subsubform2 and called in subform1')
        c.doForm('subsubsubform3')
        c.endForm()

        c.beginForm('subform1')
        c.drawString(100,600,'this is written in subform1')
        c.doForm('subsubform2')
        c.endForm()

        c.doForm('subform1')
        c.save()

        pdfData = c.getpdfdata()

        exp = PdfExplorer(pdfData)
        page1text = exp.getText(0)

        assert "this is top level text" in page1text
        assert "this is written in subform1" in page1text
        assert "this is written in subsubform2 and called in subform1" in page1text
        assert "buried deep" in page1text

def makeSuite():
    return unittest.TestSuite((
                unittest.makeSuite(PdfExplorer,'test'),
                )
            )

if __name__=='__main__':
    unittest.main()
