import requests
import networkx as nx
from typing import Dict, List
import sys
import matplotlib.pyplot as plt
from requetes_neo4j import SaverNeo4j, ImportExportObjectNeo4j
from data_structure import Concept, Node, InformationAPI
from PyQt5.QtWidgets import  QVBoxLayout, QMainWindow,QScrollArea, QCompleter, QPushButton, QListWidgetItem,  QLabel, QLineEdit, QGridLayout, QWidget, QApplication
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class GraphConcept(InformationAPI):

    def __init__(self):
        '''
        Cree un graph qui presente le concept de niveau n les noeuds de niveau n-1 et n-2
        '''
        InformationAPI.__init__(self)
        self.figure, self.ax = plt.subplots()


    def update_plot(self, concept: Concept):

        G = nx.Graph()
        G.add_node(-1, label=concept.name)

        params = {"name": concept.name, 'category': concept.categories[0]}
        nodes_connections = requests.get(self.url_node_n_n_1, params=params).json()
        for index, (node_n, nodes_n_1) in enumerate(nodes_connections.items()):
            # mais index des noeud n-1 sont paires et n-2 somt impaires
            G.add_node(2 * index, label=node_n)
            G.add_edge(-1, 2 * index)

            for index_n, node_n_1 in enumerate(nodes_n_1):
                G.add_node(2 * index + 2 * index_n + 1, label=node_n_1)
                G.add_edge(2 * index, 2 * index + 2 * index_n + 1)


        # Création de la représentation graphique
        ax = self.figure.add_subplot(111)
        pos = nx.spring_layout(G)  # Positionnement des nœuds
        # nx.draw(G, pos, ax=ax, node_color='skyblue', node_size=2000, font_size=10, font_weight='bold')  # Dessin du graphe
        nx.draw(G, pos, ax=ax, node_color=['red' if node == -1 else 'skyblue' for node in G.nodes()],
                node_size=2000, font_size=10, font_weight='bold')

        labels = nx.get_node_attributes(G, 'label')
        nx.draw_networkx_labels(G, pos, labels)




        # plt.show()


class PlotWidget(GraphConcept, QMainWindow):

    def __init__(self, concept: Concept):

        super().__init__()
        QMainWindow.__init__(self)

        self.setGeometry(0, 0, 1000, 1000)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.update_plot(concept)
        # self.show()




if __name__ == '__main__':
    saver = SaverNeo4j()
    aa = ImportExportObjectNeo4j(saver)
    concept = aa.get_concept('Maman', 'Personne')
    # GraphConcept(concept)
    # GraphConcept(concept)

    app = QApplication(sys.argv)
    window = PlotWidget(concept)
    window.show()
    sys.exit(app.exec_())
# # Création d'un graphe vide
#
#
# # Ajout de nœuds avec des attributs
#
# G.add_node(2, label="B")
# G.add_node(3, label="C")
#
# # Ajout de relations entre les nœuds
# G.add_edge(1, 2)
# G.add_edge(1, 3)
# G.add_edge(2, 3)
#
# # Création de la représentation graphique
# plt.figure(figsize=(6, 4))
# pos = nx.spring_layout(G)  # Positionnement des nœuds
# nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2000, font_size=10, font_weight='bold')  # Dessin du graphe
# edge_labels = nx.get_edge_attributes(G, 'weight')
# nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
# plt.title("Graphe de données avec des nœuds et des relations")
# plt.show()

