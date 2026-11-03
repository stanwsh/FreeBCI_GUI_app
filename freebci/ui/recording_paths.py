import os
from datetime import datetime
import pandas as pd
import numpy as np
import csv

class RecordingPaths:
    
    def __init__(self):
        self.user_path = os.path.expanduser('~')
        self.doc_path = os.environ.get('FREEBCI_HOME') or (self.user_path + '\\Documents\\FreeBCI')
        if not os.path.exists(self.doc_path):
            os.mkdir(self.doc_path)
        self.record_path = self.doc_path + '\\Recordings'
        if not os.path.exists(self.record_path):
            os.mkdir(self.record_path)
        self.session_path = ''
        self.count = 0
        self.txt_file = 1
        self.f = None
        self.f_csv = None

    
    def record_data(self, df: np.array, channel, name, sampling_rate):
        if self.count == 0:
            if self.f is not None:
                self.f.close()
                self.f = None
            if self.f_csv is not None:
                self.f_csv.close()
                self.f_csv = None
            if self.txt_file == 1:
                self.create_dir()
            path = self.session_path + '\\' + str(self.txt_file) + '.txt'
            path_csv = self.session_path + '\\' + str(self.txt_file) + '.csv'
            self.f = open(path, 'w+')
            self.f_csv = open(path_csv, 'w+', encoding='utf-8')
            csv_writer = csv.writer(self.f_csv)
            subtitle = []
            subtitle = [ 'channel' + str(i + 1) for i in (range(channel)) ]
            subtitle += [ '<AUX ' + str(j) + '>' for j in (range(3)) ]
            csv_writer.writerow(subtitle)
            subtitle_txt = []
            subtitle_txt = [ str(i + 1) + ' ' for i in (range(channel)) ]
            subtitle_txt += [ '<AUX ' + str(j) + '>' for j in (range(3)) ]
            subtitle_txt = ''.join(subtitle_txt)
            title = 'FreeBCI Raw Data\nNumber of Channels: ' + str(channel) + '\n' + 'Sampling Rate: ' + str(sampling_rate) + ' Hz' + '\n' + 'Board: ' + name + '\n' + subtitle_txt + '\n'
            self.f.write(title + 'Start Time:' + datetime.now().strftime('%Y_%m_%d_%H%M%S') + '\n')
        self.count += 1
        for yy in range(1, 4):
            for xx in range(0, len(df[1 + channel + yy])):
                df[1 + channel + yy][xx] = int(df[1 + channel + yy][xx])
        np.savetxt(self.f, df[1:4 + channel].T, fmt=' , '.join([
            '%f'] * channel + [
            '%d'] * 3), delimiter=',', newline='\n')
        data_csv = df[1:4 + channel].T
        for x in data_csv:
            csv_writer = csv.writer(self.f_csv)
            csv_writer.writerow(x)
        if self.count >= 9:
            self.f.close()
            self.f_csv.close()
            self.f = None
            self.f_csv = None
            self.txt_file += 1
            self.count = 0

    
    def stop_record(self):
        if self.f is not None:
            self.f.close()
            self.f = None
        if self.f_csv is not None:
            self.f_csv.close()
            self.f_csv = None
        self.count = 0
        self.txt_file = 1

    
    def create_dir(self):
        self.session_path = self.record_path + '\\' + 'Stream_' + datetime.now().strftime('%Y_%m_%d_%H%M%S')
        os.mkdir(self.session_path)


