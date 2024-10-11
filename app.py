import os
import random
import subprocess
import string
import sys

from PyQt5.QtGui import QIcon, QPixmap
from pytubefix import YouTube
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import traceback


vid_dir = os.path.expanduser("~\\Documents\\Tubular Videos")
print(vid_dir)
if os.path.isdir(vid_dir) is False:
    os.mkdir(vid_dir)

def id_generator(size=6, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class YTManager(QThread):
    prog_log = pyqtSignal(str)
    progress = pyqtSignal(int)
    failed = pyqtSignal()
    finished = pyqtSignal()
    process = pyqtSignal()

    def __init__(self, URL: str):
        super().__init__()
        self.media_processing = None
        self.URL = URL
        self.vid_quality_itags = {
            "1440p": [
                271
            ],
            "1080p": [
                248
            ],
            "720p": [
                247
            ],
            "480p": [
                244
            ],
            "360p": [
                243
            ],
            "240p": [
                242
            ],
            "144p": [
                278
            ]
        }

    def run(self):
        try:
            quality = self.quality
            media_type = self.media_type
            filename = f"{self.filename}"
            if media_type == "Video":
                if quality == "Auto":
                    quality = None
                self.download_video(filename, quality)
            elif media_type == "Audio":
                self.download_audio(filename)
        except Exception as e:
            print(f"Error: {e}")
            self.failed.emit()

    def download_video(self, filename: str, quality: str = None):
        try:
            yt = YouTube(self.URL, on_progress_callback=self.on_progress)
            vid_streams = yt.streams.filter(progressive=False, type="video", video_codec="vp9")

            if quality is None:
                print(yt.streams.filter(type="audio"))
                vid_stream = vid_streams.order_by("resolution").last()
                print(vid_stream)
            if quality is not None:
                vid_stream = vid_streams.filter(resolution=quality).first()


            if not vid_stream:
                self.prog_log.emit("Selected video quality is not available.")
                self.failed.emit()
                return

            self.prog_log.emit("Downloading Video Stream...")
            vid_stream.download(output_path=vid_dir, filename=f"vid_temp_{filename}.mp4")

            aud_stream = yt.streams.filter(progressive=False, type="audio", audio_codec="mp4a.40.5").order_by("abr").first()

            self.prog_log.emit("Downloading Audio Stream...")
            aud_stream.download(output_path=vid_dir, filename=f"aud_temp_{filename}.mp3")

            title = yt.title
            author = yt.author

            self.prog_log.emit("Processing your video. This may take a moment...")
            self.process.emit()
            subprocess.call(
                f'.\\ffmpeg.exe -i "{vid_dir}\\vid_temp_{filename}.mp4" -i "{vid_dir}\\aud_temp_{filename}.mp3" '
                f'-map 0:v -map 1:a -c copy -metadata title="{title}" -metadata artist="{author}" '
                f'-y "{vid_dir}\\{filename}.mp4"',
            shell=True)

            os.remove(f"{vid_dir}/vid_temp_{filename}.mp4")
            os.remove(f"{vid_dir}/aud_temp_{filename}.mp3")

            self.prog_log.emit("Video Downloaded")
            self.finished.emit()
        except Exception as e:
            print(f"Download error: {e}")
            print(traceback.format_exc())
            self.failed.emit()

    def download_audio(self, filename: str):
        try:
            yt = YouTube(self.URL, on_progress_callback=self.on_progress)
            aud_stream = yt.streams.filter(progressive=False, type="audio", audio_codec="mp4a.40.5").order_by("abr").first()

            self.prog_log.emit("Downloading Audio Stream...")
            aud_stream.download(
                output_path=vid_dir,
                filename=f"aud_temp_{filename}.mp3"
            )

            title = yt.title
            author = yt.author

            self.prog_log.emit("Finalizing audio...")
            self.process.emit()
            subprocess.call(
                f'.\\ffmpeg.exe -i "{vid_dir}\\aud_temp_{filename}.mp3" -metadata title="{title}" '
                f' -metadata artist="{author}" -y "{vid_dir}\\{filename}.mp3"'
            )

            os.remove(f"{vid_dir}/aud_temp_{filename}.mp3")

            self.prog_log.emit("Audio Downloaded")
            self.finished.emit()
        except Exception as e:
            print(f"Audio download error: {e}")
            self.failed.emit()

    def on_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = bytes_downloaded / total_size * 100
        self.progress.emit(int(percentage))

dark_stylesheet = """
QWidget {
    background-color: #2E2E2E;
    color: #FFFFFF;
}

QLineEdit {
    background-color: #3C3C3C;
    color: #FFFFFF;
    border: 1px solid #555555;
}

QPushButton {
    background-color: #555555;
    color: #FFFFFF;
    border: 1px solid #777777;
    border-radius: 5px;
}

QPushButton:hover {
    background-color: #666666;
}

QComboBox {
    background-color: #3C3C3C;
    color: #FFFFFF;
    border: 1px solid #555555;
}

QComboBox::down-arrow {
    border: none
}

QProgressBar::chunk {
    background-color: #555555;  /* Change this color as needed */
}

QListWidget {
    background-color: #3C3C3C;
    color: #FFFFFF;
}

QMenuBar {
    background-color: #444444;
    color: #FFFFFF;
}

QMenu {
    background-color: #444444;
    color: #FFFFFF;
}

QMenu::item {
    background-color: #444444;
}

QMenu::item:selected {
    background-color: #666666;
}
"""

class TubularApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        # self.setStyleSheet(dark_stylesheet)

        menubar = QMenuBar(self)
        menubar.setFixedHeight(20)
        layout.addWidget(menubar)

        file_menu = menubar.addMenu('File')
        about_menu = menubar.addMenu("About")

        wipe_action = QAction('Wipe Downloads', self)
        open_download_location_action = QAction('Open Download Location', self)
        wipe_action.triggered.connect(self.wipe_downloads)
        open_download_location_action.triggered.connect(self.open_download_location)
        file_menu.addAction(wipe_action)
        file_menu.addAction(open_download_location_action)

        help_action = QAction('Help', self)
        about_action = QAction('About', self)
        about_action.triggered.connect(self.credits)
        about_menu.addAction(help_action)
        about_menu.addAction(about_action)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15,0,15,15)




        control_layout = QVBoxLayout()

        self.label1 = QLabel('Video URL', self)
        control_layout.addWidget(self.label1)

        self.urlbox = QLineEdit(self)
        control_layout.addWidget(self.urlbox)

        self.label2 = QLabel('Media Type', self)
        control_layout.addWidget(self.label2)

        self.combobox1 = QComboBox()
        self.combobox1.addItem('Video')
        self.combobox1.addItem('Audio')
        control_layout.addWidget(self.combobox1)

        self.label4 = QLabel('Quality', self)
        control_layout.addWidget(self.label4)

        self.combobox2 = QComboBox()
        self.combobox2.addItem("Auto")
        self.combobox2.addItem("4320p")
        self.combobox2.addItem("2160p")
        self.combobox2.addItem("1440p")
        self.combobox2.addItem("1080p")
        self.combobox2.addItem("720p")
        self.combobox2.addItem("480p")
        self.combobox2.addItem("360p")
        self.combobox2.addItem("240p")
        self.combobox2.addItem("144p")
        control_layout.addWidget(self.combobox2)

        self.label3 = QLabel('File Name (No File Extension)', self)
        control_layout.addWidget(self.label3)

        self.filename = QLineEdit(self)
        control_layout.addWidget(self.filename)
        self.filename.setText("MyVideo")

        self.url_input = QPushButton('Download', self)
        self.url_input.clicked.connect(self.start_download)
        control_layout.addWidget(self.url_input)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.progress_bar)

        self.prog_log = QLabel("", self)
        control_layout.addWidget(self.prog_log)

        main_layout.addLayout(control_layout)


        self.video_list = QListWidget(self)
        self.video_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        main_layout.addWidget(self.video_list)

        layout.addLayout(main_layout)

        self.setLayout(layout)
        self.setWindowTitle('Tubular')
        self.setWindowIcon(QIcon("tubular.ico"))
        self.setFixedSize(500, 350)
        self.load_video_list()

    def load_video_list(self):
        self.video_list.clear()
        for filename in os.listdir(vid_dir):
            if filename.endswith(('.mp4', '.mp3')):
                self.video_list.addItem(filename)

    def on_item_double_clicked(self, item: QListWidgetItem):
        file_name = item.text()
        full_path = os.path.join(vid_dir, file_name)

        subprocess.Popen(f'explorer /select,"{full_path}"')

    def wipe_downloads(self):
        """Delete all downloaded video and audio files with confirmation."""

        reply = QMessageBox.question(
            self,
            'Confirm Wipe',
            'Are you sure you want to delete all downloaded files?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for filename in os.listdir(vid_dir):
                if filename.endswith(('.mp4', '.mp3')):
                    try:
                        os.remove(os.path.join(vid_dir, filename))
                    except Exception as e:
                        print(f"Error deleting {filename}: {e}")
            self.load_video_list()
            QMessageBox.information(self, 'Wipe Complete', 'All downloaded files have been deleted.')
        else:
            QMessageBox.information(self, 'Wipe Cancelled', 'No files were deleted.')

    def open_download_location(self):
        print(vid_dir)
        subprocess.Popen(f'explorer "{vid_dir}"')

    def credits(self):
        msg = QMessageBox()
        msg.setText("""
Tubular V1.1
Made with <3 by limeadeTV
        """)
        msg.setStandardButtons(QMessageBox.Close)
        msg.setIconPixmap(QPixmap("tubular.png").scaled(64,64))
        msg.setWindowIcon(QIcon("tubular.ico"))
        msg.setWindowTitle("Credits")
        msg.exec_()

    def start_download(self):
        self.download_thread = YTManager(self.urlbox.text())
        self.download_thread.media_type = self.combobox1.currentText()
        self.download_thread.filename = self.filename.text()
        self.download_thread.quality = self.combobox2.currentText()
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.failed.connect(self.download_failed)
        self.download_thread.prog_log.connect(self.update_prog_log)
        self.download_thread.process.connect(self.media_processing)
        self.progress_bar.setValue(0)
        self.url_input.setDisabled(True)
        self.urlbox.setDisabled(True)
        self.combobox1.setDisabled(True)
        self.filename.setDisabled(True)
        self.combobox2.setDisabled(True)

        self.download_thread.start()

    def update_progress(self, percentage):
        self.progress_bar.setValue(percentage)

    def download_finished(self):
        self.url_input.setDisabled(False)
        self.urlbox.setDisabled(False)
        self.combobox1.setDisabled(False)
        self.filename.setDisabled(False)
        self.combobox2.setDisabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.reset()
        self.load_video_list()
        QMessageBox.information(self, 'Download Complete', 'The media has been downloaded successfully!')

    def download_failed(self):
        self.url_input.setDisabled(False)
        self.urlbox.setDisabled(False)
        self.combobox1.setDisabled(False)
        self.filename.setDisabled(False)
        self.combobox2.setDisabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.reset()
        QMessageBox.information(self, 'Download Failed', 'Failed to download media.')

    def media_processing(self):
        self.progress_bar.setRange(0, 0)

    def update_prog_log(self, message):
        self.prog_log.setText(message)

def main():
    app = QApplication(sys.argv)
    ex = TubularApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
