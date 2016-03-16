"""
Contains model class definitions.
"""
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy  as _

from taggit.managers import TaggableManager
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailadmin.edit_handlers import FieldRowPanel
from wagtail.wagtailadmin.edit_handlers import MultiFieldPanel
from wagtail.wagtailadmin.edit_handlers import ObjectList
from wagtail.wagtailadmin.taggable import TagSearchable
from wagtail.wagtailsearch import index
from wagtail.wagtailsearch.queryset import SearchableQuerySetMixin


class LinkQuerySet(SearchableQuerySetMixin, models.QuerySet):
    pass

@python_2_unicode_compatible
class BaseLink(models.Model, TagSearchable):
    """
    Abstract base class that stores either a URL or an email address.
    """
    LINK_TYPE_EXTERNAL  = 1
    LINK_TYPE_EMAIL     = 2

    created_at      = models.DateTimeField(auto_now_add=True)
    link_type       = models.PositiveIntegerField(_('Link Type'), blank=True)
    title           = models.CharField(_('Title'), max_length=100, help_text=_('Enter a title for this link'))
    email           = models.EmailField(_('Email'), blank=True, help_text=_('Enter a valid email address'))
    external_url    = models.URLField(_('URL'), blank=True, help_text=_('Enter a valid URL, including scheme (e.g. http://)'))
    tags            = TaggableManager(help_text=None, blank=True, verbose_name=_('Tags'))
    objects         = LinkQuerySet.as_manager()

    class Meta(object):
        abstract            = True
        verbose_name        = _('Link')
        verbose_name_plural = _('Links')
        ordering            = ('title',)

    # Make link searchable.
    search_fields = (
        index.SearchField('title', partial_match=True, boost=10),
        index.SearchField('get_tags', partial_match=True, boost=10),
        index.SearchField('external_url'),
        index.SearchField('email'),
        index.FilterField('link_type'),
    )

    @property
    def url(self):
        """
        Returns link URL.

        :rtype: str.
        """
        url = None

        if self.link_type == self.LINK_TYPE_EMAIL:
            url = self.email
        elif self.link_type == self.LINK_TYPE_EXTERNAL:
            url = self.external_url

        return url

    def __str__(self):
        """
        Returns link title.

        :rtype: str.
        """
        return '{0}'.format(self.title)

    def get_absolute_url(self):
        """
        Returns link URL, including "mailto:" portion for email links.

        :rtype: str.
        """
        url = None

        if self.link_type == self.LINK_TYPE_EMAIL:
            url = 'mailto:{0}'.format(self.email)
        elif self.link_type == self.LINK_TYPE_EXTERNAL:
            url = self.external_url

        return url

    @classmethod
    def edit_handler(cls):
        """
        Returns edit handler instance.

        :rtype: wagtail.wagtailadmin.edit_handlers.ObjectList.
        """
        return ObjectList(cls.content_panels)

class Link(BaseLink):
    """
    Concrete implementation of link.
    """
    pass

Link.content_panels = [
    FieldPanel('title', classname='full title'),
    MultiFieldPanel([
        FieldRowPanel([
            FieldPanel('external_url', classname='col6'),
            FieldPanel('email', classname='col6'),
        ], classname='label-above'),
    ], _('Link Type (complete one or the other)')),
    FieldPanel('tags'),
]

class EmailLinkManager(models.Manager):
    def get_queryset(self):
        qs = LinkQuerySet(model=self.model)
        return qs.filter(link_type=Link.LINK_TYPE_EMAIL)

    def search(self, query_string, fields=None, operator=None, order_by_relevance=True, backend='default'):
        return self.get_queryset().search(query_string, fields, operator, order_by_relevance, backend)

class EmailLink(Link):
    class Meta(object):
        proxy = True

    objects = EmailLinkManager()

    def __str__(self):
        """
        Returns email address.
        
        :rtype: str.
        """
        return '{0}'.format(self.email)

class ExternalLinkManager(models.Manager):
    def get_queryset(self):
        qs = LinkQuerySet(model=self.model)
        return qs.filter(link_type=Link.LINK_TYPE_EXTERNAL)

    def search(self, query_string, fields=None, operator=None, order_by_relevance=True, backend='default'):
        return self.get_queryset().search(query_string, fields, operator, order_by_relevance, backend)

class ExternalLink(Link):
    class Meta(object):
        proxy = True

    objects = ExternalLinkManager()
