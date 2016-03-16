"""
Contains application configuration.
"""
from django.apps import apps
from django.contrib.admin.apps import SimpleAdminConfig
from django.db import IntegrityError
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _


class WagtailRelationsAppConfig(SimpleAdminConfig):
    name                = 'wagtailplus.wagtailrelations'
    label               = 'wagtailrelations'
    verbose_name        = 'Relations'

    @cached_property
    def applicable_models(self):
        """
        Returns a list of model classes that subclass Page
        and include a "tags" field.

        :rtype: list.
        """
        Page        = apps.get_model('wagtailcore', 'Page')
        applicable  = []

        for model in apps.get_models():
            meta    = getattr(model, '_meta')
            fields  = meta.get_all_field_names()

            if issubclass(model, Page) and 'tags' in fields:
                applicable.append(model)

        return applicable

    def add_relationship_panels(self):
        """
        Add edit handler that includes "related" panels to applicable
        model classes that don't explicitly define their own edit handler.
        """
        from wagtailplus.utils.edit_handlers import add_panel_to_edit_handler
        from wagtailplus.wagtailrelations.edit_handlers import RelatedPanel

        for model in self.applicable_models:
            add_panel_to_edit_handler(model, RelatedPanel, _(u'Related'))

    def add_relationship_methods(self):
        """
        Adds relationship methods to applicable model classes.
        """
        Entry = apps.get_model('wagtailrelations', 'Entry')

        @cached_property
        def related(instance):
            return instance.get_related()

        @cached_property
        def related_live(instance):
            return instance.get_related_live()

        @cached_property
        def related_with_scores(instance):
            return instance.get_related_with_scores()

        def get_related(instance):
             entry = Entry.objects.get_for_model(instance)[0]
             return entry.get_related()

        def get_related_live(instance):
             entry = Entry.objects.get_for_model(instance)[0]
             return entry.get_related_live()

        def get_related_with_scores(instance):
            try:
                entry = Entry.objects.get_for_model(instance)[0]
                return entry.get_related_with_scores()
            except IntegrityError:
                return []

        for model in self.applicable_models:
            model.add_to_class(
                'get_related',
                get_related
            )
            model.add_to_class(
                'get_related_live',
                get_related_live
            )
            model.add_to_class(
                'get_related_with_scores',
                get_related_with_scores
            )
            model.add_to_class(
                'related',
                related
            )
            model.add_to_class(
                'related_live',
                related_live
            )
            model.add_to_class(
                'related_with_scores',
                related_with_scores
            )

    def ready(self):
        """
        Finalizes application configuration.
        """
        import wagtailplus.wagtailrelations.signals.handlers

        self.add_relationship_panels()
        self.add_relationship_methods()
        super(WagtailRelationsAppConfig, self).ready()
