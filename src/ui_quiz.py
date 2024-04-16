
import random
import requests
from loguru import logger
import sys
from typing import Dict, Optional, List
from PyQt5.QtWidgets import  QVBoxLayout, QListWidget,QScrollArea, QCompleter, QPushButton, QListWidgetItem,  QLabel, QLineEdit, QGridLayout, QWidget, QApplication
from PyQt5.QtCore import QStringListModel, Qt
from PyQt5.QtGui import QIcon, QColor, QFont
from data_structure import EnveloppeQuestion


class QPushButtonQuestion(QPushButton):

    def __init__(self, text: str, status: bool, **kwargs):
        QPushButton.__init__(self, text)
        self.status = status


class Question(QWidget):
    ''' Main class to decline all the differente choices of answers '''
    def __init__(self, enveloppe: EnveloppeQuestion, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        width_question = 50
        self.setGeometry(0, 0, 800, width_question * len(enveloppe.answers+enveloppe.false_answers)//2 + 1)

        self.question = enveloppe.question
        # Create dict of answer true and false
        answers = {}
        for element in enveloppe.answers:
            answers[element] = True
        for element in enveloppe.false_answers:
            answers[element] = False

        # shuffle the dictionnary
        tampon = list(answers.items())
        random.shuffle(tampon)
        dict_shuffled = dict(tampon)
        index_line = 0
        index_col = 0
        for answer, verite in dict_shuffled.items():
            # Integrate truth information inside the button
            verite = QPushButtonQuestion(text=answer, status=verite)
            verite.setFixedHeight(width_question)
            verite.clicked.connect(self.reveal_truth)

            if index_col > 1:
                index_col = 0
                index_line += 1
            self.layout.addWidget(verite, index_col, index_line)  # 2eme ligne / 1ere colone
            index_col += 1

    def reveal_truth(self):
        sender_button = self.sender()
        if sender_button.status is True:
            sender_button.setStyleSheet("background-color: green")
        else:
            sender_button.setStyleSheet("background-color: red")


class MainWindowQuestion(QWidget):

    def __init__(self, question_widget: Question, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.question_widget = question_widget
        self.setGeometry(0, 0, 1000, 1000)
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        # Creation de la zone de la question
        self._question = QLabel(question_widget.question)
        self._question.setAlignment(Qt.AlignCenter)
        self._question.setFixedHeight(230)
        font = QFont()
        font.setPointSize(16)
        self.layout.addWidget(self._question, 2, 2, 5, 4)
        self._question.setFont(font)
        # Définir la couleur de fond en blanc
        self._question.setAutoFillBackground(True)
        palette = self._question.palette()
        palette.setColor(self._question.backgroundRole(), QColor("red"))
        self._question.setPalette(palette)

        # add space vetween question and choices
        space = QWidget()
        space.setFixedHeight(300)
        self.layout.addWidget(space, 4, 2, 1, 4)

        # add the choices
        self.layout.addWidget(question_widget,5, 2, 1, 4)


        # create buttons
        self.button_next = QPushButton('Suivant')
        self.button_next.clicked.connect(self.suivant)
        self.layout.addWidget(self.button_next, 7, 7)  # 2eme ligne / 1ere colone

        button_prec = QPushButton('Précédent')
        button_prec.clicked.connect(self.precedent)
        self.layout.addWidget(button_prec, 7, 0)

        self.show()

    def switch_question(self, question: Question):
        self.question_widget.deleteLater()
        self.question_widget = question
        self.question = question.question # change l'intitule de la question
        self.layout.addWidget(question, 5, 2, 1, 4)

    def precedent(self):
        pass

    def suivant(self):
        pass

    @property
    def question(self):
        return self._question.text()

    @question.setter
    def question(self, text: str):
        self._question.setText(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InteractionMainWindowQuestion()
    window.show()
    sys.exit(app.exec())




