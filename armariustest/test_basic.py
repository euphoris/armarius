from tempfile import NamedTemporaryFile

from flask import url_for

from armarius import app
from armarius.models import initdb, Page, Session


HTTP_OK = 200
HTTP_REDIRECT= 302


class TestBase(object):
    def setup_method(self, method):
        app.config['PATH'] = '/Users/jae-myoungyu/Documents/wiki/'
        self.f = NamedTemporaryFile()
        uri = 'sqlite:///' + self.f.name
        app.config['DATABASE'] = uri
        app.config['TESTING'] = True

        self.client = app.test_client()
        self.ctx = app.test_request_context()
        self.ctx.push()

        initdb()

        fixtures = [dict(title='test', content='no content'),
                   dict(title='to rename', content='blah'),
                   dict(title='search target', content='abc123def'),
                   dict(title=u'테스트', content=u'한글')]

        session = Session()
        with session.begin():
            for fixture in fixtures:
                page = Page(**fixture)
                session.merge(page)

    def teardown_method(self, method):
        self.ctx.pop()
        self.f.close()

    def get(self, view_func, **kwargs):
        return self.client.get(url_for(view_func, **kwargs))

    def post(self, view_func, **kwargs):
        names = ['headers', 'data']
        newargs = {}
        for name in names:
            if name in kwargs:
                newargs[name] = kwargs[name]
                del kwargs[name]
            else:
                newargs[name] = {}

        return self.client.post(url_for(view_func, **kwargs), **newargs)

    def redirect(self, res, view_func, **kwargs):
        assert res.status_code == HTTP_REDIRECT
        url = url_for(view_func, **kwargs)
        location = res.headers['Location'][-len(url):]
        assert location == url

    def test_first_page(self):
        res = self.client.get('/')
        self.redirect(res, 'view_page', title='FrontPage')

    def test_view_page(self):
        res = self.get('view_page', title='test')
        assert res.status_code == HTTP_OK

        res = self.get('view_page', title=u'테스트')
        assert res.status_code == HTTP_OK

    def test_edit_page(self):
        res = self.get('edit_page', title='test')
        assert res.status_code == HTTP_OK

        referer = url_for('view_page', title='test')
        res = self.post('save_page',
                        data=dict(title='test',
                                  old_title='test',
                                  content='xxx'),
                        headers={'referer': referer})
        assert res.status_code == HTTP_OK

        page = Page.load('test')
        assert page.content == 'xxx'

    def test_rename_page(self):
        assert not Page.load('renamed')

        referer = url_for('view_page', title='to rename')
        res = self.post('save_page',
                        data=dict(title='renamed',
                                  old_title='to rename',
                                  content='blah'),
                        headers={'referer': referer})
        assert res.status_code == HTTP_OK

        assert not Page.load('to rename')
        assert Page.load('renamed')

    def test_create_page(self):
        res = self.get('create_page', title='test')
        self.redirect(res, 'view_page', title='test')

        res = self.get('create_page', title='new_page')
        assert res.status_code == HTTP_OK

        res = self.post('save_page',
                        data=dict(title='new_page',
                                  old_title='new_page',
                                  content='blah'))
        page = Page.load('new_page')
        assert page
        assert page.title == 'new_page'
        assert page.content == 'blah'

    def test_spaced_title(self):
        self.post('save_page',
                  data=dict(title='hello world',
                            old_title='hello world',
                            content='blah'))
        assert not Page.load('hello world')
        assert Page.load('hello_world')

        res = self.get('view_page', title='hello world')
        self.redirect(res, 'view_page', title='hello_world')

    def test_list_page(self):
        res = self.get('list_page')
        assert res.status_code == HTTP_OK
        assert 'test' in res.data

    def test_search(self):
        res = self.get('search')
        assert res.status_code == HTTP_OK

        res = self.get('search', q='search')
        assert res.status_code == HTTP_OK
        assert 'search target' in res.data

        res = self.get('search', q='123')
        assert res.status_code == HTTP_OK
        assert 'search target' in res.data

        res = self.get('search', q='123 abc')
        assert res.status_code == HTTP_OK
        assert 'search target' in res.data

        res = self.get('search', q='xyz 123')
        assert res.status_code == HTTP_OK
        assert 'search target' not in res.data
