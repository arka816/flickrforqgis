# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Users\arka\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\flickr\flickr_dialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_FlickrDialogBase(object):
    def setupUi(self, FlickrDialogBase):
        FlickrDialogBase.setObjectName("FlickrDialogBase")
        FlickrDialogBase.resize(780, 668)
        self.label = QtWidgets.QLabel(FlickrDialogBase)
        self.label.setGeometry(QtCore.QRect(10, 15, 121, 21))
        self.label.setObjectName("label")
        self.apiKey = QtWidgets.QLineEdit(FlickrDialogBase)
        self.apiKey.setGeometry(QtCore.QRect(142, 10, 241, 31))
        self.apiKey.setObjectName("apiKey")
        self.groupBox = QtWidgets.QGroupBox(FlickrDialogBase)
        self.groupBox.setGeometry(QtCore.QRect(10, 50, 371, 121))
        self.groupBox.setObjectName("groupBox")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(10, 40, 81, 31))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(10, 85, 81, 21))
        self.label_3.setObjectName("label_3")
        self.dbFileName = QtWidgets.QLineEdit(self.groupBox)
        self.dbFileName.setGeometry(QtCore.QRect(100, 40, 221, 31))
        self.dbFileName.setObjectName("dbFileName")
        self.dbFilePicker = QtWidgets.QPushButton(self.groupBox)
        self.dbFilePicker.setGeometry(QtCore.QRect(330, 40, 31, 31))
        self.dbFilePicker.setObjectName("dbFilePicker")
        self.tableName = QtWidgets.QLineEdit(self.groupBox)
        self.tableName.setGeometry(QtCore.QRect(100, 80, 261, 31))
        self.tableName.setObjectName("tableName")
        self.groupBox_2 = QtWidgets.QGroupBox(FlickrDialogBase)
        self.groupBox_2.setGeometry(QtCore.QRect(400, 100, 371, 141))
        self.groupBox_2.setObjectName("groupBox_2")
        self.groupBox_3 = QtWidgets.QGroupBox(self.groupBox_2)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 30, 171, 101))
        self.groupBox_3.setObjectName("groupBox_3")
        self.label_4 = QtWidgets.QLabel(self.groupBox_3)
        self.label_4.setGeometry(QtCore.QRect(10, 22, 51, 31))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.groupBox_3)
        self.label_5.setGeometry(QtCore.QRect(10, 60, 51, 31))
        self.label_5.setObjectName("label_5")
        self.north = QtWidgets.QLineEdit(self.groupBox_3)
        self.north.setGeometry(QtCore.QRect(100, 30, 61, 20))
        self.north.setObjectName("north")
        self.south = QtWidgets.QLineEdit(self.groupBox_3)
        self.south.setGeometry(QtCore.QRect(100, 70, 61, 20))
        self.south.setObjectName("south")
        self.groupBox_4 = QtWidgets.QGroupBox(self.groupBox_2)
        self.groupBox_4.setGeometry(QtCore.QRect(190, 30, 171, 101))
        self.groupBox_4.setObjectName("groupBox_4")
        self.label_6 = QtWidgets.QLabel(self.groupBox_4)
        self.label_6.setGeometry(QtCore.QRect(10, 22, 51, 31))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.groupBox_4)
        self.label_7.setGeometry(QtCore.QRect(10, 60, 51, 31))
        self.label_7.setObjectName("label_7")
        self.east = QtWidgets.QLineEdit(self.groupBox_4)
        self.east.setGeometry(QtCore.QRect(100, 30, 61, 20))
        self.east.setObjectName("east")
        self.west = QtWidgets.QLineEdit(self.groupBox_4)
        self.west.setGeometry(QtCore.QRect(100, 70, 61, 20))
        self.west.setObjectName("west")
        self.startButton = QtWidgets.QPushButton(FlickrDialogBase)
        self.startButton.setGeometry(QtCore.QRect(10, 600, 181, 31))
        self.startButton.setObjectName("startButton")
        self.stopButton = QtWidgets.QPushButton(FlickrDialogBase)
        self.stopButton.setGeometry(QtCore.QRect(200, 600, 181, 31))
        self.stopButton.setObjectName("stopButton")
        self.progressBar = QtWidgets.QProgressBar(FlickrDialogBase)
        self.progressBar.setGeometry(QtCore.QRect(10, 640, 761, 23))
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.logBox = QtWidgets.QTextBrowser(FlickrDialogBase)
        self.logBox.setGeometry(QtCore.QRect(10, 340, 761, 201))
        self.logBox.setObjectName("logBox")
        self.startDate = QtWidgets.QDateEdit(FlickrDialogBase)
        self.startDate.setGeometry(QtCore.QRect(90, 200, 131, 31))
        self.startDate.setObjectName("startDate")
        self.endDate = QtWidgets.QDateEdit(FlickrDialogBase)
        self.endDate.setGeometry(QtCore.QRect(90, 250, 131, 31))
        self.endDate.setObjectName("endDate")
        self.label_8 = QtWidgets.QLabel(FlickrDialogBase)
        self.label_8.setGeometry(QtCore.QRect(10, 200, 61, 31))
        self.label_8.setObjectName("label_8")
        self.label_9 = QtWidgets.QLabel(FlickrDialogBase)
        self.label_9.setGeometry(QtCore.QRect(10, 250, 51, 31))
        self.label_9.setObjectName("label_9")
        self.groupBox_5 = QtWidgets.QGroupBox(FlickrDialogBase)
        self.groupBox_5.setGeometry(QtCore.QRect(400, 10, 371, 80))
        self.groupBox_5.setObjectName("groupBox_5")
        self.csvFileName = QtWidgets.QLineEdit(self.groupBox_5)
        self.csvFileName.setGeometry(QtCore.QRect(100, 40, 221, 31))
        self.csvFileName.setObjectName("csvFileName")
        self.csvFilePicker = QtWidgets.QPushButton(self.groupBox_5)
        self.csvFilePicker.setGeometry(QtCore.QRect(330, 40, 31, 31))
        self.csvFilePicker.setObjectName("csvFilePicker")
        self.label_10 = QtWidgets.QLabel(self.groupBox_5)
        self.label_10.setGeometry(QtCore.QRect(10, 40, 81, 31))
        self.label_10.setObjectName("label_10")
        self.removeVectorLayer = QtWidgets.QPushButton(FlickrDialogBase)
        self.removeVectorLayer.setGeometry(QtCore.QRect(400, 600, 181, 31))
        self.removeVectorLayer.setObjectName("removeVectorLayer")
        self.closeImages = QtWidgets.QPushButton(FlickrDialogBase)
        self.closeImages.setGeometry(QtCore.QRect(590, 600, 181, 31))
        self.closeImages.setObjectName("closeImages")
        self.saveLogCheck = QtWidgets.QCheckBox(FlickrDialogBase)
        self.saveLogCheck.setGeometry(QtCore.QRect(10, 550, 231, 41))
        self.saveLogCheck.setObjectName("saveLogCheck")
        self.outputDirName = QtWidgets.QLineEdit(FlickrDialogBase)
        self.outputDirName.setGeometry(QtCore.QRect(540, 260, 191, 31))
        self.outputDirName.setObjectName("outputDirName")
        self.outputDirPicker = QtWidgets.QPushButton(FlickrDialogBase)
        self.outputDirPicker.setGeometry(QtCore.QRect(740, 260, 31, 31))
        self.outputDirPicker.setObjectName("outputDirPicker")
        self.label_11 = QtWidgets.QLabel(FlickrDialogBase)
        self.label_11.setGeometry(QtCore.QRect(400, 260, 141, 31))
        self.label_11.setObjectName("label_11")
        self.saveImages = QtWidgets.QCheckBox(FlickrDialogBase)
        self.saveImages.setGeometry(QtCore.QRect(400, 300, 171, 31))
        self.saveImages.setObjectName("saveImages")

        self.retranslateUi(FlickrDialogBase)
        QtCore.QMetaObject.connectSlotsByName(FlickrDialogBase)

    def retranslateUi(self, FlickrDialogBase):
        _translate = QtCore.QCoreApplication.translate
        FlickrDialogBase.setWindowTitle(_translate("FlickrDialogBase", "Flickr"))
        self.label.setText(_translate("FlickrDialogBase", "Flickr API key"))
        self.groupBox.setTitle(_translate("FlickrDialogBase", "Choose Table"))
        self.label_2.setText(_translate("FlickrDialogBase", "Database"))
        self.label_3.setText(_translate("FlickrDialogBase", "Table"))
        self.dbFilePicker.setText(_translate("FlickrDialogBase", "..."))
        self.groupBox_2.setTitle(_translate("FlickrDialogBase", "Choose Area"))
        self.groupBox_3.setTitle(_translate("FlickrDialogBase", "Latitude"))
        self.label_4.setText(_translate("FlickrDialogBase", "North"))
        self.label_5.setText(_translate("FlickrDialogBase", "South"))
        self.groupBox_4.setTitle(_translate("FlickrDialogBase", "Longitude"))
        self.label_6.setText(_translate("FlickrDialogBase", "East"))
        self.label_7.setText(_translate("FlickrDialogBase", "West"))
        self.startButton.setText(_translate("FlickrDialogBase", "Start"))
        self.stopButton.setText(_translate("FlickrDialogBase", "Stop"))
        self.label_8.setText(_translate("FlickrDialogBase", "From"))
        self.label_9.setText(_translate("FlickrDialogBase", "To"))
        self.groupBox_5.setTitle(_translate("FlickrDialogBase", "Choose csv file"))
        self.csvFilePicker.setText(_translate("FlickrDialogBase", "..."))
        self.label_10.setText(_translate("FlickrDialogBase", "CSV File"))
        self.removeVectorLayer.setText(_translate("FlickrDialogBase", "Remove Layer"))
        self.closeImages.setText(_translate("FlickrDialogBase", "Close Images"))
        self.saveLogCheck.setText(_translate("FlickrDialogBase", "save log?"))
        self.outputDirPicker.setText(_translate("FlickrDialogBase", "..."))
        self.label_11.setText(_translate("FlickrDialogBase", "Output Folder"))
        self.saveImages.setText(_translate("FlickrDialogBase", "Save Images?"))