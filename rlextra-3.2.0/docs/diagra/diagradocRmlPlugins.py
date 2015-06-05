"""This module creates the RML PlugInFlowables for the Diagra documentation.

NB: No longer requires RML in this directory to work."""


import sys, os, rlextra
sys.path.insert(0,os.path.join(os.path.dirname(rlextra.__file__),'examples','graphics'))

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from stackedBar import CylinderBarStacked
from slidebox import SlideBoxDrawing
from dotbox_db import DotBoxDrawing
from horizontalbarchart_db import HorizontalBarChartDrawing
from verticalbarchart_db import VerticalBarChartDrawing
#from linechart_db import LineChartDrawing

class RMLDotBox(DotBoxDrawing):
	def __init__(self,*args):
		DotBoxDrawing.__init__(self)
		self.hAlign='CENTER'
		if args: self._data = args[0]
	def wrap(self, w, h):
		self._sW=w
		return (self.width, self.height)
	def drawOn(self,canvas,x,y,_sW=0):
		DotBoxDrawing.drawOn(self, canvas, x, y, _sW=self._sW)

class RMLSlideBox(SlideBoxDrawing):
	def __init__(self,*args):
		SlideBoxDrawing.__init__(self)
		self.hAlign='CENTER'
		if args: self._data = args[0]
	def wrap(self, w, h):
		self._sW=w
		return (self.width, self.height)
	def drawOn(self,canvas,x,y,_sW=0):
		SlideBoxDrawing.drawOn(self, canvas, x, y, _sW=self._sW)

#class RMLLineChart(LineChartDrawing):
#	def __init__(self,data):
#		LineChartDrawing.__init__(self)
#		self.hAlign='CENTER'
#		self._data = data
#	def wrap(self, w, h):
#		self._sW=w
#		return (self.width, self.height)
#	def drawOn(self,canvas,x,y,_sW=0):
#		LineChartDrawing.drawOn(self, canvas, x, y, _sW=self._sW)

class RMLVerticalBarChart(VerticalBarChartDrawing):
	def __init__(self,*args):
		VerticalBarChartDrawing.__init__(self)
		self.hAlign='CENTER'
		if args: self._data = args[0]
	def wrap(self, w, h):
		self._sW=w
		return (self.width, self.height)
	def drawOn(self,canvas,x,y,_sW=0):
		VerticalBarChartDrawing.drawOn(self, canvas, x, y, _sW=self._sW)

class RMLHorizontalBarChart(HorizontalBarChartDrawing):
	def __init__(self,*args):
		HorizontalBarChartDrawing.__init__(self)
		self.hAlign='CENTER'
		if args: self._data = args[0]
	def wrap(self, w, h):
		self._sW=w
		return (self.width, self.height)
	def drawOn(self,canvas,x,y,_sW=0):
		HorizontalBarChartDrawing.drawOn(self, canvas, x, y, _sW=self._sW)

class RMLSymbolCylinderChart(CylinderBarStacked):
	def __init__(self,*args):
		CylinderBarStacked.__init__(self)
		self.hAlign='CENTER'
		if args: self._data = args[0]
	def wrap(self, w, h):
		self._sW=w
		return (self.width, self.height)
	def drawOn(self,canvas,x,y,_sW=0):
		CylinderBarStacked.drawOn(self, canvas, x, y, _sW=self._sW)

class RMLForceZeros(Drawing):
	def __init__(self, width=500,height=100, *nodes, **keywords):
		Drawing.__init__(self)
		self.add(VerticalBarChart(), 'vb1')
		self.vb1.data = [(50, 60, 70, 80, 90), (95, 55, 85, 65, 75)]
		self.vb1.valueAxis.forceZero=0
		self.vb1.x=20
		self.vb1.y=20
		self.add(VerticalBarChart(), 'vb2')
		self.vb2.data = [(50, 60, 70, 80, 90), (95, 55, 85, 65, 75)]
		self.vb2.valueAxis.forceZero=1
		self.vb2.x=250
		self.vb2.y=20
		self.transform = (0.75, 0, 0, 0.75, 0, 0)
		self.add(String(x=100, y=0,text="forceZero=0", fontName="Helvetica-Oblique", fontSize=8))
		self.add(String(x=300, y=0, text="forceZero=1", fontName="Helvetica-Oblique", fontSize=8))
		self.hAlign='CENTER'
	def wrap(self, w, h):
		self._sW=0.75*w
		return (0.75*self.width, 0.75*self.height)
	def drawOn(self,canvas,x,y,_sW=0):
		VerticalBarChart.draw(Onself, canvas, x, y, _sW=0.75*self._sW)
		
