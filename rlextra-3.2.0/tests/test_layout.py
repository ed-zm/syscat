import unittest
from reportlab.lib.testutils import makeSuiteForClasses
from rlextra.graphics.layout import shapes, getBounds, Sizer

class LayoutTestCase(unittest.TestCase):
    def testGetBounds(self):
        # try each shape quickly
        assert getBounds(shapes.Line(10,20,30,40)) == (10,20,30,40)
        assert getBounds(shapes.Rect(10,20,30,40)) == (10,20,40,60)
        assert getBounds(shapes.Circle(50,100,10)) == (40,90,60,110)
        assert getBounds(shapes.Polygon(points=[50,100,10,20,10,150])) == (10,20,50,150)
        assert getBounds(shapes.PolyLine(points=[50,100,10,20,10,150])) == (10,20,50,150)
        assert getBounds(shapes.Wedge(100,100,20,-30,90)) == (100,90,120,120)
        assert list(map(int, getBounds(shapes.String(0,0,'Hello World')))) == [0, -2, 50, 10]

        p = shapes.Path()
        p.moveTo(50,50)
        p.lineTo(60,75)
        p.lineTo(70,75)
        p.closePath()
        assert getBounds(p) == (50,50,70,75)

        g = shapes.Group()
        r = shapes.Rect(0,0,100,50)
        g.add(r)
        assert getBounds(g) == (0,0,100,50)
        g.translate(50,0)
        assert getBounds(g) == (50,0,150,50)
        g.rotate(90)
        assert list(map(int,getBounds(g))) == [0,0,50,100]

    def testSizer(self):
        r = shapes.Rect(1,2,3,4)
        s = Sizer()
        s.add(r)
        assert s.getBounds() == (1,2,4,6)

def makeSuite():
    return makeSuiteForClasses(LayoutTestCase)

#noruntests
if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
