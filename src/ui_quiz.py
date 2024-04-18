
import random
import requests
from loguru import logger
import sys
from typing import Dict, Optional, List
from PyQt5.QtWidgets import  QVBoxLayout, QListWidget,QScrollArea, QCompleter, QPushButton, QListWidgetItem,  QLabel, QLineEdit, QGridLayout, QWidget, QApplication
from PyQt5.QtCore import QStringListModel, Qt
from PyQt5.QtGui import QIcon, QColor, QFont
from data_structure import EnveloppeQuestion, InformationAPI


class QPushButtonQuestion(QPushButton):

    def __init__(self, text: str, status: bool, **kwargs):
        QPushButton.__init__(self, text)
        self.status = status
        self.value = text

class MainWindowQuestion():
    pass

class Question(QWidget):
    ''' Main class to decline all the differente choices of answers '''
    def __init__(self, enveloppe: EnveloppeQuestion, parent: MainWindowQuestion, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.parent = parent
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        width_question = 50
        self.setGeometry(0, 0, 800, width_question * len(enveloppe.answers+enveloppe.false_answers)//2 + 1)
        self.answers = enveloppe.answers
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

        self.dict_answer: List[str: QPushButtonQuestion] = {}

        self.answer_correct: Dict[QPushButtonQuestion, bool] = {} # check if the answer are answered (if inside) + wll answered or not
        for answer, verite in dict_shuffled.items():
            # Integrate truth information inside the button
            boutton = QPushButtonQuestion(text=answer, status=verite)
            self.dict_answer[answer] = boutton
            boutton.setFixedHeight(width_question)
            boutton.clicked.connect(self.reveal_truth)

            if index_col > 1:
                index_col = 0
                index_line += 1
            self.layout.addWidget(boutton, index_col, index_line)  # 2eme ligne / 1ere colone
            index_col += 1

    def reveal_truth(self):
        sender_button = self.sender()
        if sender_button.status is True:
            sender_button.setStyleSheet("background-color: green")
            self.answer_correct[sender_button.value] = True
        else:
            sender_button.setStyleSheet("background-color: red")
            self.answer_correct[sender_button.value] = False

        # activate a the parent function when a choice is made
        self.parent.question_answer_action()

    def reveal_all(self):
        ''' Show all the answers '''
        for _, boutton in self.dict_answer.items():
            if boutton.status is True:
                boutton.setStyleSheet("background-color: green")

            else:
                boutton.setStyleSheet("background-color: red")



    def all_is_true(self):
        # Check All the true answers have been answered
        if all([true_title in list(self.answer_correct.keys()) for true_title in [true_titles for true_titles, boutton in self.dict_answer.items() if boutton.status == True]]):
            return True
        return False

    def any_false(self):
        # Check All the true answers have been answered
        if any([false_title in list(self.answer_correct.keys()) for false_title in [false_titles for false_titles, boutton in self.dict_answer.items() if boutton.status == False]]):
            return True
        return False


class MainWindowQuestion(QWidget):

    def __init__(self, enveloppe_question: EnveloppeQuestion, *args, **kwargs):

        QWidget.__init__(self, *args, **kwargs)
        self.question_widget = Question(enveloppe_question, self)
        self.setGeometry(0, 0, 1000, 1000)
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        # Creation de la zone de la question
        self._question = QLabel(self.question_widget.question)
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
        self.layout.addWidget(self.question_widget,5, 2, 1, 4)


        # create buttons
        self.button_next = QPushButton('Suivant')
        self.button_next.clicked.connect(self.suivant)
        self.button_next.setEnabled(False)
        self.layout.addWidget(self.button_next, 7, 7)  # 2eme ligne / 1ere colone

        button_prec = QPushButton('Précédent')
        button_prec.clicked.connect(self.precedent)
        self.layout.addWidget(button_prec, 7, 0)

        self.show()

    def check_answer(self):
        pass

    def question_answer_action(self):
        ''' function call when a answer is clicked'''
        if self.question_widget.all_is_true():
            self.button_next.setEnabled(True)
            self.check_answer() # update in Neo4j

        # if mistake show all the answers
        if self.question_widget.any_false():
            self.question_widget.reveal_all()
            self.button_next.setEnabled(True)
            self.check_answer() # update in Neo4j

    def switch_question(self, question: Question):
        self.question_widget.deleteLater()
        self.question_widget = question
        self.question = question.question # change l'intitule de la question
        self.layout.addWidget(question, 5, 2, 1, 4)
        self.button_next.setEnabled(False)


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




class InteractionMainWindowQuestion(MainWindowQuestion, InformationAPI):
    ''' Implement the interaction of the buttons with the server side '''
    def __init__(self):
        InformationAPI.__init__(self)
        # initialisation of the first question
        feedback = requests.get(self.url_question).json()
        enveloppe_question = EnveloppeQuestion(**feedback['question'])
        MainWindowQuestion.__init__(self, enveloppe_question)
        self.show()

    def suivant(self):
        '''
        Ask a new question.
        :return:
        '''
        feedback = requests.get(self.url_question).json()
        enveloppe_question = EnveloppeQuestion(**feedback['question'])
        question = Question(enveloppe_question, self)
        self.switch_question(question)

    def check_answer(self):
        ''' if one mistake all true elements are considerated as a mistake'''
        if self.question_widget.all_is_true():
            answers = {element: True for element in self.question_widget.answers}

        if self.question_widget.any_false():
            answers = {element: False for element in self.question_widget.answers}
        requests.post(self.url_answer, json=answers)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InteractionMainWindowQuestion()
    window.show()
    sys.exit(app.exec())




