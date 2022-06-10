# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FlickrDialog
 A QGIS plugin
 ***************************************************************************/
"""

import os
import requests
from datetime import datetime
from collections import deque
import pandas as pd

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.PyQt.QtCore import QObject, QThread, pyqtSignal, QDate, QVariant, QUrl

from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsField, QgsPoint, QgsRectangle
from PyQt5.QtWebKitWidgets import QWebView
from qgis.utils import iface

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'flickr_dialog_base.ui'))

LOCATION_ACCURACY = 16
RES_PER_PAGE = 250          # defaults to 100; maximum is 500
MAX_RES_PER_QUERY = 4000    # flickr API business policy
MAX_SAME_QUERIES = MAX_RES_PER_QUERY / RES_PER_PAGE
# assuming flickr does not have a data density that would gives us more 
# than 4000 entries withing a box subtending 1e-4 latitudes and longitudes
BOX_DIVISION_THRESHOLD = 1e-4   
IMAGE_URL_TYPE = 'url_b'
IMAGE_SIZE_SUFFIX = 'b'
IMAGE_SIZE = 1024
CHUNK_SIZE = 4096


html_template_file = open(os.path.join(os.path.dirname(__file__), 'template.html'))
html_template = html_template_file.read()
html_template_file.close()


class FlickrDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FlickrDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # connect buttons to handler
        self.dbFilePicker.clicked.connect(self._select_db_file)
        self.csvFilePicker.clicked.connect(self._select_csv_file)
        self.outputDirPicker.clicked.connect(self._select_output_folder)
        self.startButton.clicked.connect(self._start_download_thread)
        self.stopButton.clicked.connect(self._stop_download_thread)
        self.removeVectorLayer.clicked.connect(self._remove_layers)
        self.closeImages.clicked.connect(self._close_browser_windows)

        # set download in progress flag as false
        self.isDownloadInProgress = False

        # set logbox empty
        self.logBox.setPlainText("")

        # set progress bar to zero
        self.progressBar.setValue(0)

        # disable stop button
        self.stopButton.setEnabled(False)

        self.elem_config_map = {
            "API_KEY": self.apiKey,
            "DB_FILE_NAME": self.dbFileName,
            "CSV_FILE_NAME": self.csvFileName,
            "OUTPUT_DIR_NAME": self.outputDirName,
            "TABLE_NAME": self.tableName,
            "NORTH": self.north,
            "SOUTH": self.south,
            "EAST": self.east,
            "WEST": self.west,
            "START_DATE": self.startDate,
            "END_DATE": self.endDate,
            "SAVE_LOG": self.saveLogCheck,
            "SAVE_IMAGES": self.saveImages
        }

        self.configFilePath = os.path.join(os.path.dirname(__file__), ".conf")
        self.logFilePath = os.path.join(os.path.dirname(__file__), ".logfile")

        # load saved input
        self._load_prev_input()

        # connect to input saver
        self.rejected.connect(self._save_input)

        # connect to layer cleanup
        self.rejected.connect(self._cleanup)

        # connect to save log
        self.rejected.connect(self._save_log)

    def _save_log(self):
        if self.saveLogCheck.isChecked():
            try:
                f = open(self.logFilePath, 'w')
            except:
                return

            f.write(self.logBox.toPlainText())
            f.close()
        return

    def _remove_layers(self):
        try:
            QgsProject.instance().removeMapLayers([self.markerLayer.id(), self.boundaryLayer.id()])
            QgsProject.instance().refreshAllLayers()
        except:
            pass

    def _close_browser_windows(self):
        if hasattr(self, 'webViews'):
            for webView in self.webViews:
                try:
                    webView.close()
                except:
                    pass

    def _cleanup(self):
        # clean vector layer
        self._remove_layers()

        # close open browser windows
        self._close_browser_windows()
        
    def _save_input(self):
        try:
            f = open(self.configFilePath, 'w')
        except:
            return
        
        l = list()

        for key, val in self.elem_config_map.items():
            if key == "START_DATE" or key == "END_DATE":
                l.append(f"{key}={val.date().toPyDate().strftime('%Y-%m-%d')}")
            elif key == 'SAVE_LOG' or key == 'SAVE_IMAGES':
                l.append(f"{key}={'true' if val.isChecked() else 'false'}")
            else:
                l.append(f"{key}={val.text()}")

        f.write('\n'.join(l))
        f.close()
        return

    def _load_prev_input(self):
        if os.path.exists(self.configFilePath):
            # load configurations from configfile
            try:
                f = open(self.configFilePath)
            except:
                self.logBox.append("Error: could not load from config file.")
                return

            for line in f.readlines():
                key, val = line.strip('\n').split("=")
                elem = self.elem_config_map[key]

                if key == "START_DATE" or key == "END_DATE":
                    y, m, d = val.split("-")
                    y, m, d = int(y), int(m), int(d)
                    d = QDate(y, m, d)
                    elem.setDate(d)
                elif key == 'SAVE_LOG' or key == 'SAVE_IMAGES':
                    elem.setChecked(val == "true")
                else:    
                    elem.setText(val)

            f.close()
            return
                
    def _select_db_file(self):
        dbFilePath, _ = QFileDialog.getOpenFileName(self, "choose database file", "", "*.sqlite")
        self.dbFileName.setText(dbFilePath)

    def _select_csv_file(self):
        csvFilePath, _ = QFileDialog.getSaveFileName(self, "choose csv file", "", "*.csv")
        self.csvFileName.setText(csvFilePath)

    def _select_output_folder(self):
        outputDir = QFileDialog.getExistingDirectory(self, "choose output directory")
        self.outputDirName.setText(outputDir)

    def _start_download_thread(self):
        # starts download thread      
        # reset stuff

        self._cleanup()  
        self.progressBar.setValue(0)

        def number_error(elem):
            QMessageBox.warning(self, "Error", "Enter valid number as latitude or longitude")
            elem.setFocus()
            elem.selectAll()

        def lat_error(elem):
            QMessageBox.warning(self, "Error", "latitude must lie between -90 and 90 degrees")
            elem.setFocus()
            elem.selectAll()

        def long_error(elem):
            QMessageBox.warning(self, "Error", "longitude must lie between -180 and 180 degrees")
            elem.setFocus()
            elem.selectAll()

        def api_key_error(elem):
            QMessageBox.warning(self, "Error", "API key cannot be empty")
            elem.setFocus()

        def date_error():
            QMessageBox.warning(self, "Error", "start date and end date not compatible")

        if not self.isDownloadInProgress:
            # collect data
            apiKey = self.apiKey.text()
            north = self.north.text()
            south = self.south.text()
            east = self.east.text()
            west = self.west.text()
            startDate = self.startDate.date()
            endDate = self.endDate.date()
            dbFileName = self.dbFileName.text()
            tableName = self.tableName.text()
            csvFileName = self.csvFileName.text()
            outputDirName = self.outputDirName.text()

            if len(dbFileName) == 0:
                QMessageBox.warning(self, "Error", "Choose db file")
                self.dbFileName.setFocus()

            if len(tableName) == 0:
                QMessageBox.warning(self, "Error", "Enter table name")
                self.tableName.setFocus()

            if len(csvFileName) == 0:
                QMessageBox.warning(self, "Error", "Choose csv file")
                self.csvFileName.setFocus()

            if len(outputDirName) == 0:
                QMessageBox.warning(self, "Error", "Choose output directory")
                self.outputDirName.setFocus()

            try:
                assert len(apiKey) != 0
            except:
                api_key_error(self.apiKey)

            try:
                northLat = float(north)
            except:
                number_error(self.north)

            try:
                southLat = float(south)
            except:
                number_error(self.south)
            
            try:
                eastLong = float(east)
            except:
                number_error(self.east)

            try:
                westLong = float(west)
            except:
                number_error(self.west)

            if not (-90 <= northLat <= 90):
                lat_error(self.north)

            if not (-90 <= southLat <= 90):
                lat_error(self.south) 

            if not (-180 <= eastLong <= 180):
                long_error(self.east)

            if not (-180 <= westLong <= 180):
                long_error(self.west)

            # swap latitudes if required
            if northLat < southLat:
                northLat, southLat = southLat, northLat

            # swap longitudes if required
            if eastLong < westLong:
                eastLong, westLong = westLong, eastLong

            if startDate > endDate:
                date_error()

            if ('northLat' in locals()) and ('southLat' in locals()) and ('eastLong' in locals()) and ('westLong' in locals())\
                -180 <= eastLong <= 180 and -180 <= westLong <= 180 and\
                -90  <= northLat <= 90  and -90  <= southLat <= 90 and \
                startDate <= endDate \
                and len(dbFileName) != 0 and len(tableName) != 0 and len(csvFileName) != 0 and len(outputDirName) != 0:

                # no error in input; set download in progress
                self.isDownloadInProgress = True
                self.startButton.setEnabled(False)
                self.stopButton.setEnabled(True)

                # clear log
                self.logBox.clear()

                # modify date to datetime object
                startDate = datetime.combine(startDate.toPyDate(), datetime.min.time())
                endDate = datetime.combine(endDate.toPyDate(), datetime.min.time())
                boundary = [westLong, southLat, eastLong, northLat, startDate, endDate]

                # create worker
                self.thread = QThread()
                self.worker = Worker(boundary, apiKey, dbFileName, tableName, csvFileName, outputDirName, self.saveImages.isChecked())
                self.worker.moveToThread(self.thread)

                # connect signals to slots
                self.worker.addMessage.connect(self._message_from_worker)
                self.worker.addError.connect(self._error_from_worker)
                self.worker.progress.connect(self._progress_from_worker)
                self.worker.total.connect(self._total_from_worker)

                self.thread.started.connect(self.worker.run)
                self.worker.finished.connect(self.thread.quit)
                self.worker.finished.connect(self.worker.deleteLater)
                self.thread.finished.connect(self.thread.deleteLater)

                # start thread and run worker
                self.thread.start()

                # enable button after thread finishes; set download not in progress
                def worker_finished(df): 
                    self.startButton.setEnabled(True)    
                    self.stopButton.setEnabled(False)
                    self.isDownloadInProgress = False
                    self.progressBar.setValue(self.progressBar.maximum())  

                    if type(df) == pd.DataFrame:
                        self.df = df
                        self._draw_layers(west, south, east, north)
                    
                self.worker.finished.connect(worker_finished)
            else:
                QMessageBox.warning(self, "Error", "Can not download without appropriate data!")
        else:
            pass

    def _add_marker(self, long, lat, title, tags, datetaken, link):
        fet = QgsFeature()
        fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(long, lat)))
        fet.setAttributes([title, tags, datetaken, link])
        self.markerProvider.addFeatures([fet])

    def _draw_line(self, lat1, lat2, long1, long2):
        start_point = QgsPoint(long1, lat1)
        end_point = QgsPoint(long2, lat2)  

        seg = QgsFeature()
        seg.setGeometry(QgsGeometry.fromPolyline([start_point, end_point]))
        seg.setAttributes(["", "", "", ""])
        self.boundaryProvider.addFeatures([seg])

    def _draw_layers(self, west, south, east, north):
        west, south, east, north  = float(west), float(south), float(east), float(north)

        self.logBox.append('drawing vector layers...')
        # create marker layer
        self.markerLayer = QgsVectorLayer("Point?crs=epsg:4326", "flickr marker", "memory")
        self.markerProvider = self.markerLayer.dataProvider()
        self.markerLayer.startEditing()

        # create boundary layer
        self.boundaryLayer = QgsVectorLayer("LineString?crs=epsg:4326", "flickr boundary", "memory")
        self.boundaryProvider = self.boundaryLayer.dataProvider()
        self.boundaryLayer.startEditing()
        
        # add attributes for features
        self.markerProvider.addAttributes([
            QgsField("title", QVariant.String), 
            QgsField("tags",  QVariant.String), 
            QgsField("datetaken", QVariant.String), 
            QgsField("link", QVariant.String)
        ])

        # add bounding box
        self._draw_line(north, north, west, east)
        self._draw_line(south, south, west, east)
        self._draw_line(north, south, east, east)
        self._draw_line(north, south, west, west)

        # create feature for each of the points
        self.logBox.append(f"adding {len(self.df)} features...")
        for _, row in self.df.iterrows():
            self._add_marker(
                float(row['longitude']),
                float(row['latitude']),
                row['title'], 
                row['tags'], 
                row['datetaken'], 
                row[IMAGE_URL_TYPE]
            )

        self.logBox.append(f"added {len(self.df)} features")
        
        self.markerLayer.commitChanges()
        self.boundaryLayer.commitChanges()
        
        QgsProject.instance().addMapLayer(self.boundaryLayer)
        QgsProject.instance().addMapLayer(self.markerLayer)

        self.markerLayer.selectionChanged.connect(self._handle_feature_selection)
        self.webViews = []

    def _open_web_view(self, title, tags, datetaken, link):
        webView = QWebView()
        self.webViews.append(webView)

        self.logBox.append(f"loading {title} ...")

        # process args
        if len(title) == 0:
            title = "no title"
        if len(tags.strip(" ")) != 0:
            tags = str(['"' + tag + '"' for tag in tags.strip().split(" ")])
        else:
            tags = []
        d = datetime.strptime(datetaken, "%Y-%m-%d %H:%M:%S").strftime('%A, %d %B, %Y')

        # generate html
        webView.setHtml(html_template.format(title, link, title, d, tags))
        webView.show()
        

    def _handle_feature_selection(self, selFeatures):
        selFeatures = self.markerLayer.selectedFeatures()
        if len(selFeatures) > 0:
            for feature in selFeatures:
                attrs = feature.attributes()
                title, tags, datetaken, link = attrs
                # draw popup on web view or use native qt dialog
                self._open_web_view(title, tags, datetaken, link)

    def _stop_download_thread(self):
        self.worker.stop()

    def _message_from_worker(self, message):
        self.logBox.append(message)

    def _error_from_worker(self, message):
        QMessageBox.warning(self, "Error", message)

    def _progress_from_worker(self, progress):
        self.progressBar.setValue(progress)

    def _total_from_worker(self, total):
        self.progressBar.setMaximum(int(total))


class Worker( QObject ):
    finished = pyqtSignal(pd.DataFrame)
    progress = pyqtSignal(int)
    addMessage = pyqtSignal(str)
    addError = pyqtSignal(str)
    total = pyqtSignal(int)

    def __init__(self, boundary, apiKey, dbFileName, tableName, csvFileName, outputDirName, saveImages):
        QObject.__init__(self)
        self.boundary = boundary
        self.apiKey = apiKey
        self.dbFileName = dbFileName
        self.csvFileName = csvFileName
        self.tableName = tableName
        self.outputDirName = outputDirName
        self.saveImages = saveImages

        self.running = None
        self.downloadCount = 0

        self.csvData = []
        self.df = None
        self.csvKeys = ["id", "latitude", "longitude", "datetaken", "accuracy", "title", "tags", IMAGE_URL_TYPE, "filepath"]

    def stop(self):
        self.running = False

    def _check_api_key(self):
        self.addMessage.emit("checking connection to flickr API...")
        url = f"https://api.flickr.com/services/rest/?api_key={self.apiKey}&method=flickr.test.echo&format=json&nojsoncallback=1"
        data = requests.get(url).json()
        
        if data['stat'] == 'ok':
            self.addMessage.emit("Connection OK")
            return True
        elif data['stat'] == 'fail':
            self.addMessage.emit(f"Error: {data['message']}")
            return False

    def _search_photos(self, boundary, page):
        self.addMessage.emit("Searching for photos on flickr...")
        bbox = ','.join([str(coords) for coords in boundary[:4]])
        startDate, endDate = boundary[4:]
        startDate = str(startDate)
        endDate = str(endDate)
        url = f"https://api.flickr.com/services/rest/?api_key={self.apiKey}&method=flickr.photos.search&bbox={bbox}&accuracy={LOCATION_ACCURACY}&format=json&nojsoncallback=1&page={page}&perpage={RES_PER_PAGE}&min_taken_date={startDate}&max_taken_date={endDate}&extras=geo%2Cdate_taken%2Ctags%2C{IMAGE_URL_TYPE}"
        data = requests.get(url).json()

        if data['stat'] == 'ok':
            self.addMessage.emit('fetched photo metadata successfully')
        elif data['stat'] == 'fail':
            self.addMessage.emit(f"Error fetching photo metadata: {data['message']}")
            return None
        return data

    def _save_image(self, url, filepath, filename):
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            try:
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(CHUNK_SIZE):
                        f.write(chunk)
            except:
                self.addMessage.emit(f"could not write file {filename}")
            else:
                self.addMessage.emit(f"saved file {filename}")
        else:
            self.addMessage.emit(f"could not write file {filename}")

        del r

    def _push_data(self, data, page):
        self.addMessage.emit(f"pushing page {page} to csv file...")

        i = 1

        # save to csv file
        for photo in data['photos']['photo']:
            filename = f"{i}.jpg"
            filepath = os.path.join(self.outputDirName, filename)
            url = f"https://live.staticflickr.com/{photo['server']}/{photo['id']}_{photo['secret']}_{IMAGE_SIZE_SUFFIX}.jpg"
            self.csvData.append([photo[key] for key in self.csvKeys[:-2]] + [url, filepath])

            # download and save photo
            if self.saveImages:
                self._save_image(url, filepath, filename)

            i += 1

        self.downloadCount += len(data['photos']['photo'])
        self.progress.emit(self.downloadCount)

    def run(self):
        self.downloadCount = 0
        self.running = True

        def _halt_error():
            self.addMessage.emit("worker halted forcefully")
            self.finished.emit(None)

        # check if api key is valid
        apiKeyValid = self._check_api_key()

        if not apiKeyValid:
            self.addError.emit("Error: invalid API key")
            self.finished.emit(None)
            return

        if not self.running:
            _halt_error()
            return

        # TODO: fix read only database issue
        # establish connection to database (spatialite)
        # try:
        #     con = qgis.utils.spatialite_connect(self.dbFileName)
        #     cursor = con.cursor()
        # except Exception as ex:
        #     self.addError.emit(f"Error: {ex}")
        #     self.finished.emit()
        #     return
        # else:
        #     self.addMessage.emit(f"Connected to database {os.path.basename(self.dbFileName)}")
        
        # drop old table; create new table
        # try:
        #     cursor.execute(f"drop table if exists {self.tableName}")
        #     cursor.execute(f"create table {self.tableName} (p_id integer primary key autoincrement, lat real, lon real, o_id text, p_date text, accuracy int, title text, tags text, url text)")
        # except Exception as ex:
        #     self.addError.emit(f"Error: {ex}")
        #     self.finished.emit()
        #     return
        # else:
        #     self.addMessage.emit(f"old table dropped if any.")
        #     self.addMessage.emit(f"created new table {self.tableName}.")

        # recursively download all metadata
        bboxes = deque()
        bboxes.append(self.boundary)

        first = True

        # main loop
        while len(bboxes) > 0:
            # halt if halted
            if not self.running:
                _halt_error()
                return
            # recursively generate new queries to download all metadata
            bbox = bboxes.popleft()
            self.addMessage.emit(f"Downloading Box: {bbox[3]}°N-{bbox[1]}°S {bbox[2]}°E-{bbox[0]}°W {bbox[4].date()}-{bbox[5].date()}")

            # download
            page = 1
            data = self._search_photos(bbox, page)

            if data['stat'] == 'fail':
                self.addError.emit(data['message'])
                return

            pages = data['photos']['pages']

            if first:
                first = False
                self.totalRecordCount = data['photos']['total']
                self.total.emit(self.totalRecordCount)
                self.addMessage.emit(f"downloading all {self.totalRecordCount} records")

            if pages > MAX_SAME_QUERIES:
                # too many same queries; dividing the box
                W, S, E, N, startDate, endDate = bbox

                if abs(N - S) > BOX_DIVISION_THRESHOLD and abs(E - W) > BOX_DIVISION_THRESHOLD:
                    # box big enough to be divided
                    self.addMessage.emit(f"{pages} pages. dividing spatially...")
                    mid_long = (E + W) / 2
                    mid_lat = (N + S) / 2
                    bboxes.append([W, mid_lat, mid_long, N, startDate, endDate])
                    bboxes.append([mid_long, mid_lat, E, N, startDate, endDate])
                    bboxes.append([mid_long, S, E, mid_lat, startDate, endDate])
                    bboxes.append([W, S, mid_long, mid_lat, startDate, endDate])
                else:
                    # box not big enough. dividing temporally
                    self.addMessage.emit(f"{pages} pages. dividing temporally...")
                    midDate = datetime.fromtimestamp((startDate.timestamp() + endDate.timestamp()) / 2)
                    bboxes.append([W, S, E, N, startDate, midDate])
                    bboxes.append([W, S, E, N, midDate, endDate])
            else:
                self._push_data(data, page)
                while page < pages:
                    page += 1
                    data = self._search_photos(bbox, page)
                    if data['stat'] == 'fail':
                        self.addError.emit(data['message'])
                        return
                    self._push_data(data, page)
                    pages = data['photos']['pages']

        self.addMessage.emit(f"Finished downloading all {self.totalRecordCount} records")
        self.addMessage.emit("Saving into csv file...")

        df = pd.DataFrame(self.csvData)
        df.columns = self.csvKeys
        try:
            df.to_csv(self.csvFileName)
        except Exception as ex:
            self.addError.emit(f"Error : {ex}")
            self.finished.emit(None)
            return
        else:
            self.addMessage.emit("csv file saved")

        self.df = pd.DataFrame(self.csvData)
        self.df.columns = self.csvKeys

        del self.csvData

        self.running = False
        self.finished.emit(self.df)
        return
