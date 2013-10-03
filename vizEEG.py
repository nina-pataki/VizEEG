import numpy as np
import pyqtgraph as pg
import h5py
from pyqtgraph.Qt import QtGui
import unicodedata #is this necessary?
import math

#TODO: axis labels, openNewWindow function, clean up the code, add comments, what language should I use in the UI?, add data processing remarks to the console output, test the memory usage and write help

def vizEEG(h5File,h5Path):
    global vb, plItem, gLeft, gRight, gTop, gBottom, dataset, visPlot, lastVisRange, plots, rateOfDec, lr, checkBoxes
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    cw = QtGui.QWidget()
    win.setCentralWidget(cw)
    layout = QtGui.QHBoxLayout()
    col1 = QtGui.QVBoxLayout()
    col2 = QtGui.QVBoxLayout()
    layout.addLayout(col1)
    layout.addLayout(col2)
    cw.setLayout(layout)
    win.show()    

    #load hdf5 data
    f = h5py.File(h5File,'r')
    dataset = f[h5Path]

    plWidget = pg.PlotWidget()
    plItem = plWidget.getPlotItem() 
    plItem.setTitle(f.filename) 
    if (plItem.listDataItems() is not []): 
        pl.removeItem(plItem.listDataItems()[0])
    vb = plItem.getViewBox()
    col1.addWidget(plWidget)
    spinbox = pg.SpinBox(value=5000, int=True, dec=True, minStep=1, step=100)
    col1.addWidget(spinbox)
    openWindowBtn = QtGui.QPushButton("Otevri vyber v novem okne")
    col1.addWidget(openWindowBtn)
    
    shift = 0 
    plots = []
    checkBoxes = []    
    
    print "...loading data, please wait..."
    #data initialization
    rateOfDec = int(np.round(dataset.shape[1]/(vb.width()*200)))
    print "debug: init rate: ", rateOfDec, "vb.width: ", vb.width()
    x = range(dataset.shape[1])[::rateOfDec]
    i = 0
    #print "debug: length of x array: ", len(x)
    for ch in range(dataset.shape[0]): #ch - channel number
        checkBoxes.append(QtGui.QCheckBox("Channel "+str(i)))
        y = dataset[ch][::rateOfDec]
        plots.append((pl.plot(x=x,y=y+shift),shift,ch))
        shift+=5000
        i+=1

    for cb in checkBoxes:
        col2.addWidget(cb)

    ckAllBtn = QtGui.QPushButton("Vybrat vsechny kanaly")
    ckNoneBtn = QtGui.QPushButton("Odebrat vsechny kanaly")
    col2.addWidget(ckAllBtn)
    col2.addWidget(ckNoneBtn)
    visPlot = 1

    print "initial data loaded"
    vb.setRange(xRange=x, yRange=(plots[0][1]-5000,plots[-1][1]+5000), padding=0)
    gLeft = 0
    gRight = dataset.shape[1]
    gTop = plots[-1][1]
    gBottom = 0
    lastVisRange = dataset.shape[1]
    print vb.viewPixelSize()[0]/rateOfDec

    #function that indicates if data update is needed when dragging
    def outOfBounds(left, right, top, bottom):
        if (vb.viewRange()[0][0] < 0 or vb.viewRange()[0][1] > dataset.shape[1] or vb.viewRange()[1][0] < -5000 or vb.viewRange()[1][1] > plots[-1][1]+5000):
            return False
        else:
            return vb.viewRange()[0][0] < left or vb.viewRange()[0][1] > right or vb.viewRange()[1][0] < bottom or vb.viewRange()[1][1] > top

    #function for updating data plots when zooming in/out or dragging the scene
    def dataUpdate(): #TODO zooming out
        global vb, plItem, dataset,visPlot, gLeft, gRight, gTop, gBottom, lastVisRange, rateOfDec
        visXRange = int(vb.viewRange()[0][1] - vb.viewRange()[0][0])
        valsOnPixel = vb.viewPixelSize()[0]/rateOfDec
        if ((valsOnPixel<=50 and rateOfDec > 1) or outOfBounds(gLeft,gRight,gTop,gBottom)):
            plItem.setTitle("loading data")
            print "loading data..."
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
            print "debug: gLeft:", gLeft, "gRight:", gRight, "gTop:", gTop, "gBottom:", gBottom
            plItem.setTitle("Signals")
            vb.setMouseEnabled(True,True)
            print "loading data OK"
        lastVisRange = visXRange
    
    def shiftChange(sb): #sb is spinbox
        global plots, vb
        changedShift = 0
        val = sb.value()
        for p in plots:
            y = p[0].getData()[1]
            p[0].setData(y=y+changedShift)
            p[2] = changedShift
            changedShift+=val

    def checkAllCBs(): #check how to join these two functions
        global checkBoxes
        for cb in checkBoxes:
            cb.setCheckState(2)

    def uncheckAllCBs():
        global checkBoxes
        for cb in checkBoxes:
            cb.setCheckState(0)

    def openWindowBtn(): #its probably wise to write some class for new windows, since we will need some buttons in them and compute the statistics, what about memory management? what will happen if the window is closed, will it be removed from the memory, or not? it seems that PlotWindow doesnt work right
        global lr, 

    vb.sigRangeChanged.connect(dataUpdate)
    spinbox.sigValueChanged.connect(shiftChange)
    ckAllBtn.clicked.connect(checkAllCBs)
    ckNoneBtn.clicked.connect(uncheckAllCBs)
    openWindowBtn.clicked.connect(openNewWindow)
   
if __name__ == '__main__':
    import sys
    vizEEG(sys.argv[1],sys.argv[2])
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
