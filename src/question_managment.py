from abc import ABC, abstractmethod
import random

from typing import Dict
from data_structure import Node, ConceptRelationNode, Concept, Relation
from requetes_neo4j import SaverNeo4j


class QuestionType(ABC, SaverNeo4j):
    @abstractmethod
    def __init__(self, **kwargs):
        SaverNeo4j.__init__(self)
        ABC.__init__(self)

    @abstractmethod
    def get_elements(self) -> Dict:
        pass

    @abstractmethod
    def get_prompt(self) -> str:
        pass


class QuestionTypeConceptFromRelation(QuestionType):
    '''
    question to identify differents relations target toward a common node:
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

    def __init__(self, c_r_n: ConceptRelationNode,  nbr_true: int = 2, nbr_false: int = 2):

        QuestionType.__init__(self)

        print(c_r_n)
        self.c_r_n = c_r_n
        # get the matching results

        instruction = "MATCH (n1)-[r:`" + c_r_n.relation.relation + "`]->(n2:" + c_r_n.noeud2.categories[0] + " {name: '" + c_r_n.noeud2.name + "'})\nRETURN n1"
        print('True instruction', instruction)
        results = self.send_instruction(instruction)


        # generate the ConceptRelationNode list result
        self.true_results = [ConceptRelationNode(c_r_n.concept, c_r_n.relation, Node(result['n1']['name'], c_r_n.noeud2.categories[0])) for result in results][:nbr_true]
        if c_r_n not in self.true_results:
            self.true_results[0] = c_r_n

        # get the NO matching results
        instruction = "MATCH (n1:" + c_r_n.concept.categories[0] + ")-[r:`" + c_r_n.relation.relation + "`]->(n2:" + c_r_n.noeud2.categories[0] + ")\nWHERE n2.name <> '"+ c_r_n.noeud2.name + "' AND n1.name <> '" + c_r_n.concept.name + "'\nRETURN n1"
        print('False instruction', instruction)
        results = self.send_instruction(instruction)
        if len(results) == 0:
            return None
        else:
            # generate the ConceptRelationNode list result
            self.false_results = [ConceptRelationNode(c_r_n.concept, c_r_n.relation,
                                                Node(result['n1']['name'], c_r_n.noeud2.categories[0])) for result
                            in results][:nbr_false]


    def get_elements(self) -> Dict:

        '''
        Return dict true answer * (nbr_true) if possible and alternative false answer * (nbr_false) if possible
        :param nbr_true: nbr true answer returned
        :param nbr_false:  nbr false answer returned
        :return:
        '''

        return {'True': list(set([c_r_n.noeud2.name for c_r_n in self.true_results])), 'False': list(set([c_r_n.noeud2.name for c_r_n in self.false_results]))}

    def get_prompt(self) -> str:

        options = self.get_elements()['True'] + self.get_elements()['False']
        random.shuffle(options)
        return f'''
        Parmi ces elements: {','.join(options)},
        Action: {self.c_r_n.relation}
        Target: {self.c_r_n.noeud2}
        '''


class QuestionTypeNodesRelation(QuestionType):
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

    def __init__(self, c_r_n: ConceptRelationNode,  nbr_true: int = 2, nbr_false: int = 2):

        QuestionType.__init__(self)

        print(c_r_n)
        self.c_r_n = c_r_n
        # get the matching results

        instruction = "MATCH (n1:" + c_r_n.concept.categories[0] + " {name: '" + c_r_n.concept.name + "'})-[r:`" + c_r_n.relation.relation + "`]->(n2)\nRETURN n2"
        print('True instruction', instruction)
        results1 = self.send_instruction(instruction)

        # generate the ConceptRelationNode list result
        self.true_results = [ConceptRelationNode(c_r_n.concept, c_r_n.relation, Node(result['n2']['name'], c_r_n.noeud2.categories[0])) for result in results1][:nbr_true]
        if c_r_n not in self.true_results:
            self.true_results[0] = c_r_n

        # get the NO matching results: all the concept category with this relation ship
        instruction = "MATCH (n1)-[r:`" + c_r_n.relation.relation + "`]->(n2:" + c_r_n.relation.categories[0] + ")\nRETURN n2"
        print('False instruction', instruction)
        results2 = self.send_instruction(instruction)
        results2 = [result2 for result2 in results2 if result2['n2']['name'] not in [result1['n2']['name'] for result1 in results1]]

        if len(results2) == 0:
            self.false_results = None
        else:
            # generate the ConceptRelationNode list result
            self.false_results = [ConceptRelationNode(c_r_n.concept, c_r_n.relation,
                                                Node(result['n2']['name'], c_r_n.noeud2.categories[0])) for result
                            in results2][:nbr_false]

        pass


    def get_elements(self) -> Dict:

        '''
        Return dict true answer * (nbr_true) if possible and alternative false answer * (nbr_false) if possible
        :param nbr_true: nbr true answer returned
        :param nbr_false:  nbr false answer returned
        :return:
        '''

        return {'True': list(set([c_r_n.noeud2.name for c_r_n in self.true_results])), 'False': list(set([c_r_n.noeud2.name for c_r_n in self.false_results]))}

    def get_prompt(self) -> str:

        options = self.get_elements()['True'] + self.get_elements()['False']
        random.shuffle(options)
        return f'''
        Parmi ces elements: {','.join(options)},
        Action: {self.c_r_n.relation}
        Sujet: {self.c_r_n.concept}
        '''




if __name__ == '__main__':
    saver = SaverNeo4j()
    relations = saver.get_all_relations()
    a = QuestionTypeNodesRelation(relations[0])
    print(a.get_elements())
    print(a.get_prompt())
