import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui

class PlotWindow(QtGui.QMainWindow):
    #TODO test if setAttribute(55) works
    def __init__(self, data, PSData=None): #data = [xData,yData,chans] where xData = range(lb,rb), yData = [maxdata, mindata], chans = [ch#]
        QtGui.QMainWindow.__init__(self)
        self.resize(600, 800)
        self.setWindowTitle("vizEEG")
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
            if self.data[1][i][1] is not None:
                self.plots.append([self.plot.plot(x=self.data[0],y=self.data[1][i][0]+shift), self.plot.plot(x=self.data[0],y=self.data[1][i][1]+shift)])
            else:
                self.plots.append([self.plot.plot(x=self.data[0],y=self.data[1][i][0]+shift)])
            self.labels.append(QtGui.QLabel("Channel "+str(self.data[2][i])))
            shift += 5000

        for l in self.labels:
            self.col2.addWidget(l) 
    #TODO change the colour scheme of power spectra 
    def showPowSpec(self):
        self.setWindowTitle("vizEEG - Power Spectra display")
        self.img = pg.ImageView()
        self.col1.addWidget(self.img)
        self.imgSlider = pg.InfiniteLine(pos=0, bounds=[0,self.PSData.shape[0]], movable=True, pen='y')
        self.img.addItem(self.imgSlider)
        self.plotSlider.sigDragged.connect(self.imgSliderFunc)
        self.imgSlider.sigDragged.connect(self.plotSliderFunc)
        #makeRGBA outputs a tuple (imgArray,isThereAlphaChannel?)
        PSRGBAImg = pg.makeRGBA(self.PSData[:,:,self.data[2][0]], levels=[np.amin(self.PSData[:,:,self.data[2][0]]), np.amax(self.PSData[:,:,self.data[2][0]])])[0]
        self.img.setImage(PSRGBAImg)

    def plotSliderUpdate(self, val):
        self.plotSlider.setPos(val)

    def imgSliderUpdate(self, val):
        ratio = len(self.data[0])/float(self.PSData.shape[0])
        self.imgSlider.setPos(np.ceil(val/ratio))

    def imgSliderFunc(self):
        self.imgSliderUpdate(self.plotSlider.value())

    def plotSliderFunc(self):
        ratio = int(len(self.data[0])/self.PSData.shape[0])
        self.plotSliderUpdate(self.imgSlider.value()*ratio)

class CorrMatrixWindow(QtGui.QMainWindow):

    def __init__(self, matData, compWinSize, compWinStep):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("vizEEG - Correlation Matrix display")
        self.resize(600, 800)
        self.img = pg.ImageView()
        self.setCentralWidget(self.img)
        self.show()
        self.cWSize = compWinSize
        self.cWStep = compWinStep
        self.matData = matData

    def showData(self, slPos):
        temp = slPos - (self.cWSize/2)
        if temp < 0:
            pos = 0
        else:
            if (temp%self.cWStep <= (self.cWStep/2)):
                pos = temp / self.cWStep
            else:
                pos = (temp / self.cWStep) + 1
        print "position is: ", pos
        matRGB = pg.makeRGBA(self.matData[:,:,pos], levels=[np.amin(self.matData[:,:,pos]), np.amax(self.matData[:,:,pos])])[0]
        self.img.setImage(matRGB)

