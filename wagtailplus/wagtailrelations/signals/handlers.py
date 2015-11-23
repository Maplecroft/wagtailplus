"""
Contains application signal handlers.
"""
from django.apps import apps
from django.db.models import signals

from taggit.models import ItemBase


#noinspection PyUnusedLocal
def create_entry_tag(sender, instance, created, **kwargs):
    """
    Creates EntryTag for Entry corresponding to specified
    ItemBase instance.

    :param sender: the sending ItemBase class.
    :param instance: the ItemBase instance.
    """
    from ..models import (
        Entry,
        EntryTag
    )

    entry   = Entry.objects.get_for_model(instance.content_object)[0]
    tag     = instance.tag

    if not EntryTag.objects.filter(tag=tag, entry=entry).exists():
        EntryTag.objects.create(tag=tag, entry=entry)

#noinspection PyUnusedLocal
def delete_entry_tag(sender, instance, **kwargs):
    """
    Deletes EntryTag for Entry corresponding to specified
    TaggedItemBase instance.

    :param sender: the sending TaggedItemBase class.
    :param instance: the TaggedItemBase instance.
    """
    from ..models import (
        Entry,
        EntryTag
    )

    entry   = Entry.objects.get_for_model(instance.content_object)[0]
    tag     = instance.tag

    EntryTag.objects.filter(tag=tag, entry=entry).delete()

#noinspection PyUnusedLocal
def delete_entry(sender, instance, **kwargs):
    """
    Deletes Entry instance corresponding to specified instance.

    :param sender: the sending class.
    :param instance: the instance being deleted.
    """
    from ..models import Entry

    Entry.objects.get_for_model(instance)[0].delete()

#noinspection PyUnusedLocal
def update_entry_attributes(sender, instance, **kwargs):
    """
    Updates attributes for Entry instance corresponding to
    specified instance.

    :param sender: the sending class.
    :param instance: the instance being saved.
    """
    from ..models import Entry

    entry = Entry.objects.get_for_model(instance)[0]

    entry.title = getattr(instance, 'title', str(instance))
    entry.live  = bool(getattr(instance, 'live', True))

    entry.save()

for model in apps.get_models():
    # Connect signals to ItemBase classes.
    if issubclass(model, ItemBase):
        # Create EntryTag instance.
        signals.post_save.connect(
            create_entry_tag,
            sender          = model,
            dispatch_uid    = 'wagtailrelations_create_entry_tag'
        )

        # Delete EntryTag instance.
        signals.post_delete.connect(
            delete_entry_tag,
            sender          = model,
            dispatch_uid    = 'wagtailrelations_delete_entry_tag'
        )

    # Connect signals to classes with a "tags" field.
    meta = getattr(model, '_meta')

    if 'tags' in meta.get_all_field_names():
        # Update attributes.
        signals.post_save.connect(
            update_entry_attributes,
            sender          = model,
            dispatch_uid    = 'wagtailrelations_update_entry_attributes'
        )
        # Delete Entry instance.
        signals.post_delete.connect(
            delete_entry,
            sender          = model,
            dispatch_uid    = 'wagtailrelations_delete_entry'
        )
