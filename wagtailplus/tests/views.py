"""

"""
from django.core.urlresolvers import reverse
from django.test import TestCase

from wagtail.tests.utils import WagtailTestUtils


class BaseTestIndexView(TestCase, WagtailTestUtils):
    """
    Base test case for CRUD index view.
    """
    url_namespace   = None
    template_dir    = None

    def _create_sequential_instance(self, index):
        """
        Stub method for extending class to create sequential
        model instances.

        :param index: the sequential index to use.
        """
        raise NotImplemented(
            'This method must be implemented by {0}'.format(
                self.__class__.__name__
            )
        )

    def setUp(self):
        self.login()

    def get(self, params=None):
        if not params:
            params = {}

        return self.client.get(
            reverse('{0}:index'.format(self.url_namespace)), params)

    def populate(self):
        """
        Populates several model class instance.
        """
        for i in range(50):
            self._create_sequential_instance(i)

    def test_get(self):
        # Generate the response.
        response = self.get()

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/index.html'.format(self.template_dir)
        )

    def test_search(self):
        # Generate the response.
        response = self.get({'q': 'keyword'})

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], 'keyword')

    def test_pagination(self):
        # Create model class instances.
        self.populate()

        # Generate the response.
        response = self.get({'p': 2})

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/index.html'.format(self.template_dir)
        )
        self.assertEqual(response.context['page_obj'].number, 2)

    def test_pagination_invalid(self):
        # Create model class instances.
        self.populate()

        # Generate the response.
        response = self.get({'p': 'fake'})

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/index.html'.format(self.template_dir)
        )
        self.assertEqual(response.context['page_obj'].number, 1)

    def test_pagination_out_of_range(self):
        # Create model class instances.
        self.populate()

        # Generate the response.
        response = self.get({'p': 99999})

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/index.html'.format(self.template_dir)
        )
        self.assertEqual(
            response.context['page_obj'].number,
            response.context['paginator'].num_pages
        )

    def test_ordering(self):
        orderings = ['title', '-created_at']
        for ordering in orderings:
            response = self.get({'ordering': ordering})
            self.assertEqual(response.status_code, 200)

class BaseTestCreateView(TestCase, WagtailTestUtils):
    """
    Base test case for CRUD add view.
    """
    url_namespace   = None
    template_dir    = None
    model_class     = None

    def _get_post_data(self):
        """
        Stub method for extending class to return data dictionary
        to create a new model instance on POST.

        :rtype: dict.
        """
        raise NotImplemented(
            'This method must be implemented by {0}'.format(
                self.__class__.__name__
            )
        )

    def setUp(self):
        self.login()

    def test_get(self):
        # Generate the response.
        response = self.client.get(
            reverse('{0}:add'.format(self.url_namespace))
        )

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/add.html'.format(self.template_dir)
        )

    def test_post(self):
        # Get POST data.
        data = self._get_post_data()

        # Generate the response.
        response = self.client.post(
            reverse('{0}:add'.format(self.url_namespace)),
            data
        )

        # Check assertions.
        self.assertRedirects(
            response,
            reverse('{0}:index'.format(self.url_namespace))
        )
        self.assertTrue(
            self.model_class.objects.filter(**data).exists()
        )

class BaseTestUpdateView(TestCase, WagtailTestUtils):
    """
    Base test case for CRUD edit view.
    """
    url_namespace   = None
    template_dir    = None
    model_class     = None

    def _get_instance(self):
        """
        Stub method for extending class to return saved model class
        instance.

        :rtype: django.db.models.Model.
        """
        raise NotImplemented(
            'This method must be implemented by {0}'.format(
                self.__class__.__name__
            )
        )

    def _get_post_data(self):
        """
        Stub method for extending class to return data dictionary
        to create a new model instance on POST.

        :rtype: dict.
        """
        raise NotImplemented(
            'This method must be implemented by {0}'.format(
                self.__class__.__name__
            )
        )

    def setUp(self):
        # Create the instance and login.
        self.instance = self._get_instance()
        self.login()

    def test_get(self):
        # Generate the response.
        response = self.client.get(
            reverse(
                '{0}:edit'.format(self.url_namespace),
                args=(self.instance.pk,)
            )
        )

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/edit.html'.format(self.template_dir)
        )

    def test_post(self):
        # Get POST data.
        data = self._get_post_data()

        # Generate the response.
        response = self.client.post(
            reverse(
                '{0}:edit'.format(self.url_namespace),
                args=(self.instance.pk,)
            ),
            data
        )

        # Check assertions.
        self.assertRedirects(
            response,
            reverse('{0}:index'.format(self.url_namespace)))
        self.assertTrue(
            self.model_class.objects.filter(**data).exists()
        )

class BaseTestDeleteView(TestCase, WagtailTestUtils):
    """
    Base test case for CRUD delete view.
    """
    url_namespace   = None
    template_dir    = None
    model_class     = None

    def _get_instance(self):
        """
        Stub method for extending class to return saved model class
        instance.

        :rtype: django.db.models.Model.
        """
        raise NotImplemented(
            'This method must be implemented by {0}'.format(
                self.__class__.__name__
            )
        )

    def setUp(self):
        # Create the instance and login.
        self.instance = self._get_instance()
        self.login()

    def test_get(self):
        # Generate the response.
        response = self.client.get(
            reverse(
                '{0}:delete'.format(self.url_namespace),
                args=(self.instance.pk,)
            )
        )

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/confirm_delete.html'.format(self.template_dir)
        )

    def test_delete(self):
        # Generate the response.
        response = self.client.post(
            reverse(
                '{0}:delete'.format(self.url_namespace),
                args=(self.instance.pk,)
            ),
            {'foo': 'bar'}
        )

        # Check assertions.
        self.assertRedirects(
            response,
            reverse('{0}:index'.format(self.url_namespace))
        )
        self.assertFalse(
            self.model_class.objects.filter(pk=self.instance.pk).exists()
        )

class BaseTestChooserView(TestCase, WagtailTestUtils):
    """
    Base test for chooser view.
    """
    url_namespace   = None
    template_dir    = None
    model_class     = None

    def _create_sequential_instance(self, index):
        """
        Stub method for extending class to create sequential
        model instances.

        :param index: the sequential index to use.
        """
        raise NotImplemented(
            'This method must be implemented by {0}'.format(
                self.__class__.__name__
            )
        )

    def setUp(self):
        self.login()

    def get(self, params=None):
        if not params:
            params = {}

        return self.client.get(
            reverse('{0}:choose'.format(self.url_namespace)),
            params
        )

    def populate(self):
        """
        Populates several model class instance.
        """
        for i in range(50):
            self._create_sequential_instance(i)

    def test_get(self):
        # Generate the response.
        response = self.get()

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/chooser.html'.format(self.template_dir)
        )
        self.assertTemplateUsed(
            response,
            '{0}/results.html'.format(self.template_dir)
        )
        self.assertTemplateUsed(
            response,
            '{0}/chooser.js'.format(self.template_dir)
        )

    def test_search(self):
        # Generate the response.
        response = self.get({'q': 'keyword'})

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], 'keyword')

    def test_pagination(self):
        # Create model class instances.
        self.populate()

        # Generate the response.
        response = self.get({'p': 2})

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/results.html'.format(self.template_dir)
        )
        self.assertEqual(response.context['page_obj'].number, 2)

    def test_pagination_invalid(self):
        # Create model class instances.
        self.populate()

        # Generate the response.
        response = self.get({'p': 'fake'})

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/results.html'.format(self.template_dir)
        )
        self.assertEqual(response.context['page_obj'].number, 1)

    def test_pagination_out_of_range(self):
        # Create model class instances.
        self.populate()

        # Generate the response.
        response = self.get({'p': 99999})

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/results.html'.format(self.template_dir)
        )
        self.assertEqual(
            response.context['page_obj'].number,
            response.context['paginator'].num_pages
        )

class BaseTestChosenView(TestCase, WagtailTestUtils):
    url_namespace   = None
    template_dir    = None
    model_class     = None

    def _get_instance(self):
        """
        Stub method for extending class to return saved model class
        instance.

        :rtype: django.db.models.Model.
        """
        raise NotImplemented(
            'This method must be implemented by {0}'.format(
                self.__class__.__name__
            )
        )

    def setUp(self):
        # Create the instance and login.
        self.instance = self._get_instance()
        self.login()

    def test_get(self):
        # Generate the response.
        response = self.client.get(
            reverse(
                '{0}:chosen'.format(self.url_namespace),
                args=(self.instance.id,)
            )
        )

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/chosen.js'.format(self.template_dir)
        )

class BaseTestChooserCreateView(TestCase, WagtailTestUtils):
    """
    Base test case for CRUD add view.
    """
    url_namespace   = None
    template_dir    = None
    model_class     = None

    def _get_post_data(self):
        """
        Stub method for extending class to return data dictionary
        to create a new model instance on POST.

        :rtype: dict.
        """
        raise NotImplemented(
            'This method must be implemented by {0}'.format(
                self.__class__.__name__
            )
        )

    def setUp(self):
        self.login()

    def test_get(self):
        # Generate the response.
        response = self.client.get(
            reverse('{0}:choose'.format(self.url_namespace))
        )

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            '{0}/chooser.html'.format(self.template_dir)
        )
        self.assertTemplateUsed(
            response,
            '{0}/results.html'.format(self.template_dir)
        )
        self.assertTemplateUsed(
            response,
            '{0}/chooser.js'.format(self.template_dir)
        )

    def test_post(self):
        # Get POST data.
        data = self._get_post_data()

        # Generate the response.
        response = self.client.post(
            reverse('{0}:choose'.format(self.url_namespace)),
            data
        )

        # Check assertions.
        self.assertTemplateUsed(
            response,
            '{0}/chosen.js'.format(self.template_dir)
        )
        self.assertContains(
            response,
            'modal.respond'
        )
        self.assertTrue(
            self.model_class.objects.filter(**data).exists()
        )
