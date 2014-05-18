import numpy as np
import pyqtgraph as pg
import h5py
from pyqtgraph.Qt import QtGui, QtCore
import math
import WindowClasses as winCl
import minmax as minmaxFunc
import Tkinter

VPP = 1
LOG = 10

class loadingTask(QtCore.QThread):

    "Loads time series data in the background thread."    

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self,parent)
        self.lock = QtCore.QMutex()

    def loadData(self,ch1,ch2, lb, rb, index, fileName, filePath):

        "Initialises the data."

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
        self.x = range(self.dataset.shape[0])[left*LOG**exp:right*LOG**exp:LOG**exp]
#        print "lb: ", self.lb, "rb: ", self.rb
#        print "left: ", left, "right: ", right
#        print "ch1: ", self.ch1
#        print "ch2: ", self.ch2
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

#TODO: axis labels

class vizEEG(QtGui.QMainWindow):

    "The main class. It constructs the GUI with signals and interacts with the user."

    def __init__(self, app, h5File, h5Path, matrixFile=None, matrixPath=None, PSFile=None, PSPath=None):

        "Initialises Qt GUI and loads the initial data."
        
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("vizEEG")
        root = Tkinter.Tk()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        self.resize(sw/2, sh/2)
        self.h5File = h5File
        self.h5Path = h5Path
        f = h5py.File(self.h5File,'r')
    
        self.dataset = f[self.h5Path]
        if PSFile is not None:
            g = h5py.File(PSFile, 'r')
            self.powSpecData = g[PSPath]
        else:
            self.powSpecData = None

        if matrixFile is not None:
            h = h5py.File(matrixFile, 'r')
            self.matrixData = h[matrixPath]
        else:
            self.matrixData = None

        self.plots = []
        self.checkBoxes = []
        self.worker = loadingTask()
        self.wins = []
        self.PSWins = []
        self.matWins = []
        self.msgbox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "vizEEG", "text")
        dialog = QtGui.QMessageBox(QtGui.QMessageBox.Question, "vizEEG", "text", buttons=QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)

        #If minmax group is not present in the hdf5 file, ask the user if they want
        #to create one.

        self.minmaxBool = 'minmax' in f
        if not self.minmaxBool:
            dialog.setText("MinMax values not present!")
            dialog.setInformativeText("Would you like to create leveled data sets and save them to your file?")
            dialog.setDefaultButton(QtGui.QMessageBox.Ok)
            retVal = dialog.exec_()

            #TODO manage opening/closing files with different privilages
            #and TEST IT!!
            if (retVal == QtGui.QMessageBox.Yes):
            #    f.close()
                minmaxFunc.createMinMax(self.h5File, self.h5Path)
                self.minmaxBool = True

        #Load the minmax data.

        if self.minmaxBool:
            minmax = f['minmax']
            maxData = minmax['h_max']
            self.maxDataLevels = [self.dataset]
            for l in maxData.keys():
                self.maxDataLevels.append(maxData[l])

            minData = minmax['h_min']
            self.minDataLevels = [self.dataset]
            for l in minData.keys():
                self.minDataLevels.append(minData[l])

        #Create the layout and a main widget.
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
        layout.setStretchFactor(col1,150)

        self.plWidget = pg.PlotWidget()
        col1.addWidget(self.plWidget)
        self.spinbox = pg.SpinBox(value=5000, int=True, step=100)
        col1.addWidget(self.spinbox)
        menuBtn = QtGui.QPushButton("Open new window options")
        menu = QtGui.QMenu()
        menuBtn.setMenu(menu)

        #Menu actions.

        newWinAct = menu.addAction("Open selection in a new window.")
        PSWinAct = menu.addAction("Open selected channel with a power spectrum.")
        matrixWinAct = menu.addAction("Open correlation matrix.")

        col1.addWidget(menuBtn)

        self.plItem = self.plWidget.getPlotItem()
        self.vb = self.plItem.getViewBox()
 
        #Create a linear region (blue sliding stripe) and a red slider.
        self.lr = pg.LinearRegionItem(values=[int(np.round(self.dataset.shape[0]*0.1)), int(np.round(self.dataset.shape[0]*0.2))], bounds=[0,self.dataset.shape[0]], movable=True)
        self.slider = pg.InfiniteLine(pos=int(np.round(self.dataset.shape[0]*0.3)), movable=True, pen='r', bounds=[0,self.dataset.shape[0]])
        self.plWidget.addItem(self.slider)
        self.plWidget.addItem(self.lr)
        self.plItem.setTitle(f.filename)
      
        print "... loading initial data, please wait..." 

        #Initialise plots of time series data.
        if self.minmaxBool:
            VPPDeg = int(np.ceil(math.log(VPP*self.vb.width(),LOG)))
            i = 0
            for i in range(len(self.maxDataLevels)): 
                dataDeg = math.log(self.maxDataLevels[i].shape[0],LOG)
                if (int(np.ceil(dataDeg)) == VPPDeg): 
                    self.index = i

            exp = int(np.floor(math.log(self.dataset.shape[0], LOG))) - int(np.floor(math.log(self.maxDataLevels[self.index].shape[0],LOG)))
            x = range(self.dataset.shape[0])[::LOG**exp]
            shift = 0
            #TODO what if we initially choose the biggest dataset?
            #actually, we should not, how can I access amount of free memory
            for ch in range(self.dataset.shape[1]): #ch - channel number
                self.checkBoxes.append(QtGui.QCheckBox("Channel "+str(ch)))
                y1 = self.maxDataLevels[self.index][:,ch]
                y2 = self.minDataLevels[self.index][:,ch]
                p1 = self.plWidget.plot(x=x,y=y1+shift)
                p2 = self.plWidget.plot(x=x,y=y2+shift)
                fill = pg.FillBetweenItem(p1,p2,'w')
                self.plWidget.addItem(fill)
                self.plots.append([p1,p2,shift,ch,fill])
#                print "channel ",ch ," finished plotting"
                shift+=5000

        else:
            x = range(self.dataset.shape[0])
            shift = 0
            for ch in range(self.dataset.shape[1]):
                self.checkBoxes.append(QtGui.QCheckBox("Channel "+str(ch)))
                y = self.dataset[:,ch]
                self.plots.append([self.plWidget.plot(x=x, y=y+shift), shift, ch])
                shift+=5000

        #Create the right-hand panel.
        for i in range(len(self.checkBoxes)):
            ckLayout.addWidget(self.checkBoxes[len(self.checkBoxes)-i-1])

        ckAllBtn = QtGui.QPushButton("Check all channels")
        ckNoneBtn = QtGui.QPushButton("Uncheck all channels")
        col2.addWidget(ckAllBtn)
        col2.addWidget(ckNoneBtn)
        ckWidget.setLayout(ckLayout)
        scrArea.setWidget(ckWidget)
        
        #Set the main area view to show the whole data-set.
        self.vb.setRange(xRange=x, yRange=(self.plots[0][2]-5000,self.plots[-1][2]+5000), padding=0)
        self.leftB = 0
        self.rightB = self.dataset.shape[0]
        self.topB = self.plots[-1][2]
        self.bottomB = 0

        print "... initial data loaded"

        #Connect UI objects' signals to handling functions.
        ckAllBtn.clicked.connect(self.checkAllCBs)
        ckNoneBtn.clicked.connect(self.uncheckAllCBs)
        self.vb.sigRangeChanged.connect(self.updateData)
        self.connect(self.worker,QtCore.SIGNAL("finished()"), self.dataLoaded)
        self.connect(self, QtCore.SIGNAL("cancelThread()"), self.worker.stopTask)
        newWinAct.triggered.connect(self.openNewPlotWin)
        if self.powSpecData is None:
            PSWinAct.setDisabled(True)
            PSWinAct.setText("Time-frequency spectra data are not available.")
        else:
            PSWinAct.triggered.connect(self.openPSWin)
        if self.matrixData is None:
            matrixWinAct.setDisabled(True)
            matrixWinAct.setText("Correlation matrix is not available.")
        else:
            matrixWinAct.triggered.connect(self.openMatrixWin)

        self.spinbox.sigValueChanged.connect(self.shiftChange)
        self.slider.sigDragged.connect(self.slidersMngFunc)

        #And show the window.
        self.show()

    def dataLoaded(self):

        """A function that fills the plot objects with loaded data from the
           background thread. It is triggered after the thread finnishes 
           fetching them from the h5 file."""

        i=0
        if not self.worker.stopping:
            for (p1,p2,sh,ch,f) in self.updatePlots:
                p1.setData(x=self.worker.x,y=self.worker.y1[:,i]+sh)
                p2.setData(x=self.worker.x,y=self.worker.y2[:,i]+sh)
                #self.plWidget.removeItem(f)
                #f = pg.FillBetweenItem(p1,p2,'w')
                #self.plWidget.addItem(f)
                f.setCurves(p1,p2)
                i+=1

            self.leftB = self.worker.x[0]
            self.rightB = self.worker.x[-1]
            self.topB = self.updatePlots[-1][2]
            self.bottomB = self.updatePlots[0][2]

    def checkAllCBs(self):

        "Checks all the checkboxes in the right-hand panel."

        for cb in self.checkBoxes:
            cb.setCheckState(2)

    def uncheckAllCBs(self):

        "Unchecks all the checkboxes in the left-hand panel."

        for cb in self.checkBoxes:
            cb.setCheckState(0)

    def outOfBounds(self):

        """
        Defines if the view range of the main area is out of bounds of loaded
        data.

        Returns a boolean value. 
        """
 
        return ((self.vb.viewRange()[0][0] < self.leftB) or (self.vb.viewRange()[0][1] > self.rightB) or (self.vb.viewRange()[1][0] < self.bottomB) or (self.vb.viewRange()[1][1] > self.topB))

#TODO test on a big screen    
#TODO otestovat nahratie regionov mimo visRange, specialne x suradnicu v najemnejsich datach
    def updateData(self):

        """Function with the data tiling algorithm. It determines if new data has 
           has to be loaded. If it is so, it calls the background loading thread.
        """

        if self.minmaxBool:
            self.emit(QtCore.SIGNAL("cancelThread()"))
            visXRange = int(self.vb.viewRange()[0][1] - self.vb.viewRange()[0][0])
            exp = int(np.floor(math.log(self.dataset.shape[0],LOG))) - int(np.floor(math.log(self.maxDataLevels[self.index].shape[0],LOG)))
#            print "-----------Debug--------------"
#            print "visXRange:", visXRange        
#            print "visXRange/LOG**exp:", visXRange/(LOG**exp)
#            print "0.1*VPP*width():", 0.1*VPP*self.vb.width()
#            print "10.0*VPP*width():", 10.0*VPP*self.vb.width()
#            print "outOfBounds:", self.outOfBounds()
#            print "current index:", self.index
#            print "-----------Debug--------------"
            if((visXRange/(LOG**exp) < (0.7*VPP*self.vb.width())) or (visXRange/(LOG**exp) > (20*VPP*self.vb.width())) or self.outOfBounds()):
                XLeftBound = int(np.floor(self.vb.viewRange()[0][0]-visXRange/4))
                if XLeftBound< 0:
                    XLeftBound = 0

                XRightBound = int(np.floor(self.vb.viewRange()[0][1] + visXRange/4))
                if XRightBound > self.dataset.shape[0]:
                    XRightBound = self.dataset.shape[0]

                visYRange = int(self.vb.viewRange()[1][1] - self.vb.viewRange()[1][0])

                self.updatePlots = [(p1,p2,xAxPos,ch,f) for (p1,p2,xAxPos,ch,f) in self.plots if xAxPos>=self.vb.viewRange()[1][0]-visYRange/4 and xAxPos<=self.vb.viewRange()[1][1]+visYRange/4]

                self.index =  int(np.floor(math.log(visXRange/self.vb.width() * VPP,LOG)))
                if self.index<0:
                    self.index = 0
                if self.index>(len(self.maxDataLevels))-1:
                    self.index = (len(self.maxDataLevels))-1
#                print "-----------Debug--------------"
#                print "newly set index:", self.index
#                print "-----------Debug--------------"
                self.worker.loadData(self.updatePlots[0][3],self.updatePlots[-1][3],XLeftBound,XRightBound, self.index,self.h5File,self.h5Path)

    def slidersMngFunc(self):

        "Manages synchronisation of sliders." 
 
        for w in self.wins:
            w.plotSliderUpdate(self.slider.value())

        for w in self.PSWins:
            w.plotSliderUpdate(self.slider.value())
            w.imgSliderUpdate(self.slider.value())

        for w in self.matWins:
            w.showData(self.slider.value())

    def openNewPlotWin(self):

        "Opens a new window with one chosen channel."

        if self.minmaxBool:

            #Load the necessary data from the data-set.
            visXRange = self.lr.getRegion()[1] - self.lr.getRegion()[0]
            root = Tkinter.Tk()
            sw = root.winfo_screenwidth()
            vbWidth = (sw/2)*0.9
            tempIndex = int(np.floor(math.log(visXRange/vbWidth * VPP,LOG)))
            exp = int(np.floor(math.log(self.dataset.shape[0],LOG))) - int(np.floor(math.log(self.maxDataLevels[tempIndex].shape[0],LOG)))
            lb = int(np.ceil(self.lr.getRegion()[0]))
            rb = int(np.ceil(self.lr.getRegion()[1]))
            left = np.round(lb/(LOG**exp))
            right = np.round(rb/(LOG**exp))
            xData = range(self.dataset.shape[0])[left*LOG**exp:right*LOG**exp:LOG**exp]
            yData = []
            chans = [] 
            i = 0

            #Find the specific channel.
            for cb in self.checkBoxes:
                if (cb.isChecked()):
                    yData.append([self.maxDataLevels[tempIndex][left:right,i], self.minDataLevels[tempIndex][left:right, i]])
                    chans.append(i)
                i += 1            
        else:
            #The same as mentioned but with a small data-set
            lb = int(np.ceil(self.lr.getRegion()[0]))
            rb = int(np.ceil(self.lr.getRegion()[1]))
            xData = range(self.dataset.shape[0])[lb:rb]
            yData = []
            chans = []
            i = 0
            for cb in self.checkBoxes:
                if (cb.isChecked()):
                    yData.append([self.dataset[lb:rb,i], None])
                    chans.append(i)
                i += 1

        #If the user has not chosen any channel, warn them.         
        if len(yData) == 0:
            self.msgbox.setText("Please, choose at least one channel to display.")
            self.msgbox.exec_()
        else:
            
            #Create and open the window.
            plWindow = winCl.PlotWindow([xData,yData,chans])
            self.wins.append(plWindow)
            plWindow.showData()

    def openPSWin(self):
     
        "Opens a new window with a chosen channel with its time-frequency spectrum."

        numOfChans = 0
        i = 0

        #Find the chosen channel.     
        for cb in self.checkBoxes:
            if (cb.isChecked()):
                numOfChans += 1
                chanNum = i
            i += 1

        #If none was chosen, issue warning, else load necessary data and create the window.
        if numOfChans != 1:
            self.msgbox.setText("Please, choose exactly one channel per window.")
            self.msgbox.exec_()
        else:
            if self.minmaxBool:
                root = Tkinter.Tk()
                sw = root.winfo_screenwidth()
                vbWidth = (sw/2)*0.9
                tempIndex = int(np.floor(math.log(self.dataset.shape[0]/vbWidth * VPP,LOG)))
                exp = int(np.floor(math.log(self.dataset.shape[0],LOG))) - int(np.floor(math.log(self.maxDataLevels[tempIndex].shape[0],LOG)))
                xData = range(self.dataset.shape[0])[::LOG**exp]
                yData = [[self.maxDataLevels[tempIndex][:,chanNum],self.minDataLevels[tempIndex][:,chanNum]]]
            else:
                xData = range(self.dataset.shape[0])
                yData = [[self.dataset[:,chanNum], None]]

            chans = [chanNum]
            window = winCl.PlotWindow([xData,yData,chans], self.powSpecData)
            self.PSWins.append(window)
            window.showData()
            window.showPowSpec() 
    
    def openMatrixWin(self):

        "Opens a new window with a picture of a correlation matrix."

        matWindow = winCl.CorrMatrixWindow(self.matrixData, 10, 2)
        self.matWins.append(matWindow)
        matWindow.showData(self.slider.value())

    def shiftChange(self, sb): #sb is spinbox

        "Handles the spinbox that manages the distance between displayed plots."

        val = sb.value()
        if self.minmaxBool:
            change = val - self.plots[1][2]
            originalShift = self.plots[1][2]
            for p in self.plots:
                x1 = p[0].getData()[0]
                x2 = p[1].getData()[0]
                y1 = p[0].getData()[1]
                y2 = p[1].getData()[1]
                changeInShift = change*p[3]
                p[0].setData(x=x1,y=y1+changeInShift)
                p[1].setData(x=x2,y=y2+changeInShift)
                p[2] = originalShift+changeInShift
                p[4].setCurves(p[0],p[1])
        else:
            originalShift = self.plots[1][1]
            change = val - self.plots[1][1]
            for p in self.plots:
                x = p[0].getData()[0]
                y = p[0].getData()[1]
                changeInShift = change*p[2]
                p[0].setData(x=x, y=y+changeInShift)
                p[1] = originalShift+changeInShift 

def parseFile(inFile):

    f = open(inFile[0], 'r')
    print inFile
    lines = []
    for line in f:
        lines.append(line)
    if len(lines) > 3:
        raise Exception("File contains too many lines, 3 lines are expected.")
    parsed = {"file":None, "path":None, "mf":None, "mp":None, "tff":None, "tfp":None}
    #strip whitespace and parse
    for i in range(len(lines)):
        lines[i].strip()
        lines[i] = lines[i].split(":")
        try:
            if lines[i][0] == 'f':
                parsed["file"] = lines[i][1]
                parsed["path"] = lines[i][2]
            elif lines[i][0] == "m":
                parsed["mf"] = lines[i][1]
                parsed["mp"] = lines[i][2]
            elif lines[i][0] == "tf":
                parsed["tff"] = lines[i][1]
                parsed["tfp"] = lines[i][2]
        except Exception as e:
            raise Exception(e)
    if parsed["file"] == None or parsed["path"] == None:
        raise Exception("File must specify at least a path to a h5 file with a h5 path to eeg data")       
    f.close()
    return parsed

if __name__ == '__main__':
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--matrix', metavar=('FILE','PATH'), nargs=2)
    parser.add_argument('-s', '--tfSpect', metavar=('FILE', 'PATH'), nargs=2)
    parser.add_argument('file', nargs=1)
    parser.add_argument('path', nargs='?')
    argsNamespace = parser.parse_args()
    args = vars(argsNamespace)
    parsedArgs = None
#    print args
    if args["path"] is None:
#        try:            
#            parsedArgs = parseFile(args["file"])
#        except Exception as e:
#            print "bum"
#            parser.error(e)
         parsedArgs = parseFile(args["file"])
    app = QtGui.QApplication(sys.argv)
    tff = None
    tfp = None
    mf = None
    mp = None
    f = None
    path = None

    if parsedArgs is None:
        if args["tfSpect"] is not None:
            tff = args["tfSpect"][0]
            tfp = args["tfSpect"][1]

        if args["matrix"] is not None:
            mf = args["matrix"][0]
            mp = args["matrix"][1]
#        print args["file"][0]
#        print type(args["file"][0])
        f = args["file"][0]
        path = args["path"]

    else: #write code for file parsing, there surely is some library for this
        f = parsedArgs["file"]
        path = parsedArgs["path"]
        tff = parsedArgs["tff"]
        tfp = parsedArgs["tfp"]
        mf = parsedArgs["mf"]
        mp = parsedArgs["mp"] 
#    print f
#    print path
    mainwin = vizEEG(app, f, path, PSFile=tff,PSPath=tfp, matrixFile=mf, matrixPath=mp)
#    mainwin.show()
#    mainwin.fillPlots(mainwin.plots)
    sys.exit(app.exec_())

#    app = QtGui.QApplication([])
#    if (len(sys.argv)>3):
#        mainwin = vizEEG(app, sys.argv[1],sys.argv[2],PSFile=sys.argv[3],PSPath=sys.argv[4], matrixFile=sys.argv[5], matrixPath=sys.argv[6])
#    else:
#        mainwin = vizEEG(app,sys.argv[1],sys.argv[2])

#    mainwin.show()
#    sys.exit(app.exec_())
