# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import requests
from datetime import date, datetime

from django.core.files.base import ContentFile
from django.db import models
from django.test import TestCase

from allauth.compat import base36_to_int, int_to_base36

from . import utils

were
wr
wer
ew
rew
r

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch  # noqa


class MockedResponse(object):
    def __init__(self, status_code, content, headers=None):
        if headers is None:
            headers = {}

        self.status_code = status_code
        self.content = content.encode('utf8')
        self.headers = headers

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        pass

    @property
    def text(self):
        return self.content.decode('utf8')


class mocked_response:
    def __init__(self, *responses):
        self.responses = list(responses)

    def __enter__(self):
        self.orig_get = requests.get
        self.orig_post = requests.post
        self.orig_request = requests.request

        def mockable_request(f):
            def new_f(*args, **kwargs):
                if self.responses:
                    return self.responses.pop(0)
                return f(*args, **kwargs)
            return new_f
        requests.get = mockable_request(requests.get)
        requests.post = mockable_request(requests.post)
        requests.request = mockable_request(requests.request)

    def __exit__(self, type, value, traceback):
        requests.get = self.orig_get
        requests.post = self.orig_post
        requests.request = self.orig_request


class BasicTests(TestCase):

    def test_generate_unique_username(self):
        examples = [('a.b-c@example.com', 'a.b-c'),
                    ('Üsêrnamê', 'username'),
                    ('User Name', 'user_name'),
                    ('', 'user')]
        for input, username in examples:
            self.assertEqual(utils.generate_unique_username([input]),
                             username)

    def test_email_validation(self):
        s = 'this.email.address.is.a.bit.too.long.but.should.still.validate@example.com'  # noqa
        self.assertEqual(s, utils.valid_email_or_none(s))

    def test_serializer(self):

        class SomeValue:
            pass

        some_value = SomeValue()

        class SomeField(models.Field):
            def get_prep_value(self, value):
                return 'somevalue'

            def from_db_value(self, value, expression, connection, context):
                return some_value

        class SomeModel(models.Model):
            dt = models.DateTimeField()
            t = models.TimeField()
            d = models.DateField()
            img1 = models.ImageField()
            img2 = models.ImageField()
            img3 = models.ImageField()
            something = SomeField()

        def method(self):
            pass

        instance = SomeModel(dt=datetime.now(),
                             d=date.today(),
                             something=some_value,
                             t=datetime.now().time())
        content_file = ContentFile(b'%PDF')
        content_file.name = 'foo.pdf'
        instance.img1 = content_file
        instance.img2 = 'foo.png'
        # make sure serializer doesn't fail if a method is attached to
        # the instance
        instance.method = method
        instance.nonfield = 'hello'
        data = utils.serialize_instance(instance)
        instance2 = utils.deserialize_instance(SomeModel, data)
        self.assertEqual(getattr(instance, 'method', None), method)
        self.assertEqual(getattr(instance2, 'method', None), None)
        self.assertEqual(instance2.something, some_value)
        self.assertEqual(instance2.img1.name, 'foo.pdf')
        self.assertEqual(instance2.img2.name, 'foo.png')
        self.assertEqual(instance2.img3.name, '')
        self.assertEqual(instance.nonfield, instance2.nonfield)
        self.assertEqual(instance.d, instance2.d)
        self.assertEqual(instance.dt.date(), instance2.dt.date())
        for t1, t2 in [(instance.t, instance2.t),
                       (instance.dt.time(), instance2.dt.time())]:
            self.assertEqual(t1.hour, t2.hour)
            self.assertEqual(t1.minute, t2.minute)
            self.assertEqual(t1.second, t2.second)
            # AssertionError: datetime.time(10, 6, 28, 705776)
            #     != datetime.time(10, 6, 28, 705000)
            self.assertEqual(int(t1.microsecond / 1000),
                             int(t2.microsecond / 1000))

    def test_serializer_binary_field(self):
        class SomeBinaryModel(models.Model):
            bb = models.BinaryField()
            bb_empty = models.BinaryField()

        instance = SomeBinaryModel(bb=b'some binary data')

        serialized = utils.serialize_instance(instance)
        deserialized = utils.deserialize_instance(SomeBinaryModel, serialized)

        self.assertEqual(serialized['bb'], 'c29tZSBiaW5hcnkgZGF0YQ==')
        self.assertEqual(serialized['bb_empty'], '')
        self.assertEqual(deserialized.bb, b'some binary data')
        self.assertEqual(deserialized.bb_empty, b'')

    def test_build_absolute_uri(self):
        self.assertEqual(
            utils.build_absolute_uri(None, '/foo'),
            'http://example.com/foo')
        self.assertEqual(
            utils.build_absolute_uri(None, '/foo', protocol='ftp'),
            'ftp://example.com/foo')
        self.assertEqual(
            utils.build_absolute_uri(None, 'http://foo.com/bar'),
            'http://foo.com/bar')

    def test_int_to_base36(self):
        n = 55798679658823689999
        b36 = 'brxk553wvxbf3'
        assert int_to_base36(n) == b36
        assert base36_to_int(b36) == n
