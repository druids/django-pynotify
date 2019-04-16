from collections import Iterable

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model


class BaseSerializer:
    """
    Base class for serializing/deserializing signal kwargs. Its puprose is to transform signal kwargs to be directly
    JSON serializable (for compatible types, see https://docs.python.org/3/library/json.html#py-to-json-table).
    """
    def serialize(self, signal_kwargs):
        """
        This method should return serialized ``signal_kwargs``.
        """
        raise NotImplementedError()  # pragma: no cover

    def deserialize(self, signal_kwargs):
        """
        This method should return deserialized ``signal_kwargs``.
        """
        raise NotImplementedError()  # pragma: no cover


class ModelSerializer:
    """
    Serializes any model instance into its PK and ContentType PK and deserializes by fetching the model instance from
    database. Works recursively on nested dicts and iterables. Values that are not model instances are left intact.
    """
    CONTENT_TYPE_PK_KEY = 'ct_pk'
    INSTANCE_PK_KEY = 'obj_pk'

    def _is_serialized(self, value):
        return isinstance(value, dict) and list(value.keys()) == [self.CONTENT_TYPE_PK_KEY, self.INSTANCE_PK_KEY]

    def _is_deserialized(self, value):
        return isinstance(value, Model) and hasattr(value, 'pk')

    def _serialize(self, value):
        return {
            self.CONTENT_TYPE_PK_KEY: ContentType.objects.get_for_model(value).pk,
            self.INSTANCE_PK_KEY: value.pk,
        }

    def _deserialize(self, value):
        model_class = ContentType.objects.get_for_id(value[self.CONTENT_TYPE_PK_KEY]).model_class()
        return model_class.objects.get(pk=value[self.INSTANCE_PK_KEY])

    def _process(self, check_method, process_method, input):
        output = {}
        for key, value in input.items():
            if check_method(value):
                output[key] = process_method(value)
            elif isinstance(value, dict):
                output[key] = self._process(check_method, process_method, value)
            elif isinstance(value, Iterable) and not isinstance(value, str):
                output[key] = [process_method(i) if check_method(i) else i for i in value]
            else:
                output[key] = value

        return output

    def serialize(self, signal_kwargs):
        return self._process(self._is_deserialized, self._serialize, signal_kwargs)

    def deserialize(self, signal_kwargs):
        return self._process(self._is_serialized, self._deserialize, signal_kwargs)
