
from fastapi import FastAPI
from typing import Dict
from loguru import logger
from datetime import datetime, timedelta
from question_managment import QuestionManagment, SaverNeo4j
from data_structure import EnveloppeAnswer


# Obtenir l'heure et la date actuelles
time_run_server = datetime.now()
time_run_server = time_run_server.strftime("%Y-%m-%d %H:%M:%S")
app = FastAPI()
saver = SaverNeo4j()

# generate a question
@app.get("/question/")
async def get_question():
    global question_managment
    question_managment = QuestionManagment(saver=saver)
    question = question_managment.create_enveloppe()
    logger.info('Generation new question')
    return {'question': question}


# send the dict of answer with the correct answers
@app.post("/answer/")
async def answer(answer: Dict):
    global question_managment
    answers = EnveloppeAnswer(answer)
    question_managment.submit_answer(answers)








