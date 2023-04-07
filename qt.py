import sys
import toupcam
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel, QApplication, QWidget, QDesktopWidget, QCheckBox, QMessageBox, QSlider

class MainWin(QWidget):
    eventImage = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.hcam = None
        self.buf = None      # video buffer
        self.w = 0           # video width
        self.h = 0           # video height
        self.total = 0
        self.setFixedSize(1024, 768)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        self.initUI()
        self.initCamera()

    def initUI(self):
        self.cb = QCheckBox('Auto Exposure', self)
        self.cb.move(5, 10)
        self.cb.stateChanged.connect(self.changeAutoExposure)
        self.sbt = QSlider(1, self)
        self.sbt.setMaximum(15000)
        self.sbt.setMinimum(2000)
        self.sbt.setTickInterval(1)
        self.sbt.sliderMoved.connect(self.changeTemp)
        self.cont = QSlider(1, self)
        self.cont.setMaximum(100)
        self.cont.setMinimum(-100)
        self.cont.setTickInterval(1)
        self.cont.sliderMoved.connect(self.changeContrast)
        self.hue = QSlider(1, self)
        self.hue.setMaximum(180)
        self.hue.setMinimum(-180)
        self.hue.setTickInterval(1)
        self.hue.sliderMoved.connect(self.changeHue)
        self.sat = QSlider(1, self)
        self.sat.setMaximum(255)
        self.sat.setMinimum(0)
        self.sat.setTickInterval(1)
        self.sat.sliderMoved.connect(self.changeSaturation)
        self.bri = QSlider(1, self)
        self.bri.setMaximum(64)
        self.bri.setMinimum(-64)
        self.bri.setTickInterval(1)
        self.bri.sliderMoved.connect(self.changeBrightness)
        self.gam = QSlider(1, self)
        self.gam.setMaximum(180)
        self.gam.setMinimum(20)
        self.gam.setTickInterval(1)
        self.gam.sliderMoved.connect(self.changeGamma)
        self.label = QLabel(self)
        self.label.setScaledContents(True)
        self.sbt.move(100, 0)
        self.labelsbt = QLabel(self)
        self.labelsbt.setText("Temp/Tint:")
        self.labelsbt.move(100, 20)
        self.labelsbtdata = QLabel(self)
        self.labelsbtdata.resize(100, 10)
        self.labelsbtdata.move(155, 20)
        self.cont.move(200, 0)
        self.labelcont = QLabel(self)
        self.labelcont.setText("Contrast:")
        self.labelcont.move(200, 20)
        self.labelcontdata = QLabel(self)
        self.labelcontdata.resize(100, 10)
        self.labelcontdata.move(255, 20)
        self.hue.move(300, 0)
        self.labelhue = QLabel(self)
        self.labelhue.setText("Hue:")
        self.labelhue.move(300, 20)
        self.labelhuedata = QLabel(self)
        self.labelhuedata.resize(100, 10)
        self.labelhuedata.move(355, 20)
        self.labelsat = QLabel(self)
        self.labelsat.setText("Saturation:")
        self.labelsat.move(400, 20)
        self.labelsatdata = QLabel(self)
        self.labelsatdata.resize(100, 10)
        self.labelsatdata.move(455, 20)
        self.labelbri = QLabel(self)
        self.labelbri.setText("Brightness:")
        self.labelbri.move(500, 20)
        self.labelbridata = QLabel(self)
        self.labelbridata.resize(100, 10)
        self.labelbridata.move(555, 20)
        self.labelgam = QLabel(self)
        self.labelgam.setText("Gamma:")
        self.labelgam.move(600, 20)
        self.labelgamdata = QLabel(self)
        self.labelgamdata.resize(100, 10)
        self.labelgamdata.move(655, 20)
        self.sat.move(400, 0)
        self.bri.move(500, 0)
        self.gam.move(600, 0)
        self.label.move(0, 50)
        self.label.resize(self.geometry().width(), self.geometry().height())

# the vast majority of callbacks come from toupcam.dll/so/dylib internal threads, so we use qt signal to post this event to the UI thread
    @staticmethod
    def cameraCallback(nEvent, ctx):
        if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
            ctx.eventImage.emit()

# run in the UI thread
    @pyqtSlot()
    def eventImageSignal(self):
        if self.hcam is not None:
            try:
                self.hcam.PullImageV2(self.buf, 24, None)
                self.total += 1
            except toupcam.HRESULTException as ex:
                QMessageBox.warning(self, '', 'pull image failed, hr=0x{:x}'.format(ex.hr), QMessageBox.Ok)
            else:
                self.setWindowTitle('{}: {}'.format(self.camname, self.total))
                img = QImage(self.buf, self.w, self.h, (self.w * 24 + 31) // 32 * 4, QImage.Format_RGB888)
                self.label.setPixmap(QPixmap.fromImage(img))


    def initCamera(self):
        a = toupcam.Toupcam.EnumV2()
        if len(a) <= 0:
            self.setWindowTitle('No camera found')
            self.cb.setEnabled(False)
        else:
            self.camname = a[0].displayname
            self.setWindowTitle(self.camname)
            self.eventImage.connect(self.eventImageSignal)
            try:
                self.hcam = toupcam.Toupcam.Open(a[0].id)
            except toupcam.HRESULTException as ex:
                QMessageBox.warning(self, '', 'failed to open camera, hr=0x{:x}'.format(ex.hr), QMessageBox.Ok)
            else:
                self.w, self.h = self.hcam.get_Size()
                bufsize = ((self.w * 24 + 31) // 32 * 4) * self.h
                self.buf = bytes(bufsize)
                self.cb.setChecked(self.hcam.get_AutoExpoEnable())
                try:
                    if sys.platform == 'win32':
                        self.hcam.put_Option(toupcam.TOUPCAM_OPTION_BYTEORDER, 0) # QImage.Format_RGB888
                    self.hcam.StartPullModeWithCallback(self.cameraCallback, self)
                except toupcam.HRESULTException as ex:
                    QMessageBox.warning(self, '', 'failed to start camera, hr=0x{:x}'.format(ex.hr), QMessageBox.Ok)

    def changeAutoExposure(self, state):
        if self.hcam is not None:
            self.hcam.put_AutoExpoEnable(state == Qt.Checked)

    def changeTemp (self, state):
        if self.hcam is not None:
            self.labelsbtdata.setText(str(state))
            self.hcam.put_TempTint(state, 1000)

    def changeContrast(self, state):
        if self.hcam is not None:
            self.labelcontdata.setText(str(state))
            self.hcam.put_Contrast(state)

    def changeHue(self, state):
        if self.hcam is not None:
            self.labelhuedata.setText(str(state))
            self.hcam.put_Hue(state)

    def changeSaturation(self, state):
        if self.hcam is not None:
            self.labelsatdata.setText(str(state))
            self.hcam.put_Saturation(state)

    def changeBrightness(self, state):
        if self.hcam is not None:
            self.labelbridata.setText(str(state))
            self.hcam.put_Brightness(state)

    def changeGamma(self, state):
        if self.hcam is not None:
            self.labelgamdata.setText(str(state))
            self.hcam.put_Gamma(state)

    def closeEvent(self, event):
        if self.hcam is not None:
            self.hcam.Close()
            self.hcam = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWin()
    win.show()
    sys.exit(app.exec_())