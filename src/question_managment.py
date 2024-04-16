from abc import ABC, abstractmethod
import random
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from data_structure import Node, ConceptRelationNode, Concept, Relation, EnveloppeQuestion, EnveloppeAnswer
from requetes_neo4j import SaverNeo4j, ImportExportObjectNeo4j, ModifyConcept
from loguru import logger


class QuestionType(ImportExportObjectNeo4j):
    """
    Server - side
    In relation with neo4j Create the possible answers and the question
    if we submit a ConceptRelationNode
    """

    def __init__(self, saver: SaverNeo4j, **kwargs):

        ImportExportObjectNeo4j.__init__(self, saver=saver)
        self.false_results: [ConceptRelationNode] = []

    def get_elements(self) -> Dict:
        pass

    def get_prompt(self) -> str:
        pass

    def is_valid(self) -> bool:
        if self.false_results is None:
            return False
        else:
            return True


class QuestionTypeOnConcept(QuestionType):
    '''
    question to identify the matching concepts
    C1 -R0-> N1 <-R0- C2
    wrong result:
    C1 -R0-> N2 // C1 -R0-> N1
    exemple :

    (1) Pierre eats poire (we test here mange between Pierre and poire)
    (2) Anne eats poire
    (3) Claire eats salade

    Question: Who eats poire
    choice: Claire / Anne / Pierre
    answer Pierre and Anne:


    '''

    def __init__(self, c_r_n: ConceptRelationNode,  nbr_true: int = 3, nbr_false: int = 3, saver: SaverNeo4j=None):

        QuestionType.__init__(self, saver=saver)

        self.c_r_n = c_r_n
        # get the matching results

        instruction = "MATCH (n1)-[r:`" + c_r_n.relation.relation + "`]->(n2:" + c_r_n.noeud2.categories[0] + " {name: '" + c_r_n.noeud2.name + "'})\nRETURN n1"
        results = self.send_instruction(instruction)

        # generate the ConceptRelationNode list result
        self.true_results = {result['n1']['name']: ConceptRelationNode(Concept(name=result['n1']['name'], category=c_r_n.concept.categories[0]), c_r_n.relation,  c_r_n.noeud2) for result in results[:nbr_true]}

        # get the NO matching results
        # tout les concept qui ont la meme relation mais qui ne pointe pas vers le meme noeud
        instruction = f"MATCH (n1)-[:" + c_r_n.relation.relation + "]->(n2)\nWHERE  NOT (n1)-[:" + c_r_n.relation.relation + "]-(:" + c_r_n.noeud2.categories[0] + " {name: '" + c_r_n.noeud2.name + "'})\nRETURN n1"

        results = self.send_instruction(instruction)

        if len(results) == 0:
            self.false_results = None
        else:
            # generate the ConceptRelationNode list result
            self.false_results = {result['n1']['name']: ConceptRelationNode(Concept(name=result['n1']['name'],
                                                                                  category=c_r_n.concept.categories[0]), c_r_n.relation,
                                                                                  noeud2=c_r_n.noeud2) for result in results[:nbr_false]}
        pass

    def get_prompt(self) -> str:

        options = list(self.true_results.keys()) + list(self.false_results.keys())
        random.shuffle(options)
        return f'''
        Parmi ces elements: {','.join(options)},
        Action: {self.c_r_n.relation}
        Target: {self.c_r_n.noeud2}
        '''


class SimpleQuestionOnConcept(QuestionTypeOnConcept):

    '''
    Question with choices answer expected I know or I dont know
    '''

    def __init__(self, c_r_n: ConceptRelationNode, saver: SaverNeo4j = None):
        QuestionTypeOnConcept.__init__(self, c_r_n, saver=saver)

        self.true_results = {'yes': c_r_n}
        self.false_results = {'No': c_r_n}

    def get_prompt(self) -> str:

        # only 1 answer
        options = list(self.true_results.values())

        # no alternative choice

        random.shuffle(options)
        return f'''
        Qui ou quoi realise,
        Action: {self.c_r_n.relation}
        sur Target: {self.c_r_n.noeud2}
        Connais tu la reponse
        '''

    def is_valid(self) -> bool:
        return True


class QuestionTypeOnNode(QuestionType):
    '''
    question to identify differents relations target toward a common node:
    C1 -R0-> N1
    C1 -R0-> N2
    C2 -R0-> N3

    question on C1 and R0, good answer N1 and N2, wrong answer N3


    exemple :

    (1) Pierre eats poire (we test here mange between Pierre and poire)
    (2) Pierre eats fraise
    (3) Claire eats salade

    Question: what eats Pierre
    choice: poire, fraise, salade
    answer poire and fraise


    '''

    def __init__(self, c_r_n: ConceptRelationNode,  nbr_true: int = 2, nbr_false: int = 2, saver: SaverNeo4j = None):

        QuestionType.__init__(self, saver=saver)

        self.c_r_n = c_r_n
        # get the matching results

        instruction = "MATCH (n1:" + c_r_n.concept.categories[0] + " {name: '" + c_r_n.concept.name + "'})-[r:`" + c_r_n.relation.relation + "`]->(n2)\nRETURN n2"
        results1 = self.send_instruction(instruction)

        # generate the ConceptRelationNode list result
        self.true_results = {result['n2']['name']: ConceptRelationNode(c_r_n.concept, c_r_n.relation, Node(result['n2']['name'], c_r_n.noeud2.categories[0])) for result in results1[:nbr_true]}

        # get the NO matching results: all the concept category with this relation ship
        # instruction = "MATCH (n1)-[r:`" + c_r_n.relation.relation + "`]->(n2:" + c_r_n.relation.categories[0] + ")\nRETURN n2"
        instruction = f"MATCH (n1)-[:" + c_r_n.relation.relation + "]->(n2)\nWHERE  NOT (n1:" + c_r_n.concept.categories[0] + " {name: '" + c_r_n.concept.name + "'})-[:" + c_r_n.relation.relation + "]->(n2)\nRETURN n2"
        results2 = self.send_instruction(instruction)

        if len(results2) == 0:
            self.false_results = None
        else:
            # generate the ConceptRelationNode list result
            self.false_results = {result['n2']['name']: ConceptRelationNode(c_r_n.concept, c_r_n.relation,
                                                Node(result['n2']['name'], c_r_n.noeud2.categories[0])) for result
                            in results2[:nbr_false]}

        # cas rare ou une clef est dans le false et true dictionnary:
        # si le node target par une relation vrai avec la concept et avec un autre concept
        # on le supprime des faux_results
        to_delet =[]
        for key in self.false_results.keys():
            if key in list(self.true_results.keys()):
                to_delet.append(key)
        [self.false_results.pop(element) for element in to_delet]


    def get_prompt(self) -> str:

        options = list(self.true_results.keys()) + list(self.false_results.keys())
        random.shuffle(options)
        return f'''
        Parmi ces elements: {','.join(options)},
        Action: {self.c_r_n.relation}
        Sujet: {self.c_r_n.concept}
        '''


class SimpleQuestionOnNode(QuestionTypeOnNode):

    '''
    Question with choices answer expected I know or I dont know
    '''

    def __init__(self, c_r_n: ConceptRelationNode,  saver: SaverNeo4j = None):
        QuestionTypeOnNode.__init__(self, c_r_n, saver=saver)

        self.true_results = {'yes': c_r_n}
        self.false_results = {'No': c_r_n}

    def get_prompt(self) -> str:

        # only 1 answer
        options = list(self.true_results.values())

        # no alternative choice

        random.shuffle(options)
        return f'''
        Qu'est ce que {self.c_r_n.concept}
        Action: {self.c_r_n.relation}
       
        Connais tu la reponse
        '''



class QuestionManagment(ImportExportObjectNeo4j):
    '''
    Get any ConceptRelationNode (randomly), generate, the question types and choose one
    Ceeate EnveloppeQuestion object.
    '''
    def __init__(self, saver: SaverNeo4j, **kwargs):
        ImportExportObjectNeo4j.__init__(self, saver=saver, **kwargs)
        c_r_ns = self.get_all_relations()
        # get all the relation with a correct datetime now > the planned one
        c_r_ns = [c_r_n for c_r_n in c_r_ns if datetime.strptime(c_r_n.relation.properties['next'] , "%Y-%m-%d") < datetime.today()]
        if c_r_ns == 0:
            logger.info('All knowledges up to date !')
        random.shuffle(c_r_ns)
        self.c_r_n = c_r_ns[0]
        questions = [QuestionTypeOnConcept(self.c_r_n, saver=saver), QuestionTypeOnNode(self.c_r_n, saver=saver), SimpleQuestionOnConcept(c_r_n=self.c_r_n, saver=saver), SimpleQuestionOnConcept(c_r_n=self.c_r_n, saver=saver)]
        questions = [question for question in questions if question.is_valid()] # keep question with at leat 1 wrong choice
        random.shuffle(questions)
        self.question = questions[0] # QuestionType
        self.answers = {}
        self.answers.update(self.question.true_results)
        self.answers.update(self.question.false_results)


    def create_enveloppe(self) -> Tuple[EnveloppeAnswer, EnveloppeQuestion]:
        question = EnveloppeQuestion(question=self.question.get_prompt(),
                                     answers=list(self.question.true_results.keys()),
                                     false_answers=list(self.question.false_results.keys()))

        answer_user = EnveloppeAnswer(question)

        return answer_user, question

    def submit_answer(self, answers: EnveloppeAnswer):
        for key_answer, value in answers.dict_answer.items():
            c_r_n = ModifyConcept(self.answers[key_answer])
            if value == 1:
                c_r_n.increase_level()
            else:
                c_r_n.decrease_level()










        # pour la validation considerer les 2 cas si la question est de type simplequestiom





if __name__ == '__main__':
    saver = SaverNeo4j()
    a = QuestionManagment(saver=saver)
    answer, question = a.create_enveloppe()


