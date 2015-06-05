#Autogenerated by ReportLab guiedit do not edit
from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.shapes import _DrawingEditorMixin, String
from rlextra.graphics.guiedit.datacharts import DataAwareDrawing, ODBCDataSource, DataAssociation

class SampleDataChart(_DrawingEditorMixin,DataAwareDrawing):
	def __init__(self,width=400,height=200,*args,**kw):
		DataAwareDrawing.__init__(self,width,height,*args,**kw)
		self._add(self,HorizontalBarChart(),name='chart',validate=None,desc=None)
		self.chart.x                = 75
		self.chart.y                = 30
		self._add(self,String(125, 124, 'I am a string'),name='title',validate=None,desc=None)
		self.title.x              = 125
		self.title.y              = 125
		self.dataSource      = ODBCDataSource()
		self.dataSource.sql            = 'SELECT chartId, rowId, name, value1, value2, value3 FROM generic_bar'
		self.dataSource.associations.size = 4
		self.dataSource.associations.element00 = DataAssociation(column=0, target='chartId', assocType='scalar')
		self.dataSource.associations.element01 = DataAssociation(column=2, target='title.text', assocType='scalar')
		self.dataSource.associations.element02 = DataAssociation(column=[3,4,5], target='chart.data', assocType='tmatrix')
		self.dataSource.associations.element03 = DataAssociation(column=2, target='chart.categoryAxis.categoryNames', assocType='vector')

if __name__=="__main__": #NORUNTESTS
	SampleDataChart().go()	
