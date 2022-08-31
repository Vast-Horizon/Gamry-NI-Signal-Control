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
        global scale, writing_dev_name, reading_dev_name, num_of_channels_read, num_of_channels_write    
        scale = float(self.ampInput.text())
        writing_dev_name = self.wrtname_edit.text()
        reading_dev_name = self.readname_edit.text()
        num_of_channels_read = int(self.InChannelNumspinBox.text())
        num_of_channels_write = int(self.outChannelNumspinBox.text())
        self.test()

    #Creat Directory to save
    def folderDir(self):
        objname = self.objNameEdit.text()
        condition = self.conditionEdit.text()
        Temp = self.TempEdit.text()
        subdir = "Temp"+Temp+" "+condition
        cdir = os.getcwd() #Get the current directory
        parent_dir = os.path.join(cdir,objname)
        global outputPath
        outputPath = os.path.join(parent_dir,subdir)
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)
        else:
            pass

    def openF(self):
        global scale, ideal_signal, ideal_time, timeout_estimation, num_of_samples,buffer_signal
        csv_file_user = filedialog.askopenfilename()
        
        #defining the buffer in the system
        global buffer_length, buffer_signal, fs
        fs = float(self.FrequencyInput.text())
        buffer_length = int(fs/5) 
        buffer_signal = np.zeros(buffer_length)

        #importing the csv file 
        #csv_file_user = input("Input the csv file path: ") #------ User Input-----------#
        path_csv = os.path.abspath(csv_file_user) 
        df = pd.read_csv(path_csv) 

        #converting csv file's data into a numpy array
        csv_data = df.to_numpy()
        scale = float(self.ampInput.text())
        csv_signal = scale*csv_data[:,1]
        ideal_signal = np.concatenate((buffer_signal, csv_signal, buffer_signal))
        num_of_samples = len(ideal_signal)

        #adding a timeout estimation
        ideal_time = np.arange(0.0, (num_of_samples)/fs, 1.0/fs)
        ideal_time = np.transpose(ideal_time)
        timeout_estimation = int(num_of_samples/fs) + 1
        self.clear()
        self.draw()

    #performing data acquisition
    def test(self):
        print("DONE0")
        header_Official = ['Time']
        with nidaqmx.Task() as task_write, nidaqmx.Task() as task_read: 
            #adding the analog channels to read/write to the task
            if self.CheckBox_out_1.isChecked():
                temp_str = self.wrtname_edit.text() + "/aO0"
                print(temp_str)
                task_write.ao_channels.add_ao_voltage_chan(temp_str)        
            if self.CheckBox_out_2.isChecked():
                temp_str = self.wrtname_edit.text() + "/aO1"
                task_write.ao_channels.add_ao_voltage_chan(temp_str)
            if self.CheckBox_out_3.isChecked():
                temp_str = self.wrtname_edit.text() + "/aO2"
                task_write.ao_channels.add_ao_voltage_chan(temp_str)
            if self.CheckBox_out_4.isChecked():
                temp_str = self.wrtname_edit.text() + "/aO3"
                task_write.ao_channels.add_ao_voltage_chan(temp_str)
            if self.CheckBox_out_5.isChecked():
                temp_str = self.wrtname_edit.text() + "/aO4"
                task_write.ao_channels.add_ao_voltage_chan(temp_str)

            if self.CheckBox_in_1.isChecked():
                header_Official.append(self.INdevname_1.text())
                temp_str = self.readname_edit.text() + "/ai0"
                print(temp_str)
                task_read.ai_channels.add_ai_voltage_chan(temp_str)
            if self.CheckBox_in_2.isChecked():
                header_Official.append(self.INdevname_2.text())
                temp_str = self.readname_edit.text() + "/ai1"
                task_read.ai_channels.add_ai_voltage_chan(temp_str)
            if self.CheckBox_in_3.isChecked():
                header_Official.append(self.INdevname_3.text())
                temp_str = self.readname_edit.text() + "/ai2"
                task_read.ai_channels.add_ai_voltage_chan(temp_str)
            if self.CheckBox_in_4.isChecked():
                header_Official.append(self.INdevname_4.text())
                temp_str = self.readname_edit.text() + "/ai3"
                task_read.ai_channels.add_ai_voltage_chan(temp_str)
            if self.CheckBox_in_5.isChecked():
                header_Official.append(self.INdevname_5.text())
                temp_str = self.readname_edit.text() + "/ai4"
                task_read.ai_channels.add_ai_voltage_chan(temp_str)

            print("DONE1")        
            #specifying the timing, this is done by making it finite, rate being the user input, samples per channel is the calculation given from the time the user wanted
            task_read.timing.cfg_samp_clk_timing(rate = fs, sample_mode = nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan= num_of_samples)
            task_write.timing.cfg_samp_clk_timing(rate = fs, sample_mode = nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan= num_of_samples)
            
            reader = AnalogMultiChannelReader(task_read.in_stream)
            writer = AnalogSingleChannelWriter(task_write.out_stream)
            
            writer.write_many_sample(ideal_signal, timeout = timeout_estimation)
            output = np.zeros([num_of_channels_read, num_of_samples])
            print(np.shape(output))
            task_write.start()
            task_read.start()
            reader.read_many_sample(data = output, timeout = timeout_estimation)
            task_write.stop()
            task_read.stop()
            print("DONE2")
        
        #combining data array
        global final_write_data
        final_write_data = np.column_stack((ideal_time, np.transpose(output)))

        #save output files
        self.folderDir()#get the path of the output folder
        testnum = self.TestNumEdit.text()
        temp = self.TempEdit.text()
        cellID = self.IDEdit.text()
        condition = self.conditionEdit.text()
        dday = str(self.dateEdit.date().day())
        mmonth = str(self.dateEdit.date().month())
        yyear = str(self.dateEdit.date().year())
        yyear = yyear[-2:]
        datafileout = outputPath+"\Test"+testnum +"ID"+cellID+"Temp"+temp+condition+mmonth+dday+yyear+".csv"
        pd.DataFrame(final_write_data).to_csv(datafileout, header=header_Official) #------ User Input-----------#
        nidaqmx.system._collections.device_collection.DeviceCollection.device_names
    
    def draw(self):
        self.graphicsView.plot(ideal_time,ideal_signal,pen=(10,10,200))
    
    #Clear plots
    def clear(self):
        self.graphicsView.clear()

def mainfunc():
    app = QtWidgets.QApplication(sys.argv)
    ui = UI()
    sys.exit(app.exec())