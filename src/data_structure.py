from typing import Optional, Dict, Union, List
from datetime import date
import re


class CommonStructureDataNeo4j():

    '''
    Implementation of the common structure between Node and relation
    '''

    def __init__(self, name: str, category: str, default_properties: Dict,  properties: Optional[Dict] = None):

        self.name = name
        self.id = {'name': name} # Dict of the ID Parameter
        self.properties = properties
        self.default_properties = default_properties
        self.categories = [category.capitalize()]

    def get_properties(self):
        if self.properties is not None:
            # remove the id key if inside the properties
            for key, _ in self.id.items():
                if key in list(self.properties.keys()):
                    del self.properties[key]
        else:
            self.properties = self.default_properties

        # check if no missing element
        for key, value in self.default_properties.items():
            # mandatory setting properties
            if key not in list(self.properties.keys()):
                self.properties.update({key: value})


class Relation(CommonStructureDataNeo4j):
    def __init__(self, name: str, category_target: str, properties: Optional[Dict] = None):

        '''
        Create a relationship part Neo4j code and instantiate the type object of destination of the relationship
        :param name: name of the relation ship
        :param category_target: type of the object resultant of the relation ship
        '''

        self.default_properties = {'creation': f'{str(date.today())}'}
        super().__init__(name=name,
                         category=category_target,
                         default_properties=self.default_properties,
                         properties=properties)

        self.relation = "_".join(name.split()).upper()

        self.syntax_properties = '{' + f'''{', '.join([str(f'{key}: "{str(value)}"') for key, value in self.id.items()])}''' + '}'

    def __str__(self):
        return f'{self.relation} {self.syntax_properties}'


class Node(CommonStructureDataNeo4j):

    def __init__(self, name: str = None, category: str = None, properties: Optional[Dict] = None):

        self.default_properties = {'creation': f'{date.today()}', 'compteur': 0}
        super().__init__(name=name,
                         category=category,
                         default_properties=self.default_properties,
                         properties=properties)

        self.properties['compteur'] = int(self.properties['compteur']) + 1

        self.syntax_properties = '{' + f'''{', '.join([str(f"{key}: '{str(value)}'") for key, value in self.id.items()])}''' + '}'

    def get_code(self):

        # node creation
        instruction_1 = f'''MERGE ({self.name}:{self.categories[0]} {self.syntax_properties})'''
        # update the properties
        instruction_2 = 'SET ' + f',\n'.join([f"{self.name}.{str(name_property)} = '{str(value)}'" for name_property, value in self.properties.items()])

        return f'{instruction_1}\n{instruction_2}'

    def __str__(self):
        return f'''({self.name}:{self.categories[0]} {self.syntax_properties})'''


class Concept(Node):

    def __init__(self, name: str = None, category: str = None, properties: Optional[Dict] = None):

        super().__init__(name, category, properties)
        self.categories.append('Concept')
        self.nodes: List[Node] = []
        self.relations: List[ConceptRelationNode] = []  # all the connections to this concept

    def get_code(self):

        '''
        get list of instruction to create the Concept in cypher
        '''

        code_this_node = [f'''MERGE ({self.name}:{self.categories[0]} {self.syntax_properties})''']

        # update the properties
        instruction_2 = ['SET ' + ',\n'.join(
            [f"{self.name}.{str(name_property)} = '{str(value)}'" for name_property, value in
             self.properties.items()])]

        return [f'{code_this_node[0]}\n{instruction_2[0]}'] + [element.get_code() for element in self.nodes + self.relations]

    def add_relation(self, target: Union[str|Node], relation: Relation):

        '''
        Create a new relation. with an existing Node (of an appropriate catracteristique (Concept or category of the
         relation) or create a new Node of the Category of the relation
        :param target:
        :param relation:
        :return:
        '''

        if isinstance(target, str):
            target = Node(target, relation.categories[0])

        self.relations.append(ConceptRelationNode(self, relation, target))
        self.nodes.append(target)


class ConceptRelationNode:
    def __init__(self, concept: Concept, relation: Relation, noeud2: Node):

        self.concept, self.noeud2 = concept, noeud2
        self.relation = relation

        assert isinstance(concept, Concept), 'Noeud 1 nust be a concept.'
        assert any([cat in relation.categories + concept.categories for cat in noeud2.categories]), f'The target node must be {relation.categories} or {concept.categories} category, get {noeud2.categories}.'

    def get_code(self):
        instruction1 = f'''MATCH{self.concept}, {self.noeud2}\nMERGE({self.concept.name})-[r:{self.relation}]->({self.noeud2.name})'''
        instruction2 = 'SET ' + ',\n'.join(
            [f"r.{str(name_property)} = '{str(value)}'" for name_property, value in
             self.relation.properties.items()])

        return instruction1 + '\n' + instruction2

    def __str__(self):
        return f'''({self.concept.name})-[:{self.relation}]->({self.noeud2.name})'''



if __name__ == '__main__':
    r = Relation('is', 'Caracteristique')
    n1 = Concept('Pierre', 'Personne')

    # n = (Concept(name='Pierre', category='personne'))
    n1.add_relation('petit', r)
    [print(mot) for mot in n1.get_code()]