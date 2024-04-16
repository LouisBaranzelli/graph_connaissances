from pathlib import Path
from typing import Dict, Optional
from PyQt5.QtWidgets import QVBoxLayout, QListWidget,QScrollArea, QCompleter, QPushButton, QListWidgetItem,  QLabel, QLineEdit, QGridLayout, QWidget, QApplication
from PyQt5.QtCore import QStringListModel, Qt
from PyQt5.QtGui import QIcon
import sys
import re
from requetes_neo4j import SaverNeo4j, ImportExportObjectNeo4j
from data_structure import Node, ConceptRelationNode, Concept, Relation


class QListWidgetItemConcept(QListWidgetItem):

    def __init__(self, concept: Concept, **kwargs):
        super().__init__(**kwargs)
        self.concept = concept
        self.setText(f"{concept.name} [{', '.join([category for category in concept.categories])}]")


class QListWidgetItemRelation(QListWidgetItem):

    def __init__(self, c_relation_n: ConceptRelationNode, **kwargs):
        super().__init__(**kwargs)
        self.c_relation_n = c_relation_n
        self.setText(f"{c_relation_n.noeud2.name} [{', '.join([category for category in c_relation_n.noeud2.categories])}]")


class RelationWindow(ImportExportObjectNeo4j, QWidget):
    '''
    interface to display 1 relation and all the node which share this relation
    '''

    def __init__(self, main_concept: Concept, name_relation: str, category: str, saver: SaverNeo4j, *args, **kwargs):

        super().__init__(saver)
        QWidget.__init__(self)

        self.setGeometry(0, 0, 600, 50)
        self.name_relation = name_relation
        self.category = category
        self.main_concept = main_concept

        self.relation = Relation(self.name_relation, self.category)

         # Creation de la structure
        # Organization
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        # Empty list of the target
        self.list_target = QListWidget(self)
        self.layout.addWidget(self.list_target, 1, 0, 1,5)

        # Relation - name
        self.lineedit_name_relation = QLineEdit()
        self.lineedit_name_relation.setText(name_relation)
        self.lineedit_name_relation.setEnabled(False)
        self.layout.addWidget(self.lineedit_name_relation, 0, 1)
        label_relation = QLabel("Relation")
        self.layout.addWidget(label_relation, 0, 0)

        # Relation target category
        self.lineedit_category = QLineEdit()
        self.lineedit_category.setText(self.category)
        self.lineedit_category.setEnabled(False)
        self.layout.addWidget(self.lineedit_category, 0, 3)
        label_relation = QLabel("Target category")
        self.layout.addWidget(label_relation, 0, 2)

        # all the availables choice for the auto completions - target Name of the relation
        # suggest the node with the right category (considering the relation)
        self.target_names = [concept.name for concept in self.get_nodes() if concept.categories[0] == category]
        self.target_name_entries = QCompleter(self.target_names)
        self.target_name_entries.setFilterMode(Qt.MatchContains)
        self.target_name_entries.setCaseSensitivity(False)
        self.lineedit_name = QLineEdit()
        self.lineedit_name.setCompleter(self.target_name_entries)
        self.layout.addWidget(self.lineedit_name, 2, 1)
        label_target = QLabel("Name")
        self.layout.addWidget(label_target, 2, 0)

        # create buttons
        add_button = QPushButton('Add')
        icon_add = QIcon(str(Path('add.png')))
        add_button.setIcon(icon_add)
        # add_button.setIconSize(icon_add.actualSize())
        add_button.clicked.connect(self.add)
        self.layout.addWidget(add_button, 2, 3)

        del_button = QPushButton('Delete')
        del_button.clicked.connect(self.delete)
        icon_delete = QIcon(str(Path('delete.png')))
        del_button.setIcon(icon_delete)
        self.layout.addWidget(del_button, 2, 2)


    def add(self):
        ''' Add a new target to the relation '''
        if not re.search(r'[a-zA-Z]', self.lineedit_name.text()):
            # empty string not accepted
            return

        # create the new relation in neo4j
        new_concept = Node(name=self.lineedit_name.text(), category=self.lineedit_category.text())
        self.send_instruction(new_concept.get_code())

        new_relation = ConceptRelationNode(concept=self.main_concept, relation=self.relation, noeud2=new_concept)
        self.send_instruction(new_relation.get_code())

        # display in the list box
        new_item = QListWidgetItemRelation(new_relation)
        self.list_target.addItem(new_item)

    def delete(self):
        ''' delete the relation to the targeted item not the item '''
        selected_items = self.list_target.selectedItems() # [list of ConceptRelationNode]

        # delete from Neo4J
        for select_item in selected_items:
            instruction_del = select_item.c_relation_n.get_code_delete_relation()

            if instruction_del is not None:
                self.send_instruction(instruction_del)

        if selected_items:
            for item in selected_items:
                self.list_target.takeItem(self.list_target.row(item))

    def add_item(self, name: str):

        ''' Display in the QLIST the initial relation ship with the name in input'''


        if not re.search(r'[a-zA-Z]', name):
            # empty string not accepted
            return
        existing_target = Node(name=name, category=self.lineedit_category.text())
        existint_relation = ConceptRelationNode(concept=self.main_concept, relation=self.relation, noeud2=existing_target)
        new_item = QListWidgetItemRelation(existint_relation)
        self.list_target.addItem(new_item)

    def __str__(self):
        self.name_relation


class RelationWindows(ImportExportObjectNeo4j, QWidget):

    '''
    from a name and category: load all the relation and connected nodes
    '''

    def __init__(self, name_concept: str, category_concept: str, saver: SaverNeo4j, *args, **kwargs):
        super().__init__(saver)
        QWidget.__init__(self)

        self.setGeometry(0, 0, 600, 400)
        self.relation_displays: Dict[str, RelationWindow] = {}
        self.layout = QGridLayout(self)
        self.index_position: int = 0


        # If concept exist load it
        self.main_concept = self.get_concept(node_name=name_concept, category=category_concept)
        if self.main_concept is not None:
            for n_relation_m in self.main_concept.relations: # ConceptRelationNode
                # Create the relation window if not yet existing
                if n_relation_m.relation.name not in list(self.relation_displays.keys()):
                    self.relation_displays[n_relation_m.relation.name] = RelationWindow(main_concept=self.main_concept ,
                                                                                        name_relation=n_relation_m.relation.name,
                                                                                        saver=saver,
                                                                                        category=n_relation_m.noeud2.categories[0])
                    self.layout.addWidget(self.relation_displays[n_relation_m.relation.name], self.index_position, 0)
                    self.index_position += 1

                # Now relation exist -> add the node
                self.relation_displays[n_relation_m.relation.name].add_item(name=n_relation_m.noeud2.name)


        # Create a scrolling area if to much properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_widget = QWidget()
        scroll_widget.setLayout(self.layout)

        scroll_area.setWidget(scroll_widget)
        main_layout = QGridLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def add_new_properties(self, name_relation: str, name_category):
        self.relation_displays[f'new_relation_{self.index_position}'] = RelationWindow(main_concept=self.main_concept,
                                                                                       name_relation= name_relation,
                                                                                       category= name_category)
        self.layout.addWidget( self.relation_displays[f'new_relation_{self.index_position}'], self.index_position, 0)
        self.index_position += 1


class MainWindow(ImportExportObjectNeo4j, QWidget):

    def __init__(self, saver: SaverNeo4j):

        super().__init__(saver)
        QWidget.__init__(self)

        self.setGeometry(0, 0, 1000, 1000)
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        # Load the datas
        self.concepts = self.get_nodes()

        self.list_concept = QListWidget(self)
        # list_concept.setGeometry(50, 70, 150, 60)
        # Create the list of concept
        for concept in self.concepts:
            new_item = QListWidgetItemConcept(concept)
            self.list_concept.addItem(new_item)
        self.layout.addWidget(self.list_concept, 0, 0, 3,1)# 1ere ligne / 1ere colone

        # all the availables choice for the auto completions - Name of the concept
        concept_names = [concept.name for concept in self.concepts]
        self.concept_name_entries = QCompleter(concept_names)
        self.concept_name_entries.setFilterMode(Qt.MatchContains) # match not only the biginning of the world
        self.concept_name_entries.setCaseSensitivity(False)
        self.lineedit_name = QLineEdit()
        self.lineedit_name.setCompleter(self.concept_name_entries)
        self.layout.addWidget(self.lineedit_name, 0, 3)
        label_concept = QLabel("Concept")
        self.layout.addWidget(label_concept, 0, 2)

        # all the availables choice for the auto completions - Category of the concept
        self.concept_categories = set([concept.categories[0] for concept in self.concepts])
        self.concept_category_entries = QCompleter(self.concept_categories)
        self.concept_category_entries.setFilterMode(Qt.MatchContains)
        self.concept_category_entries.setCaseSensitivity(False)
        self.lineedit_category = QLineEdit()
        self.lineedit_category.setCompleter(self.concept_category_entries)
        self.layout.addWidget(self.lineedit_category, 0, 5)
        label_category = QLabel("Category")
        self.layout.addWidget(label_category, 0, 4)

        # self.refresh_concept_autofill()

        # create buttons
        add_button = QPushButton('Add')
        add_button.clicked.connect(self.add)
        self.layout.addWidget(add_button, 0, 6)  # 2eme ligne / 1ere colone

        del_button = QPushButton('Delete')
        del_button.clicked.connect(self.delete)
        self.layout.addWidget(del_button, 4, 0)  # 2eme ligne / 1ere colone

        # to update the list of node when create new target node of a realtion ship
        ref_button = QPushButton('Refresh')
        ref_button.clicked.connect(self.refresh)
        self.layout.addWidget(ref_button, 3, 0)

        # Create new relation with the suggestion
        self.relation_names = set([relation.relation.name for relation in self.get_all_relations()])
        self.relation_name_entries = QCompleter(self.relation_names)
        self.relation_name_entries.setFilterMode(Qt.MatchContains)  # match not only the biginning of the world
        self.relation_name_entries.setCaseSensitivity(False)
        self.lineedit_new_relation_name = QLineEdit()
        self.lineedit_new_relation_name.setCompleter(self.relation_name_entries)
        self.lineedit_new_relation_category = QLineEdit()
        self.lineedit_new_relation_category.setCompleter(self.concept_category_entries)
        label_name_relation = QLabel("New relation name")
        label_category_relation = QLabel("New relation category")
        self.layout.addWidget(label_name_relation, 4, 2)
        self.layout.addWidget(self.lineedit_new_relation_name, 4, 3)
        self.layout.addWidget(label_category_relation, 4, 4)
        self.layout.addWidget(self.lineedit_new_relation_category, 4, 5)

        self.create_button = QPushButton('Create new relation')
        icon_creation = QIcon(str(Path('create.png')))
        self.create_button.setIcon(icon_creation)
        self.create_button.clicked.connect(self.create_relation)
        self.layout.addWidget(self.create_button, 4, 6)

        # action when we fulfill character
        # activate the change_autofill_concept_name if we touch the entry or the suggestions
        self.lineedit_name.textEdited.connect(self.change_autofill_concept_name)
        self.concept_name_entries.activated.connect(self.select_concept_name)
        self.lineedit_category.textEdited.connect(self.change_autofill_concept_category)
        self.list_concept.itemClicked.connect(self.handle_item_clicked)

        # # add the relations managments variable (updated when the fillin text name or category is modified)
        self.window_relationships = RelationWindows(saver=saver,
                                                    name_concept=self.lineedit_name.text(),
                                                    category_concept=self.lineedit_category.text())

        # ajouter toutes les proprite en creant ou pas un objet si il n'existe pas
        self.show()

    def add(self):
        ''' Create the concept if not existing'''

        name_new_concept = self.lineedit_name.text()
        category_new_concept = self.lineedit_category.text()
        # must not be empty
        if not re.search(r'[a-zA-Z]', name_new_concept) or not re.search(r'[a-zA-Z]', category_new_concept):
            return

        concept = self.get_concept(node_name=name_new_concept, category=category_new_concept)
        # if concept doesnt exist create it
        if concept is None:
            concept = Concept(name=self.lineedit_name.text(), category=self.lineedit_category.text())
            instruction_creation = concept.get_code()[0]
            self.send_instruction(instruction_creation)
            # display the new concept
            new_item = QListWidgetItemConcept(concept)
            self.list_concept.addItem(new_item)
            # Update the auto completion if not already in
            model = QStringListModel()
            existing_entries = self.concept_name_entries.model().stringList()
            if concept.name not in existing_entries:
                existing_entries.append(concept.name)
                model.setStringList(existing_entries)
                self.concept_name_entries.setModel(model)

    def refresh(self):

        ''' Display all the existing node in the list box (update the display not refreshed if adding new target node of
        a relation)'''

        nodes = self.get_nodes()
        for node in nodes:

            new_item = QListWidgetItemConcept(node)
            # check idf not already in
            item_exists = False
            for index in range(self.list_concept.count()):
                existing_item = self.list_concept.item(index)
                if existing_item.text() == new_item.text():
                    item_exists = True
                    break
            if not item_exists:
                self.list_concept.addItem(new_item)


    def delete(self):

        '''
        Delete the concept selected
        :return:
        '''

        selected_items = self.list_concept.selectedItems()  #
        # delete from Neo4J
        for select_item in selected_items:
            instruction_del = select_item.concept.get_code_deletion()
            self.send_instruction(instruction_del)

        # delete from the list displayed
        if selected_items:
            for item in selected_items:
                self.list_concept.takeItem(self.list_concept.row(item))

    def create_relation(self):
        ''' To add a new empty relation ship'''
        name_new_relation = self.lineedit_new_relation_name.text().capitalize()
        name_new_category = self.lineedit_new_relation_category.text().capitalize()
        if not re.search(r'[a-zA-Z]', name_new_category) or not re.search(r'[a-zA-Z]', name_new_relation):
            return
        self.window_relationships.add_new_properties(name_relation=name_new_relation,
                                                     name_category=name_new_category)

        # Update the auto completion if not already in
        model = QStringListModel()
        existing_entries = self.relation_name_entries.model().stringList()
        if name_new_relation not in existing_entries:
            existing_entries.append(name_new_relation)
            model.setStringList(existing_entries)
        self.relation_name_entries.setModel(model)

    def update_relationships(self) -> None:
        ''' Use the fillin text to find the right concept and load it properties if the concept exist'''

        # check if the concept exist
        # self.layout.removeWidget(self.window_relationships)
        concept = self.get_concept(node_name=self.lineedit_name.text(), category=self.lineedit_category.text())

        if concept is not None:
            # self.layout.removeWidget(self.window_relationships)
            self.window_relationships = RelationWindows(saver=saver,
                                                        name_concept=self.lineedit_name.text(),
                                                        category_concept=self.lineedit_category.text())
            self.layout.addWidget(self.window_relationships, 1, 1, 2, 5)


    def select_concept_name(self, text):
        self.lineedit_name.setText(text)
        self.change_autofill_concept_name()

    def change_autofill_concept_name(self):

        ''' When a concept name is fulfill automatically add a category if match'''

        # First letter is Capital
        self.lineedit_name.setText(self.lineedit_name.text().capitalize())

        input_name = self.lineedit_name.text()
        input_category = self.lineedit_category.text()

        # if a concept name match, fulfill automatically the category
        category_suggestion = [concept.categories[0] for concept in self.concepts if concept.name == input_name]
        if len(category_suggestion) > 0:
            self.lineedit_category.setText(category_suggestion[0])

        # if concept exist allow to add properties
        concept = self.get_concept(node_name=self.lineedit_name.text(), category=self.lineedit_category.text())
        if concept is None:
            self.create_button.setEnabled(False)
        else:
            self.create_button.setEnabled(True)

        # Highlight the current concept if identified
        output_concept = [concept for concept in self.concepts if
                          concept.name == input_name and concept.categories[0] == input_category]
        if len(output_concept) > 0:
            match_concept = output_concept[0]
        else:
            return
        for index in range(self.list_concept.count()):
            item = self.list_concept.item(index)
            if item.text() == QListWidgetItemConcept(match_concept).text():
                self.list_concept.setCurrentItem(item)
                break

        self.update_relationships()


    def change_autofill_concept_category(self):

        ''' When a concept name is fulfill update the choice of names'''

        pass
        # input = self.lineedit_category.text()
        # motif = re.compile(input, re.IGNORECASE)
        # self.concept_names = [concept.name for concept in self.concepts if bool(motif.match(concept.categories[0]))]
        # self.refresh_concept_autofill()
        # self.update_relationships()

    def handle_item_clicked(self, item):
        self.lineedit_category.setText(item.concept.categories[0])
        self.lineedit_name.setText(item.concept.name)
        self.update_relationships()

        # to acivate 'create_relation'
        self.change_autofill_concept_name()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    saver = SaverNeo4j()
    window = MainWindow(saver=saver)
    # window = RelationWindows(name_concept='Baranzelli', category_concept='Famille')
    sys.exit(app.exec())
    window.show()






