import numpy as np
import pyqtgraph as pg
import h5py
from pyqtgraph.Qt import QtGui, QtCore
import math

VPP = 10
LOG = 10

class loadingTask(QtCore.QThread):
    def __init__(self, parent=None):
        QtCore.QThread.__init__(self,parent)
        self.stopping = False
        self.lock = QtCore.QMutex()

    def loadData(self,ch1,ch2, lb, rb, exp, index, fileName, filePath):
        print "... loading data..."
        self.fileName = fileName
        self.filePath = filePath
        self.lb = lb
        self.rb = rb
        self.index = index
        self.running = True
        self.ch1 = ch1
        self.ch2 = ch2
        self.exp = exp
        self.start()

    def run(self):

        self.lock.lock()

        f = h5py.File(self.fileName, 'r')
        self.dataset = f[self.filePath]

        minmax = f['minmax']
        maxData = minmax['h_max']
        maxDataLevels = [self.dataset]
        for l in maxData.keys():
            maxDataLevels.append(maxData[l])

        minData = minmax['h_min']
        minDataLevels = [self.dataset]
        for l in minData.keys():
            minDataLevels.append(minData[l])
        
        exp = int(np.floor(math.log(self.dataset.shape[0],LOG))) - int(np.floor(math.log(maxDataLevels[self.index].shape[0],LOG)))
        print "exp: ", exp
        print "self.exp: ", self.exp
        left = np.round(self.lb/(LOG**exp))
        right = np.round(self.rb/(LOG**exp))
        self.x = range(self.dataset.shape[0])[self.lb:self.rb:LOG**exp]
        print "shape of x: ", len(self.x)
        print "lenght of maxDataLevels: ", len(maxDataLevels)
        print "index: ", self.index
        print "ch1: ", self.ch1, "ch2: ", self.ch2
        print "lb: ", self.lb, "rb: ", self.rb
        print "left: ", left, "right: ", right        
        self.y1 = maxDataLevels[self.index][left:right,self.ch1:self.ch2+1]
        self.y2 = minDataLevels[self.index][left:right,self.ch1:self.ch2+1] 
       # if (abs(self.y1.shape[0]-len(self.x)==1)):
       #     if((y1.shape[0]>len(self.x)) and (x[-1]==self.rb)):
       #         self.x.append(self.rb*(LOG**exp))
       #     elif (y1.shape[0]<len(x)):
       #         self.x.pop()
       #     else: 
       #         x.append(self.rb)
                
        self.lock.unlock()
    def stopTask(self):
        self.stopping = True     

#TODO: axis labels, scrolling of checkbox area

class vizEEG(QtGui.QMainWindow):

    def __init__(self, app, h5File, h5Path, matrixFile=None):
        
        QtGui.QMainWindow.__init__(self)
        self.h5File = h5File
        self.h5Path = h5Path
        f = h5py.File(self.h5File,'r')
        self.dataset = f[self.h5Path]
        self.plots = []
        self.checkBoxes = []
        self.worker = loadingTask()

        minmax = f['minmax']
        maxData = minmax['h_max']
        self.maxDataLevels = [self.dataset]
        for l in maxData.keys():
            self.maxDataLevels.append(maxData[l])

        minData = minmax['h_min']
        self.minDataLevels = [self.dataset]
        for l in minData.keys():
            self.minDataLevels.append(minData[l])

        #create the layout and main widget
        cw = QtGui.QWidget()
        self.setCentralWidget(cw)
        layout = QtGui.QHBoxLayout()
        col1 = QtGui.QVBoxLayout()
        col2 = QtGui.QVBoxLayout()
        layout.addLayout(col1)
        layout.addLayout(col2)
        cw.setLayout(layout)

        #create widgets in the first row of the layout
        self.plWidget = pg.PlotWidget() #plotWidget segfaults for some reason
        col1.addWidget(self.plWidget)
        self.spinbox = pg.SpinBox(value=5000, int=True, step=100)
        col1.addWidget(self.spinbox)
        openWindowBtn = QtGui.QPushButton("Open region in a new window")
        openMatrixBtn = QtGui.QPushButton("Open correlation matrix for slider position")
        col1.addWidget(openWindowBtn)
        col1.addWidget(openMatrixBtn)

        #create widgets in the second row of the layout
        self.plItem = self.plWidget.getPlotItem()
        self.vb = self.plItem.getViewBox()
        self.lr = pg.LinearRegionItem(values=[int(np.round(self.dataset.shape[0]*0.1)), int(np.round(self.dataset.shape[0]*0.2))], bounds=[0,self.dataset.shape[0]], movable=True)
        self.slider = pg.InfiniteLine(pos=20000, movable=True, pen='r')
        self.plWidget.addItem(self.slider)
        self.plWidget.addItem(self.lr)
        self.plItem.setTitle(f.filename)

        print "... loading initial data, please wait..." 

        #initialise plots of hdf5 data
        VPPDeg = int(np.ceil(math.log(VPP*self.vb.width(),LOG)))
        i = 0
        for i in range(len(self.maxDataLevels)): 
            dataDeg = math.log(self.maxDataLevels[i].shape[0],LOG)
            if (int(np.ceil(dataDeg)) == VPPDeg): 
               # self.maxDataDisplayed = self.maxDataLevels[i]
               # self.minDataDisplayed = self.minDataLevels[i]
                self.index = i
               # displDataDeg = int(np.floor(dataDeg))
        #print "dlzka vybrateho datasetu: ", self.maxDataDisplayed.shape[0]
        self.exp = int(np.floor(math.log(self.dataset.shape[0], LOG))) - int(np.floor(math.log(self.maxDataLevels[self.index].shape[0],LOG)))
        #self.VPPDisplDeg = int(np.floor(np.log10((self.dataset.shape[0]/self.vb.width())/(10**self.exp))))
        print "---------intialisation debug-----------"
        print "VPPDeg: ", VPPDeg
        print "VPP*vb.width: ", VPP*self.vb.width()
        print "index: ", self.index
        print "maxDataLevels length: ", len(self.maxDataLevels)
        print "exp: ", self.exp
        #print "VPPDisplDeg: ", self.VPPDisplDeg
        x = range(self.dataset.shape[0])[::LOG**self.exp]
        shift = 0
        for ch in range(self.dataset.shape[1]): #ch - channel number
            self.checkBoxes.append(QtGui.QCheckBox("Channel "+str(ch)))
            #y1 = self.maxDataDisplayed[:,ch]
            #y2 = self.minDataDisplayed[:,ch]
            y1 = self.maxDataLevels[self.index][:,ch]
            y2 = self.minDataLevels[self.index][:,ch]
            #print "plots of channel ",ch," initialised"
            self.plots.append([self.plWidget.plot(x=x,y=y1+shift),self.plWidget.plot(x=x,y=y2+shift),shift,ch])
            shift+=5000
        print "Plots initialised."
        print "---------intialisation debug end-----------"

        #check boxes for choosing channels
        for cb in self.checkBoxes:
            col2.addWidget(cb)

        ckAllBtn = QtGui.QPushButton("Check all channels")
        ckNoneBtn = QtGui.QPushButton("Uncheck all channels")
        col2.addWidget(ckAllBtn)
        col2.addWidget(ckNoneBtn)
        
        self.vb.setRange(xRange=x, yRange=(self.plots[0][2]-5000,self.plots[-1][2]+5000), padding=0)
        self.leftB = 0
        self.rightB = self.dataset.shape[1]
        self.topB = self.plots[-1][2]
        self.bottomB = 0

        print "... initial data loaded"
        #connect UI objects' signals to handling functions
        ckAllBtn.clicked.connect(self.checkAllCBs)
        ckNoneBtn.clicked.connect(self.uncheckAllCBs)
        self.vb.sigRangeChanged.connect(self.updateData)
        self.connect(self.worker,QtCore.SIGNAL("finished()"), self.dataLoaded)
#        self.connect(self.worker,QtCore.SIGNAL("update(int)"), self.dataLoadProgress)

#    def dataLoadProgress(self, n):
#        print "Loaded channel %d." %n

    def dataLoaded(self):
        i=0
        print "---------thread finished debug----------"
        print "v dataLoaded len(updatePlots): ", len(self.updatePlots)
        print "worker.y1.shape: ", self.worker.y1.shape
        print "worker.x length: ", len(self.worker.x)
        print "---------thread finished debug end------"
        for (p1,p2,sh,ch) in self.updatePlots:
            p1.setData(x=self.worker.x,y=self.worker.y1[:,i]+sh)
            p2.setData(x=self.worker.x,y=self.worker.y2[:,i]+sh)
            i+=1
        print "... data loaded successfully."

    def checkAllCBs(self): #check how to join these two functions
        for cb in self.checkBoxes:
            cb.setCheckState(2)

    def uncheckAllCBs(self):
        for cb in self.checkBoxes:
            cb.setCheckState(0)

    def outOfBounds(self):
        if (self.vb.viewRange()[0][0] < 0 or self.vb.viewRange()[0][1] > self.dataset.shape[0] or self.vb.viewRange()[1][0] < -5000 or self.vb.viewRange()[1][1] > self.plots[-1][2]+5000):
            return False
        else:
            return self.vb.viewRange()[0][0] < self.leftB or self.vb.viewRange()[0][1] > self.rightB or self.vb.viewRange()[1][0] < self.bottomB or self.vb.viewRange()[1][1] > self.topB

    def computeVPPDisplDeg(self):
        return int(np.floor(math.log(self.maxDataLevels[self.index].shape[0],LOG)))

    def updateData(self):
        currVPPDisplDeg = int(np.floor(math.log(self.vb.viewPixelSize()[0]/(LOG**self.exp),LOG)))
        print "----------data update debug info----------"
        print "VPPDisplDeg: ", self.computeVPPDisplDeg()
        print "current index data shape: ", self.maxDataLevels[self.index].shape
        print "currVPPDisplDeg: ", currVPPDisplDeg
        print "exp: ", self.exp
        print "pixel size: ", self.vb.viewPixelSize()[0]
        print "index: ", self.index
        print "----------data update debug info end------"
        if((self.computeVPPDisplDeg()!=currVPPDisplDeg) or self.outOfBounds()):

            visXRange = int(self.vb.viewRange()[0][1] - self.vb.viewRange()[0][0])            
            XLeftBound = int(np.floor(self.vb.viewRange()[0][0]-visXRange/4))
            if XLeftBound< 0:
                XLeftBound = 0

            XRightBound = int(np.floor(self.vb.viewRange()[0][1] + visXRange/4))
            if XRightBound > self.dataset.shape[0]:
                XRightBound = self.dataset.shape[0]

            visYRange = int(self.vb.viewRange()[1][1] - self.vb.viewRange()[1][0])

            self.updatePlots = [(p1,p2,xAxPos,ch) for (p1,p2,xAxPos,ch) in self.plots if xAxPos>=self.vb.viewRange()[1][0]-visYRange/4 and xAxPos<=self.vb.viewRange()[1][1]+visYRange/4]
            self.leftB = XLeftBound
            self.rightB = XRightBound
            self.topB = self.updatePlots[-1][2]
            self.bottomB = self.updatePlots[0][2]
            #malo by by rovnake ako int(np.floor(log10(self.maxDataLevels[self.index].shape[0])))
            self.index -= self.computeVPPDisplDeg()-currVPPDisplDeg
            self.exp = int(np.floor(math.log(self.dataset.shape[0],LOG))) - int(np.floor(math.log(self.maxDataLevels[self.index].shape[0],LOG)))
            #self.VPPDisplDeg += self.VPPDisplDeg-currVPPDisplDeg
            if (self.index < 0):
                self.index = 0

            if (self.index > len(self.maxDataLevels)-1):
                self.index = len(self.maxDataLevels)-1
            print "----------new vals debug-----------"
            print "new index: ", self.index
            print "new exp: ", self.exp
            print "----------new vals debug end-------"
            self.worker.loadData(self.updatePlots[0][3],self.updatePlots[-1][3],XLeftBound,XRightBound, self.exp, self.index,self.h5File,self.h5Path)

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    mainwin = vizEEG(app,sys.argv[1],sys.argv[2])
    mainwin.show()
    sys.exit(app.exec_())
