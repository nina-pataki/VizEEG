import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui

class PlotWindow(QtGui.QMainWindow):
    #TODO test if setAttribute(55) works
    def __init__(self, data, PSData=None): #data = [xData,yData,chans] where xData = range(lb,rb), yData = [maxdata, mindata], chans = [ch#]
        QtGui.QMainWindow.__init__(self)
        self.resize(600, 800)
        cw = QtGui.QWidget()
        self.plot = pg.PlotWidget()
        self.setCentralWidget(cw)
        self.layout = QtGui.QHBoxLayout()
        self.col1 = QtGui.QVBoxLayout()
        self.col2 = QtGui.QVBoxLayout()
        self.layout.addLayout(self.col1)
        self.layout.addLayout(self.col2)
        cw.setLayout(self.layout)
        self.col1.addWidget(self.plot)
        self.data = data
        self.setAttribute(55) #sets the window to delete on closing
        self.plotSlider = pg.InfiniteLine(pos=0, bounds=[self.data[0][0],self.data[0][-1]], movable=True, pen='y')
        self.plot.addItem(self.plotSlider)
        self.PSData = PSData
        self.plots = []
        self.checkBoxes = []
        self.labels = []
        self.show()
        
    def showData(self):
        shift = 0
        for i in range(len(self.data[1])):
            self.plots.append([self.plot.plot(x=self.data[0],y=self.data[1][i][0]+shift), self.plot.plot(x=self.data[0],y=self.data[1][i][1]+shift)])
            self.labels.append(QtGui.QLabel("Channel "+str(self.data[2][i])))
            shift += 5000

        for l in self.labels:
            self.col2.addWidget(l) 
    #TODO change the colour scheme of power spectra 
    def showPowSpec(self):
        self.img = pg.ImageView()
        self.col1.addWidget(self.img)
        self.imgSlider = pg.InfiniteLine(pos=0, bounds=[self.data[0][0],self.data[0][-1]], movable=True, pen='y')
        self.img.addItem(self.imgSlider)
        self.plotSlider.sigDragged.connect(self.imgSliderUpdate)
        self.imgSlider.sigDragged.connect(self.plotSliderUpdate)
        #makeRGBA outputs a tuple (imgArray,isThereAlphaChannel?)
        PSRGBAImg = pg.makeRGBA(self.PSData[:,:,self.data[2][0]], levels=[np.amin(self.PSData[:,:,self.data[2][0]]), np.amax(self.PSData[:,:,self.data[2][0]])])[0]
        self.img.setImage(PSRGBAImg)

    def plotSliderUpdate(self, val):
        self.plotSlider.setPos(val)

    def imgSliderUpdate(self, val):
        self.imgSlider.setPos(val)

#class PowSpecWindow(QtGui.QMainWindow):
#
#    def __init__(self, plData, psData):
#        QtGui.QMainWindow.__init__(self)
#        self.resize(600, 800)
#        cw = QtGui.QWidget()
#        self.plot = pg.PlotWidget()
#        img = pg.ImageView()
#        self.setCentralWidget(cw)
#        self.layout = QtGui.QVBoxLayout()
#        cw.setLayout(self.layout)
#        self.layout.addWidget(self.plot)
#        self.layout.addWidget(self.img)
#        self.plData = plData
#        self.psData = psData
#        self.plots = []
#        self.show()
#
#    def showData(self):
#        #load plots to the plot widget
#        shift = 0
#        for i in range(len(self.plData[1])):
#            self.plots.append([self.plot.plot(x=self.plData[0],y=self.plData[1][i][0]+shift), self.plot.plot(x=self.plData[0],y=self.plData[1][i][1]+shift)])
#            shift += 5000

        #load power spectra to the image view object

class CorrMatrixWindow(QtGui.QMainWindow):

    def __init__(self, matData, compWinSize, compWinStep):
        QtGui.QMainWindow.__init__(self)
        self.resize(600, 800)
        self.img = pg.ImageView()
        self.setCentralWidget(img)
        self.show()
        self.cWsize = compWinSize
        self.cWStep = compWinStep

    def showData(self, slPos):
        temp = slPos - (cWsize/2)
        if temp < 0:
            pos = 0
        else:
            if (temp%cWStep <= (cWStep/2)):
                pos = temp / cWStep
            else:
                pos = (temp / cWStep) + 1

        matRBG = pg.makeRGBA(matData[:,:,pos])[0]
        self.img.setImage(matRGB)

#    def updateData(self):
#        pass
