# encoding: utf-8
import functools
import os
import re
#! encoding: utf-8

from flask import Flask, request, render_template, redirect, url_for

from .models import initdb, Page, Session


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
    return pjax_render('view_page.html',
                       title=page.pretty_title, content=page.content)


@app.route('/edit/<title>')
@load_page
def edit_page(page):
    return pjax_render('edit_page.html',
                       title=page.pretty_title, content=page.content)


@app.route('/create/<title>')
def create_page(title):
    if Page.load(title):
        return redirect(url_for('view_page', title=title))
    return render_template('edit_page.html', title=title)


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

    referer = request.headers.get('referer', '')
    if url_for('view_page', title=old_title) in referer:
        return 'OK'
    else:
        return redirect(url_for('view_page', title=title))


@app.route('/page/special:page_list')
def list_page():
    content = u''
    session = Session()
    pages = session.query(Page).all()
    for page in pages:
        content += u'<li><a href="{}">{}</a>'.format(
            url_for('view_page', title=page.title), page.pretty_title)

    return pjax_render('view_page.html',
                       title='Page list', content=content, special=True)


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
