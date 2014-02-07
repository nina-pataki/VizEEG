import numpy as np
import pyqtgraph as pg
import h5py
from pyqtgraph.Qt import QtGui, QtCore
import math
import WindowClasses as winCl

VPP = 1
LOG = 10

class loadingTask(QtCore.QThread):
    def __init__(self, parent=None):
        QtCore.QThread.__init__(self,parent)
        self.lock = QtCore.QMutex()

    def loadData(self,ch1,ch2, lb, rb, index, fileName, filePath):
        print "... loading data..."
        self.fileName = fileName
        self.filePath = filePath
        self.lb = lb
        self.rb = rb
        self.index = index
        self.running = True
        self.ch1 = ch1
        self.ch2 = ch2
        self.start()

    def run(self):

        self.lock.lock()
        self.stopping = False

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
        left = np.round(self.lb/(LOG**exp))
        right = np.round(self.rb/(LOG**exp))
        #self.x = range(self.dataset.shape[0])[self.lb:self.rb:LOG**exp]
        self.x = range(self.dataset.shape[0])[left*LOG**exp:right*LOG**exp:LOG**exp]
        print "lb: ", self.lb, "rb: ", self.rb
        print "left: ", left, "right: ", right
        print "ch1: ", self.ch1
        print "ch2: ", self.ch2
        self.y1 = np.zeros((right-left,(self.ch2-self.ch1)+1))
        self.y2 = np.zeros((right-left,(self.ch2-self.ch1)+1)) 
        j = 0
        for i in range(self.ch1,self.ch2+1):
            if (self.stopping):
                break        
            else:
                self.y1[:,j] = maxDataLevels[self.index][left:right,i]
                self.y2[:,j] = minDataLevels[self.index][left:right,i]
                j += 1
                
        self.lock.unlock()
    def stopTask(self):
        self.stopping = True
        print "cancelling thread"     

#TODO: axis labels, scrolling of checkbox area

class vizEEG(QtGui.QMainWindow):

    def __init__(self, app, h5File, h5Path, matrixFile=None, matrixPath=None, PSFile=None, PSPath=None):
        
        QtGui.QMainWindow.__init__(self)
        self.resize(600, 800)
        self.h5File = h5File #TODO preco su ako verejne premenne?
        self.h5Path = h5Path
        f = h5py.File(self.h5File,'r')
        self.dataset = f[self.h5Path]
        g = h5py.File(PSFile, 'r')
        self.powSpecData = g[PSPath]
        self.plots = []
        self.checkBoxes = []
        self.worker = loadingTask()
        self.wins = []
        self.PSWins = []
        self.matWins = []

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
        ckWidget = QtGui.QWidget()
        ckLayout = QtGui.QVBoxLayout()
        scrArea = QtGui.QScrollArea()
        col2.addWidget(scrArea)
        layout.addLayout(col1)
        layout.addLayout(col2)
        cw.setLayout(layout)

        #create widgets in the first row of the layout
        self.plWidget = pg.PlotWidget() #plotWidget segfaults for some reason
        col1.addWidget(self.plWidget)
        self.spinbox = pg.SpinBox(value=5000, int=True, step=100)
        col1.addWidget(self.spinbox)
        openWindowBtn = QtGui.QPushButton("Open region in a new window")
        openPSWinBtn = QtGui.QPushButton("Open chosen channel with its power spectrum")
        openMatrixBtn = QtGui.QPushButton("Open correlation matrix for slider position")
        col1.addWidget(openWindowBtn)
        col1.addWidget(openMatrixBtn)
        col1.addWidget(openPSWinBtn)

        #create widgets in the second row of the layout
        self.plItem = self.plWidget.getPlotItem()
        self.vb = self.plItem.getViewBox()
        self.lr = pg.LinearRegionItem(values=[int(np.round(self.dataset.shape[0]*0.1)), int(np.round(self.dataset.shape[0]*0.2))], bounds=[0,self.dataset.shape[0]], movable=True)
        self.slider = pg.InfiniteLine(pos=int(np.round(self.dataset.shape[0]*0.3)), movable=True, pen='r')
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
                self.index = i
        exp = int(np.floor(math.log(self.dataset.shape[0], LOG))) - int(np.floor(math.log(self.maxDataLevels[self.index].shape[0],LOG)))
        x = range(self.dataset.shape[0])[::LOG**exp]
        shift = 0
        for ch in range(self.dataset.shape[1]): #ch - channel number
            self.checkBoxes.append(QtGui.QCheckBox("Channel "+str(ch)))
            y1 = self.maxDataLevels[self.index][:,ch]
            y2 = self.minDataLevels[self.index][:,ch]
            self.plots.append([self.plWidget.plot(x=x,y=y1+shift),self.plWidget.plot(x=x,y=y2+shift),shift,ch])
            shift+=5000

        #check boxes for choosing channels
            for cb in self.checkBoxes:
                ckLayout.addWidget(cb)
                cb.setContentsMargins(-1,0,-1,0)

        ckAllBtn = QtGui.QPushButton("Check all channels")
        ckNoneBtn = QtGui.QPushButton("Uncheck all channels")
        col2.addWidget(ckAllBtn)
        col2.addWidget(ckNoneBtn)
        ckWidget.setLayout(ckLayout)
        #ckLayout.addSpacing(0)
        scrArea.setWidget(ckWidget)
        
        
        self.vb.setRange(xRange=x, yRange=(self.plots[0][2]-5000,self.plots[-1][2]+5000), padding=0)
        self.leftB = 0
        self.rightB = self.dataset.shape[0]
        self.topB = self.plots[-1][2]
        self.bottomB = 0

        print "... initial data loaded"

        #connect UI objects' signals to handling functions
        ckAllBtn.clicked.connect(self.checkAllCBs)
        ckNoneBtn.clicked.connect(self.uncheckAllCBs)
        self.vb.sigRangeChanged.connect(self.updateData)
        self.connect(self.worker,QtCore.SIGNAL("finished()"), self.dataLoaded)
        self.connect(self, QtCore.SIGNAL("cancelThread()"), self.worker.stopTask)
        openWindowBtn.clicked.connect(self.openNewPlotWin)
        openPSWinBtn.clicked.connect(self.openPSWin)
        self.slider.sigDragged.connect(self.synSliders)
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
        if not self.worker.stopping:
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
            print "left ", (self.vb.viewRange()[0][0] < self.leftB)
            print "right ", (self.vb.viewRange()[0][1] > self.rightB)
            print "self.vb.viewRange()[0][1] and rightB: ", self.vb.viewRange()[0][1], self.rightB
            print "bottom ", (self.vb.viewRange()[1][0] < self.bottomB)
            print "top ", (self.vb.viewRange()[1][1] > self.topB)
            return ((self.vb.viewRange()[0][0] < self.leftB) or (self.vb.viewRange()[0][1] > self.rightB) or (self.vb.viewRange()[1][0] < self.bottomB) or (self.vb.viewRange()[1][1] > self.topB))

    def updateData(self):

        self.emit(QtCore.SIGNAL("cancelThread()"))
        visXRange = int(self.vb.viewRange()[0][1] - self.vb.viewRange()[0][0])
        print "visXRange: ", visXRange        
        exp = int(np.floor(math.log(self.dataset.shape[0],LOG))) - int(np.floor(math.log(self.maxDataLevels[self.index].shape[0],LOG)))
        if((visXRange/(LOG**exp) < (0.1*VPP*self.vb.width())) or (visXRange/(LOG**exp) > (10.0*VPP*self.vb.width())) or self.outOfBounds()):
            print "visXRange/LOG**exp: ", visXRange/(LOG**exp)
            print "0.1*VPP*width(): ", 0.1*VPP*self.vb.width()
            print "10.0*VPP*width(): ", 10.0*VPP*self.vb.width()
            print "outOfBounds: ", self.outOfBounds()
            #TODO otestovat nahratie regionov mimo visRange
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

            self.index =  int(np.floor(math.log(visXRange/self.vb.width() * VPP,LOG)))
 
            self.worker.loadData(self.updatePlots[0][3],self.updatePlots[-1][3],XLeftBound,XRightBound, self.index,self.h5File,self.h5Path)

    def synSliders(self):
        for w in self.wins:
            w.sliderUpdate(self.slider.value())

    def openNewPlotWin(self):
        exp = int(np.floor(math.log(self.dataset.shape[0],LOG))) - int(np.floor(math.log(self.maxDataLevels[self.index].shape[0],LOG)))
        lb = int(np.ceil(self.lr.getRegion()[0]))
        rb = int(np.ceil(self.lr.getRegion()[1]))
        left = np.round(lb/(LOG**exp))
        right = np.round(rb/(LOG**exp))
        xData = range(self.dataset.shape[0])[left*LOG**exp:right*LOG**exp:LOG**exp]
        yData = []
        chans = [] 
        i = 0
        for cb in self.checkBoxes:
            if (cb.isChecked()):
                yData.append([self.maxDataLevels[self.index][left:right,i], self.minDataLevels[self.index][left:right, i]])
                chans.append(i)
            i += 1
        plWindow = winCl.PlotWindow([xData,yData,chans])
        self.wins.append(plWindow)
        plWindow.showData()
    
    def openPSWin(self):
        numOfChans = 0
        i = 0
        for cb in self.checkBoxes:
            if (cb.isChecked()):
                numOfChans += 1
                chanNum = i
            i += 1

        if numOfChans != 1:
            print "Please, choose exactly one channel per window."
        else:
            exp = int(np.floor(math.log(self.dataset.shape[0],LOG))) - int(np.floor(math.log(self.maxDataLevels[self.index].shape[0],LOG)))
            xData = range(self.dataset.shape[0])[::LOG**exp]
            yData = [[self.maxDataLevels[self.index][:,chanNum],self.minDataLevels[self.index][:,chanNum]]]
            chans = [chanNum]
            window = winCl.PlotWindow([xData,yData,chans], self.powSpecData)
            self.PSWins.append(window)
            window.showData()
            window.showPowSpec() 
        

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    if (len(sys.argv)>3):
        mainwin = vizEEG(app, sys.argv[1],sys.argv[2],PSFile=sys.argv[3],PSPath=sys.argv[4])
    else:
        mainwin = vizEEG(app,sys.argv[1],sys.argv[2])

    mainwin.show()
    sys.exit(app.exec_())
