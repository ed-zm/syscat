#Autogenerated by ReportLab guiedit do not edit
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, _DrawingEditorMixin, String
from reportlab.lib.colors import Color, red, green

class LegendDrawing(_DrawingEditorMixin,Drawing):
	def __init__(self,width=400,height=200,*args,**kw):
		Drawing.__init__(self,width,height,*args,**kw)
		self._add(self,VerticalBarChart(),name='chart',validate=None,desc=None)
		self.chart.y                = 20
		self.chart.categoryAxis.categoryNames       = ['North','South','East','West']
		self._add(self,String(200,180,"Chart Title Here"),name='title',validate=None,desc=None)
		self.title.textAnchor='middle'
		self.title.fontSize   = 12
		self.title.fontName   = 'Times-Bold'
		self._add(self,Legend(),name='legend',validate=None,desc=None)
		self.legend.boxAnchor      = 'sw'
		self.legend.x              = 200
		self.legend.y              = 20
		self.legend.x              = 220
		self.title.text       = 'Chart with Legend - example 1'
		self.legend.colorNamePairs = [(red, 'widgets'), (green, 'sprockets')]
		self.title.text       = 'Chart with Legend - example 2'

if __name__=="__main__": #NORUNTESTS
	LegendDrawing().save(formats=['pdf'],outDir='.',fnRoot=None)
