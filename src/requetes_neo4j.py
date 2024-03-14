from typing import List
from neo4j import GraphDatabase
from data_structure import Relation, Concept, Node, ConceptRelationNode
from loguru import logger

from typing import Dict, Optional

# ici toute les requette pour ecrire dans la base de donne ou rechercher

# Connexion à la base de données Neo4j


class SaverNeo4j():

    def __init__(self):

        uri = "bolt://localhost:7687"
        username = "Louis"
        password = "Bankbook0"
        self.driver = GraphDatabase.driver(uri, auth=(username, password), database='quiz')
        assert self.driver.verify_connectivity() is None, f'Connection impossible a {uri}'

    def send_concept(self, concept: Concept):
        with self.driver.session() as graphDB_Session:
            # Create nodes
            for instruction in concept.get_code():
                print(instruction)
                graphDB_Session.run(instruction)

    def get_concept(self, node_name: str, category: str):

        '''
        Returns the Concept that corresponds to the unique identifier provided as an argument: main node and relationship.
        Returns None if the concept is not found.
        '''

        with self.driver.session() as graphDB_Session:

            instruction_node = "MATCH (c: " + category + "{name: '" + node_name + "'}) RETURN properties(c)"
            print(instruction_node)
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

        with self.driver.session() as graphDB_Session:
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

    def get_nodes(self, category: str) -> List[Node]:

        with self.driver.session() as graphDB_Session:
            instruction_node = "MATCH (c: " + category + ") RETURN properties(c), labels(c)"
            results = graphDB_Session.run(instruction_node).data()
            concepts: [Concept] = []
            for result in results:
                concepts.append(Concept(name=result['properties(c)']['name'], category=result['labels(c)'][0],
                                  properties=result['properties(c)']))

        return concepts


saver = SaverNeo4j()
# famille = Concept('Baranzelli', 'famille', properties={'creation':'yooo'})
# relation_contient = Relation('est compose de', 'personne')
# famille.add_relation('Claire', relation_contient)
# famille.add_relation('Maman', relation_contient)
# famille.add_relation('Papa', relation_contient)
# saver.send(famille)
# a = saver.get_concept('Baranzelli', 'Famille')
# saver.send_concept(a)

for r in saver.get_nodes(category="Personne"):
    print(r)

pass



