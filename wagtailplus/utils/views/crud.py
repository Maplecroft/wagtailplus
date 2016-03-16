"""
Contains application CRUD view definitions.
"""
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy  as _
from django.views import generic
from django.views.decorators.vary import vary_on_headers

from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin import messages
from wagtail.wagtailsearch.backends import get_search_backends


class IndexView(generic.ListView):
    """
    CRUD index view for specified model class.
    """
    paginate_by         = 20
    page_kwarg          = 'p'
    search_form_class   = SearchForm
    template_dir        = None

    def __init__(self, *args, **kwargs):
        """
        Initializes the view instance.
        """
        #noinspection PyArgumentList
        super(IndexView, self).__init__(*args, **kwargs)

        if not self.template_dir:
            raise ImproperlyConfigured(
                'You must set the template_dir attribute.'
            )

    @method_decorator(vary_on_headers('X-Requested-With'))
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatches the request.

        :param request: the request instance.
        :rtype: django.http.HttpResponse.
        """
        return super(IndexView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Returns context dictionary for view.

        :rtype: dict.
        """
        #noinspection PyUnresolvedReferences
        query_str           = self.request.GET.get('q', None)
        queryset            = kwargs.pop('object_list', self.object_list)
        context_object_name = self.get_context_object_name(queryset)

        # Build the context dictionary.
        context = {
            'ordering':     self.get_ordering(),
            'query_string': query_str,
            'is_searching': bool(query_str),
        }

        # Add extra variables to context for non-AJAX requests.
        #noinspection PyUnresolvedReferences
        if not self.request.is_ajax() or kwargs.get('force_search', False):
            context.update({
                'search_form':  self.get_search_form(),
                'popular_tags': self.model.popular_tags()
            })

        if context_object_name is not None:
            context[context_object_name] = queryset

        # Update context with any additional keyword arguments.
        context.update(kwargs)

        return super(IndexView, self).get_context_data(**context)

    def get_ordering(self):
        """
        Returns ordering value for list.

        :rtype: str.
        """
        #noinspection PyUnresolvedReferences
        ordering = self.request.GET.get('ordering', None)

        if ordering not in ['title', '-created_at']:
            ordering = '-created_at'

        return ordering

    def get_queryset(self):
        """
        Returns queryset instance.

        :rtype: django.db.models.query.QuerySet.
        """
        queryset    = super(IndexView, self).get_queryset()
        search_form = self.get_search_form()

        if search_form.is_valid():
            query_str   = search_form.cleaned_data.get('q', '').strip()
            queryset    = self.model.objects.search(query_str)

        return queryset

    def get_search_form(self):
        """
        Returns search form instance.

        :rtype: django.forms.ModelForm.
        """
        #noinspection PyUnresolvedReferences
        if 'q' in self.request.GET:
            #noinspection PyUnresolvedReferences
            return self.search_form_class(self.request.GET)
        else:
            return self.search_form_class(placeholder=_(u'Search'))

    def get_template_names(self):
        """
        Returns a list of template names for the view.

        :rtype: list.
        """
        #noinspection PyUnresolvedReferences
        if self.request.is_ajax():
            template_name = '/results.html'
        else:
            template_name = '/index.html'

        return ['{0}{1}'.format(self.template_dir, template_name)]

    def paginate_queryset(self, queryset, page_size):
        """
        Returns tuple containing paginator instance, page instance,
        object list, and whether there are other pages.

        :param queryset: the queryset instance to paginate.
        :param page_size: the number of instances per page.
        :rtype: tuple.
        """
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans                 = self.get_paginate_orphans(),
            allow_empty_first_page  = self.get_allow_empty()
        )

        page_kwarg  = self.page_kwarg
        #noinspection PyUnresolvedReferences
        page_num    = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1

        # Default to a valid page.
        try:
            page = paginator.page(page_num)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        #noinspection PyRedundantParentheses
        return (paginator, page, page.object_list, page.has_other_pages())

class BaseEditView(generic.edit.ModelFormMixin, generic.edit.ProcessFormView):
    """
    Base CRUD edit view.
    """
    url_namespace   = None
    template_dir    = None

    def __init__(self, *args, **kwargs):
        """
        Initializes the view instance.
        """
        super(BaseEditView, self).__init__(*args, **kwargs)

        if not self.url_namespace:
            raise ImproperlyConfigured(
                'You must set the namespace attribute.'
            )

        if not self.template_dir:
            raise ImproperlyConfigured(
                'You must set the template_dir attribute.'
            )

    @method_decorator(vary_on_headers('X-Requested-With'))
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatches the request.

        :param request: the request instance.
        :rtype: django.http.HttpResponse.
        """
        return super(BaseEditView, self).dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        """
        Processes an invalid form submittal.

        :param form: the form instance.
        :rtype: django.http.HttpResponse.
        """
        meta = getattr(self.model, '_meta')

        #noinspection PyUnresolvedReferences
        messages.error(
            self.request,
            _(u'The {0} could not be saved due to errors.').format(
                meta.verbose_name.lower()
            )
        )

        return super(BaseEditView, self).form_invalid(form)

    def form_valid(self, form):
        """
        Processes a valid form submittal.

        :param form: the form instance.
        :rtype: django.http.HttpResponse.
        """
        #noinspection PyAttributeOutsideInit
        self.object = form.save()
        meta        = getattr(self.object, '_meta')

        # Index the object.
        for backend in get_search_backends():
            backend.add(object)

        #noinspection PyUnresolvedReferences
        messages.success(
            self.request,
            _(u'{0} "{1}" saved.').format(
                meta.verbose_name,
                str(self.object)
            ),
            buttons=[messages.button(
                reverse(
                    '{0}:edit'.format(self.url_namespace),
                    args=(self.object.id,)
                ),
                _(u'Edit')
            )]
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        """
        Returns redirect URL for valid form submittal.

        :rtype: str.
        """
        if self.success_url:
            url = force_text(self.success_url)
        else:
            url = reverse('{0}:index'.format(self.url_namespace))

        return url

class CreateView(BaseEditView, generic.CreateView):
    """
    CRUD create view for specified model class.
    """
    def get_template_names(self):
        """
        Returns a list of template names for the view.

        :rtype: list.
        """
        return ['{0}/add.html'.format(self.template_dir)]

class UpdateView(BaseEditView, generic.UpdateView):
    """
    CRUD edit view for specified model class.
    """
    def get_template_names(self):
        """
        Returns a list of template names for the view.

        :rtype: list.
        """
        return ['{0}/edit.html'.format(self.template_dir)]

class DeleteView(generic.DeleteView):
    """
    CRUD delete view for specified model class.
    """
    url_namespace   = None
    template_dir    = None

    def delete(self, request, *args, **kwargs):
        """
        Processes deletion of the specified instance.

        :param request: the request instance.
        :rtype: django.http.HttpResponse.
        """
        #noinspection PyAttributeOutsideInit
        self.object = self.get_object()
        success_url = self.get_success_url()
        meta        = getattr(self.object, '_meta')

        self.object.delete()

        messages.success(
            request,
            _(u'{0} "{1}" deleted.').format(
                meta.verbose_name.lower(),
                str(self.object)
            )
        )

        return redirect(success_url)

    def get_success_url(self):
        """
        Returns redirect URL for valid form submittal.

        :rtype: str.
        """
        return reverse('{0}:index'.format(self.url_namespace))

    def get_template_names(self):
        """
        Returns a list of template names for the view.

        :rtype: list.
        """
        return ['{0}/confirm_delete.html'.format(self.template_dir)]
