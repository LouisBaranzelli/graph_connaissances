from neo4j import GraphDatabase
from data_structure import Relation, Concept, Node
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

            instruction_node = "MATCH (concept: " + category + "{name: '" + node_name + "'}) RETURN properties(concept)"
            print(instruction_node)
            results = graphDB_Session.run(instruction_node).data()
            if len(results) == 0:
                logger.warning(f"{category}:{node_name} does not exist")
                return None
            else:
                load_concept = Concept(name=node_name, category=category, properties_node=results[0]['properties(concept)'])

            instruction_relation = "MATCH (concept: " + category + "{name: '" + node_name + "'})-[r]->(m) RETURN labels(concept), properties(concept), r, properties(r) ,labels(m), properties(m)"
            results = graphDB_Session.run(instruction_relation).data()
            if len(results) == 0:
                logger.warning(f"{category}:{node_name} does not have any relation")
                return load_concept

            for result in results:
                relation = Relation(name=result['properties(r)']['name'], category_target=result['labels(m)'][0],
                                    properties=result['properties(r)'])
                node_target = Node(name=result['properties(m)']['name'], category=result['labels(m)'][0],
                                   properties=result['properties(m)'])
                load_concept.add_relation(relation=relation, target=node_target)

            return load_concept




saver = SaverNeo4j()
# famille = Concept('Baranzelli', 'famille', properties={'creation':'yooo'})
# relation_contient = Relation('est compose de', 'personne')
# famille.add_relation('Claire', relation_contient)
# famille.add_relation('Maman', relation_contient)
# famille.add_relation('Papa', relation_contient)
# saver.send(famille)
a = saver.get_concept('Maman', 'Personne')

pass



