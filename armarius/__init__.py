# encoding: utf-8
import functools
import os
import re
import xml.etree.ElementTree as etree
#! encoding: utf-8

from flask import Flask, request, render_template, redirect, url_for
from sqlalchemy.sql import func

from .models import initdb, Page, Link, Session


app = Flask(__name__)
app.debug = True
app.secret_key = os.urandom(24)


def pjax_render(template, **kwargs):
    if 'special' not in kwargs:
        kwargs['special'] = False
    if request.headers.get('X-PJAX',False):
        template = 'pjax/' + template
    return render_template(template, **kwargs)


def load_page(view):
    @functools.wraps(view)
    def wrapper(title):
        if ' ' in title:
            return redirect(url_for(view.__name__,
                                    title=re.sub(r'\s+', r'_', title)))

        page = Page.load(title)

        if page:
            return view(page)
        else:
            return redirect(url_for('create_page', title=title))
    return wrapper


@app.route('/page/<title>')
@load_page
def view_page(page):
    return pjax_render('view_page.html', page=page)


@app.route('/edit/<title>')
@load_page
def edit_page(page):
    return pjax_render('edit_page.html', page=page)


@app.route('/create/<title>')
def create_page(title):
    if Page.load(title):
        return redirect(url_for('view_page', title=title))
    return render_template('edit_page.html',
                           page=dict(title=title, pretty_title=title))


clear_cr = re.compile(r'\r+')
clear_nbsp = re.compile(r'\&nbsp;')
@app.route('/edit', methods=['POST'])
def save_page():
    old_title = request.form['old_title']
    title = request.form['title']
    title = re.sub(r'\s+', r'_', title)

    content = request.form['content']
    content = clear_cr.sub('', content)
    content = clear_nbsp.sub(' ', content)

    session = Session()
    with session.begin():
        page = Page.load(old_title, session)
        if page:
            page.title = title
            page.content = content
        else:
            page = Page(title=title, content=content)
        session.merge(page)

    # link
    targets = set()
    url = url_for('view_page', title='')
    xml = u'<page>{}</page>'.format(content)

    root = etree.fromstring(xml.encode('utf-8'))
    for a in root.iter('a'):
        href = a.attrib.get('href','')
        if href.startswith(url):
            targets.add(unicode(href[len(url):]))

    with session.begin():
        links = session.query(Link).filter_by(source=title)
        old_targets = set([link.target for link in links])

        removed = old_targets - targets
        for target in removed:
            link = session.query(Link).filter_by(target=target).first()
            session.delete(link)

        appended = targets - old_targets
        for target in appended:
            link = Link(source=title, target=target)
            session.merge(link)

    # redirect
    referer = request.headers.get('referer', '')
    if url_for('view_page', title=old_title) in referer:
        return 'OK'
    else:
        return redirect(url_for('view_page', title=title))


def special_list(query):
    @functools.wraps(query)
    def view(title=None):
        content = u''
        page_title, pages = query(title)
        for page in pages:
            content += u'<li><a href="{}">{}</a>'.format(
                url_for('view_page', title=page.title), page.pretty_title)

        return pjax_render('view_page.html',
                           page=dict(pretty_title=page_title,
                                     content=content),
                           special=True)
    return view


@app.route('/page_list')
@special_list
def list_page(title):
    session = Session()
    pages = session.query(Page).all()
    return 'Page list', pages


@app.route('/backlink/<title>')
@special_list
def backlink(title):
    session = Session()
    links = session.query(Page, Link).\
            filter(Link.target==title).\
            filter(Page.title==Link.source).\
            all()
    links = [link.Page for link in links]
    return 'Backlink: ' + title, links


@app.route('/orphan')
@special_list
def orphan(title):
    session = Session()
    stmt = session.query(Link.target, func.count('*').\
            label('link_count')).\
            group_by(Link.target).subquery()
    results = session.query(Page, stmt.c.link_count).\
            outerjoin(stmt, Page.title==stmt.c.target).\
            filter(stmt.c.link_count==None)
    pages = [page for page, _ in results]
    return 'Orphan', pages


@app.route('/delete/<title>', methods=['GET', 'POST'])
def delete_page(title):
    if request.method == 'GET':
        return render_template('delete_page.html', title=title)
    else:
        session = Session()
        with session.begin():
            page = Page.load(title, session)
            session.delete(page)
        return redirect(url_for('home'))


@app.route('/search')
def search():
    query = request.args.get('q','')
    titles = contents = []

    if query:
        titles, contents = Page.search(query)

    return render_template('search.html',
                           query=query, titles=titles, contents=contents)


@app.route('/')
def home():
    return redirect('/page/FrontPage')
