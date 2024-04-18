
from fastapi import FastAPI
from typing import Dict
from loguru import logger
from datetime import datetime, timedelta
from question_managment import QuestionManagment, SaverNeo4j, ImportExportObjectNeo4j
from data_structure import EnveloppeAnswer, Concept


# Obtenir l'heure et la date actuelles
time_run_server = datetime.now()
time_run_server = time_run_server.strftime("%Y-%m-%d %H:%M:%S")
app = FastAPI()
saver = SaverNeo4j()
i_o = ImportExportObjectNeo4j(saver=saver)

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


# get all the node n-1 and n-2 connected to the concept
# all the node n-2 connected to 1 node are in the same list of value in a dict with key the node n
@app.get("/get_node_n-1_and_n-2/")
async def get_node_n_1(name: str, category: str):
    output = {}
    concept = Concept(name, category)
    nodes = i_o.get_node_connected(concept)
    for node in nodes:
        output[node.name] = [n_node.name for n_node in i_o.get_node_connected(node)]
    return output







