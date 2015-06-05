"""
Basic tests of embedding & restoring forms
"""


import string, os, sys

import unittest
from reportlab.lib.testutils import ScriptThatMakesFileTest
from rlextra.pageCatcher import pageCatcher
from reportlab.pdfgen.canvas import Canvas

global VERBOSE
VERBOSE = 0

# locations must be relative to reportlab package for this test to work, or absolute

class PageCatcherTests(unittest.TestCase):
    """Various tests of pageCatcher's capabilities"""

    def setUp(self):
        #check we're in the pagecatcher directory
        self.startDir = os.getcwd()
        cwd = os.getcwd()
        
        if not cwd.endswith('pagecatcher'):
            if os.path.isdir('pagecatcher'):
                os.chdir('pagecatcher')
    
    
        if not os.path.isfile('sample.frm'):
            pageCatcher.storeForms('sample1.pdf',
                                   'sample1.frm',
                                   prefix='sample1_page',
                                   all=1)
            if VERBOSE: print('cached sample1.frm for later tests')

    def tearDown(self):
        os.chdir(self.startDir)

    def testRestore(self):
        "store and restore a form"
        c = Canvas('test_pc_1.pdf')
        c.setFont('Helvetica-Bold',24)
        c.drawString(100,700, 'Testing how forms are restored and used')
        names = pageCatcher.restoreForms('sample1.frm',c)
        if VERBOSE: print('restored %s' % names)
        c.scale(0.5, 0.5)
        c.translate(200,600)
        c.doForm('sample1_page0')
        #dumpObjects(c)
        if VERBOSE: print('drew page 1 of sample')
        c.translate(0,-400)
        c.doForm('sample1_page1')
        if VERBOSE: print('drew page 2 of sample')
        c.save()
        if VERBOSE: print('saved test_pc_1.pdf')

    def xxtestDrawBeforeRestore(self):
        "draw forms before restoring them form"
        c = Canvas('test_pc_2.pdf')
        c.setFont('Helvetica-Bold',24)
        c.drawString(100,700, 'Testing draw before restore')

        c.scale(0.5, 0.5)
        c.translate(200,600)
        c.doForm('sample1_page0')
        if VERBOSE: print('drew page 1 of sample')
        c.translate(0,-400)
        c.doForm('sample1_page1')
        if VERBOSE: print('drew page 2 of sample')
        names = pageCatcher.restoreForms('sample1.frm',c)
        if VERBOSE: print('restored %s' % names)
        c.save()
        if VERBOSE: print('saved test_pc_2.pdf')


    def testDrawNonExistent(self):
        "Draw a form we have not restored. Should raise error"
        c = Canvas('test_pc_3.pdf')
        c.setFont('Helvetica-Bold',24)
        c.drawString(100,700, 'Testing draw before restore')
        c.scale(0.5, 0.5)
        c.translate(200,600)
        c.doForm('sample1_page0')
        if VERBOSE: print('drew page 1 of sample')
        self.failUnlessRaises(KeyError, c.save)
        if VERBOSE: print('saved test_pc_3.pdf, oh dear')

    def testDoubleRestore(self):
        "Restore Twice. Should raise error"
        c = Canvas('test_pc_4.pdf')
        c.setFont('Helvetica-Bold',24)
        c.drawString(100,700, 'Testing double restore')
        c.scale(0.5, 0.5)
        c.translate(200,600)
        names = pageCatcher.restoreForms('sample1.frm',c)
        if VERBOSE: print('double restore coming...')
        self.failUnlessRaises(ValueError, pageCatcher.restoreForms, 'sample1.frm',c)

    def testCombinePdfsInMemory(self):
        "Merge 3 files using combinePdfInMemory"
        if os.path.isfile('combined_mem.pdf'):
            os.remove('combined_mem.pdf')

        stuff = []
        stuff.append(open('sample1.pdf','rb').read())
        stuff.append(open('sample2.pdf','rb').read())
        stuff.append(open('sample3.pdf','rb').read())
        pdf = pageCatcher.combinePdfsInMemory(stuff)

        open('combined_mem.pdf','wb').write(pdf)
        if VERBOSE: print('saved combined_mem.pdf')

    def testCombinePdfsOnDisk(self):
        "Merge 3 files using combinePdf"
        if os.path.isfile('combined_disk.pdf'):
            os.remove('combined_disk.pdf')
        stuff = []
        stuff.append('sample1.pdf')
        stuff.append('sample2.pdf')
        stuff.append('sample3.pdf')
        pageCatcher.combinePdfs('combined_disk.pdf',stuff)
        assert os.path.isfile('combined_disk.pdf')
        if VERBOSE: print('saved combined_disk.pdf')

    def testNeedsPyPdf(self):
        with open('needs-pypdf.pdf','rb') as f:
            pdfContent = f.read()
        pageCatcher.storeFormsInMemory(pdfContent,all=True)
        if VERBOSE: print('Stored needs-pypdf.pdf in memory')

def dumpObjects(canvas):
    """Show the PDF objects within"""
    doc = canvas._doc
    import pprint
    print('forms:')
    for (key, value) in list(doc.idToObject.items()):
        if key[0:7] == 'FormXob':
            print('   ',key,'=',value)

def makeSuite():
    return unittest.TestSuite((
##                ScriptThatMakesFileTest('../rlextra/pageCatcher/demos',
##                               'example1_fillform.py',
##                               'out1_fillform.pdf',
##                                verbose=VERBOSE),
##                ScriptThatMakesFileTest('../rlextra/pageCatcher/demos',
##                               'example2_reverse.py',
##                               'out2_reversed.pdf',
##                                verbose=VERBOSE),
##                ScriptThatMakesFileTest('../rlextra/pageCatcher/demos',
##                               'example3_append.py',
##                               'out3_combined.pdf',
##                                verbose=VERBOSE),
##                ScriptThatMakesFileTest('../rlextra/pageCatcher/demos',
##                               'example4_fourpage.py',
##                               'out4_fourpage.pdf',
##                                verbose=VERBOSE),
##                ScriptThatMakesFileTest('../rlextra/pageCatcher/demos',
##                               'example5_background.py',
##                               'out5_background.pdf',
##                                verbose=VERBOSE),
##                ScriptThatMakesFileTest('../rlextra/pageCatcher/demos',
##                               'example6_twopage.py',
##                               'out6_twopage.pdf',
##                                verbose=VERBOSE),
##                ScriptThatMakesFileTest('../rlextra/pageCatcher/demos',
##                               'example7_split.py',
##                               'out7_page9.pdf',
##                                verbose=VERBOSE),
                unittest.makeSuite(PageCatcherTests,'test'),
                )
        )

#noruntests
if __name__ == "__main__":
    VERBOSE = ('-v' in sys.argv)
    w = os.path.dirname(sys.argv[0])
    if w: os.chdir(w)
    unittest.TextTestRunner().run(makeSuite())
