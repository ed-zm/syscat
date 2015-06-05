#Autogenerated by ReportLab guiedit do not edit
from reportlab.graphics.charts.axes import NormalDateXValueAxis
from reportlab.lib.units import cm
from rlextra.graphics.guiedit.datacharts import CSVDataSource, ODBCDataSource, DataAssociation, DataAwareDrawing, Array
from reportlab.graphics.shapes import _DrawingEditorMixin, String
from reportlab.graphics.charts.lineplots import GridLinePlot

class GridLinePlotDrawing(_DrawingEditorMixin,DataAwareDrawing):
	def __init__(self,width=400,height=200,*args,**kw):
		DataAwareDrawing.__init__(self,width,height,*args,**kw)
		self.add(GridLinePlot(), 'chart')
		self.width = 205
		self.height = 130
		self.chart.x = 20
		self.chart.y = 30
		self.chart.height = 3.1*cm
		self.chart.width = 6.1*cm
		self.chart.xValueAxis.visibleAxis = 0
		self.chart.xValueAxis.visibleTicks = 0
		self.chart.xValueAxis.labels.fontSize = 6
		self.chart.xValueAxis.labels.fontName = "Helvetica"
		self.chart.xValueAxis.labels.textAnchor = 'start'
		self.chart.xValueAxis.labels.boxAnchor = 'e'
		self.chart.xValueAxis.labels.angle = 45
		self.chart.xValueAxis.xLabelFormat = '{mmm} {yy}'
		self.chart.yValueAxis.valueMin = 100.0
		self.chart.yValueAxis.valueMax = None
		self.chart.yValueAxis.visibleAxis = 0
		self.chart.yValueAxis.visibleTicks = 0
		self.chart.yValueAxis.labels.fontSize = 6
		self.chart.yValueAxis.labels.fontName = "Helvetica"
		self.chart.yValueAxis.labelTextFormat = '%5d%% '
		self.dataSource = ODBCDataSource()
		self.dataSource.sql = 'SELECT chartId, date, value1*100, value2*100, value3*100 FROM generic_time_series'
		self.dataSource.groupingColumn = 0
		self.dataSource.associations = Array(2, DataAssociation)
		self.dataSource.associations.element00 = DataAssociation(column=0, target='chartId', assocType='scalar')
		self.dataSource.associations.element01 = DataAssociation(column=[[1, 2], [1,3], [1,4]], target='chart.data', assocType='tmatrix')
		self.chart.yValueAxis.valueMin = None
		self.verbose = 1
		self.formats = ['eps', 'pdf']
		self.outDir = './output/'
		self.fileNamePattern = 'linechart%03d'
		self.chart.xValueAxis.labels.angle          = 30
		self.formats         = ['eps', 'pdf','gif']
		self._add(self,String(200,180,'Fund Performance'),name='title',validate=None,desc=None)
		self.title.y          = 0
		self.title.x          = 0

if __name__=="__main__": #NORUNTESTS
	GridLinePlotDrawing().go()
