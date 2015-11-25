#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contains model unit tests.
"""
from __future__ import unicode_literals
from django.test import TestCase

from wagtail.wagtailadmin.edit_handlers import ObjectList

from ..models import (
    EmailLink,
    ExternalLink,
    Link
)


class TestLink(TestCase):
    def test_edit_handler(self):
        self.assertTrue(
            isinstance(Link.edit_handler(), ObjectList)
        )

class TestEmailLink(TestCase):
    def setUp(self):
        self.model = Link.objects.create(
            link_type   = Link.LINK_TYPE_EMAIL,
            title       = 'Test Email Address',
            email       = 'somébody@something.com'
        )

    def test_url_property(self):
        self.assertEqual(self.model.url, self.model.email)

    def test_get_absolute_url(self):
        self.assertEqual(
            self.model.get_absolute_url(),
            'mailto:{0}'.format(self.model.email)
        )

    def test_manager(self):
        self.assertTrue(
            self.model in EmailLink.objects.all()
        )

    def test_unicode_email_addres(self):
        try:
            str(self.model)
        except UnicodeDecodeError:
            raise AssertionError("Failed to `str` the unicode email address")

class TestExternalLink(TestCase):
    def setUp(self):
        self.model = Link.objects.create(
            link_type       = Link.LINK_TYPE_EXTERNAL,
            title           = 'Test Link',
            external_url    = 'http://www.test.com'
        )

    def test_url_property(self):
        self.assertEqual(self.model.url, self.model.external_url)

    def test_get_absolute_url(self):
        self.assertEqual(
            self.model.get_absolute_url(),
            '{0}'.format(self.model.external_url)
        )

    def test_manager(self):
        self.assertTrue(
            self.model in ExternalLink.objects.all()
        )
