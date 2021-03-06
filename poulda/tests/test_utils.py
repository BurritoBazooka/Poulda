"""Test ``utils`` module."""

from unittest import TestCase


class TestGetFileFromRequest(TestCase):

    def call_fut(self, request):
        from poulda.utils import get_file_from_request
        return get_file_from_request(request)

    def make_dummy_request(self, length, body):
        class Dummy(dict):
            headers = {'Content-Length': length}
        return Dummy(**{'wsgi.input': body})

    def test_basics(self):
        import os
        path = os.path.join(os.path.dirname(__file__),
                            'data', 'body_small.txt')
        with open(path) as body:
            request = self.make_dummy_request(353, body)
            in_file, size, filename = self.call_fut(request)
            self.assertEqual(filename, 'small.txt')
            self.assertEqual(size, 20)
            self.assertEqual(in_file.read(size), 'This is a test file.')


class TestCheckEnabled(TestCase):

    def call_fut(self, func):
        from poulda.utils import check_enabled
        return check_enabled(func)

    def make_request(self, enabled):
        class DummyLocalizer(object):
            def translate(self, s):
                return s

        class DummyRequest(object):
            class DummyRegistry(object):
                settings = {'poulda.enabled': enabled}
            registry = DummyRegistry()
            localizer = DummyLocalizer()
        return DummyRequest()

    def test_enabled(self):
        def func(request):
            return request
        req = self.make_request('true')
        got = self.call_fut(func)(req)
        self.assertEqual(got, req)

    def test_disabled(self):
        func = lambda: 'should not be called at all'
        req = self.make_request('false')
        got = self.call_fut(func)(req)
        self.assertEqual(got.body, u'This service has been disabled.')


class TestCopyToFile(TestCase):

    def call_fut(self, *args, **kwargs):
        from poulda.utils import copy_to_file
        return copy_to_file(*args, **kwargs)

    def test_basics(self):
        from StringIO import StringIO
        length = 100
        with open(__file__) as in_file:
            out = StringIO()
            self.call_fut(in_file, length, out)
            in_file.seek(0)
            self.assertEqual(in_file.read(length), out.getvalue())
            self.assertEqual(len(out.getvalue()), length)

    def test_wrong_larger_content_length(self):
        # Try to copy more than the size of the file.
        import os
        from StringIO import StringIO
        this_size = os.stat(__file__).st_size
        length_to_copy = 100000000  # more than the size of this file
        with open(__file__) as in_file:
            out = StringIO()
            self.call_fut(in_file, length_to_copy, out)
            in_file.seek(0)
            self.assertEqual(in_file.read(), out.getvalue())
            self.assertEqual(len(out.getvalue()), this_size)


class TestCheckPassword(TestCase):

    def call_fut(self, settings, user, password):
        from poulda.views import check_password
        return check_password(settings, user, password)

    def test_no_accounts(self):
        self.assert_(not self.call_fut({}, 'jsmith', 'secret'))
        self.assert_(not self.call_fut({'poulda.accounts': ''},
                                       'jsmith', 'secret'))

    def test_single_account(self):
        self.assert_(not self.call_fut({'poulda.accounts': 'jdoe:secret'},
                                       'jsmith', 'secret'))
        self.assert_(self.call_fut({'poulda.accounts': 'jsmith:secret'},
                                   'jsmith', 'secret'))

    def test_multi_accounts(self):
        self.assert_(not self.call_fut(
                {'poulda.accounts': 'jdoe:secret jmiller:secret'},
                'jsmith', 'secret'))
        self.assert_(self.call_fut(
                {'poulda.accounts': 'jdoe:secret jsmith:secret'},
                'jsmith', 'secret'))
