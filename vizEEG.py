import numpy as np
import pyqtgraph as pg
import h5py
from pyqtgraph.Qt import QtGui
import unicodedata
import math

def vizEEG(h5File,h5Path):
    global vb, plItem, gLeft, gRight, gTop, gBottom, dataset
    app = QtGui.QApplication([])

    #load hdf5 data
    f = h5py.File(h5File,'r')
    dataset = f[h5Path]

    pl = pg.plot()
    plItem = pl.getPlotItem() 
    plItem.setTitle("Signals") #TODO: do title dat nazov suboru
    if (plItem.listDataItems() is not []): 
        pl.removeItem(plItem.listDataItems()[0])
    vb = plItem.getViewBox()
    shift = 0 
    plots = []    
    print "...loading data, please wait..."
    #data initialization
    rateOfDec = dataset.shape[1]/(int(vb.width())*200)
    print "debug: init rate: ", rateOfDec, "vb.width: ", vb.width()
    x = range(dataset.shape[1])[::rateOfDec]
    print "debug: length of x array: ", len(x)
    for ch in range(dataset.shape[0]): #ch - channel number
        y = dataset[ch][::rateOfDec]
        plots.append((pl.plot(x=x,y=y+shift),shift,ch))
        shift+=5000

    print "initial data loaded"
    vb.setRange(xRange=x, yRange=(plots[0][1]-5000,plots[-1][1]+5000), padding=0)
    gLeft = 0
    gRight = dataset.shape[1]
    gTop = plots[-1][1]
    gBottom = 0

    #function that indicates if data update is needed when dragging
    def outOfBounds():
        global gLeft, gRight, gTop, gBottom
        print "vosli sme do outofbounds"
        if (vb.viewRange()[0][0] < 0 or vb.viewRange()[0][1] > dataset.shape[1] or vb.viewRange()[1][0] < -5000 or vb.viewRange()[1][1] > plots[-1][1]+5000):
            return False
        else:
            return vb.viewRange()[0][0] < gLeft or vb.viewRange()[0][1] > gRight or vb.viewRange()[1][0] < gBottom or vb.viewRange()[1][1] > gTop

    #function for updating data plots when zooming in/out or dragging the scene
    def dataUpdate():
        global vb, plItem, dataset
        visXRange = int(vb.viewRange()[0][1] - vb.viewRange()[0][0])
        rateOfDec = visXRange/(int(vb.width())*200)
        valsOnPixel = len(plots[0][0].getData()[1][vb.viewRange()[0][0]:vb.viewRange()[0][1]]) / int(vb.width())        
        print "debug: visX: ", visXRange, "valsOnPixel: ", valsOnPixel
        if (valsOnPixel<=100 or valsOnPixel>300 or outOfBounds()):
            plItem.setTitle("loading data")

            if (vb.viewRange()[0][0] < 0):
                XLeftBound = 0
            else:
                XLeftBound = int(vb.viewRange()[0][0])

            if (vb.viewRange()[0][1] > dataset.shape[1]):
                XRightBound = dataset.shape[1]
            else:
                XRightBound = int(vb.viewRange()[0][1])

            visYRange = int(vb.viewRange()[1][1] - vb.viewRange()[1][0])
            updatePlots = [(p,xAxPos,ch) for (p,xAxPos,ch) in plots if xAxPos>vb.viewRange()[1][0]+visYRange/2 and xAxPos<vb.viewRange()[1][1]+visYRange/2]
            print "debug: new rate: ", rateOfDec
            x = range(dataset.shape[1])[XLeftBound:XRightBound:rateOfDec]
            print "debug: length of x array in zooming: ", len(x)
            for (p,sh,ch) in updatePlots:
                p.setData(x=x,y=dataset[ch][XLeftBound:XRightBound:rateOfDec])
            
            gLeft = XLeftBound
            gRight = XRightBound
            gTop = updatePlots[-1][1]
            gBottom = updatePlots[0][1]
            
            plItem.setTitle("Signals")

    vb.sigRangeChanged.connect(dataUpdate)
   
if __name__ == '__main__':
    import sys
    vizEEG(sys.argv[1],sys.argv[2])
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
