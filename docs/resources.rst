
Resource classes
================

.. module:: flask.ext.presst

There are three Resource classes that ship with Flask-Presst:

- :class:`PresstResource`: a base class for item collections.
- :class:`ModelResource`: primary class for SQLAlchemy models.
- :class:`PolymorphicModelResource`: extension for SQLAlchemy models with polymorphic inheritance.

All of these resource classes are designed to be extended, for instance to implement authentication or resource
permissions.

The Base-class
--------------


.. autoclass:: PresstResource
   :members:


Resources for SQLAlchemy models
-------------------------------


.. autoclass:: ModelResource


.. autoclass:: PolymorphicModelResource