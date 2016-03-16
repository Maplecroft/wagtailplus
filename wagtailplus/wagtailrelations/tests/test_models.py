#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contains model unit tests.
"""
from __future__ import unicode_literals

import decimal

from django.test import TestCase
from django.utils import timezone

from taggit.models import Tag
from wagtail.wagtailcore.models import Page
from wagtail.tests.testapp.models import TaggedPage
from ..models import (
    Category,
    Entry,
    EntryTag
)


class TestCategory(TestCase):
    def setUp(self):
        # Create some categories.
        self.category       = Category.add_root(name='category')
        self.sub_category   = self.category.add_child(name='sub category')
        self.unicode_sub    = self.category.add_child(name='sub catégory')

        # Get the root page.
        self.root_page = Page.objects.get(id=2)

        # Add a published page.
        self.published = self.root_page.add_child(instance=TaggedPage(
            title   = 'Published Page',
            slug    = 'published-page'
        ))

        # Add a future published page.
        self.unpublished = self.root_page.add_child(instance=TaggedPage(
            title   = 'Unpublished Page',
            slug    = 'unpublished-page'
        ))
        self.unpublished.save_revision(
            approved_go_live_at=timezone.now() + timezone.timedelta(days=3)
        )

        # Add a tag to both pages.
        for page in [self.published, self.unpublished]:
            page.tags.through.objects.create(
                content_object  = page,
                tag             = self.sub_category.tag
            )

    def test_live_entries(self):
        self.assertEqual(Category.live_entries.all().count(), 1)

    def test_entries_property(self):
        self.assertEqual(len(self.sub_category.entries), 2)

    def test_total_property(self):
        self.assertEqual(self.sub_category.total, 2)

    def test_str(self):
        self.assertEqual(
            str(self.sub_category),
            self.sub_category.name.title()
        )

    def test_set_tag(self):
        self.sub_category.set_tag()
        self.assertEqual(type(self.sub_category.tag), Tag)

    def test_unicode_category_name(self):
        try:
            str(self.unicode_sub)
        except UnicodeDecodeError:
            raise AssertionError("Failed to `str` the unicode category name")


class TestEntity(TestCase):
    def setUp(self):
        # Create some categories.
        self.beer       = Category.add_root(name='beer')
        self.ale        = self.beer.add_child(name='ale')
        self.ipa        = self.ale.add_child(name='india pale ale')
        self.porter     = self.ale.add_child(name='porter')

        # Create some tags.
        self.spicy  = Tag.objects.create(name='spicy')
        self.fruity = Tag.objects.create(name='fruity')
        self.piny   = Tag.objects.create(name='piny')

        # Find root page.
        self.root_page = Page.objects.get(id=2)

        # Add child page.
        self.child_page = TaggedPage(title='Sculpin', slug='sculpin')
        self.root_page.add_child(instance=self.child_page)

        # Get corresponding Entity instance.
        self.entry= Entry.objects.get_for_model(self.child_page)[0]

    def create_related_pages(self):
        # Create some additional pages.
        pliny = self.root_page.add_child(instance=TaggedPage(
            title   = 'Pliny the Elder',
            slug    = 'pliny-elder'
        ))

        anchor_porter = self.root_page.add_child(instance=TaggedPage(
            title   = 'Anchor Porter',
            slug    = 'anchor-porter'
        ))

        # Relate pages through tags.
        for tag in [self.beer.tag, self.ale.tag, self.ipa.tag, self.fruity]:
            self.child_page.tags.through.objects.create(
                content_object  = self.child_page,
                tag             = tag
            )
        for tag in [self.beer.tag, self.ale.tag, self.ipa.tag, self.piny]:
            pliny.tags.through.objects.create(
                content_object  = pliny,
                tag             = tag
            )
        for tag in [self.beer.tag, self.ale.tag, self.porter.tag]:
            anchor_porter.tags.through.objects.create(
                content_object  = anchor_porter,
                tag             = tag
            )

        self.pliny          = pliny
        self.anchor_porter  = anchor_porter

    def test_get_for_tag(self):
        self.child_page.tags.through.objects.create(
            content_object  = self.child_page,
            tag             = self.ipa.tag
        )

        self.assertTrue(
            self.entry
            in Entry.objects.get_for_tag(self.ipa.tag)
        )

    def test_tags_property(self):
        # Add some tags.
        tags = [
            self.beer.tag,
            self.ale.tag,
            self.ipa.tag,
            self.fruity
        ]

        for tag in tags:
            self.child_page.tags.through.objects.create(
                content_object  = self.child_page,
                tag             = tag
            )

        for result in self.entry.tags:
            self.assertTrue(result in tags)

    def test_related_property(self):
        # Should get a list of other Entity instances that
        # share at least one tag.
        self.create_related_pages()

        entries = [
            Entry.objects.get_for_model(self.anchor_porter)[0],
            Entry.objects.get_for_model(self.pliny)[0]
        ]

        for entity in self.entry.related:
            self.assertTrue(entity in entries)

    def test_related_with_score_property(self):
        # Should get a list of tuples (entity, score) for other
        # Entity instances that shae at least one tag.
        self.create_related_pages()

        entries = [
            Entry.objects.get_for_model(self.anchor_porter)[0],
            Entry.objects.get_for_model(self.pliny)[0]
        ]

        for entity, score in self.entry.related_with_scores:
            self.assertTrue(entity in entries)
            self.assertEqual(type(score), decimal.Decimal)
