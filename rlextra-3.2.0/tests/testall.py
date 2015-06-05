"""Invokes all relevant tests for the rlextra framework

This is being totally rewritten for reportlab/rlextra 2.7.
Our test suite used archaic techniques.  We have also just
rearranged the rlextra tree to separate cleanly into
   src/
   tests/
   docs/
   examples/

It is assumed that you execute the tests inside 'tests', in a
source distribution.  Therefore we can hop 'back up' to run
demos and check docs build.




"""
import os, sys, glob, shutil
from reportlab.lib.utils import annotateException
import unittest
import doctest

class MyTestCase(unittest.TestCase):
    def testMaths(self):
        self.assertEqual(2+2, 4, "the world is OK")

from rlextra.rml2pdf import rml2pdf

class ParameterizedTestCase(unittest.TestCase):
    """ TestCase classes that want to be parametrized should
        inherit from this class.

        Borrowed from Eli Bendersky, spelling fixed by ReportLab ;-)
          http://eli.thegreenplace.net/2011/08/02/python-unit-testing-parametrized-test-cases/
    """
    def __init__(self, methodName='runTest',**kwds):
        super(ParameterizedTestCase, self).__init__(methodName)
        self.__dict__.update(kwds)

    @staticmethod
    def parameterize(testcase_klass, **kwds):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_klass(name, **kwds))
        return suite

class RmlTestCase(ParameterizedTestCase):
    #assume rml full path name stored in self.param
    def setUp(self):
        self.dirName, self.fileName = os.path.split(self.param)
        self.startDir = os.getcwd()
        if self.dirName:
            os.chdir(self.dirName)
    def tearDown(self):
        os.chdir(self.startDir)
    def shortDescription(self):
        return 'rml2pdf: %s' % self.fileName

    def testRml(self):
        source = open(self.fileName, 'rb').read()
        expectError = getattr(self,'expectError',False)
        matchError = getattr(self,'matchError',False)
        try:
            rml2pdf.go(source)
            if expectError:
                raise ValueError('Expected error in %s did not occur' % self.fileName)
        except Exception as e:
            if not expectError:
                annotateException('while rendering %s' % self.fileName)
            else:
                if matchError and matchError not in str(e):
                    annotateException('\nexpected text %r was not found in error\n'% matchError)

class ManualsAndDemos(unittest.TestCase):
    """Initialise this with the current directory.

    It will CD to wherever and generate each needed manual"""
    baseDir = os.getcwd()  #provide a default, but the actual one is set at run time

    def setUp(self):
        self.startDir = os.getcwd()
        self.docsDir = os.path.normpath(os.path.join(self.startDir, '../docs'))
        os.chdir(self.baseDir)


    def tearDown(self):
        os.chdir(self.startDir)

    def testRmlUserGuide(self):
        os.chdir('../docs/rml2pdf')
        sys.path.insert(0, os.getcwd())
        #need some fakery to run it 'as if from command line'
        class FakeOptions(object):
            pass

        fakeOptions = FakeOptions()
        fakeOptions.DULL = False
        import gen_rmluserguide
        gen_rmluserguide.run(fakeOptions)
        sys.path = sys.path[1:]
        shutil.copyfile('rml2pdf-userguide.pdf', self.docsDir + '/rml2pdf-userguide.pdf')

    def testRmlForIdiots(self):
        os.chdir('../docs/rml2pdf/rml-for-idiots')
        sys.path.insert(0, os.getcwd())

        class FakeOptions(object):
            pass

        fakeOptions = FakeOptions()
        fakeOptions.DULL = False
        import gen_rml_for_idiots
        gen_rml_for_idiots.run(fakeOptions)
        sys.path = sys.path[1:]
        shutil.copyfile('rml-for-idiots.pdf', self.docsDir + '/rml-for-idiots.pdf')

    def testPageCatcherUserGuide(self):
        os.chdir('../docs/pagecatcher')
        rml = open('pagecatcher-userguide.rml','rb').read()
        rml2pdf.go(rml, outDir='..')  #create in docs

    def testDiagraUserGuide(self):
        os.chdir('../docs/diagra')
        rml = open('diagradoc.rml','rb').read()
        rml2pdf.go(rml, outDir='..')  #create in docs


        #diagra guide not yet done, depends heavily on graphics examples directory

def makeRmlTests():
    suite = unittest.TestSuite()
    targets = sorted(glob.glob(os.path.join('rml2pdf', '*.rml')))

    #one quirk:  we need test_000_simple.rml to execute before test_000_complex.rml,
    #so put it first.  At some point we should arrange in alpha order.

    do_first = os.path.join('rml2pdf','test_000_simple.rml')
    targets.remove(do_first)
    targets.insert(0, do_first)

    for target in targets:
        expectError = target.endswith('_error.rml')
        if '_broken_' in target:
            matchError = 'borken.pdf'
        elif '_pdf_missing_error.rml' in target:
            matchError = 'missing.pdf'
        else:
            matchError = None
        suite.addTest(ParameterizedTestCase.parameterize(RmlTestCase, param=target, expectError=expectError, matchError=matchError))
    return suite

class PostRmlTests(unittest.TestCase):
    def setUp(self):
        self.startDir = os.getcwd()
        os.chdir('rml2pdf')

    def tearDown(self):
        os.chdir(self.startDir)

    def testDiagraUserGuide(self):
        from reportlab.lib.utils import recursiveImport
        main = recursiveImport('post_encryption').main
        main('test_000_simple.pdf')
        main('test_016_orientations.pdf')

    def testIncludePdfFlowable(self):
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from rlextra.pageCatcher.pageflow import IncludePdfFlowable
        styleSheet = getSampleStyleSheet()
        bt = styleSheet['BodyText']
        redhl = ParagraphStyle('redhl',parent=bt,fontSize=14,textColor='red')

        class MyData:
            def __init__(self,label):
                self.label = label
                self.record = []

            def __str__(self):
                return self.label

        def callback(key,canvas,obj,pdf_data,user_data):
            text = '%s %s %s %r %s' % (key,canvas.__class__.__name__,obj.__class__.__name__,pdf_data,user_data)
            canvas.saveState()
            color1 = (1,0,0) if 'raw' in key else (0,1,0)
            color2 = (0,0,1) if 'post' in key else (0,0,0)
            canvas.setFont('Helvetica',14)
            x = 72
            y = 72 + len(user_data.record)*16
            canvas.setFillColor(color1)
            canvas.drawString(x,y,'x=%s y=%s:'% (x,y))
            canvas.setFillColor(color2)
            x = 148
            canvas.drawString(x,y,text)
            canvas.restoreState()
            user_data.record.append(text)

        story = []
        aS = story.append
        aS(Paragraph('This should be overwritten by included pdf',style=redhl))
        aS(IncludePdfFlowable('test_014_graphics.pdf',pages="1,2-3",leadingBreak=False,callback=callback,user_data=MyData('A')))
        aS(IncludePdfFlowable('test_002_paras.pdf',pages="1,2-3",dx=72,dy=-72,callback=callback,user_data=MyData('B')))
        aS(IncludePdfFlowable('test_014_graphics.pdf',pages="1,2-3",callback=callback,user_data=MyData('C')))
        myData = MyData('D')
        aS(IncludePdfFlowable('test_002_paras.pdf',pages="4-5",callback=callback,user_data=myData))
        aS(IncludePdfFlowable('cropped-media.pdf',pages="1",callback=callback,user_data=MyData('no box uncropped')))
        aS(IncludePdfFlowable('cropped-media.pdf',pdfBoxType='cropbox',callback=callback,user_data=MyData('CropBox')))
        aS(IncludePdfFlowable('cropped-media.pdf',pdfBoxType='cropbox',autoCrop=True, callback=callback,user_data=MyData('CropBox cropped')))
        aS(IncludePdfFlowable('cropped-media.pdf',pdfBoxType='cropbox',autoCrop=True, pageSize='set', callback=callback,user_data=MyData('cropped & set')))
        aS(IncludePdfFlowable('test_002_paras.pdf',pages="1",callback=callback,user_data=MyData('Back to A4 sized?')))
        aS(IncludePdfFlowable('cropped-media.pdf',pdfBoxType='cropbox',autoCrop=True, pageSize='orthofit', callback=callback,user_data=MyData('cropped & orthofit')))
        aS(IncludePdfFlowable('cropped-media.pdf',pdfBoxType='cropbox',autoCrop=True, pageSize='fit', callback=callback,user_data=MyData('cropped & fit')))
        aS(IncludePdfFlowable('cropped-media.pdf',pdfBoxType='cropbox',autoCrop=True, pageSize='center', callback=callback,user_data=MyData('cropped & center')))
        doc = SimpleDocTemplate('test_IncludePdfFlowable.pdf')
        doc.multiBuild(story)
        expected = ["raw-pre Canvas ShowPdfFlowable ('test_002_paras.pdf', 4) D", "raw-post Canvas ShowPdfFlowable ('test_002_paras.pdf', 4) D", "raw-pre Canvas ShowPdfFlowable ('test_002_paras.pdf', 5) D", "raw-post Canvas ShowPdfFlowable ('test_002_paras.pdf', 5) D"]
        self.assertEqual(myData.record, expected, 'myData recorded wrongly %r' % myData.record)

    def test_pageflow(self):
        #check for chaos on repeated use
        import reportlab.rl_config
        reportlab.rl_config.invariant = 1

        from rlextra.pageCatcher.pageflow import loadPdf
        from reportlab.pdfgen.canvas import Canvas
        c = Canvas('test_pageflow1.pdf')
        loadPdf("ir684.pdf", c)
        c.setFont("Helvetica", 36)
        c.drawString(100,700, "Test restore forms")
        c.showPage()
        c.doForm("ir684_page0")
        c.showPage()
        c.doForm("ir684_page1")
        c.save()

        c = Canvas('test_pageflow2.pdf')
        loadPdf("ir684.pdf", c)
        loadPdf("ir684.pdf", c)
        c.setFont("Helvetica", 36)
        c.drawString(100,700, "Test restore forms")
        c.showPage()
        c.doForm("ir684_page0")
        c.showPage()
        c.doForm("ir684_page1")
        c.save()

        c = Canvas('test_pageflow3.pdf')
        loadPdf("ir684.pdf", c, pageNumbers=[0])
        loadPdf("ir684.pdf", c, pageNumbers=[1])
        c.setFont("Helvetica", 36)
        c.drawString(100,700, "Test restore forms")
        c.showPage()
        c.doForm("ir684_page0")
        c.showPage()
        c.doForm("ir684_page1")
        c.save()

class QuickChartTests(unittest.TestCase):
    def testQuickChart(self):
        from rlextra.graphics.quickchart import testAll
        testAll(False,'output-qc')

def makeSuite():
    from reportlab.lib.testutils import eqCheck, equalStrings
    from reportlab.lib.utils import rl_add_builtins
    rl_add_builtins(eqCheck=eqCheck,equalStrings=equalStrings)

    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()

    ManualsAndDemos.baseDir = os.getcwd()
    suite.addTests(loader.loadTestsFromTestCase(ManualsAndDemos))

    #trivial test to make sure machinery works OK
    suite.addTests(loader.loadTestsFromTestCase(MyTestCase))

    #load all RML samples in test directory
    suite.addTests(makeRmlTests())
    suite.addTests(loader.loadTestsFromTestCase(PostRmlTests))
    suite.addTests(loader.loadTestsFromTestCase(QuickChartTests))

    #pagecatcher tests subdirectory
    from pagecatcher import test_pagecatcher
    suite.addTests(test_pagecatcher.makeSuite())
    from pagecatcher import test_pdfexplorer
    suite.addTests(test_pdfexplorer.makeSuite())

    #all modules we know have doctests.  In next release, we'll walk
    #the package and discover these automatically.  We have some
    #doctests that are currently broken (and have been for years);
    #these are commented out.

    import rlextra.rml2pdf.readxls
    suite.addTests(doctest.DocTestSuite(rlextra.rml2pdf.readxls))

#    import rlextra.utils.dbcheck
#    suite.addTests(doctest.DocTestSuite(rlextra.utils.dbcheck))
#    import rlextra.utils.tagstripper
#    suite.addTests(doctest.DocTestSuite(rlextra.utils.tagstripper))
#    import rlextra.utils.namedtuple
#    suite.addTests(doctest.DocTestSuite(rlextra.utils.namedtuple))
    import rlextra.utils.irr
    suite.addTests(doctest.DocTestSuite(rlextra.utils.irr))
    import rlextra.utils.baseconvert
    suite.addTests(doctest.DocTestSuite(rlextra.utils.baseconvert))
#    import rlextra.utils.pdf2jpeg   #jpeg finding issue
#    #suite.addTests(doctest.DocTestSuite(rlextra.utils.pdf2jpeg))
#

    import rlextra.radxml.html_cleaner
    suite.addTests(doctest.DocTestSuite(rlextra.radxml.html_cleaner))
#    import rlextra.radxml.xmlutils   #dtd finding issue
#    suite.addTests(doctest.DocTestSuite(rlextra.radxml.xmlutils))
    import rlextra.radxml.xhtml2rml
    suite.addTests(doctest.DocTestSuite(rlextra.radxml.xhtml2rml))

    import rlextra.graphics.chartconfig
    suite.addTests(doctest.DocTestSuite(rlextra.graphics.chartconfig))

    #some other specific suites
    import test_layout
    suite.addTests(test_layout.makeSuite())
    import test_canvasadapter
    suite.addTests(test_canvasadapter.makeSuite())
    import test_importing
    suite.addTests(test_importing.makeSuite())

    #find all the RML samples
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
