import json

from django.contrib.auth.models import User
from django.test import TestCase

from pynotify.serializers import ModelSerializer

from articles.models import Article


class ModelSerizalizerTestCase(TestCase):

    def setUp(self):
        user1 = User.objects.create_user('John')
        user2 = User.objects.create_user('Bill')
        article = Article.objects.create(author=user1, title='Example')

        self.serializer = ModelSerializer()
        self.input = {
            # primitive values
            'a': 1,
            'c': [1, 'two', True],
            'd': {'number': 1, 'string': 'two', 'boolean': True},

            # model instances
            'e': user1,
            'f': [user1, user2, article],
            'g': {'user1': user1, 'user2': user2, 'article': article}
        }

    def test_serializer_should_serialize_and_deserialize_model_instances(self):
        output = self.serializer.serialize(self.input)
        input = self.serializer.deserialize(output)
        self.assertEqual(input, self.input)

    def test_serializer_output_should_be_json_serializable(self):
        # model instances are not directly JSON serializable
        with self.assertRaises(TypeError):
            json.dumps(self.input)

        # serializer output should be directly JSON serializable
        try:
            json.dumps(self.serializer.serialize(self.input))
        except TypeError:
            self.fail('ModelSerializer output is not JSON serializable!')
