''' Tests for graphics. '''
import unittest,os,sys
from reportlab.lib.logger import warnOnce

from legendedpie import LegendedPieDrawing
from scatterplot import ScatterPlotDrawing
from slidebox import SlideBoxDrawing
from stackedBar import CylinderBarStacked
TESTS=(
        LegendedPieDrawing,
        ScatterPlotDrawing,
        SlideBoxDrawing,
        CylinderBarStacked,
        )

class devnull:
    def write(*a, **kw):
        pass

class TestCase(unittest.TestCase):

    def setUp(self):
        self.stdout = sys.stdout
        sys.stdout = devnull()
        self.olddir = os.getcwd()
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    def tearDown(self):
        os.chdir(self.olddir)
        sys.stdout = self.stdout

def makeSuite():
    class NullTest(unittest.TestCase):
        pass

    try:
        from reportlab.graphics import renderPM
    except ImportError:
        warnOnce('''Could not import _renderPM.
Therefore the rlextra.examples.graphics tests won't be run.
See http://www.reportlab.org/rl_addons.html''')
        return unittest.makeSuite(NullTest)
    canv = renderPM.PMCanvas(1,1)
    try:
        canv.setFont('Times-Roman', 10)
    except renderPM.RenderPMError:
        warnOnce('''Could not find the standard PFB fonts in reportlab/fonts.
Therefore the rlextra.examples.graphics tests won't be run.
The required fonts may be downloaded from http://www.reportlab.com/ftp/pfbfer.zip
and unzipped into reportlab/fonts.''')
        return unittest.makeSuite(NullTest)
    del canv, renderPM

    # Add tests to class before making the suite
    for test in TESTS:
        def func(self,t=test):
            t().go()
        setattr(TestCase, 'test_%s' % test.__name__, func)
    return unittest.makeSuite(TestCase)

if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
