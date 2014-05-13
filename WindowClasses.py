import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui
import re
import Tkinter

class PlotWindow(QtGui.QMainWindow):
    #TODO test if setAttribute(55) works

    """Class that creates a new window with a specific channel. 
       Optionally, it can display a time-frequency spectrum."""

    def __init__(self, data, PSData=None): #data = [xData,yData,chans] where xData = range(lb,rb), yData = [maxdata, mindata], chans = [ch#]

        "Initialises the Qt GUI and variables."
  
        QtGui.QMainWindow.__init__(self)
        root = Tkinter.Tk()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        self.resize(sw/2, sh/2)
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

        "Function that shows the plot."

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
     
    def showPowSpec(self):

        """Function that shows the plot and its time-frequency spectrum.
           The user is asked for the colours that should be used in the spectrum.
           If Cancel is clicked, the spectrum is displayed in gray scale."""

        #Some more initialisation.
        self.setWindowTitle("vizEEG - Time-frequency Spectrum display")
        self.img = pg.ImageView()
        self.col1.addWidget(self.img)
        self.imgSlider = pg.InfiniteLine(pos=0, bounds=[0,self.PSData.shape[0]], movable=True, pen='y')
        self.img.addItem(self.imgSlider)
        self.plotSlider.sigDragged.connect(self.imgSliderFunc)
        self.imgSlider.sigDragged.connect(self.plotSliderFunc)
        self.r3 = None

        colours, self.ok = self.colourInput("Choose a colouring for time-frequency spectum images or enter a different one in format RRR,GGG,BBB.\n Please, separate colours (2 or 3) with space.\n If Cancel is clicked spectrum will be displayed in gray scale.")

        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle("vizEEG: Colour Error")

        if self.ok:
           
            #If the input was without an error, parse the user input.
            parsed = re.findall("\d{0,3},\d{0,3},\d{0,3}", colours)
            if len(parsed) < 2 or len(parsed) > 3:
                self.ok = False
                msgBox.setText("Colours input in an incorrect format.\nPlease, input 2 or 3 colours in format RRR,GGG,BBB separated by space, where RRR or GGG or BBB are numbers in range 0-255.")
                msgBox.exec_()
            else:
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

                #Check if the input colours are in a proper format.
                okRange = range(256)
                areColsOk = self.r1 in okRange and self.r2 in okRange and self.g1 in okRange and self.g2 in okRange and self.b1 in okRange and self.b2 in okRange

                if len(parsed) == 3:
                    areColsOk = areColsOk and self.r3 in okRange and self.g3 in okRange and self.b3 in okRange

                if not areColsOk:
                    self.ok = False
                    msgBox.setText("Colours are out of RGB range. \nPlease, input 2 or 3 colours in format RRR,GGG,BBB separated by space, where RRR or GGG or BBB are numbers in range 0-255.")
                    msgBox.exec_()            

        #Create the gray scale image.
        #makeRGBA outputs a tuple (imgArray,isThereAlphaChannel?)
        TFRGBImg = pg.makeRGBA(self.PSData[:,:,self.data[2][0]], levels=[np.amin(self.PSData[:,:,self.data[2][0]]), np.amax(self.PSData[:,:,self.data[2][0]])])[0]

        if self.ok:
            
            #Colour the image with 2 colours.
            TFRGBCol = np.zeros(TFRGBImg.shape, dtype=TFRGBImg.dtype)
            if self.r3 is None:
                TFRGBCol[:,:,0] = (TFRGBImg[:,:,0]/255.0)*self.r1 + (1 - (TFRGBImg[:,:,0].astype(int)/255.0))*self.r2
                TFRGBCol[:,:,1] = (TFRGBImg[:,:,1]/255.0)*self.g1 + (1 - (TFRGBImg[:,:,1].astype(int)/255.0))*self.g2
                TFRGBCol[:,:,2] = (TFRGBImg[:,:,2]/255.0)*self.b1 + (1 - (TFRGBImg[:,:,2].astype(int)/255.0))*self.b2
                TFRGBCol[:,:,3] = 255

            else: 
                
                #Colour the image with 3 colours.
                a = ((TFRGBImg[:,:,0]/128)*(TFRGBImg[:,:,0]/255.0))+(abs(TFRGBImg[:,:,0].astype(int)/128 - 1)*(TFRGBImg[:,:,0]/128.0))
                b = ((TFRGBImg[:,:,0]/128)*self.r3)+(abs(TFRGBImg[:,:,0].astype(int)/128 - 1)*self.r2)
                c = 1 - (((TFRGBImg[:,:,0]/128)*(TFRGBImg[:,:,0]/255.0))+(abs(TFRGBImg[:,:,0].astype(int)/128 - 1)*(TFRGBImg[:,:,0]/128.0)))
                d = ((TFRGBImg[:,:,0]/128)*self.r2)+(abs(TFRGBImg[:,:,0].astype(int)/128 - 1)*self.r1)
                TFRGBCol[:,:,0] = (a * b) + (c * d)

                a = ((TFRGBImg[:,:,1]/128)*(TFRGBImg[:,:,1]/255.0))+(abs(TFRGBImg[:,:,1].astype(int)/128 - 1)*(TFRGBImg[:,:,1]/128.0))
                b = ((TFRGBImg[:,:,1]/128)*self.g3)+(abs(TFRGBImg[:,:,1].astype(int)/128 - 1)*self.g2)
                c = 1 - (((TFRGBImg[:,:,1]/128)*(TFRGBImg[:,:,1]/255.0))+(abs(TFRGBImg[:,:,1].astype(int)/128 - 1)*(TFRGBImg[:,:,1]/128.0)))
                d = ((TFRGBImg[:,:,1]/128)*self.g2)+(abs(TFRGBImg[:,:,1].astype(int)/128 - 1)*self.g1)
                TFRGBCol[:,:,1] = (a * b) + (c * d)

                a = ((TFRGBImg[:,:,2]/128)*(TFRGBImg[:,:,2]/255.0))+(abs(TFRGBImg[:,:,2].astype(int)/128 - 1)*(TFRGBImg[:,:,2]/128.0))
                b = ((TFRGBImg[:,:,2]/128)*self.b3)+(abs(TFRGBImg[:,:,2].astype(int)/128 - 1)*self.b2)
                c = 1 - (((TFRGBImg[:,:,2]/128)*(TFRGBImg[:,:,2]/255.0))+(abs(TFRGBImg[:,:,2].astype(int)/128 - 1)*(TFRGBImg[:,:,2]/128.0)))
                d = ((TFRGBImg[:,:,2]/128)*self.b2)+(abs(TFRGBImg[:,:,2].astype(int)/128 - 1)*self.b1)
                TFRGBCol[:,:,2] = (a * b) + (c * d)
                TFRGBCol[:,:,3] = 255

            self.img.setImage(TFRGBCol)
        else:
            self.img.setImage(TFRGBImg)

    def colourInput(self, text):
        colOptions = ["0,0,255 255,0,0", "0,255,0 255,0,0","0,0,255 0,255,0 255,0,0"]
        return QtGui.QInputDialog.getItem(self, "vizEEG", text, colOptions, editable=True)

    #Slider management functions.

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

    """Class for displaying the correlation matrix. If the user clicks Cancel during
       the colour input dialog the matrix shows in gray scale.
    """

    def __init__(self, matData, compWinSize, compWinStep):

        "Initialise the GUI and variables."

        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("vizEEG - Correlation Matrix display")
        root = Tkinter.Tk()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        self.resize(sw/2, sh/2)
#        self.setAttribute(55)
        self.img = pg.ImageView()
        self.setCentralWidget(self.img)
        self.cWSize = compWinSize
        self.cWStep = compWinStep
        self.matData = matData
        self.r3 = None
        colours, self.ok = self.colourInput("Choose a colouring for correlation matrix images or enter a different one in format RRR,GGG,BBB.\nPlease, separate colours (2 or 3) with space.\nIf Cancel is clicked matrix will be displayed in gray scale.")
        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle("vizEEG: Colour Error")

        if self.ok:

            #Parse the user input. 
            parsed = re.findall("\d{0,3},\d{0,3},\d{0,3}", colours)
            if len(parsed) < 2 or len(parsed) > 3:
                self.ok = False
                msgBox.setText("Colours input in an incorrect format.\nPlease, input 2 or 3 colours in format RRR,GGG,BBB separated by space, where RRR or GGG or BBB are numbers in range 0-255.")
                msgBox.exec_()
            else:
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

                #Check if the colours are in the proper format.
                okRange = range(256)
                areColsOk = self.r1 in okRange and self.r2 in okRange and self.g1 in okRange and self.g2 in okRange and self.b1 in okRange and self.b2 in okRange 

                if len(parsed) == 3:
                    areColsOk = areColsOk and self.r3 in okRange and self.g3 in okRange and self.b3 in okRange

                if not areColsOk:
                    self.ok = False
                    msgBox.setText("Colours are out of RGB range. \nPlease, input 2 or 3 colours in format RRR,GGG,BBB separated by space, where RRR or GGG or BBB are numbers in range 0-255.")
                    msgBox.exec_()
        self.show()

    def colourInput(self, text):
        colOptions = ["0,0,255 255,0,0", "0,255,0 255,0,0","0,0,255 0,255,0 255,0,0"]
        return QtGui.QInputDialog.getItem(self, "vizEEG", text, colOptions, editable=True)
        
    def showData(self, slPos):

        "Loads the data into a displaying object."

        temp = slPos - (self.cWSize/2)
        if temp < 0:
            pos = 0
        else:
            if (temp%self.cWStep <= (self.cWStep/2)):
                pos = temp / self.cWStep
            else:
                pos = (temp / self.cWStep) + 1

        #Create the gray scale image.
        matRGB = pg.makeRGBA(self.matData[:,:,pos], levels=[np.amin(self.matData[:,:,pos]), np.amax(self.matData[:,:,pos])])[0]
        if self.ok:

            #Colours the gray scale image with 2 colours.
            matRGBCol = np.zeros(matRGB.shape, dtype=matRGB.dtype)
            if self.r3 is None: 
                matRGBCol[:,:,0] = (matRGB[:,:,0]/255.0)*self.r1 + (1 - (matRGB[:,:,0]/255.0))*self.r2
                matRGBCol[:,:,1] = (matRGB[:,:,1]/255.0)*self.g1 + (1 - (matRGB[:,:,1]/255.0))*self.g2
                matRGBCol[:,:,2] = (matRGB[:,:,2]/255.0)*self.b1 + (1 - (matRGB[:,:,2]/255.0))*self.b2
                matRGBCol[:,:,3] = 255

            else: 

                #Or with 3 colours.
                a = ((matRGB[:,:,0]/128)*(matRGB[:,:,0]/255.0))+(abs(matRGB[:,:,0].astype(int)/128 - 1)*(matRGB[:,:,0]/128.0))
                b = ((matRGB[:,:,0]/128)*self.r3)+(abs(matRGB[:,:,0].astype(int)/128 - 1)*self.r2)
                c = 1 - (((matRGB[:,:,0]/128)*(matRGB[:,:,0]/255.0))+(abs(matRGB[:,:,0].astype(int)/128 - 1)*(matRGB[:,:,0]/128.0)))
                d = ((matRGB[:,:,0]/128)*self.r2)+(abs(matRGB[:,:,0].astype(int)/128 - 1)*self.r1)
                matRGBCol[:,:,0] = (a * b) + (c * d)

                a = ((matRGB[:,:,1]/128)*(matRGB[:,:,1]/255.0))+(abs(matRGB[:,:,1].astype(int)/128 - 1)*(matRGB[:,:,1]/128.0))
                b = ((matRGB[:,:,1]/128)*self.g3)+(abs(matRGB[:,:,1].astype(int)/128 - 1)*self.g2)
                c = 1 - (((matRGB[:,:,1]/128)*(matRGB[:,:,1]/255.0))+(abs(matRGB[:,:,1].astype(int)/128 - 1)*(matRGB[:,:,1]/128.0)))
                d = ((matRGB[:,:,1]/128)*self.g2)+(abs(matRGB[:,:,1].astype(int)/128 - 1)*self.g1)
                matRGBCol[:,:,1] = (a * b) + (c * d)

                a = ((matRGB[:,:,2]/128)*(matRGB[:,:,2]/255.0))+(abs(matRGB[:,:,2].astype(int)/128 - 1)*(matRGB[:,:,2]/128.0))
                b = ((matRGB[:,:,2]/128)*self.b3)+(abs(matRGB[:,:,2].astype(int)/128 - 1)*self.b2)
                c = 1 - (((matRGB[:,:,2]/128)*(matRGB[:,:,2]/255.0))+(abs(matRGB[:,:,2].astype(int)/128 - 1)*(matRGB[:,:,2]/128.0)))
                d = ((matRGB[:,:,2]/128)*self.b2)+(abs(matRGB[:,:,2].astype(int)/128 - 1)*self.b1)
                matRGBCol[:,:,2] = (a * b) + (c * d)
                matRGBCol[:,:,3] = 255

            self.img.setImage(matRGBCol)
        else:
            self.img.setImage(matRGB)

