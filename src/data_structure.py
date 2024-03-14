from typing import Optional, Dict, Union, List
from datetime import date
import re

class Relation:
    def __init__(self, name: str, category_target: str, properties: Optional[Dict] = None):

        '''
        Create a relationship part Neo4j code and instantiate the type object of destination of the relationship
        :param name: name of the relation ship
        :param category_target: type of the object resultant of the relation ship
        '''

        self.name = name
        self.category = category_target.capitalize()
        self.relation = "_".join(name.split()).upper()

        id_properties = {'name': self.name}

        mandatory_settings = {'creation': f'{str(date.today())}'}
        if properties is not None:
            self.update_properties = properties
            # remove the id key if inside the properties
            for key, _ in id_properties.items():
                if key in list(self.update_properties.keys()):
                    del self.update_properties[key]
        else:
            self.update_properties = mandatory_settings

        # check if no missing element
        for key, value in mandatory_settings.items():
            # mandatory setting properties
            if key not in list(self.update_properties.keys()):
                self.update_properties.update({key: value})
            # value must be between ""
            if not re.match(r'^".*"$', self.update_properties[key]):
                self.update_properties[key] = f"'{self.update_properties[key]}'"

        self.syntax_properties = '{' + f'''{', '.join([str(f'{key}: "{str(value)}"') for key, value in id_properties.items()])}''' + '}'

    def __str__(self):
        return f'{self.relation} {self.syntax_properties}'


class Node:

    def __init__(self, name: str = None, category: str = None, properties: Optional[Dict] = None):
        self.name = name
        self.categories = [category.capitalize()]

        self.id = {'name': name}

        mandatory_settings = {'creation': f'{date.today()}', 'compteur': 0}
        if properties is not None:
            self.update_properties = properties
            # remove the id key if inside the properties
            for key, _ in self.id.items():
                if key in list(self.update_properties.keys()):
                    del self.update_properties[key]
        else:
            self.update_properties = mandatory_settings

        # check if no missing element
        for key, value in mandatory_settings.items():
            # mandatory setting properties
            if key not in list(self.update_properties.keys()):
                self.update_properties.update({key: value})
            # # value must be between ""
            # if not re.match(r'^".*"$', self.update_properties[key]):
            #     self.update_properties[key] = f"'{self.update_properties[key]}'"

        self.update_properties['compteur'] = int(self.update_properties['compteur']) + 1
        # self.update_properties['compteur'] = int(re.findall(r'\b\d+\b', self.update_properties['compteur'])[0])
        # self.update_properties['compteur'] = str(self.update_properties['compteur'] + 1)

        self.syntax_properties = '{' + f'''{', '.join([str(f"{key}: '{str(value)}'") for key, value in self.id.items()])}''' + '}'

    def get_code(self):

        # node creation
        instruction_1 = f'''MERGE ({self.name}:{self.categories[0]} {self.syntax_properties})'''
        # update the properties
        instruction_2 = 'SET ' + f',\n'.join([f"{self.name}.{str(name_property)} = '{str(value)}'" for name_property, value in self.update_properties.items()])

        return f'{instruction_1}\n{instruction_2}'

    def __str__(self):
        return f'''({self.name}:{self.categories[0]} {self.syntax_properties})'''


class Concept(Node):

    def __init__(self, name: str = None, category: str = None, properties_node: Optional[Dict] = None):

        super().__init__(name, category, properties_node)
        self.categories.append('Concept')
        self.nodes: List[Node] = []
        self.connections: List[ConceptRelationNode] = [] # all the connections to this concept

    def get_code(self):

        '''
        get list of instruction to create the Concept in cypher
        '''

        code_this_node = [f'''MERGE ({self.name}:{self.categories[0]} {self.syntax_properties})''']

        # update the properties
        instruction_2 = ['SET ' + ',\n'.join(
            [f"{self.name}.{str(name_property)} = '{str(value)}'" for name_property, value in
             self.update_properties.items()])]

        return [f'{code_this_node[0]}\n{instruction_2[0]}'] + [element.get_code() for element in self.nodes + self.connections]

    def add_relation(self, target: Union[str|Node], relation: Relation):

        '''
        Create a new relation. with an existing Node (of an appropriate catracteristique (Concept or category of the
         relation) or create a new Node of the Category of the relation
        :param target:
        :param relation:
        :return:
        '''

        if isinstance(target, str):
            target = Node(target, relation.category)

        self.connections.append(ConceptRelationNode(self, relation, target))
        self.nodes.append(target)


class ConceptRelationNode:
    def __init__(self, concept: Concept, relation: Relation, noeud2: Node):

        self.concept, self.noeud2 = concept, noeud2
        self.relation = relation

        assert isinstance(concept, Concept), 'Noeud 1 nust be a concept.'
        assert any([cat in [relation.category] + concept.categories for cat in noeud2.categories]), f'The target node must be {[relation.category]} or {concept.categories} category, get {noeud2.categories}.'

    def get_code(self):
        instruction1 = f'''MATCH{self.concept}, {self.noeud2}\nMERGE({self.concept.name})-[r:{self.relation}]->({self.noeud2.name})'''
        instruction2 = 'SET ' + ',\n'.join(
            [f'r.{str(name_property)} = {str(value)}' for name_property, value in
             self.relation.update_properties.items()])

        return instruction1 + '\n' + instruction2

    def __str__(self):
        return f'''({self.concept.name})-[:{self.relation}]->({self.noeud2.name})'''



if __name__ == '__main__':
    r = Relation('is', 'Caracteristique')
    n1 = Concept('Pierre', 'Personne')

    # n = (Concept(name='Pierre', category='personne'))
    n1.add_relation('petit', r)
    [print(mot) for mot in n1.get_code()]