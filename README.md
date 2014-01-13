# Flask-Presst

[![Build Status](https://travis-ci.org/biosustain/flask-presst.png)](https://travis-ci.org/biosustain/flask-presst)
[![Coverage Status](https://coveralls.io/repos/biosustain/flask-presst/badge.png?branch=master)](https://coveralls.io/r/biosustain/flask-presst?branch=master)

Flask-Presst is a Flask extension for REST APIs (that itself extends
[Flask-RESTful](https://github.com/twilio/flask-restful)) and is designed for the SQLAlchemy ORM in general and
PostgreSQL in particular.

This extension is a work in progress. It was extracted from another project recently and has not yet been fully rewritten.
The documentation is only being started on just now. In the meant time check out the test cases for guidance.

## Features

- Support for SQLAlchemy models, including:
    - PostgreSQL __JSON & HSTORE__ field types
    - Model __inheritance__
- __Embeddable resources__ & relationship fields
- __Nested resources__
- __Object-based permissions__
- __Resource & resource-item methods__
- GitHub-style __pagination__

### Planned features

- Built-in caching support
- Batch updates for nested resources
- Batch requests using `/resource/1;2;3;4/` with atomicity through nested transactions.
- Built-in `/schema` resource & resource methods for all resources in an API.
- True child resources for non-polymorphic models with foreign-key primary keys
- Namespaces


## Example code

```python

    app = Flask(__name__)
    api = PresstApi(app)
    db = SQLAlchemy(app)

    class Tree(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(60), nullable=False)


    class Fruit(db.Model):
        id = db.Column(db.Integer, primary_key=True)

        name = db.Column(db.String(60), nullable=False)
        sweetness = db.Column(db.Integer)

        tree_id = db.Column(db.Integer, db.ForeignKey(Tree.id))
        tree = db.relationship(Tree, backref=backref('fruits', lazy='dynamic'))

    db.create_all()

    class TreeResource(ModelResource):
        class Meta:
            model = Tree

        fruits = Relationship('Fruit')


    class FruitResource(ModelResource):
        class Meta:
            model = Fruit

        tree = fields.ToOne(TreeResource, embedded=True)

    api.add_resource(FruitResource)
    api.add_resource(TreeResource)
```
