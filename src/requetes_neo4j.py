from datetime import datetime, timedelta
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


class ImportExportObjectNeo4j():
    '''
    All the functions to import or export object from Neo4j server
    '''

    def __init__(self, saver: SaverNeo4j):
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

            instruction_node = "MATCH (c: `" + category + "`{name: '" + node_name + "'}) RETURN properties(c)"
            results = graphDB_Session.run(instruction_node).data()
            if len(results) == 0:
                logger.warning(f"{category}:{node_name} does not exist")
                return None
            else:
                load_concept = Concept(name=node_name, category=category, properties=results[0]['properties(c)'])

            instruction_relation = "MATCH (c: `" + category + "`{name: '" + node_name + "'})-[r]->(t) RETURN labels(c), properties(c), r, properties(r) ,labels(t), properties(t)"
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
                instruction_node = "MATCH (c) RETURN properties(c), labels(c) ORDER BY c.name"
            else:
                instruction_node = "MATCH (c: `" + category + "`) RETURN properties(c), labels(c) ORDER BY c.name"
            results = graphDB_Session.run(instruction_node).data()
            concepts: [Concept] = []
            for result in results:
                concepts.append(Concept(name=result['properties(c)']['name'], category=result['labels(c)'][0],
                                  properties=result['properties(c)']))
        return concepts

    def send_instruction(self, instruction: str):
        with self.saver.driver.session() as graphDB_Session:
            # Create nodes
            # graphDB_Session.run(instruction)
            results = graphDB_Session.run(instruction).data()
            return results

    def get_node_connected(self, concept: Node) -> List[Node]:
        output: List[Node] = []
        with self.saver.driver.session() as graphDB_Session:
            instruction_relation = "MATCH (c: `" + concept.categories[0] + "` {name: '" + concept.name + "'})-[r]-(t) RETURN labels(t), properties(t)"
            results = graphDB_Session.run(instruction_relation).data()

            for result in results:

                node_target = Node(name=result['properties(t)']['name'], category=result['labels(t)'][0],
                                   properties=result['properties(t)'])
                output.append(node_target)
        return output

    def delete_not_connected_node(self):

        instruction = 'MATCH (n)\nWHERE NOT ()--(n)\nDELETE n'
        self.send_instruction(instruction)



class ModifyConcept(ImportExportObjectNeo4j):

    '''
    server - side
    class qui embarque toute les fonction pour modifier des information sur le server neo4j
    '''

    def __init__(self, c_r_n: ConceptRelationNode, saver: SaverNeo4j):

        ImportExportObjectNeo4j.__init__(self, saver)

        # check if the concept exist
        self.instruction_match = "MATCH (n1:`" + c_r_n.concept.categories[0] + "` {name: '" + c_r_n.concept.name + "'})-[r:`" + c_r_n.relation.relation + "`]->(n2:`" + c_r_n.noeud2.categories[0] + "` {name: '" + c_r_n.noeud2.name + "'})"
        instruction = self.instruction_match + '\nRETURN n1, r, n2'
        results = self.send_instruction(instruction)
        assert len(results) == 1
        self.c_r_n = c_r_n

        # level : nbr of day before to ask again
        self.levels = {0:1, 1:3, 2:7, 3: 14, 4:150}

    def increase_level(self):
        # increase the level and set the new next date

        # get the infotmation
        instruction = self.instruction_match + '\nRETURN r.level'
        result = self.send_instruction(instruction)

        # update the new level
        level = int(result[0]['r.level']) + 1
        level = max(level, 0)  # no negatif
        level = min(level, max(list(self.levels.keys())))
        # update the new date
        new_next = (datetime.today() + timedelta(days=self.levels[level])).strftime("%Y-%m-%d")

        # update new date and new level
        instruction = self.instruction_match + f'\nSET r.level = {level}'
        self.send_instruction(instruction)
        instruction = self.instruction_match + f"\nSET r.next = '{new_next}'"
        self.send_instruction(instruction)

    def decrease_level(self):
        # decrease the level and set the new next date

        # get the infotmation
        instruction = self.instruction_match + '\nRETURN r.level'
        result = self.send_instruction(instruction)

        # update the new level
        level = int(result[0]['r.level']) - 1
        level = min(level, max(list(self.levels.keys()))) # no > max level
        level = max(level, 0) # no negatif
        # update the new date
        new_next = (datetime.today() + timedelta(days=self.levels[level])).strftime("%Y-%m-%d")

        # update new date and new level
        instruction = self.instruction_match + f'\nSET r.level = {level}'
        self.send_instruction(instruction)
        instruction = self.instruction_match + f"\nSET r.next = '{new_next}'"
        self.send_instruction(instruction)

if __name__  == '__main__':

    saver = SaverNeo4j()
    aa = ImportExportObjectNeo4j(saver)
    concept = aa.get_concept('Maman', 'Personne')
    print(aa.get_node_connected(concept))
# #
# b = ModifyConcept(a)
# b.increase_level()
