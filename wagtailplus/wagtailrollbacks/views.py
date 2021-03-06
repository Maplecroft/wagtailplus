"""
Contains application views.
"""
from django.core.exceptions import PermissionDenied
from django.core.paginator import (
    EmptyPage,
    PageNotAnInteger,
    Paginator
)
from django.core.urlresolvers import reverse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render
)
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.utils import send_notification
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import (
    Page,
    PageRevision
)


def get_revisions(page, page_num=1):
    """
    Returns paginated queryset of PageRevision instances for
    specified Page instance.

    :param page: the page instance.
    :param page_num: the pagination page number.
    :rtype: django.db.models.query.QuerySet.
    """
    revisions   = page.revisions.order_by('-created_at')
    current     = page.get_latest_revision()

    if current:
        revisions.exclude(id=current.id)

    paginator = Paginator(revisions, 5)

    try:
        revisions = paginator.page(page_num)
    except PageNotAnInteger:
        revisions = paginator.page(1)
    except EmptyPage:
        revisions = paginator.page(paginator.num_pages)

    return revisions

def page_revisions(request, page_id, template_name='wagtailrollbacks/edit_handlers/revisions.html'):
    """
    Returns GET response for specified page revisions.

    :param request: the request instance.
    :param page_id: the page ID.
    :param template_name: the template name.
    :rtype: django.http.HttpResponse.
    """
    page        = get_object_or_404(Page, pk=page_id)
    page_perms  = page.permissions_for_user(request.user)

    if not page_perms.can_edit():
        raise PermissionDenied

    page_num    = request.GET.get('p', 1)
    revisions   = get_revisions(page, page_num)

    return render(
        request,
        template_name,
        {
            'page':         page,
            'revisions':    revisions,
            'p':            page_num,
        }
    )

def preview_page_version(request, revision_id):
    """
    Returns GET response for specified page preview.

    :param request: the request instance.
    :param reversion_pk: the page revision ID.
    :rtype: django.http.HttpResponse.
    """
    revision = get_object_or_404(PageRevision, pk=revision_id)

    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    page                = revision.as_page_object()
    request.revision_id = revision_id

    return page.serve_preview(request, page.default_preview_mode)

def confirm_page_reversion(request, revision_id, template_name='wagtailrollbacks/pages/confirm_reversion.html'):
    """
    Handles page reversion process (GET and POST).

    :param request: the request instance.
    :param revision_id: the page revision ID.
    :param template_name: the template name.
    :rtype: django.http.HttpResponse.
    """
    revision    = get_object_or_404(PageRevision, pk=revision_id)
    page        = revision.page

    if page.locked:
        messages.error(
            request,
            _("Page '{0}' is locked.").format(page.title),
            buttons = []
        )

        return redirect(reverse('wagtailadmin_pages:edit', args=(page.id,)))

    page_perms = page.permissions_for_user(request.user)
    if not page_perms.can_edit():
        raise PermissionDenied

    if request.POST:
        is_publishing   = bool(request.POST.get('action-publish')) and page_perms.can_publish()
        is_submitting   = bool(request.POST.get('action-submit'))
        new_revision    = page.rollback(
            revision_id                 = revision_id,
            user                        = request.user,
            submitted_for_moderation    = is_submitting
        )

        if is_publishing:
            new_revision.publish()

            messages.success(
                request,
                _("Page '{0}' published.").format(page.title),
                buttons=[
                    messages.button(page.url, _('View live')),
                    messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
                ]
            )
        elif is_submitting:
            messages.success(
                request,
                _("Page '{0}' submitted for moderation.").format(page.title),
                buttons=[
                    messages.button(reverse('wagtailadmin_pages:view_draft', args=(page.id,)), _('View draft')),
                    messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
                ]
            )
            send_notification(new_revision.id, 'submitted', request.user.id)
        else:
            messages.success(
                request,
                _("Page '{0}' updated.").format(page.title),
                buttons=[]
            )

        for fn in hooks.get_hooks('after_edit_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        return redirect('wagtailadmin_explore', page.get_parent().id)

    return render(
        request,
        template_name,
        {
            'page':         page,
            'revision':     revision,
            'page_perms':   page_perms
        }
    )
