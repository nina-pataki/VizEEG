import numpy as np
import pyqtgraph as pg
import h5py
from pyqtgraph.Qt import QtGui
import unicodedata
import math

def vizEEG(h5File,h5Path):
    global vb, plItem, gLeft, gRight, gTop, gBottom, dataset, visPlot, lastVisRange, plots, rateOfDec
    app = QtGui.QApplication([])
   # w = QtGui.QWidget()
   # layout = QtGui.QGridLayout()
  #  w.setLayout(layout)
    #load hdf5 data
    f = h5py.File(h5File,'r')
    dataset = f[h5Path]

    pl = pg.plot()
    plItem = pl.getPlotItem() 
    plItem.setTitle("Signals") #TODO: do title dat nazov suboru
    if (plItem.listDataItems() is not []): 
        pl.removeItem(plItem.listDataItems()[0])
    vb = plItem.getViewBox()
   # layout.addWidget(pl)
    #spinbox = pg.SpinBox(value=5000, int=True, dec=True, minStep=1, step=100)
    #layout.addWidget(spinbox)
    shift = 0 
    plots = []
        
    print "...loading data, please wait..."
    #data initialization
    rateOfDec = int(np.round(dataset.shape[1]/(vb.width()*200)))
    print "debug: init rate: ", rateOfDec, "vb.width: ", vb.width()
    x = range(dataset.shape[1])[::rateOfDec]
    #print "debug: length of x array: ", len(x)
    for ch in range(dataset.shape[0]): #ch - channel number
        y = dataset[ch][::rateOfDec]
        plots.append((pl.plot(x=x,y=y+shift),shift,ch))
        shift+=5000
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
    def dataUpdate(): #TODO stale problemy s spravnym zobrazovanim pri zoom out a panning, zoom a pan hrozne seka, ked dokoncis zisti memory consumption
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
    
    def shiftChange(sb):
        global plots, vb
        changedShift = 0
        val = sb.value()
        for i in range(len(plots)):
            y = plots[i][0].getData()[1]
            plots[i][0].setData(y=y+changedShift)
            plots[i][2] = changedShift
            changedShift+=val

    vb.sigRangeChanged.connect(dataUpdate)
  #  spinbox.sigValueChanged.connect(shiftChange)
  #  w.show()
   
if __name__ == '__main__':
    import sys
    vizEEG(sys.argv[1],sys.argv[2])
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
