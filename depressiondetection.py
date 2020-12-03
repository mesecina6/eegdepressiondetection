# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'depressiondetection.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

import sys

from PyQt5 import QtCore, QtGui, QtWidgets
import mne 
import numpy as np
import pandas as pd 
import scipy
import numpy
import pickle 

def get_features (x):
    #reading edf files 
    raw = mne.io.read_raw_edf (x, preload=True, stim_channel='auto', verbose=False)
    fs = 256
    
    #bandwidth filtering 
    f_l=0.5
    f_h=60.0
    raw.filter(f_l, f_h, fir_design='firwin', skip_by_annotation='edge')
   
    #notch filtering
    raw.notch_filter(50)
 
      #no need in final thesis
   # ica = mne.preprocessing.ICA(n_components =15, random_state=97, max_iter=800)
   # ica.fit(raw)
   # raw.load_data()
   # ica.exclude = [0,1,2,3]
   # ica.apply(raw)
    
    # function for normalization of the signal 
    def normalize(eeg, level):
        amp_new = 10**(level / 20)
        amp_max = np.max(np.abs(eeg))
        return amp_new * eeg / amp_max
    #function for bandpower calculaiton 
    
    data = raw.get_data()
    channels = raw.ch_names
    data = data.transpose()
    df = pd.DataFrame(data = data, columns = channels)
    F3 = normalize(df['EEG F3-LE'].values, 0)
    F4 = normalize(df['EEG F4-LE'].values, 0)
  
    
    def bandpower(x, fs, fmin, fmax):
        f, Pxx = scipy.signal.welch(x, fs=fs,window='hann', nperseg=4*fs)
        ind_min = numpy.argmax(f > fmin) - 1
        ind_max = numpy.argmax(f > fmax) - 1
        return numpy.trapz(Pxx[ind_min: ind_max], f[ind_min: ind_max])
    
    def totalpower(x, fs):
        f, Pxx = scipy.signal.welch(x, fs=fs,window='hann', nperseg=4*fs)
        return numpy.trapz(Pxx, f)
    
    def spectral_entropy (x, fs):
        _, psd = scipy.signal.welch(x, fs=fs,window='hann', nperseg=4*fs)
        psd_norm = np.divide(psd, psd.sum())
        se = -np.multiply(psd_norm, np.log2(psd_norm)).sum()
        se /= np.log2(psd_norm.size)
        return se 
    
    def mean_psd (x, fs):
        _,  psd = scipy.signal.welch(x, fs=fs,window='hann', nperseg=4*fs)
        mps = np.mean(psd)
        return mps

    out = pd.DataFrame()
    n_win = 30*fs
    n_hop = n_win//2
    pos = 0 
    while  (pos<=F3.size-n_win):
        
        frameF3= F3[pos:pos+n_win]
        frameF4= F4[pos:pos+n_win]
        
        F3_pow_delta_abs = bandpower(frameF3, fs, 0.5, 4)
        F4_pow_delta_abs = bandpower(frameF4, fs, 0.5, 4)
        
        F3_pow_teta_abs = bandpower(frameF3, fs, 4, 8)
        F4_pow_teta_abs = bandpower(frameF4, fs, 4, 8)
        
        F3_pow_alfa_abs = bandpower(frameF3, fs, 8, 13)
        F4_pow_alfa_abs = bandpower(frameF4, fs, 8, 13)
        
        F3_pow_beta_abs = bandpower(frameF3, fs, 13, 32)
        F4_pow_beta_abs = bandpower(frameF4, fs, 13, 32)
        
        F3_pow_gama_abs = bandpower(frameF3, fs, 32, 60)
        F4_pow_gama_abs = bandpower(frameF4, fs, 32, 60)
        
        F3_pow_tot = totalpower(frameF3, fs)
        F4_pow_tot = totalpower(frameF4, fs)
        
        F3_pow_delta_rel = F3_pow_delta_abs/ F3_pow_tot 
        F4_pow_delta_rel =  F4_pow_delta_abs/F4_pow_tot 
        
        F3_pow_teta_rel = F3_pow_teta_abs/ F3_pow_tot
        F4_pow_teta_rel = F4_pow_teta_abs/ F4_pow_tot
        
        F3_pow_alfa_rel = F3_pow_alfa_abs/ F3_pow_tot
        F4_pow_alfa_rel = F4_pow_alfa_abs/ F4_pow_tot
        
        F3_pow_beta_rel = F3_pow_beta_abs/ F3_pow_tot
        F4_pow_beta_rel = F4_pow_beta_abs/ F4_pow_tot
        
        F3_pow_gama_rel = F3_pow_gama_abs/ F3_pow_tot
        F4_pow_gama_rel = F4_pow_gama_abs/ F4_pow_tot
        
        se_F3 = spectral_entropy(frameF3, fs)
        se_F4 = spectral_entropy(frameF4, fs)
        
        mpsd_F3 = mean_psd (frameF3, fs)
        mpsd_F4 = mean_psd (frameF4, fs)
        
        alpha = np.log((F4_pow_alfa_abs/F3_pow_alfa_abs))
        
        pom = pd.DataFrame([F3_pow_delta_abs, F4_pow_delta_abs, 
                  F3_pow_teta_abs,  F4_pow_teta_abs, 
                  F3_pow_alfa_abs, F4_pow_alfa_abs,
                  F3_pow_beta_abs, F4_pow_beta_abs, 
                  F3_pow_gama_abs,  F4_pow_gama_abs, 
                  F3_pow_tot,  F4_pow_tot, 
                  F3_pow_delta_rel, F4_pow_delta_rel, 
                  F3_pow_teta_rel,  F4_pow_teta_rel, 
                  F3_pow_alfa_rel, F4_pow_alfa_rel,
                  F3_pow_beta_rel, F4_pow_beta_rel, 
                  F3_pow_gama_rel,  F4_pow_gama_rel,
                  mpsd_F3, mpsd_F4,
                  se_F3, se_F4,
                  alpha])
        
        pom = pom.T
        out = out.append(pom, ignore_index=True) 
        pos = pos + n_hop

    return out

def depression_predict (df, pom):
    df=pd.concat([df,pom])
    df=df.T
    df.columns=(['EC', 'EO', 'TASK',
                 'F3_pow_delta_abs', 'F4_pow_delta_abs', 
                  'F3_pow_teta_abs', 'F4_pow_teta_abs', 
                  'F3_pow_alfa_abs', 'F4_pow_alfa_abs',
                  'F3_pow_beta_abs', 'F4_pow_beta_abs', 
                  'F3_pow_gama_abs', 'F4_pow_gama_abs', 
                  'F3_pow_tot',  'F4_pow_tot', 
                  'F3_pow_delta_rel', 'F4_pow_delta_rel', 
                  'F3_pow_teta_rel',  'F4_pow_teta_rel', 
                  'F3_pow_alfa_rel', 'F4_pow_alfa_rel',
                  'F3_pow_beta_rel', 'F4_pow_beta_rel', 
                  'F3_pow_gama_rel',  'F4_pow_gama_rel',
                  'mpsd_F3', 'mpsd_F4',
                  'se_F3', 'se_F4',
                  'alpha'])
    return df



class Ui_DepressionDetect(object):
    def setupUi(self, DepressionDetect):
     
        

        DepressionDetect.setObjectName("DepressionDetect")
        DepressionDetect.resize(950, 400)
        self.centralwidget = QtWidgets.QWidget(DepressionDetect)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(250, 50, 700, 100))
        font = QtGui.QFont()
        font.setFamily("Goudy Old Style")
        font.setPointSize(30)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(220, 150, 545, 91))
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(self.widget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.plainTextEdit0 = QtWidgets.QPlainTextEdit(self.widget)
        self.plainTextEdit0.setObjectName("plainTextEdit")
        self.horizontalLayout.addWidget(self.plainTextEdit0)
        self.Browse = QtWidgets.QPushButton(self.widget)
        self.Browse.setObjectName("Browse")
        self.horizontalLayout.addWidget(self.Browse)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_4 = QtWidgets.QLabel(self.widget)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_3.addWidget(self.label_4)
        self.comboBox = QtWidgets.QComboBox(self.widget)
        self.comboBox.setObjectName("comboBox")
        self.horizontalLayout_3.addWidget(self.comboBox)
        self.horizontalLayout_4.addLayout(self.horizontalLayout_3)
        self.Detect = QtWidgets.QPushButton(self.widget)
        self.Detect.setObjectName("Detect")
        self.horizontalLayout_4.addWidget(self.Detect)
        self.horizontalLayout_5.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_3 = QtWidgets.QLabel(self.widget)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.plainTextEdit = QtWidgets.QPlainTextEdit(self.widget)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.horizontalLayout_2.addWidget(self.plainTextEdit)
        self.horizontalLayout_5.addLayout(self.horizontalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        DepressionDetect.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(DepressionDetect)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 723, 26))
        self.menubar.setObjectName("menubar")
        DepressionDetect.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(DepressionDetect)
        self.statusbar.setObjectName("statusbar")
        DepressionDetect.setStatusBar(self.statusbar)
 #       self.plainTextEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
  #                                               QtWidgets.QSizePolicy.Expanding))
       
     
        self.retranslateUi(DepressionDetect)
        QtCore.QMetaObject.connectSlotsByName(DepressionDetect)
          

    def retranslateUi(self, DepressionDetect):
        _translate = QtCore.QCoreApplication.translate
        DepressionDetect.setWindowTitle(_translate("DepressionDetect", "Depression Detection"))
        self.label.setText(_translate("DepressionDetect", "Depression Detection "))
        self.label_2.setText(_translate("DepressionDetect", "File :"))
        self.Browse.setText(_translate("DepressionDetect", "Browse"))
        self.label_4.setText(_translate("DepressionDetect", "State :"))
        self.Detect.setText(_translate("DepressionDetect", "Detect"))
        self.label_3.setText(_translate("DepressionDetect", "Results:"))
        self.Browse.clicked.connect(self.BrowseHandler)
        self.comboBox.addItem("Eyes Open")
        self.comboBox.addItem("Eyes Closed")
        self.comboBox.addItem("Task")
        
    
    def BrowseHandler(self):
        self.open_dialog_box()
        self.plainTextEdit.clear()
        
    def open_dialog_box(self):
        filename =  QtWidgets.QFileDialog.getOpenFileName()
        file = filename[0] 
        self.plainTextEdit0.appendPlainText(file)
        self.pom = pd.DataFrame()
        self.pom = get_features(file)
        self.pom = self.pom.mean()
        self.Detect.clicked.connect( self.DetectHandler)
      
    def DetectHandler(self):
        
        if self.comboBox.currentText() == "Eyes Closed" :
            df=pd.DataFrame([1,0,0])
            
        elif (self.comboBox.currentText() == "Eyes Open") :
             df=pd.DataFrame([0,1,0])
            
        elif (self.comboBox.currentText() == "Task") :
             df=pd.DataFrame([0,0,1])
             
        df= depression_predict(df, self.pom)
        model = pickle.load(open('bestRFmodel.sav', 'rb'))
        prediction=model.predict(df)
        
        if prediction == 0:
            self.plainTextEdit.appendPlainText("NOT DEPRESSED")
        elif prediction == 1:
            self.plainTextEdit.appendPlainText("DEPRESSED")
        
        
        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    DepressionDetect = QtWidgets.QMainWindow()
    ui = Ui_DepressionDetect()
    ui.setupUi(DepressionDetect)
    DepressionDetect.show()
    sys.exit(app.exec_())
        