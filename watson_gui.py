import threading
import sys
import sip

from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from PyQt5 import QtCore, QtWidgets,QtGui


class IBMWatsonManager(QtCore.QObject):
    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()
    messageChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._assistant_id = "8e3469cd-deaa-465f-8f6d-e1e4cbf7d9c1"
        self._session_id = ""
        self._service = None
        self.connected.connect(self.send_message)

        self._is_active = False

    @property
    def assistant_id(self):
        return self._assistant_id

    @property
    def session_id(self):
        return self._session_id

    @property
    def service(self):
        return self._service

    @property
    def is_active(self):
        return self._is_active

    def create_session(self):
        threading.Thread(target=self._create_session, daemon=True).start()

    def _create_session(self):
        authenticator = IAMAuthenticator(
            "4CpKAKUsLRpYvcUX_nQRR1MGnYM1WqJLUhE4XS-p4B7Y"
        )  # replace with API key
        self._service = AssistantV2(version="2020-04-01", authenticator=authenticator)
        self.service.set_service_url(
            "https://api.eu-gb.assistant.watson.cloud.ibm.com/instances/49abc832-b899-4359-aca3-ea100ceb777a"
        )

        self._session_id = self.service.create_session(
            assistant_id=self.assistant_id
        ).get_result()["session_id"]
        self._is_active = True
        self.connected.emit()

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(str)
    def send_message(self, text=""):
        threading.Thread(target=self._send_message, args=(text,), daemon=True).start()

    def _send_message(self, text):
        response = self.service.message(
            self.assistant_id, self.session_id, input={"text": text}
        ).get_result()
        generic = response["output"]["generic"]
        if generic:
            t = "\n".join([g["text"] for g in generic if g["response_type"] == "text"])
            self.messageChanged.emit(t)
        output = response["output"]
        if "actions" in output:
            client_response = output["actions"][0]
            if client_response["type"] == "client":
                current_action = client_response["name"]
                if current_action == "end_conversation":
                    self._close_session()
                    self._is_active = False
                    self.disconnected.emit()

    def _close_session(self):
        self.service.delete_session(
            assistant_id=self.assistant_id, session_id=self.session_id
        )


class Widget(QtWidgets.QWidget):
    sendSignal = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui(Dialog)

    def init_ui(self,Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(642, 800)

        #Text 
        self.message_lbl = QtWidgets.QTextBrowser(Dialog)
        self.message_lbl.setGeometry(QtCore.QRect(30, 20, 580, 670))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.message_lbl.setFont(font)
        self.message_lbl.setObjectName("textBrowser")

        #Button 
        self.send_button = QtWidgets.QPushButton(Dialog)
        self.send_button.setGeometry(QtCore.QRect(520, 725, 90, 40))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.send_button.setFont(font)
        self.send_button.setObjectName("pushButton")

        #Text Input 
        self.message_le = QtWidgets.QLineEdit(Dialog)
        self.message_le.setGeometry(QtCore.QRect(30, 725, 470, 40))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.message_le.setFont(font)
        self.message_le.setObjectName("lineEdit")
        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

        self.disable()
        self.send_button.clicked.connect(self.on_clicked)


    @QtCore.pyqtSlot()
    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.send_button.setText(_translate("Dialog", "Send"))

    @QtCore.pyqtSlot()
    def enable(self):
        self.message_le.setEnabled(True)
        self.send_button.setEnabled(True)

    @QtCore.pyqtSlot()
    def disable(self):
        self.message_le.setEnabled(False)
        self.send_button.setEnabled(False)

    @QtCore.pyqtSlot()
    def on_clicked(self):
        text = self.message_le.text()
        self.message_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.message_lbl.append("You : ")
        self.message_lbl.append(text)
        self.message_lbl.append("\n")
        self.sendSignal.emit(text)
        self.message_le.clear()

    @QtCore.pyqtSlot(str)
    def set_message(self, text):
        self.message_lbl.setAlignment(QtCore.Qt.AlignLeft)
        self.message_lbl.append("Bot : ")
        self.message_lbl.append(text)
        self.message_lbl.append("\n")

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    Dialog = QtWidgets.QMainWindow()
    w = Widget()
    w.init_ui(Dialog)
    Dialog.show()

    manager = IBMWatsonManager()

    manager.connected.connect(w.enable)
    manager.disconnected.connect(w.disable)
    w.sendSignal.connect(manager.send_message)
    manager.messageChanged.connect(w.set_message)

    manager.create_session()

    sys.exit(app.exec_())