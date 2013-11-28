import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui

class PlotWindow(QtGui.QMainWindow):

    def __init__(self, data): #data = [xData,yData,chans] where xData = range(lb,rb), yData = [maxdata, mindata], chans = [ch#]
        QtGui.QMainWindow.__init__(self)
        cw = QtGui.QWidget()
        self.plot = pg.PlotWidget()
        self.setCentralWidget(cw)
        layout = QtGui.QHBoxLayout()
        self.col1 = QtGui.QVBoxLayout()
        self.col2 = QtGui.QVBoxLayout()
        layout.addLayout(self.col1)
        layout.addLayout(self.col2)
        cw.setLayout(layout)
        self.col1.addWidget(self.plot)
        self.data = data
        self.setAttribute(55) #sets the window to delete on closing
        self.slider = pg.InfiniteLine(pos=0, bounds=[self.data[0][0],self.data[0][-1]], movable=True, pen='y')
        self.plot.addItem(self.slider)
        self.plots = []
        self.labels = []
        self.show()
        
    def plotData(self):
        shift = 0
        for i in range(len(self.data[1])):
            self.plots.append([self.plot.plot(x=self.data[0],y=self.data[1][i][0]+shift), self.plot.plot(x=self.data[0],y=self.data[1][i][1]+shift)])
            self.labels.append(QtGui.QLabel("Channel "+str(self.data[2][i])))
            shift += 5000

        for l in self.labels:
            self.col2.addWidget(l) 

    def sliderUpdate(self, val):
        self.slider.setPos(val)
