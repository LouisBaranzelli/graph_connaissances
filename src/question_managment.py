import os
from pathlib import Path
import pandas as pd
from datetime import datetime, date, timedelta
from ui import AnswerQuestion, Question


class Dataset():
    def __init__(self, path_dataset: Path):

        assert path_dataset.is_file(), f'{path_dataset} does not exist'
        self.path_csv = path_dataset
        self.pd_quiz = pd.read_csv(path_dataset, sep=';')
        self.pd_quiz = AutoCheckDataset(self).dataset
        self.available_state = [1, 3, 7, 21]
        while(True):
            if not self.get_question():
                break

    def get_question(self):
        # available_question = self.pd_quiz.loc[]#
        # les ligne dont nbr de jour / frequence de rapel > 0
        available_questions = self.pd_quiz.loc[self.pd_quiz.days_before_last / self.pd_quiz.apply(lambda row: self.available_state[row.state], axis=1) >= 1]
        available_questions = available_questions.loc[str(date.today()) != self.pd_quiz.date] # question must not has been asked today
        if len(available_questions) == 0:
            return False

        available_question = available_questions.sample(n=1)
        object_question = Question(available_question.question.values[0], available_question.reponse.values[0])

        answer = AnswerQuestion(object_question).run()

        self.pd_quiz.loc[available_question.index[0], 'date'] = str(date.today())
        self.pd_quiz.loc[available_question.index[0], 'historique'] = f"{str(self.pd_quiz.loc[available_question.index[0], 'historique'])} {str(date.today())}/"

        state = self.pd_quiz.loc[available_question.index[0], 'state']
        if answer:
            if state < len(self.available_state):
                self.pd_quiz.loc[available_question.index[0], 'state'] += 1
        else:
            if state > 0:
                self.pd_quiz.loc[available_question.index[0], 'state'] -= 1

        self.pd_quiz.to_csv(self.path_csv, sep=';', index=False)
        return True


class AutoCheckDataset():
    def __init__(self, dataset: Dataset):
        self.dataset = dataset.pd_quiz
        self.check_header()
        self.check_rows()

    def check_header(self):
        headers = ['date', 'historique', 'days_before_last']
        for header in headers:
            if header not in self.dataset.columns:
                self.dataset[header] = ''

    def check_rows(self):

        # add a last date if new element
        for index, row in self.dataset.iterrows():
            if pd.isna(row.date):
                self.dataset.iloc[index, self.dataset.columns.get_loc('date')] = str(date.today() - timedelta(days=1))
            if pd.isna(row.historique):
                self.dataset.iloc[index, self.dataset.columns.get_loc('historique')] = ''

        for index, row in self.dataset.iterrows():
            # update the number of days before the last reading of the data
            list_date = row.date.split('-') if not pd.isna(row.date) else []
            if len(list_date) == 3:
                last_day = date(int(list_date[0]), int(list_date[1]), int(list_date[2]))
                self.dataset.iloc[index, self.dataset.columns.get_loc('days_before_last')] = (date.today() - last_day).days
            else: row.days_before_last = 1


    def __str__(self):
        return self.dataset







if __name__ == '__main__':
    Dataset(Path('../quiz.csv'))