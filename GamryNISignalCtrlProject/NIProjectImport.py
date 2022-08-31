# -*- coding: utf-8 -*-
"""
Created on Thu Aug 25 11:43:42 2022

@author: kawad
"""
#importing libraries 
import nidaqmx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.stream_writers import AnalogSingleChannelWriter
import sys
import os
from PyQt6 import QtWidgets, uic,QtCore, QtGui
from tkinter import filedialog
from pyqtgraph import PlotWidget
import time
from datetime import datetime

class UI(QtWidgets.QMainWindow):
   #Load UI 
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("NIprojectUI.ui", self)
        self.graphicsView.setBackground('w')
        self.graphicsView_2.setBackground('w')
        self.graphicsView_3.setBackground('w')
        self.graphicsView_4.setBackground('w')
        #Get current time
        currentDay = datetime.now().day
        currentMonth = datetime.now().month
        currentYear = datetime.now().year
        self.dateEdit.setDateTime(QtCore.QDateTime(QtCore.QDate(currentYear, currentMonth, currentDay), QtCore.QTime(0, 0, 0)))
        #Connect buttons with functions
        self.DataFileButton_1.clicked.connect(self.openF)
        self.pushButton.clicked.connect(self.draw)
        self.ClearPushButton.clicked.connect(self.clear)
        self.TestButton.clicked.connect(self.readinput)
        #Show UI
        self.show()

    def readinput(self):
        #sampling frequency and defined
        global fs, scale, writing_dev_name, reading_dev_name, num_of_channels_read, num_of_channels_write
        fs = float(self.FrequencyInput.text())
        scale = float(self.ampInput.text())
        writing_dev_name = self.INdevname_1.text()
        reading_dev_name = self.Outdevname_1.text()
        num_of_channels_read = int(self.InChannelNumspinBox.text())
        num_of_channels_write = int(self.OutChannelNumspinBox.text())
        # fs = float(input("Input the sampling frequency: ")) #------ User Input-----------#
        # scale = float(input("Input the scaling factor: ")) #------ User Input-----------#
        # writing_dev_name = input("Input the device's name that will be writing the data (ex. cDAQ1MOD1): ") #------ User Input-----------#
        # reading_dev_name = input("Input the device's name that will be reading the data (ex. cDAQ1MOD1): ") #------ User Input-----------#
        # num_of_channels_read = int(input("Input number of measurement channels: "))#------ User Input-----------#
        # num_of_channels_write = int(input("Input number of writing channels: ")) #------ User Input-----------#
        #add a check box of the user channel inputs with a name beside it and what device this corresponds too

        #defining the buffer in the system
        global buffer_length, buffer_signal
        buffer_length = int(fs/5) 
        buffer_signal = np.zeros(buffer_length)
        self.test()

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

    def openF(self):
        global ideal_signal, ideal_time, timeout_estimation, num_of_samples
        csv_file_user = filedialog.askopenfilename()
        
        #importing the csv file 
        #csv_file_user = input("Input the csv file path: ") #------ User Input-----------#
        path_csv = os.path.abspath(csv_file_user) 
        df = pd.read_csv(path_csv) 

        #converting csv file's data into a numpy array
        csv_data = df.to_numpy()
        csv_signal = scale*csv_data[:,1]
        ideal_signal = np.concatenate((buffer_signal, csv_signal, buffer_signal))
        num_of_samples = len(ideal_signal)

        #adding a timeout estimation
        ideal_time = np.arange(0.0, (num_of_samples)/fs, 1.0/fs)
        ideal_time = np.transpose(ideal_time)
        timeout_estimation = int(num_of_samples/fs) + 1

    #performing data acquisition
    def test(self):
        with nidaqmx.Task() as task_write, nidaqmx.Task() as task_read: 
            #adding the analog channels to read/write to the task
            task_write.ao_channels.add_ao_voltage_chan("cDAQ1Mod1/ao0")#------ User Input-----------#
            task_read.ai_channels.add_ai_voltage_chan("cDAQ2Mod1/ai0") #------ User Input-----------#
            task_read.ai_channels.add_ai_voltage_chan("cDAQ2Mod1/ai1") #------ User Input-----------#
            task_read.ai_channels.add_ai_voltage_chan("cDAQ2Mod1/ai2") #------ User Input-----------#
            
            #specifying the timing, this is done by making it finite, rate being the user input, samples per channel is the calculation given from the time the user wanted
            task_read.timing.cfg_samp_clk_timing(rate = fs, sample_mode = nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan= num_of_samples)
            task_write.timing.cfg_samp_clk_timing(rate = fs, sample_mode = nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan= num_of_samples)
            
            reader = AnalogMultiChannelReader(task_read.in_stream)
            writer = AnalogSingleChannelWriter(task_write.out_stream)
            
            writer.write_many_sample(ideal_signal, timeout = timeout_estimation)
            task_write.start()
            task_read.start()
            output = np.zeros([num_of_channels_read, num_of_samples])
            reader.read_many_sample(data = output, timeout = timeout_estimation)
            task_write.stop()
            task_read.stop()
        
        #combining data array
        final_write_data = np.column_stack((ideal_time, np.transpose(output)))

        pd.DataFrame(final_write_data).to_csv('C:\\Users\\kawad\\Desktop\\Measured_Data.csv', header=['Time', 'AI0', 'AI1', 'AI2']) #------ User Input-----------#
        nidaqmx.system._collections.device_collection.DeviceCollection.device_names
    
    def draw(self):
        pass
        # self.graphicsView.plot(timeList,PointsList,pen=(10,10,200))
        # self.graphicsView_2.plot(timeList,currentList,pen=(10,10,200))
        # self.graphicsView_3.plot(timeList,voltsList,pen=(10,10,200))
     
    
    #Clear plots
    def clear(self):
        self.graphicsView.clear()
        self.graphicsView_2.clear()
        self.graphicsView_3.clear()
        self.graphicsView_4.clear()

def mainfunc():
    app = QtWidgets.QApplication(sys.argv)
    ui = UI()
    sys.exit(app.exec())