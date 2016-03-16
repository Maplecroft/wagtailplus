"""
Contains edit handler-related utilities.
"""
from wagtail.wagtailadmin.edit_handlers import ObjectList


def add_panel_to_edit_handler(model, panel_cls, heading, index=None):
    """
    Adds specified panel class to model class.

    :param model: the model class.
    :param panel_cls: the panel class.
    :param heading: the panel heading.
    :param index: the index position to insert at.
    """
    try:
        # Wagtail < 1.4
        from wagtail.wagtailadmin.views.pages import get_page_edit_handler
        edit_handler = get_page_edit_handler(model)
    except ImportError:
        edit_handler = model.get_edit_handler()

    panel_instance = ObjectList(
        [panel_cls(),],
        heading = heading
    ).bind_to_model(model)

    if index:
        edit_handler.children.insert(index, panel_instance)
    else:
        edit_handler.children.append(panel_instance)
