import pytest
from datetime import date
from src.data_structure import CommonStructureDataNeo4j, Node

@pytest.fixture()
def node1():
    return Node(name='louis', category='personne')

def test_node_creation(node1):
    assert node1.name == 'Louis'
    assert node1.categories[0] == 'Personne'
    assert node1.properties['compteur'] == 1
