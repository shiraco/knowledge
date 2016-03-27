from SPARQLWrapper import SPARQLWrapper, JSON
from model import Category, Page


class Wikipedia():

    def __init__(self, sparql_endpoint="http://ja.dbpedia.org/sparql"):
        self.sparql = SPARQLWrapper(sparql_endpoint)
        self.sparql.setReturnFormat(JSON)

    def update_query(self, query):
        self.sparql.setQuery(query)

    def exec_query(self):
        return self.sparql.query().convert()

    def subject_of(self, category):
        """
        categoryにあるページ一覧を取得
        :param category:
        :return:
        """

        base_query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT *
            WHERE {{ ?subject <http://purl.org/dc/terms/subject> <{0}> }}
        """
        query = base_query.format(category.url)

        self.update_query(query)
        results = self.exec_query()

        children_pages = [Page(url=result["subject"]["value"], category_id=category.id) for result in results["results"]["bindings"]]

        return children_pages

    def broader_of(self, category):
        """
        categoryの下位のカテゴリ一覧を取得
        :param category:
        :return:
        """

        base_query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT *
            WHERE {{ ?subject <http://www.w3.org/2004/02/skos/core#broader> <{0}> }}
        """
        query = base_query.format(category.url)

        self.update_query(query)
        results = self.exec_query()

        children_categories = [Category(url=result["subject"]["value"], parent_id=category.id) for result in results["results"]["bindings"]]

        return children_categories

    def load(self, category, nested_depth=2):

        yield category
        if nested_depth > 0:
            children_categories = self.broader_of(category)
            print(children_categories)
            if children_categories:
                for child_category in children_categories:
                    yield from self.load(child_category, nested_depth - 1)


if __name__ == 'main':

    wiki = Wikipedia()

    category = Category(url='http://ja.dbpedia.org/resource/Category:旅行', parent_id=None)

    gen = wiki.load(category, 3)
