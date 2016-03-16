"""
Contains application model definitions.
"""
from __future__ import unicode_literals

import decimal
import inspect
import six

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy  as _

from taggit.models import Tag
from treebeard.mp_tree import MP_Node

from .app_settings import (
    AUTHORITATIVE_FACTOR,
    CATEGORY_FACTOR,
    LIKE_TYPE_FACTOR,
    TAG_FACTOR
)


class LiveEntryCategoryManager(models.Manager):
    """
    Custom manager for Category models.
    """
    def get_queryset(self):
        """
        Returns queryset limited to categories with live Entry instances.

        :rtype: django.db.models.query.QuerySet.
        """
        queryset = super(LiveEntryCategoryManager, self).get_queryset()
        return queryset.filter(tag__in=[
            entry_tag.tag
            for entry_tag
            in EntryTag.objects.filter(entry__live=True)
        ])

@python_2_unicode_compatible
class Category(MP_Node):
    """
    Stores a hierarchical category, which is essentially a specialized tag.
    """
    name            = models.CharField(_(u'Name'), max_length=255, unique=True)
    tag             = models.ForeignKey('taggit.Tag', editable=False)
    objects         = models.Manager()
    live_entries    = LiveEntryCategoryManager()
    node_order_by   = ('name',)

    class Meta(object):
        verbose_name        = _(u'Category')
        verbose_name_plural = _(u'Categories')
        ordering            = ('path',)

    @cached_property
    def entries(self):
        """
        Returns list of Entry instances assigned to this category.

        :rtype: list.
        """
        return self.get_entries()

    @cached_property
    def total(self):
        """
        Returns the total number of entries tagged with this category.

        :rtype: int.
        """
        return EntryTag.objects.for_category(self).count()

    def __str__(self):
        """
        Returns category name.

        :rtype: str.
        """
        return '{0}'.format(self.name.title())

    def get_entries(self):
        """
        Returns list of Entry instances assigned to this category.

        :rtype: list.
        """
        return [
            result.entry
            for result
            in EntryTag.objects.for_category(self)
        ]

    def save(self, *args, **kwargs):
        """
        Saves the category instance.
        """
        self.set_tag()
        super(Category, self).save(*args, **kwargs)

    def set_tag(self):
        """
        Sets corresponding Tag instance.
        """
        try:
            self.tag = Tag.objects.get(name__iexact=self.name)
        except Tag.DoesNotExist:
            self.tag = Tag.objects.create(name=self.name)

class EntryManager(models.Manager):
    """
    Custom manager for Entry models.
    """
    def get_for_model(self, model):
        """
        Returns tuple (Entry instance, created) for specified
        model instance.

        :rtype: wagtailplus.wagtailrelations.models.Entry.
        """
        return self.get_or_create(
            content_type    = ContentType.objects.get_for_model(model),
            object_id       = model.pk
        )

    def get_for_tag(self, tag):
        """
        Returns queryset of Entry instances assigned to specified
        tag, which can be a PK value, a slug value, or a Tag instance.

        :param tag: tag PK, slug, or instance.
        :rtype: django.db.models.query.QuerySet.
        """
        tag_filter = {'tag': tag}

        if isinstance(tag, six.integer_types):
            tag_filter = {'tag_id': tag}
        elif isinstance(tag, str):
            tag_filter = {'tag__slug': tag}

        return self.filter(id__in=[
            entry_tag.entry_id
            for entry_tag
            in EntryTag.objects.filter(**tag_filter)
        ])

@python_2_unicode_compatible
class Entry(models.Model):
    """
    Generically stores information for a tagged model instance.
    """
    content_type    = models.ForeignKey('contenttypes.ContentType')
    object_id       = models.PositiveIntegerField(_(u'Object ID'))
    content_object  = GenericForeignKey('content_type', 'object_id')
    created         = models.DateTimeField(_(u'Created'))
    modified        = models.DateTimeField(_(u'Modified'))
    title           = models.CharField(_(u'Title'), max_length=255, blank=True)
    url             = models.CharField(_(u'URL'), max_length=255, blank=True)
    live            = models.BooleanField(_(u'Live?'), default=True)
    objects         = EntryManager()

    class Meta(object):
        verbose_name        = _(u'Entry')
        verbose_name_plural = _(u'Entries')
        ordering            = ('title',)

    @cached_property
    def related(self):
        """
        Returns list related Entry instances.

        :rtype: list.
        """
        return self.get_related()

    @cached_property
    def related_with_scores(self):
        """
        Returns list of related tuples (Entry instance, score).

        :rtype: list.
        """
        return self.get_related_with_scores()

    @property
    def tags(self):
        """
        Returns list of Tag instances associated with this instance.

        :rtype: list.
        """
        return [
            result.tag
            for result
            in self.entry_tags.all()
        ]

    def __str__(self):
        """
        Returns title for this instance.

        :rtype: str.
        """
        return '{0}'.format(self.title)

    @staticmethod
    def get_authoritative_score(related):
        """
        Returns authoritative score for specified related Entry instance.

        :param related: the related Entry instance.
        :rtype: decimal.Decimal.
        """
        # Older entries that are updated over time *should* be more
        # considered more authoritative than older entries that are
        # not updated.
        age     = max((timezone.now() - related.created).total_seconds(), 1)
        delta   = max((related.modified - related.created).total_seconds(), 1)

        return decimal.Decimal(
            (float(delta) / float(age)) * AUTHORITATIVE_FACTOR
        )

    def get_categories(self):
        """
        Returns queryset of assigned Category instances.

        :rtype: django.db.models.query.QuerySet.
        """
        return Category.objects.filter(tag__in=self.tags)

    def get_category_score(self, related):
        """
        Returns category score for this instance and specified related
        Entry instance.

        :param related: the related Entry instance.
        :rtype: decimal.Decimal.
        """
        score   = 0
        tags    = set(self.tags) & set(related.tags)
        total   = len(tags)

        # Score each category by dividing it's depth by the total
        # number of entries assigned to that category.
        for category in Category.objects.filter(tag__in=tags):
            score += (float(category.depth) / float(category.total))

        return decimal.Decimal(
            min((float(score) / float(total)), 1) * CATEGORY_FACTOR
        )

    def get_like_type_score(self, related):
        """

        :rtype: decimal.Decimal.
        """
        s_tree  = inspect.getmro(self.content_type.model_class())
        r_tree  = inspect.getmro(related.content_type.model_class())
        shared  = len(set(s_tree) & set(r_tree))
        total   = len(set(s_tree + r_tree))

        return decimal.Decimal(
            (float(shared) / float(total)) * LIKE_TYPE_FACTOR
        )

    def get_related(self):
        """
        Returns set of related Entry instances.

        :rtype: set.
        """
        return set([
            result.entry
            for result
            in EntryTag.objects.related_to(self)
        ])

    def get_related_score(self, related):
        """
        Returns related score for this instance and specified related
        Entry instance.

        :param related: the related Entry instance.
        :rtype: decimal.Decimal.
        """
        return sum([
            self.get_authoritative_score(related),
            self.get_category_score(related),
            self.get_like_type_score(related),
            self.get_tag_score(related),
        ])

    def get_related_with_scores(self):
        """
        Returns list of related tuples (Entry instance, score).

        :rtype: list.
        """
        scored = {}

        for related in self.get_related():
            scored[related] = self.get_related_score(related)

        return sorted(six.iteritems(scored), key=lambda x: x[1], reverse=True)

    def get_tag_score(self, related):
        """
        Returns tag score for this instance and specified related Entry
        instance.

        :param related: the related Entry instance.
        :rtype: decimal.Decimal.
        """
        common  = len(set(self.tags) & set(related.tags))
        total   = len(set(self.tags + related.tags))

        return decimal.Decimal(
            (float(common) / float(total)) * TAG_FACTOR
        )

    def save(self, *args, **kwargs):
        """
        Saves the instance.
        """
        if not self.pk:
            self.created = timezone.now()

        self.modified = timezone.now()

        super(Entry, self).save(*args, **kwargs)

class EntryTagManager(models.Manager):
    """
    Custom manager for EntryTag models.
    """
    def for_category(self, category, live_only=False):
        """
        Returns queryset of EntryTag instances for specified category.

        :param category: the Category instance.
        :param live_only: flag to include only "live" entries.
        :rtype: django.db.models.query.QuerySet.
        """
        filters = {'tag': category.tag}

        if live_only:
            filters.update({'entry__live': True})

        return self.filter(**filters)

    def live_entries(self):
        """

        :return:
        """
        return self.filter(entry__live=True)

    def related_to(self, entry, live_only=False):
        """
        Returns queryset of Entry instances related to specified
        Entry instance.

        :param entry: the Entry instance.
        :param live_only: flag to include only "live" entries.
        :rtype: django.db.models.query.QuerySet.
        """
        filters = {'tag__in': entry.tags}

        if live_only:
            filters.update({'entry__live': True})

        return self.filter(**filters).exclude(entry=entry)

@python_2_unicode_compatible
class EntryTag(models.Model):
    """
    Stores a correlation between a Tag and an Entry instance.
    """
    tag     = models.ForeignKey('taggit.Tag', related_name='relation_entries')
    entry   = models.ForeignKey('wagtailrelations.Entry', related_name='entry_tags')
    objects = EntryTagManager()

    class Meta(object):
        verbose_name        = _(u'Entry Tag')
        verbose_name_plural = _(u'Entry Tags')
        ordering            = ('tag__name', 'entry__title')
        unique_together     = ('tag', 'entry')

    def __str__(self):
        """
        Returns entry tag label.

        :rtype: str.
        """
        return '{0}: {1}'.format(self.entry, self.tag)
