import numpy as np
#import pdb
import pyqtgraph as pg
import h5py
from pyqtgraph.Qt import QtGui, QtCore
import math

class OpenedWindow():

    def __init__(self, data): 

        #create the window
        self.win = QtGui.QMainWindow()
        self.cw = QtGui.QWidget()
        self.win.setCentralWidget(self.cw)
        self.data = data
    
    def plotData(self): #data are selected plots in the main window

        #create a layout
        self.win.setAttribute(55) #sets the window to delete on closing
        self.layout = QtGui.QVBoxLayout()
        self.row1 = QtGui.QHBoxLayout()
        self.row2 = QtGui.QHBoxLayout()
        self.layout.addLayout(self.row1)
        self.layout.addLayout(self.row2)
        self.cw.setLayout(self.layout)
        self.win.show()

        #fill the layout with widgets
        self.plWidget = pg.PlotWidget()
        self.plItem = self.plWidget.getPlotItem()
        self.vb = self.plItem.getViewBox()
        #plot the data
        rate = int(np.round(len(self.data[0])/(vb.width()*200)))
        self.plots = []
        shift = 0        
        x = self.data[0][::rate]
        ch = 0
        print "only data array of data[1] ", self.data[1][0][0]
        for ch in range(len(self.data[1])): #data = [xData,yData] where xData = range(lb,rb) and yData = [[dataset[ch#,lb:rb], ch#]]
            self.plots.append([self.plWidget.plot(x=x,y=self.data[1][ch][0][::rate]+shift),shift,ch])
            shift += 5000
        self.vb.setRange(xRange=self.data[0],yRange=[-10000,shift+10000],padding=0)
        self.sl = pg.InfiniteLine(bounds=[0,self.data[0][-1]],pos=int(np.round(self.data[0][-1]*0.1)))
        self.plWidget.addItem(self.sl)
        self.row1.addWidget(self.plWidget)

    def showMatrix(self): #data is the correlation matrix

        self.layout = QtGui.QVBoxLayout()
        self.cw.setLayout(self.layout)
        self.win.show()

        self.matrixImg = pg.ImageView()
        self.layout.addWidget(self.matrixImg)

        self.matrixImg.setImage(self.data[:,:,slider.value()])

    def updateMatrix(self):
        
        self.matrixImg.setImage(self.data[:,:,slider.value()])

    def showSpectrum(self): #data is what?
        pass
        

#TODO: axes labels, test the memory usage and write help

def vizEEG(h5File,h5Path,mf=None):
    global matrixFile, matrixWin, wins, app, win, vb, plItem, gLeft, gRight, gTop, gBottom, dataset, visPlot, lastVisRange, plots, rateOfDec, lr, checkBoxes, slider

    #create the main window
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    cw = QtGui.QWidget()
    win.setCentralWidget(cw)
    wins = []
    matrixFile = mf

    #create a layout
    layout = QtGui.QHBoxLayout()
    col1 = QtGui.QVBoxLayout()
    col2 = QtGui.QVBoxLayout()
    layout.addLayout(col1)
    layout.addLayout(col2)
    cw.setLayout(layout)
    win.show()    

    #create widgets in the first row of the layout
    plWidget = pg.PlotWidget()
    plItem = plWidget.getPlotItem() 

    vb = plItem.getViewBox()
    col1.addWidget(plWidget)
    spinbox = pg.SpinBox(value=5000, int=True, step=100)
    col1.addWidget(spinbox)
    openWindowBtn = QtGui.QPushButton("Open region in a new window")
    openMatrixBtn = QtGui.QPushButton("Open correlation matrix for slider position")
    col1.addWidget(openWindowBtn)
    col1.addWidget(openMatrixBtn)
    #pdb.set_trace()
    #data initialization and creation of the second row of the layout
    f = h5py.File(h5File,'r')
    dataset = f[h5Path]
    shift = 0 
    plots = []
    checkBoxes = []   
    matrixWin = None 
    
    lr = pg.LinearRegionItem(values=[int(np.round(dataset.shape[1]*0.1)), int(np.round(dataset.shape[1]*0.2))], bounds=[0,dataset.shape[1]], movable=True)
    slider = pg.InfiniteLine(bounds=[0,dataset.shape[1]],pos=int(np.round(dataset.shape[1]*0.3)), movable=True)
    plWidget.addItem(slider)
    plWidget.addItem(lr)
    plItem.setTitle(f.filename) 

    print "... loading initial data, please wait..."

    #create plots of hdf5 data
    rateOfDec = int(np.round(dataset.shape[1]/(vb.width()*200)))
    x = range(dataset.shape[1])[::rateOfDec]
    i = 0

    for ch in range(dataset.shape[0]): #ch - channel number
        checkBoxes.append(QtGui.QCheckBox("Channel "+str(i)))
        y = dataset[ch][::rateOfDec]
        plots.append([plWidget.plot(x=x,y=y+shift),shift,ch])
        shift+=5000
        i+=1

    for cb in checkBoxes:
        col2.addWidget(cb)

    ckAllBtn = QtGui.QPushButton("Check all channels")
    ckNoneBtn = QtGui.QPushButton("Uncheck all channels")
    col2.addWidget(ckAllBtn)
    col2.addWidget(ckNoneBtn)

    visPlot = 1

    print "... initial data loaded"

    #pdb.set_trace()
    vb.setRange(xRange=x, yRange=(plots[0][1]-5000,plots[-1][1]+5000), padding=0)
    gLeft = 0
    gRight = dataset.shape[1]
    gTop = plots[-1][1]
    gBottom = 0
    lastVisRange = dataset.shape[1]
#    print vb.viewPixelSize()[0]/rateOfDec

    #function that indicates if data update is needed when dragging
    def outOfBounds(left, right, top, bottom):
        if (vb.viewRange()[0][0] < 0 or vb.viewRange()[0][1] > dataset.shape[1] or vb.viewRange()[1][0] < -5000 or vb.viewRange()[1][1] > plots[-1][1]+5000):
            return False
        else:
            return vb.viewRange()[0][0] < left or vb.viewRange()[0][1] > right or vb.viewRange()[1][0] < bottom or vb.viewRange()[1][1] > top

    #function for updating data plots when zooming in/out or dragging the scene
    def dataUpdate(): #TODO zooming out, think it through
        global vb, plItem, dataset,visPlot, gLeft, gRight, gTop, gBottom, lastVisRange, rateOfDec

        visXRange = int(vb.viewRange()[0][1] - vb.viewRange()[0][0])
        valsOnPixel = vb.viewPixelSize()[0]/rateOfDec

        if ((valsOnPixel<=50 and rateOfDec > 1) or outOfBounds(gLeft,gRight,gTop,gBottom) or valsOnPixel>500):

            print "... loading data, please wait..."
            vb.setMouseEnabled(False,False)
            rateOfDec = int(np.round(vb.viewPixelSize()[0]/200))

            if rateOfDec < 1:
                rateOfDec = 1

            XLeftBound = int(np.floor(vb.viewRange()[0][0]-visXRange/4))
            if XLeftBound< 0:
                XLeftBound = 0

            XRightBound = int(np.floor(vb.viewRange()[0][1] + visXRange/4))
            if XRightBound > dataset.shape[1]:
                XRightBound = dataset.shape[1]

            visYRange = int(vb.viewRange()[1][1] - vb.viewRange()[1][0])

            visRange = vb.viewRange()

            updatePlots = [(p,xAxPos,ch) for (p,xAxPos,ch) in plots if xAxPos>=vb.viewRange()[1][0]-visYRange/4 and xAxPos<=vb.viewRange()[1][1]+visYRange/4]

            x = range(dataset.shape[1])[XLeftBound:XRightBound:rateOfDec]

            for (p,sh,ch) in updatePlots:
                p.setData(x=x,y=dataset[ch][XLeftBound:XRightBound:rateOfDec]+sh)

            visPlot = updatePlots[0][2]
            gLeft = XLeftBound
            gRight = XRightBound
            gTop = updatePlots[-1][1]
            gBottom = updatePlots[0][1]

            #print "debug: gLeft:", gLeft, "gRight:", gRight, "gTop:", gTop, "gBottom:", gBottom
            vb.setMouseEnabled(True,True)
            print "... data loaded successfully"

        lastVisRange = visXRange
    
    def shiftChange(sb): #sb is spinbox
        global plots
        changedShift = 0
        val = sb.value()
        change = val - plots[1][1]
        originalShift = plots[1][1]
        for p in plots:
            x = p[0].getData()[0]
            y = p[0].getData()[1]
            changeInShift = change*p[2] 
            print "shift is changed by ", changeInShift, " for channel ",p[2]
            p[0].setData(x=x,y=y+changeInShift)
            p[1] = originalShift+changeInShift
            print "new shift is ", p[1]

    def checkAllCBs(): #check how to join these two functions
        global checkBoxes
        for cb in checkBoxes:
            cb.setCheckState(2)

    def uncheckAllCBs():
        global checkBoxes
        for cb in checkBoxes:
            cb.setCheckState(0)

    def openPlotWindow(): #check whether the windows are kicked out of the memory after closing or not
        global wins, lr, dataset, checkBoxes
        lb = int(np.round(lr.getRegion()[0])) #left bound
        rb = int(np.round(lr.getRegion()[1])) #right bound
        yData = []
        i = 0
        for cb in checkBoxes:
            if (cb.isChecked()):
                yData.append([dataset[i,lb:rb], i]) #len(yData) gives number of plots
            i += 1
        xData = range(lb,rb)
        plotWin = OpenedWindow([xData,yData])
        wins.append(plotWin)
        plotWin.plotData() 

    def openMatrixWindow():
        global matrixFile, matrixWin
        if (matrixFile is None):
            print "No file with correlation matrix given."
        elif (matrixWin is None):
            npzData = np.load(matrixFile)
            matrix = npzData[0]
            matrixWin = OpenedWindow(matrix)
            matrixWin.showMatrix()

    def updateMatrixWin():
        global matrixWin
        matrixWin.updateMatrix()

    def openSpectrumWindow():
        pass

    #pdb.set_trace()
    vb.sigRangeChanged.connect(dataUpdate)
    spinbox.sigValueChanged.connect(shiftChange)
    ckAllBtn.clicked.connect(checkAllCBs)
    ckNoneBtn.clicked.connect(uncheckAllCBs)
    openWindowBtn.clicked.connect(openPlotWindow)
    slider.sigDragged.connect(updateMatrixWin)
    openMatrixBtn.clicked.connect(openMatrixWindow)
    
   
if __name__ == '__main__':
    import sys
    vizEEG(sys.argv[1],sys.argv[2])
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
