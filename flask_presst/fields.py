"""
Contains some additional field types that are not included in Flask-RESTful.
"""
from flask.ext.restful.fields import *
from werkzeug.utils import cached_property
from flask_presst.references import Reference


class BaseRelationshipField(Raw):
    def __init__(self, resource, embedded=False, relationship_name=None, *args, **kwargs):
        super(BaseRelationshipField, self).__init__(*args, **kwargs)
        self.bound_resource = None
        self._resource = resource
        self.embedded = embedded
        self.relationship_name = None

    @cached_property
    def python_type(self):
        return Reference(self._resource_class)

    @cached_property
    def _resource_class(self):
        return self.bound_resource.api.get_resource_class(self._resource, self.bound_resource.__module__)


class ToManyField(BaseRelationshipField):
    def format(self, item_list):
        marshal_fn = self._resource_class.item_get_resource_uri \
            if not self.embedded else self._resource_class.marshal_item

        return list(marshal_fn(item) for item in item_list)


class ToOneField(BaseRelationshipField):
    def __init__(self, resource, embedded=False, required=False, *args, **kwargs):
        super(ToOneField, self).__init__(resource, embedded, *args, **kwargs)
        self.required = required

    def format(self, item):
        if not self.embedded:
            return self._resource_class.item_get_resource_uri(item)
        return self._resource_class.marshal_item(item)


class ArrayField(Raw):
    pass


class KeyValueField(Raw):
    pass


class JSONField(Raw):
    pass
