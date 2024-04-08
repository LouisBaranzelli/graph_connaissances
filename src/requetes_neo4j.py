from typing import List
from neo4j import GraphDatabase
from data_structure import Relation, Concept, Node, ConceptRelationNode
from loguru import logger
from typing import Dict, Optional


class SaverNeo4j():

    def __init__(self):

        uri = "bolt://localhost:7687"
        username = "Louis"
        password = "Bankbook0"
        self.driver = GraphDatabase.driver(uri, auth=(username, password), database='quiz')
        assert self.driver.verify_connectivity() is None, f'Connection impossible a {uri}'
        logger.success(f'Coonection to {uri} done')

    def send_instruction(self, instruction: str):
        with self.driver.session() as graphDB_Session:
            # Create nodes
            # graphDB_Session.run(instruction)
            results = graphDB_Session.run(instruction).data()
            return results


saver = SaverNeo4j()


class ImportExportObjectNeo4j():
    '''
    All the functions to import or export object from Neo4j server
    '''

    def __init__(self, saver: Optional[SaverNeo4j] = saver):
        self.saver = saver

    def get_concept(self, node_name: str, category: str):
        '''
        Returns the Concept ( main node and relationship) object type that corresponds to the unique identifier provided as an argument..
        Returns None if the concept is not found.
        '''

        if node_name == '' or category == '':
            logger.warning(f'Impossible to load concept: missing information name:{node_name} cat:{category}')
            return

        with self.saver.driver.session() as graphDB_Session:

            instruction_node = "MATCH (c: " + category + "{name: '" + node_name + "'}) RETURN properties(c)"
            results = graphDB_Session.run(instruction_node).data()
            if len(results) == 0:
                logger.warning(f"{category}:{node_name} does not exist")
                return None
            else:
                load_concept = Concept(name=node_name, category=category, properties=results[0]['properties(c)'])

            instruction_relation = "MATCH (c: " + category + "{name: '" + node_name + "'})-[r]->(t) RETURN labels(c), properties(c), r, properties(r) ,labels(t), properties(t)"
            results = graphDB_Session.run(instruction_relation).data()
            if len(results) == 0:
                logger.warning(f"{category}:{node_name} does not have any relation")
                return load_concept

            for result in results:
                relation = Relation(name=result['properties(r)']['name'], category_target=result['labels(t)'][0],
                                    properties=result['properties(r)'])
                node_target = Node(name=result['properties(t)']['name'], category=result['labels(t)'][0],
                                   properties=result['properties(t)'])
                load_concept.add_relation(relation=relation, target=node_target)

            return load_concept

    def get_all_relations(self) -> List[ConceptRelationNode]:

        with self.saver.driver.session() as graphDB_Session:
            instruction = "MATCH (c)-[r]->(t) RETURN labels(c), properties(c), properties(r), labels(t), properties(t)"
            results = graphDB_Session.run(instruction).data()
            relations: [ConceptRelationNode] = []
            for result in results:

                concept = Concept(name=result['properties(c)']['name'], category=result['labels(c)'][0],
                                  properties=result['properties(c)'])
                relation = Relation(name=result['properties(r)']['name'], category_target=result['labels(t)'][0],
                                    properties=result['properties(r)'])
                node_target = Node(name=result['properties(t)']['name'], category=result['labels(t)'][0],
                                   properties=result['properties(t)'])
                relations.append(ConceptRelationNode(concept, relation, node_target))
        return relations

    def get_nodes(self, category:Optional[str]=None) -> List[Node]:
        ''' Retourne tout les noeuds correspondant a une categorie'''

        with self.saver.driver.session() as graphDB_Session:
            if category is None:
                instruction_node = "MATCH (c) RETURN properties(c), labels(c)"
            else:
                instruction_node = "MATCH (c: " + category + ") RETURN properties(c), labels(c)"
            results = graphDB_Session.run(instruction_node).data()
            concepts: [Concept] = []
            for result in results:
                concepts.append(Concept(name=result['properties(c)']['name'], category=result['labels(c)'][0],
                                  properties=result['properties(c)']))
        return concepts
#
#
saver = SaverNeo4j()
famille = Concept('Baranzelli', 'famille', properties={'creation':'yooo'})
relation_contient = Relation('Parle', 'Langue')
famille.add_relation('Francais', relation_contient)
# famille.add_relation('Maman', relation_contient)
# famille.add_relation('Papa', relation_contient)
saver.send_concept(famille)
# a = saver.get_concept('Baranzelli', 'Famille')
# saver.send_concept(a)

    def decrease_level(self):
        # decrease the level and set the new next date

        # get the infotmation
        instruction = self.instruction_match + '\nRETURN r.level'
        result = self.saver.send_instruction(instruction)

        # update the new level
        level = max(int(result[0]['r.level']) - 1, 0)
        # update the new date
        new_next = (datetime.today() + timedelta(days=self.levels[level])).strftime("%Y-%m-%d")

        # update new date and new level
        instruction = self.instruction_match + f'\nSET r.level = {level}'
        self.saver.send_instruction(instruction)
        instruction = self.instruction_match + f"\nSET r.next = '{new_next}'"
        self.saver.send_instruction(instruction)




# aa = ImportExportObjectNeo4j()
# a = aa.get_all_relations()[0]
# #
# b = ModifyConcept(a)
# b.increase_level()
