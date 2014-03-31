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
#        self.setAttribute(55) #sets the window to delete on closing
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
#        self.setAttribute(55)
        self.img = pg.ImageView()
        self.setCentralWidget(self.img)
        self.show()
        self.cWSize = compWinSize
        self.cWStep = compWinStep
        self.matData = matData
        r3 = None
        colours, self.ok = self.colourInput("Choose a colouring for power spectra images or enter a different one in format RRR,GGG,BBB.\n Please, separate colours (2 or 3) with space.\n If Cancel is clicked matrix will be displayed in gray scale.")        
        if self.ok: #este sa treba postarat o format, nie len o rozsah hodnot
            parsed = colours.split()
            self.r1 = int(parsed[0].split(',')[0])
            self.g1 = int(parsed[0].split(',')[1])
            self.b1 = int(parsed[0].split(',')[2])
            self.r2 = int(parsed[1].split(',')[0])
            self.g2 = int(parsed[1].split(',')[1])
            self.b2 = int(parsed[1].split(',')[2])
            if len(parsed) == 3:
                self.r3 = int(parsed[2].split(',')[0])
                self.g3 = int(parsed[2].split(',')[1])
                self.b3 = int(parsed[2].split(',')[2])
            okRange = range(256)
            areColsOk = r1 in okRange and r2 in okRange and g1 in okRange and g2 in okRange and b1 in okRange and b2 in okRange 
            areColsOk = areColsOk and r3 in okRange and g3 in okRange and b3 in okRange if len(parsed) == 3        
            if not areColsOk:
                msgBox = QtGui.MessageBox()
                msgBox.setWindowTitle("Colour Error")
                msgBox.setText("Colours input in incorrect format.")
                msgBox.exec_()
                self.close()

    def colourInput(self, text):
        colOptions = ["0,0,255 255,0,0", "0,255,0 255,0,0","0,0,255 0,255,0 255,0,0"]
        return QtGui.QInputDialog.getItem(self, "vizEEG", text, colOptions, editable=True)
        
    def showData(self, slPos):
        temp = slPos - (self.cWSize/2)
        if temp < 0:
            pos = 0
        else:
            if (temp%self.cWStep <= (self.cWStep/2)):
                pos = temp / self.cWStep
            else:
                pos = (temp / self.cWStep) + 1

        matRGB = pg.makeRGBA(self.matData[:,:,pos], levels=[np.amin(self.matData[:,:,pos]), np.amax(self.matData[:,:,pos])])[0]

        if ok:
            okRange = range(256)
            colsOk = self.r1 in okRange and self.r2 in okRange and self.g1 in okRange and self.g2 in okRange and self.b1 in okRange and self.b2 in okRange
            colsOk = colsOk and self.r3 in okRange and self.g3 in okRange and self.b3 in okRange if len(parsed) == 3

            if not colsOk:
                msgBox = QtGui.MessageBox()
                msgBox.setWindowTitle("Colour Error")
                msgBox.setText("Colours input in incorrect format.")
                msgBox.exec_()
                self.close()

            matRGBCol = np.zeros(matRGB.shape, dtype="int")
            for i in matRGB.shape[0]:
                for j in matRGB.shape[1]:
                    if self.r3 is not None:
                        if matRGB[i,j,0] < 128:
                            matRGBCol[i,j,0] = int((matRGB[i,j,0]/128.0)*self.r1 + (1-(matRGB[i,j,0]/128.0))*self.r2)
                            matRGBCol[i,j,1] = int((matRGB[i,j,1]/128.0)*self.g1 + (1-(matRGB[i,j,1]/128.0))*self.g2)
                            matRGBCol[i,j,2] = int((matRGB[i,j,2]/128.0)*self.b1 + (1-(matRGB[i,j,2]/128.0))*self.b2)
                        else:
                            matRGBCol[i,j,0] = int((matRGB[i,j,0]/128.0 -1)*self.r2 + (1-(matRGB[i,j,0]/128.0))*self.r3)
                            matRGBCol[i,j,1] = int((matRGB[i,j,1]/128.0 -1)*self.g2 + (1-(matRGB[i,j,1]/128.0))*self.g3)
                            matRGBCol[i,j,0] = int((matRGB[i,j,2]/128.0 -1)*self.b2 + (1-(matRGB[i,j,2]/128.0))*self.b3)
                    else:
                        matRGBCol[i,j,0] = int((matRGB[i,j,0]/255.0)*self.r1 + (1-(matRGB[i,j,0]/255.0))*self.r2)
                        matRGBCol[i,j,1] = int((matRGB[i,j,1]/255.0)*self.g1 + (1-(matRGB[i,j,1]/255.0))*self.g2)
                        matRGBCol[i,j,2] = int((matRGB[i,j,2]/255.0)*self.b1 + (1-(matRGB[i,j,2]/255.0))*self.b2)

            self.img.setImage(matRGBCol)
        else:
            self.img.setImage(matRGB)

