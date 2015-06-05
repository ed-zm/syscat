import unittest, sys
from rlextra.graphics.guiedit import mutils
from reportlab.lib.testutils import makeSuiteForClasses

class ImportingTestCase(unittest.TestCase):
    def test_importing_all(self):
        FAILS=[]
        M=mutils.getModules(
                    P=['reportlab.lib', 'reportlab', 'rlextra'],
                    X=[],
                    FAILS=FAILS,
                    allowCompiled=False,
                    )
        assert not FAILS,'Could not import modules\n %s' % ' \n'.join(FAILS)

def makeSuite():
    return makeSuiteForClasses(ImportingTestCase)

#noruntests
if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
