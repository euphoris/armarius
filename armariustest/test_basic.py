#! encoding: utf8
from tempfile import NamedTemporaryFile

from bs4 import BeautifulSoup
from flask import url_for

from armarius import app, decode_quoted
from armarius.models import initdb, Page, Link, Session


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

        fixtures = [(Page, dict(title='test', content='no content')),
                    (Page, dict(title='to rename', content='blah')),
                    (Page, dict(title='to delete', content='blah')),
                    (Page, dict(title='search target', content='abc123def')),
                    (Page, dict(title=u'테스트', content=u'한글')),
                    (Page, dict(title='orphan', content='blah')),
                    # link test
                    (Page, dict(title='link_source', content='blah')),
                    (Link, dict(source='link_source', target='link_target1')),
                    (Link, dict(source='link_source', target='link_target2'))]

        session = Session()
        with session.begin():
            for table, fixture in fixtures:
                t = table(**fixture)
                session.merge(t)

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

    def test_parse_error(self):
        res = self.post('save_page',
                        data=dict(title='test',
                                  old_title='test',
                                  content='<a>xxx'))
        assert res.status_code == HTTP_REDIRECT


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

    def test_link(self):
        session = Session()

        def link(target):
            return session.query(Link).filter_by(source='link_source',
                                                 target=target).first()

        assert link('link_target1')
        assert link('link_target2')     # to be removed
        assert not link('link_target3') # to be appended

        content = """
        <a href="/page/link_target1">link_target1</a>
        <a href="/page/link_target3">link_target3</a>
        """
        self.post('save_page',
                  data=dict(title='link_source',
                            old_title='link_source',
                            content=content))

        assert link('link_target1')
        assert not link('link_target2')
        assert link('link_target3')

    def test_spaced_link(self):
        session = Session()

        self.post('save_page',
                  data=dict(title='spaced_link',
                            old_title='spaced_link',
                            content="""
        <a href="/page/link target1">link_target1</a>
        <a href="/page/link%20target3">link_target3</a>"""))

        def link(target):
            return session.query(Link).filter_by(source='spaced_link',
                                                 target=target).first()

        assert link('link_target1')
        assert not link('link_target2')
        assert link('link_target3')

    def test_toc(self):
        self.post('save_page',
                  data=dict(title='toc_test',
                            old_title='toc_test',
                            content="""
                                <h1>heading 1</h1>
                                <h2>heading 1.1</h2>
                                <h1>heading 2</h1>
                            """))

        res = self.get('view_page', title='toc_test')
        soup = BeautifulSoup(res.data)
        toc = soup.find(id="toc")
        assert toc

        first_h1 = toc.ul.li.a
        assert first_h1.string == 'heading 1'
        assert first_h1['data-level'] == '1'
        assert first_h1['data-pos'] == '0'

        first_h2 = toc.ul.ul.li.a
        assert first_h2.string == 'heading 1.1'
        assert first_h2['data-level'] == '2'
        assert first_h2['data-pos'] == '0'

    def test_decode_quoted(self):
        assert decode_quoted(u'%ED%85%8C%EC%8A%A4%ED%8A%B8') == u'테스트'
        assert decode_quoted(u'테스트') == u'테스트'

    def test_backlink(self):
        res = self.get('backlink', title='link_target1')
        assert res.status_code == HTTP_OK

    def test_orphan(self):
        res = self.get('orphan')
        assert res.status_code == HTTP_OK
        assert 'link_target1' not in res.data
        assert 'orphan' in res.data

    def test_list_page(self):
        res = self.get('list_page')
        assert res.status_code == HTTP_OK
        assert 'test' in res.data

    def test_recent_changes(self):
        res = self.get('recent_changes')
        assert res.status_code == HTTP_OK

    def test_delete_page(self):
        res = self.get('delete_page', title='to delete')
        assert res.status_code == HTTP_OK

        session = Session()
        before = session.query(Page).count()
        res = self.post('delete_page', title='to delete')
        self.redirect(res, 'home')
        after = session.query(Page).count()
        assert not Page.load('to delete')
        assert before-1 == after

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
