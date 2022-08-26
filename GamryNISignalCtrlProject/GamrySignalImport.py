__author__ = "Fiavi(Zhaoen) Yang"
#Github: https://github.com/Vast-Horizon/Gamry-Signal-Generator-Python3

from PyQt6 import QtWidgets, uic,QtCore, QtGui
from tkinter import filedialog
from pyqtgraph import PlotWidget
import comtypes
import comtypes.client as client
import gc
import time
from datetime import datetime
import os
import sys
import csv

active = False #Flag
global mode
mode = "Gstat" #default mode is galvanostat
fpath = 'InputProfile_Default.csv' #default name of the signal data file

############################Gamry Classes#################################
class GamryCOMError(Exception):
    pass

def gamry_error_decoder(e):
    if isinstance(e, comtypes.COMError):
        hresult = 2**32+e.args[0]
        if hresult & 0x20000000:
            return GamryCOMError('0x{0:08x}: {1}'.format(2**32+e.args[0], e.args[1]))
    return e
c = 0
class GamryDtaqEvents(object):
    def __init__(self, dtaq):
        self.dtaq = dtaq
        self.acquired_points = [] #This is a list of tuples with 10 columns of measurement data
        
    def cook(self):
        count = 1
        while count > 0:
            count, points = self.dtaq.Cook(32768)
            self.acquired_points.extend(zip(*points))

    def _IGamryDtaqEvents_OnDataAvailable(self, this):
        self.cook()

    def _IGamryDtaqEvents_OnDataDone(self, this):
        self.cook() # final data acquisition 
        time.sleep(1)
        global active
        active = False
        print("DONE ")

############################################################################
class UI(QtWidgets.QMainWindow):
   #Load UI 
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("MainProjectUI.ui", self)
        self.graphicsView.setBackground('w')
        self.graphicsView_2.setBackground('w')
        self.graphicsView_3.setBackground('w')
        #Get current time
        currentDay = datetime.now().day
        currentMonth = datetime.now().month
        currentYear = datetime.now().year
        self.dateEdit.setDateTime(QtCore.QDateTime(QtCore.QDate(currentYear, currentMonth, currentDay), QtCore.QTime(0, 0, 0)))
        self.progressBar.setValue(0)   
        #Check if the default signal file exist
        if os.path.isfile(fpath) == False:
            print("Note: The default signal file"+fpath+"does not appear to exist in current directory.\n Please select an input file.") 
            self.signalPathlabel.setText("Please select an input signal data file")
        else:
            self.signalPathlabel.setText(fpath)
        #Connect buttons with functions
        self.DataFileButton_1.clicked.connect(self.openF)
        self.pushButton.clicked.connect(self.draw)
        self.ClearPushButton.clicked.connect(self.clear)
        self.TestButton.clicked.connect(self.modeSwitcher)
        #Show UI
        self.show()
    
    #Select an Input Signal file
    def openF(self):
        global fpath
        fpath = filedialog.askopenfilename()
        self.signalPathlabel.setText(fpath)

    #Creat Directory to save
    def folderDir(self):
        objname = self.objNameEdit.text()
        temperature = self.TempEdit.text()
        testnum = self.TestNumEdit.text()
        dday = str(self.dateEdit.date().day())
        mmonth = str(self.dateEdit.date().month())
        yyyyear = str(self.dateEdit.date().year())
        subdir = "Test"+testnum+"-"+temperature + "-"+mmonth+"-"+dday+"-"+yyyyear
        cdir = os.getcwd() #Get the current directory
        parent_dir = os.path.join(cdir,objname)
        global outputPath
        outputPath = os.path.join(parent_dir,subdir)
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)
        else:
            pass
  
    #Switch between Gstat and Pstat mode
    def modeSwitcher(self):        
        if self.radioButton.isChecked():
            global mode
            mode = "Gstat"
            self.initializeGstat()
        else:
            mode = "Pstat"
            self.initializePstat()

    #Set up connection with the Gamry instrument in Potentiostat mode
    def initializePstat(self):
        global active
        active=True
        global GamryCOM,pstat,dtaqcpiv,dtaqsink,connection
        GamryCOM=client.GetModule(['{BD962F0D-A990-4823-9CF5-284D1CDD9C6D}', 1, 0])
        devices=client.CreateObject('GamryCOM.GamryDeviceList')
        #Gamry Instrument object
        pstat=client.CreateObject('GamryCOM.GamryPC6Pstat')
        pstat.Init(devices.EnumSections()[0]) 
        #Open
        pstat.Open()
        pstat.SetCtrlMode(GamryCOM.PstatMode)#Set it to Potentiostat mode
        #Data acquisition object cpiv
        dtaqcpiv=client.CreateObject('GamryCOM.GamryDtaqCpiv')
        dtaqcpiv.Init(pstat)
        dtaqsink = GamryDtaqEvents(dtaqcpiv)
        connection = client.GetEvents(dtaqcpiv, dtaqsink)
        print("\n========================================================================")
        print(devices.EnumSections()[0], " Initialization Completed In Potentiostat Mode")  
        self.test()

    #Set up connection with the Gamry instrument in Galvanostat mode
    def initializeGstat(self):
        global active
        active=True
        global GamryCOM,pstat,dtaqciiv,dtaqsink,connection
        GamryCOM=client.GetModule(['{BD962F0D-A990-4823-9CF5-284D1CDD9C6D}', 1, 0])
        devices=client.CreateObject('GamryCOM.GamryDeviceList')
        #Gamry Instrument object
        pstat=client.CreateObject('GamryCOM.GamryPC6Pstat')
        pstat.Init(devices.EnumSections()[0]) 
        #Open
        pstat.Open()
        pstat.SetCtrlMode(GamryCOM.GstatMode)#Set it to galvanostat mode
        #Data acquisition object ciiv
        dtaqciiv=client.CreateObject('GamryCOM.GamryDtaqCiiv')
        dtaqciiv.Init(pstat)
        dtaqsink = GamryDtaqEvents(dtaqciiv)
        connection = client.GetEvents(dtaqciiv, dtaqsink)
        print("\n========================================================================")
        print(devices.EnumSections()[0], " Initialization Completed In Galvanostat Mode")  
        self.test()
    
    #To close
    def toclose(self):
            pstat.SetCell(GamryCOM.CellOff)
            pstat.Close()
            gc.collect()

    #To test    
    def test(self):
        #Prepare parameters
        amp = float(self.ampInput.text())
        global numOfPoints, PointsList
        try:
            f = open(fpath)
            self.IndicatorLabel.setStyleSheet("QLabel {background-color: rgb(255,224,102);border: 1.5px inset gray;border-radius: 8px;}")
            PointsList = f.readlines()
            numOfPoints = len(PointsList)
            PointsList = [float(i)*amp for i in PointsList]
        except (NameError, IOError): #If error, stop test()
            print("Error - No Input Signal file Is Selected or the file does not appear to exist.") 
            self.signalPathlabel.setText("Error - No Signal Profile Is Selected")
            self.toclose()
            return False

        Cycles = int(self.spinBox.text())
        temprate = float(numOfPoints/(int(self.FrequencyInput.text())*1000)/numOfPoints)
        temprate = round(temprate,8)
        SampleRate = temprate
        Sig=client.CreateObject('GamryCOM.GamrySignalArray')
        if mode == "Gstat":
            Sig.Init(pstat, Cycles, SampleRate, numOfPoints, PointsList, GamryCOM.GstatMode)
        elif mode == "Pstat":
            Sig.Init(pstat, Cycles, SampleRate, numOfPoints, PointsList, GamryCOM.PstatMode)
        pstat.SetSignal(Sig)

        #Print out information
        print("###################################################")
        print("Number of Data Points of each period: ", numOfPoints)
        print("Number of Cycles: ", Cycles)
        print("Time gap between each output data point in second: ", SampleRate)
        runTime = SampleRate*Cycles*numOfPoints
        print("Estimated total signal length in second: ", runTime)
        print("Frequcency of data point outputing in Hz: ", 1/SampleRate) 
        print("###################################################")
        pstat.SetCell(GamryCOM.CellOn)
        
        #Make it to run
        try:
            if mode == "Gstat":            
                dtaqciiv.Run(True)
            elif mode == "Pstat":
                dtaqcpiv.Run(True)
            print("Running...")
        except Exception as e:
            raise gamry_error_decoder(e)
        prograssList = []
        counter = 0
        while active == True:
            client.PumpEvents(1)
            time.sleep(0.1)
            counter+=1
            prograssList.append(counter)
            if self.progressBar.value() >= 30:
                self.progressBar.setValue(29)
            else:
                self.progressBar.setValue(counter)
 
        #Turn off
        while active == False: 
            self.progressBar.setValue(30)  
            self.clear()
            self.draw()
            print("Terminating...")
            print("Total Number of Output Data Points Detected: ", len(dtaqsink.acquired_points))
            self.toclose()  
            try:
                f.close()
                break

            except (NameError, IOError):
                pass
        self.progressBar.setValue(0)

        #Save Raw Data to the directory
        self.folderDir()
        testnum = self.TestNumEdit.text()
        cellID = self.IDEdit.text()
        model = self.objNameEdit.text()
        subdir = outputPath+"\Test"+testnum +"-Object"+cellID+"-"+model+".csv"
        rawDataList = []
        #titleList = ["Time(s)","Input","Measur. V(V)","Uncompens. V","Measur. I(A)","Vsig","Aux Input","IE Range","Overload Info","Stop","Temp"]
        titleList = ["Time(s)","Input","Measur. V(V)","Measur. I(A)"]
        c=0
        with open(subdir, 'w') as file_handler:
            writer = csv.writer(file_handler)
            writer.writerow(titleList)
            #convert a list of tuples to a list of strings, note: 
                #dtaqsink.acquired_points is a list of tuples
                #item is a list of string lists
                #rawDataList is a list of strings, and stritem is string
            for item in dtaqsink.acquired_points:
                item = [item[i] for i in (0,1,3)] #delete or comment out this line to save all data
                item.insert(1,PointsList[c])#insert input signal list to the first column
                c+=1
                rawDataList.append(','.join([str(j) for j in item])) 
            for stritem in rawDataList:
                 file_handler.write("{}\n".format(stritem))#write the string
        print("Data file ",subdir," is saved")
        print("END")
    
    #Process acquired_points list to plot
    def draw(self):
        timeList = [x[0] for x in dtaqsink.acquired_points]
        voltsList = [x[1] for x in dtaqsink.acquired_points]
        currentList = [x[3] for x in dtaqsink.acquired_points]         
        timeList = [float(i) for i in timeList]
        voltsList = [float(j) for j in voltsList]
        currentList = [float(j) for j in currentList]
        self.graphicsView.plot(timeList,PointsList,pen=(10,10,200))
        self.graphicsView_2.plot(timeList,currentList,pen=(10,10,200))
        self.graphicsView_3.plot(timeList,voltsList,pen=(10,10,200))
        self.IndicatorLabel.setStyleSheet("QLabel {background-color: rgb(50,200,50);border: 1.5px inset gray;border-radius: 8px;}")
    
    #Clear plots
    def clear(self):
        self.graphicsView.clear()
        self.graphicsView_2.clear()
        self.graphicsView_3.clear()

def mainfunc():
    app = QtWidgets.QApplication(sys.argv)
    ui = UI()
    sys.exit(app.exec())