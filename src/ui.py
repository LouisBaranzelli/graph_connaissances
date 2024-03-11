from typing import Optional, List
import time
import random
import tkinter as tk

class Question():
    def __init__(self, question: str, answer: str):
        self.question = question
        self.answer = answer



class Boutton():

    def __init__(self,canvas: tk.Canvas, x: int, y: int, width: int =100, height:int=20, text: str ='', answer: bool=False, motion: bool = True, **kwargs):

        self.answer = answer
        self.canvas = canvas
        self.border_width = 2
        self.font_size = 9
        self.x1, self.x2 = x - width/2, x + width/2
        self.y1, self.y2 = y - height/2, y + height/2
        radius = 10
        self.rectangle = self.round_rectangle(self.x1, self.y1, self.x2, self.y2, radius,  width=self.border_width, **kwargs)
        self.text = canvas.create_text(x, y, text=text, justify='center', font=("Arial", self.font_size))
        if motion:
            canvas.tag_bind(self.rectangle, '<Motion>', self.event_mousse_position)
        # canvas.tag_bind(rectangle, '<Leave>', on_leave_rectangle)

    def round_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):

        points = [x1 + radius, y1,
                  x1 + radius, y1,
                  x2 - radius, y1,
                  x2 - radius, y1,
                  x2, y1,
                  x2, y1 + radius,
                  x2, y1 + radius,
                  x2, y2 - radius,
                  x2, y2 - radius,
                  x2, y2,
                  x2 - radius, y2,
                  x2 - radius, y2,
                  x1 + radius, y2,
                  x1 + radius, y2,
                  x1, y2,
                  x1, y2 - radius,
                  x1, y2 - radius,
                  x1, y1 + radius,
                  x1, y1 + radius,
                  x1, y1]

        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def event_mousse_position(self, event):
        x, y = event.x, event.y
        if self.is_inside(x, y):
            self.canvas.itemconfig(self.text, font=("Arial", self.font_size, 'bold'))
        else: self.canvas.itemconfig(self.text, font=("Arial", self.font_size))


    def is_inside(self, x, y) -> bool:
        if self.x1 < x < self.x2 and self.y1 < y < self.y2:
           return True
        else: return False



class DisplayQuestion():

    def __init__(self, question: Question, fenetre: tk.Tk, width: Optional[int] = 100, height=200, optional_answers: List[str]=[]):
        self.answers = [(False, optional_answer) for optional_answer in optional_answers] + [(True, question.answer)]
        random.shuffle(self.answers)
        self.fenetre = fenetre
        self.area_question = tk.Canvas(self.fenetre, width=width, height=height)

        Boutton(canvas=self.area_question, x=width/2, y=height/2, width=width*0.99,
                height=height*0.4, text=question.question, answer=False, fill='ivory', motion=False)

        self.answer = None
        self.width = width
        self.height = height
        self.height_answer, self.width_answer = 0.1 * height, 0.48 * width
        self.boutton = []
        for (is_answer, text),(x_boutton, y_boutton) in zip(self.answers, self.get_position_answer()):
            self.boutton.append(
                Boutton(canvas=self.area_question, x=x_boutton, y=y_boutton, width=self.width_answer,
                        height=self.height_answer, text=text, answer=is_answer, fill='pink'))

        self.area_question.pack()
        self.area_question.update()

    def run(self):
        self.area_question.bind('<Button-1>', self.click)
        self.fenetre.mainloop()
        return self.answer

    def get_position_answer(self) -> List[tuple[float, float]]:
        if len(self.answers) == 1:
            return [(self.width/2, 0.8 * self.height)]
        elif len(self.answers) == 2:
            return [(self.width/4, 0.8 * self.height), (3*self.width/4, 0.8 * self.height)]

    def click(self, event):
        inside_boutton = [boutton for boutton in self.boutton if boutton.is_inside(event.x, event.y)]

        if len(inside_boutton) > 0:
            self.area_question.itemconfig(inside_boutton[0].rectangle, outline='black', width=0.5, fill='deep pink')
            self.area_question.update()
            self.answer = inside_boutton[0].answer
            time.sleep(0.1)
            self.area_question.destroy()
            self.fenetre.quit()


class AnswerQuestion():
    def __init__(self, question: Question):
        self.question_step1 = Question(question=question.question, answer='Get the answer ?')
        self.question_step2 = Question(question=f'{question.question} \n Answer: {question.answer} , do you have the answer ?', answer='Yes')

    def run(self) -> bool:
        fenetre = tk.Tk()
        DisplayQuestion(self.question_step1, fenetre, width=500).run()
        return DisplayQuestion(self.question_step2, fenetre, optional_answers=['No'], width=500).run()



if __name__ == '__main__':
    question = Question('Comment tappelle tu ?', 'Louis')

    print(AnswerQuestion(question).run())


