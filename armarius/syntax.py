import re

moin_link = re.compile(r'\[\[(https?://[^\]]+)\]\]')
moin_wiki_link = re.compile(r'\[\[([^\]]+)\]\]')
moin_em = re.compile(r'``([^`]+)``')
moin_strong = re.compile(r'```([^`]+)```')
moin_paragraph = re.compile(r'\n\n+')
moin_h2 = re.compile(r'\n*==([^=\n]+)==\n')
moin_h3 = re.compile(r'\n*===([^=\n]+)===\n')
moin_h4 = re.compile(r'\n*====([^=\n]+)====\n')
moin_li = re.compile(r' \* ([^\n]+)\n')
moin_code_begin = re.compile(r'\n+{{{\n')
moin_code_end = re.compile(r'}}}')

def moinmoin(content):
    content = moin_code_begin.sub(r'<pre><code>', content)
    content = moin_code_end.sub(r'</code></pre>', content)
    content = moin_li.sub(r'<li>\1</li>', content)
    content = moin_link.sub(r'<a href="\1">link</a>', content)
    content = moin_wiki_link.sub(r'<a href="/page/\1">\1</a>', content)
    content = moin_strong.sub(r'<strong>\1</strong>', content)
    content = moin_em.sub(r'<em>\1</em>', content)
    content = moin_h2.sub(r'<h2>\1</h2>\n', content)
    content = moin_h3.sub(r'<h3>\1</h3>\n', content)
    content = moin_h4.sub(r'<h4>\1</h4>\n', content)
    content = moin_paragraph.sub('<p>', content)
    return content

