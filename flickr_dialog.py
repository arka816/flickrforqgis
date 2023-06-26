# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FlickrForQgis
 A QGIS plugin
 ***************************************************************************/
"""

import os
import requests
from datetime import datetime
from collections import deque
import pandas as pd
import socket

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.PyQt.QtCore import QObject, QThread, pyqtSignal, QDate, QVariant, QUrl

from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsField, QgsPoint, QgsRectangle
from PyQt5.QtWebKitWidgets import QWebView
from qgis.utils import iface

from .constants import IMAGE_SIZE_SUFFIX, IMAGE_URL_TYPE, LOCATION_ACCURACY, RES_PER_PAGE, \
    MAX_RES_PER_QUERY, MAX_SAME_QUERIES, BOX_DIVISION_THRESHOLD, CHUNK_SIZE, PROFILE_LOAD_TIME

localdir = os.path.join(os.getenv('APPDATA'), 'qgis-flickr')
if not os.path.exists(localdir):
    os.makedirs(localdir)

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'flickr_dialog_base.ui'))



html_template_file = open(os.path.join(os.path.dirname(__file__), 'template.html'))
html_template = html_template_file.read()
html_template_file.close()

def is_connected():
    try:
        # connect to the host google.com -- tells us if the host is actually reachable
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        pass
    return False


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
        self.progressBar.setMaximum(100)

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

        self.configFilePath = os.path.join(localdir, ".conf")
        self.logFilePath = os.path.join(localdir, ".logfile")

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

                # create thread handler
                self.thread = QThread()

                # create worker
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

                # start thread
                self.thread.start()

                # enable button after thread finishes; set download not in progress
                def worker_finished(df): 
                    self.logBox.append("worker finished")
                    self.startButton.setEnabled(True)    
                    self.stopButton.setEnabled(False)
                    self.isDownloadInProgress = False
                    self.progressBar.setValue(self.progressBar.maximum())  

                    if type(df) == pd.DataFrame and len(df) > 0:
                        self.df = df
                        self._draw_layers(west, south, east, north)
                    
                self.worker.finished.connect(worker_finished)
            else:
                QMessageBox.warning(self, "Error", "Can not download without appropriate data!")
        else:
            pass

    def _add_marker(self, long, lat, title, tags, datetaken, link, ownername):
        fet = QgsFeature()
        fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(long, lat)))
        fet.setAttributes([title, tags, datetaken, link, ownername])
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
            QgsField("link", QVariant.String),
            QgsField("name", QVariant.String)
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
                row[IMAGE_URL_TYPE],
                row['ownername']
            )

        self.logBox.append(f"added {len(self.df)} {'features' if len(self.df) > 1 else 'feature'}")
        
        self.markerLayer.commitChanges()
        self.boundaryLayer.commitChanges()
        
        QgsProject.instance().addMapLayer(self.boundaryLayer)
        QgsProject.instance().addMapLayer(self.markerLayer)

        self.markerLayer.selectionChanged.connect(self._handle_feature_selection)
        self.webViews = []

    def _open_web_view(self, title, tags, datetaken, link, ownername):
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
        webView.setHtml(html_template.format(title, link, title, d, ownername, tags))
        webView.show()
        
    def _handle_feature_selection(self, selFeatures):
        selFeatures = self.markerLayer.selectedFeatures()
        if len(selFeatures) > 0:
            for feature in selFeatures:
                attrs = feature.attributes()
                title, tags, datetaken, link, ownername = attrs
                # draw popup on web view or use native qt dialog
                self._open_web_view(title, tags, datetaken, link, ownername)

    def _stop_download_thread(self):
        self.worker.stop()

    def _message_from_worker(self, message):
        self.logBox.append(message)

    def _error_from_worker(self, message):
        QMessageBox.warning(self, "Error", message)

    def _progress_from_worker(self, progress):
        self.progressBar.setValue(int((100 - PROFILE_LOAD_TIME) * progress / self.total_count))

    def _total_from_worker(self, total):
        self.total_count = total
        


class Worker( QObject ):
    finished = pyqtSignal(pd.DataFrame)
    progress = pyqtSignal(int)
    addMessage = pyqtSignal(str)
    addError = pyqtSignal(str)
    total = pyqtSignal(int)

    UNIQUE_KEY = IMAGE_URL_TYPE

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
        self.csvKeys = ["id", "owner", "place_id", "latitude", "longitude", "datetaken", "accuracy", "title", "tags", "ownername", IMAGE_URL_TYPE, "filepath"]

    def stop(self):
        self.running = False

    def _check_api_key(self):
        self.addMessage.emit("checking connection to flickr API...")
        url = f"https://api.flickr.com/services/rest/?api_key={self.apiKey}&method=flickr.test.echo&format=json&nojsoncallback=1"
        r = requests.get(url)

        if r.status_code == 200:
            data = r.json()
            if data['stat'] == 'ok':
                self.addMessage.emit("Connection OK")
                return True
            elif data['stat'] == 'fail':
                self.addMessage.emit(f"Error: {data['message']}")
                return False
        else:
            if is_connected():
                self.addError.emit(f"Error: {r.text}")
            else:
                self.addError.emit(f"Check Internet connection")

    def _search_photos(self, boundary, page):
        if not self.running:
            self._halt_error()
            return
        
        self.addMessage.emit("Searching for photos on flickr...")
        bbox = ','.join([str(coords) for coords in boundary[:4]])
        startDate, endDate = boundary[4:]
        startDate = str(startDate)
        endDate = str(endDate)

        extras = ["geo", "date_taken", "tags", IMAGE_URL_TYPE, "owner_name"]

        params = {
            "api_key": self.apiKey,
            "method": "flickr.photos.search",
            "bbox": bbox,
            "accuracy": LOCATION_ACCURACY,
            "format": "json",
            "nojsoncallback": 1,
            "page": page,
            "perpage": RES_PER_PAGE,
            "min_taken_date": startDate,
            "max_taken_date": endDate,
            "extras": ",".join(extras),
            "media": "photos"
        }
        url = f"https://api.flickr.com/services/rest/"
        data = requests.get(url, params=params).json()

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
                with open(os.path.join(filepath, filename), 'wb') as f:
                    for chunk in r.iter_content(CHUNK_SIZE):
                        if not self.running:
                            self._halt_error()
                            return
                        f.write(chunk)
            except:
                self.addMessage.emit(f"could not write file {filename}")
            else:
                self.addMessage.emit(f"saved file {filename}")
                return True
        else:
            self.addMessage.emit(f"could not write file {filename}")

        r.close()
        del r

        return False

    def _push_data(self, data, page):
        self.addMessage.emit(f"pushing page {page} to dataframe...")

        # save to csv file
        for photo in data['photos']['photo']:
            if not self.running:
                self._halt_error()
                return

            filepath = self.outputDirName

            filename = f"{photo['id']}_{photo['secret']}{IMAGE_SIZE_SUFFIX}.jpg"
            url = f"https://live.staticflickr.com/{photo['server']}/{filename}"
            filename = f"{photo['server']}_{filename}"

            fallback_filename = f"{photo['id']}_{photo['secret']}_o.jpg"
            fallback_url = f"https://live.staticflickr.com/{photo['server']}/{fallback_filename}"
            fallback_filename = f"{photo['server']}_{fallback_filename}"
            
            image_filepath = ''

            # download and save photo
            if self.saveImages:
                downloaded_flag = self._save_image(url, filepath, filename)
                if not downloaded_flag:
                    # TODO: test fallback code
                    if self._save_image(fallback_url, filepath, fallback_filename):
                        image_filepath = os.path.join(filepath, fallback_filename)
                        url = fallback_url
                else:
                    image_filepath = os.path.join(filepath, filename)

            self.csvData.append(
                [photo.get(key, None) for key in self.csvKeys[:-2]] + 
                [url, image_filepath]
            )

            self.downloadCount += 1
            self.progress.emit(self.downloadCount)

        # self.downloadCount += len(data['photos']['photo'])
        self.progress.emit(self.downloadCount)

    def _halt_error(self):
        self.addMessage.emit("worker halted forcefully")
        self.finished.emit(pd.DataFrame())

    def _get_user_data(self, subg):
        user_id = subg['owner'].iloc[0]

        params = {
            "api_key": self.apiKey,
            "method": "flickr.profile.getProfile",
            "user_id": user_id,
            "format": "json",
            "nojsoncallback": 1,
        }

        url = f"https://api.flickr.com/services/rest/"
        r = requests.get(url, params=params)

        if r.status_code == 200:
            data = r.json()

            if data['stat'] == 'ok':
                if 'hometown' in data['profile']:
                    subg['user_hometown'] = data['profile']['hometown']
                # subg['user_city'] = data['profile']['city']
                # subg['user_country'] = data['profile']['country']
                self.addMessage.emit(f"fetched user data successfully for: {user_id}")
            elif data['stat'] == 'fail':
                self.addMessage.emit(f"Error fetching user data: {data['message']}")

        return subg
    
    def run(self):
        self.downloadCount = 0
        self.running = True

        # check if api key is valid
        apiKeyValid = self._check_api_key()

        if not apiKeyValid:
            self.addError.emit("Error: invalid API key")
            self.finished.emit(pd.DataFrame())
            return

        if not self.running:
            self._halt_error()
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
        while len(bboxes) and self.running > 0:
            # halt if halted
            if not self.running:
                self._halt_error()
                return
            # recursively generate new queries to download all metadata
            bbox = bboxes.popleft()
            self.addMessage.emit(f"Downloading Box: {bbox[3]}°N-{bbox[1]}°S {bbox[2]}°E-{bbox[0]}°W {bbox[4].date()}->{bbox[5].date()}")

            # download
            page = 1
            data = self._search_photos(bbox, page)

            if data['stat'] == 'fail':
                self.addError.emit(data['message'])
                self.finished.emit(pd.DataFrame())
                return

            pages = data['photos']['pages']

            if pages == 0:
                if first:
                    # first search returns no results
                    # verdict: return control
                    self.addError.emit('no results found within given box')
                    self.finished.emit(pd.DataFrame())
                    return
                else:
                    # recursive search returns no results
                    # verdict: move on to next bbox
                    self.addMessage.emit('no results found within given box')
                    continue

            if first:
                first = False
                self.totalRecordCount = data['photos']['total']
                self.total.emit(self.totalRecordCount)
                self.addMessage.emit(f"downloading all {self.totalRecordCount} {'records' if self.totalRecordCount > 1 else 'record'}")

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
                    if data == None:
                        return
                    if data['stat'] == 'fail':
                        self.addError.emit(data['message'])
                        self.finished.emit(pd.DataFrame())
                        return
                    self._push_data(data, page)
                    pages = data['photos']['pages']

        self.addMessage.emit(f"Finished downloading all {self.totalRecordCount} records")

        self.addMessage.emit('dropping duplicates...')

        try:
            self.df = pd.DataFrame(self.csvData)
            self.df.columns = self.csvKeys

            self.addMessage.emit(f"found {self.df.shape[0] - self.df[self.UNIQUE_KEY].unique().shape[0]} duplicates. dropping...")

            self.df.drop_duplicates(subset=[self.UNIQUE_KEY], inplace=True)

            del self.csvData
        except Exception as ex:
            self.addMessage.emit(ex)

        self.df = self.df.groupby('owner').apply(self._get_user_data)


        self.addMessage.emit("flushing data into csv file...")
        try:
            with open(self.csvFileName, 'w') as f:
                self.df.to_csv(f, line_terminator='\n')
        except Exception as ex:
            self.addError.emit(f"Error : {ex}")
            self.finished.emit(pd.DataFrame())
            return
        else:
            self.addMessage.emit("csv file saved")

        self.running = False
        self.finished.emit(self.df)
        return
