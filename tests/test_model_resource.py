from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from flask.ext.presst import ModelResource, fields, PolymorphicModelResource, Relationship
from tests import PresstTestCase


class TestModelResource(PresstTestCase):
    def setUp(self):
        super(TestModelResource, self).setUp()

        app = self.app
        app.config['SQLALCHEMY_ENGINE'] = 'sqlite://'
        app.config['TESTING'] = True

        self.db = db = SQLAlchemy(app)

        class Tree(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(60), nullable=False)

        class Fruit(db.Model):
            fruit_id = db.Column(db.Integer, primary_key=True)

            name = db.Column(db.String(60), nullable=False)
            sweetness = db.Column(db.Integer, default=5)

            tree_id = db.Column(db.Integer, db.ForeignKey(Tree.id))
            tree = db.relationship(Tree, backref=backref('fruits', lazy='dynamic'))

        db.create_all()

        self.Fruit = Fruit
        self.Tree = Tree

        class TreeResource(ModelResource):
            class Meta:
                model = Tree

            fruits = Relationship('Fruit')

        class FruitResource(ModelResource):
            class Meta:
                model = Fruit

            tree = fields.ToOne(TreeResource)

        self.api.add_resource(FruitResource)
        self.api.add_resource(TreeResource)

        self.FruitResource = FruitResource
        self.TreeResource = TreeResource

    def tearDown(self):
        self.db.drop_all()

    def test_field_discovery(self):
        self.assertEqual(set(self.TreeResource._fields.keys()), {'name'})
        self.assertEqual(set(self.FruitResource._fields.keys()), {'name', 'sweetness', 'tree'})
        self.assertEqual(self.FruitResource.resource_name, 'fruit')
        self.assertEqual(self.TreeResource.resource_name, 'tree')

    def test_create(self):
        self.request('POST', '/fruit', {'name': 'Apple'},
                     {'sweetness': 5, 'name': 'Apple', 'resource_uri': '/fruit/1', 'tree': None}, 200)

        self.request('POST', '/fruit', {'name': 'Apple', 'sweetness': 9001},
                     {'sweetness': 9001, 'name': 'Apple', 'resource_uri': '/fruit/2', 'tree': None}, 200)

        self.request('POST', '/fruit', {'sweetness': 1}, None, 400)

        self.request('POST', '/tree', {'name': 'Apple'}, {'name': 'Apple', 'resource_uri': '/tree/1'}, 200)

        self.request('POST', '/fruit', {'name': 'Apple', 'tree': '/tree/1'},
                     {'sweetness': 5, 'name': 'Apple', 'resource_uri': '/fruit/3', 'tree': '/tree/1'}, 200)


    def test_get(self):
        apple = lambda id: {'sweetness': 5, 'name': 'Apple', 'resource_uri': '/fruit/{}'.format(id), 'tree': None}

        for i in range(1, 10):
            self.request('POST', '/fruit', {'name': 'Apple'}, apple(i), 200)
            self.request('GET', '/fruit', None, [apple(i) for i in range(1, i + 1)], 200)
            self.request('GET', '/fruit/{}'.format(i), None, apple(i), 200)
            self.request('GET', '/fruit/{}'.format(i + 1), None, None, 404)

    def test_pagination(self):
        apple = lambda id: {'sweetness': 5, 'name': 'Apple', 'resource_uri': '/fruit/{}'.format(id), 'tree': None}

        for i in range(1, 10):
            self.request('POST', '/fruit', {'name': 'Apple'}, apple(i), 200)

        with self.app.test_client() as client:
            response = client.get('/fruit')
            self.assertEqual(response.headers['Link'],
                             '</fruit?page=1&per_page=20>; rel="self"')

            response = client.get('/fruit?per_page=5')
            self.assertEqual(set(response.headers['Link'].split(',')),
                             {'</fruit?page=1&per_page=5>; rel="self"',
                              '</fruit?page=2&per_page=5>; rel="last"',
                              '</fruit?page=2&per_page=5>; rel="next"'})

            response = client.get('/fruit?page=1&per_page=5')
            self.assertEqual(set(response.headers['Link'].split(',')),
                             {'</fruit?page=1&per_page=5>; rel="self"',
                              '</fruit?page=2&per_page=5>; rel="last"',
                              '</fruit?page=2&per_page=5>; rel="next"'})

            response = client.get('/fruit?page=2&per_page=5')
            self.assertEqual(set(response.headers['Link'].split(',')),
                             {'</fruit?page=2&per_page=5>; rel="self"',
                              '</fruit?page=1&per_page=5>; rel="first"',
                              '</fruit?page=1&per_page=5>; rel="prev"'})

            response = client.get('/fruit?page=2&per_page=2')
            self.assertEqual(set(response.headers['Link'].split(',')),
                             {'</fruit?page=3&per_page=2>; rel="next"',
                              '</fruit?page=5&per_page=2>; rel="last"',
                              '</fruit?page=1&per_page=2>; rel="prev"',
                              '</fruit?page=1&per_page=2>; rel="first"',
                              '</fruit?page=2&per_page=2>; rel="self"'})


    def test_update(self):
        self.request('POST', '/fruit', {'name': 'Apple'},
                     {'sweetness': 5, 'name': 'Apple', 'resource_uri': '/fruit/1', 'tree': None}, 200)

        # TODO implement support for ColumnDefault
        # FIXME defaults with update
        # self.request('POST', '/fruit/1', {'name': 'Golden Apple'},
        #              {'sweetness': 5, 'name': 'Golden Apple', 'resource_uri': '/fruit/1', 'tree': None}, 200)

        self.request('POST', '/fruit/1', {'name': 'Golden Apple', 'sweetness': 0},
                     {'sweetness': 0, 'name': 'Golden Apple', 'resource_uri': '/fruit/1', 'tree': None}, 200)

        self.request('POST', '/fruit/1', {}, None, 400)

    def test_patch(self):

        self.request('POST', '/tree', {'name': 'Apple tree'}, {'name': 'Apple tree', 'resource_uri': '/tree/1'}, 200)

        expected_apple = {'sweetness': 5, 'name': 'Apple', 'resource_uri': '/fruit/1', 'tree': None}
        self.request('POST', '/fruit', {'name': 'Apple'}, expected_apple, 200)

        changes = [
            {'name': 'Golden Apple'},
            {'name': 'Golden Apple'},
            {'tree': '/tree/1'},
            {'sweetness': 3},
            {},
            {'name': 'Golden Apple', 'tree': None},
            ]

        for change in changes:
            expected_apple.update(change)
            self.request('PATCH', '/fruit/1', change, expected_apple, 200)

    def test_delete(self):
        self.request('POST', '/tree', {'name': 'Apple tree'}, {'name': 'Apple tree', 'resource_uri': '/tree/1'}, 200)
        self.request('DELETE', '/tree/1', {'name': 'Apple tree'}, None, 204)
        self.request('DELETE', '/tree/1', {'name': 'Apple tree'}, None, 404)
        self.request('DELETE', '/tree/2', {'name': 'Apple tree'}, None, 404)

    def test_no_model(self):
        class OopsResource(ModelResource):
            class Meta:
                pass

        self.api.add_resource(OopsResource)

    def test_relationship_post(self):
        self.request('POST', '/tree', {'name': 'Apple tree'}, {'name': 'Apple tree', 'resource_uri': '/tree/1'}, 200)
        self.request('GET', '/tree/1/fruits', None, [], 200)

        self.request('POST', '/fruit', {'name': 'Apple'},
                     {'name': 'Apple', 'resource_uri': '/fruit/1', 'sweetness': 5, 'tree': None}, 200)

        self.request('POST', '/tree/1/fruits', '/fruit/1',
                     {'name': 'Apple', 'resource_uri': '/fruit/1', 'sweetness': 5, 'tree': '/tree/1'}, 200)

    def test_relationship_get(self):
        self.test_relationship_post()
        self.request('GET', '/tree/1/fruits', None,
                     [{'name': 'Apple', 'resource_uri': '/fruit/1', 'sweetness': 5, 'tree': '/tree/1'}], 200)

    def test_relationship_delete(self):
        self.test_relationship_post()
        self.request('DELETE', '/tree/1/fruits', '/fruit/1', None, 204)
        #self.request('GET', '/apple/seed_count', None, 2, 200)

    def test_get_schema(self):
        self.api.enable_schema()
        self.request('GET', '/', None, {
            "$schema": "http://json-schema.org/hyper-schema#",
            "definitions": {
                "fruit": {
                    "definitions": {
                        "name": {
                            "type": "string"
                        },
                        "resource_uri": {
                            "format": "uri",
                            "readOnly": True,
                            "type": "string"
                        },
                        "sweetness": {
                            "type": "integer"
                        }
                    },
                    "links": [
                        {
                            "href": "/fruit/{id}",
                            "rel": "self"
                        }
                    ],
                    "properties": {
                        "name": {
                            "$ref": "#/definitions/fruit/definitions/name"
                        },
                        "resource_uri": {
                            "$ref": "#/definitions/fruit/definitions/resource_uri"
                        },
                        "sweetness": {
                            "$ref": "#/definitions/fruit/definitions/sweetness"
                        },
                        "tree": {
                            "$ref": "#/definitions/tree/definitions/resource_uri"
                        }
                    },
                    "required": [
                        "name"
                    ]
                },
                "tree": {
                    "definitions": {
                        "name": {
                            "type": "string"
                        },
                        "resource_uri": {
                            "format": "uri",
                            "readOnly": True,
                            "type": "string"
                        }
                    },
                    "links": [
                        {
                            "href": "/tree/{id}/fruits",
                            "rel": "fruits",
                            "targetSchema": {
                                "$ref": "#/definitions/fruit"
                            }
                        },
                        {
                            "href": "/tree/{id}",
                            "rel": "self"
                        }
                    ],
                    "properties": {
                        "name": {
                            "$ref": "#/definitions/tree/definitions/name"
                        },
                        "resource_uri": {
                            "$ref": "#/definitions/tree/definitions/resource_uri"
                        }
                    },
                    "required": [
                        "name"
                    ]
                }
            },
            'properties': {
                'tree': {'$ref': '#/definitions/tree'},
                'fruit': {'$ref': '#/definitions/fruit'}
            }
        }, 200)

class TestPolymorphicModelResource(PresstTestCase):
    def setUp(self):
        super(TestPolymorphicModelResource, self).setUp()

        app = self.app
        app.config['SQLALCHEMY_ENGINE'] = 'sqlite://'
        app.config['TESTING'] = True
        self.db = db = SQLAlchemy(app)

        class Fruit(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(60), nullable=False)
            table = db.Column(db.String(60))
            color = db.Column(db.String)

            __mapper_args__ = {
                'polymorphic_identity': 'fruit',
                'polymorphic_on': table
            }

        class CitrusFruit(Fruit):
            id = db.Column(db.Integer, db.ForeignKey(Fruit.id), primary_key=True)
            sweetness = db.Column(db.Integer)

            __mapper_args__ = {
                'polymorphic_identity': 'citrus',
                }

        class FruitResource(PolymorphicModelResource):
            class Meta:
                model = Fruit
                exclude_fields = ['table']

        class CitrusFruitResource(ModelResource):
            class Meta:
                model = CitrusFruit
                resource_name = 'citrus'
                exclude_fields = ['table']

        db.create_all()

        self.CitrusFruit = CitrusFruit
        self.api.add_resource(FruitResource)
        self.api.add_resource(CitrusFruitResource)

    def test_polymorphic(self):
        self.request('POST', '/fruit', {'name': 'Banana', 'color': 'yellow'},
                     {'name': 'Banana', 'color': 'yellow', 'resource_uri': '/fruit/1'}, 200)

        self.request('POST', '/citrus', {'name': 'Lemon', 'color': 'yellow'},
                     {'name': 'Lemon', 'sweetness': 0, 'color': 'yellow', 'resource_uri': '/citrus/2'}, 200)

        self.request('GET', '/fruit', None, [
            {'color': 'yellow', 'name': 'Banana', 'resource_uri': '/fruit/1'},
            {'citrus': {'color': 'yellow',
                        'name': 'Lemon',
                        'resource_uri': '/citrus/2',
                        'sweetness': 0},
             'color': 'yellow',
             'name': 'Lemon',
             'resource_uri': '/fruit/2'}
        ], 200)

    def test_exclude_polymorphic(self):
        class CitrusFruitAltResource(ModelResource):
            class Meta:
                model = self.CitrusFruit
                exclude_polymorphic = True
                resource_name = 'citrus_alt'
                exclude_fields = ['table']

        self.api.add_resource(CitrusFruitAltResource)

        self.request('POST', '/citrus', {'name': 'Lemon', 'sweetness': 1},
                     {'name': 'Lemon', 'sweetness': 1, 'color': None, 'resource_uri': '/citrus/1'}, 200)

        self.request('GET', '/citrus_alt/1', None,
                     {'sweetness': 1, 'resource_uri': '/citrus_alt/1'}, 200)
