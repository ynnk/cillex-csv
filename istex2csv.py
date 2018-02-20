#-*- coding:utf-8 -*-

import unicodecsv as csv
import json
import requests
import urllib
import collections
from StringIO import StringIO

from botapi import BotaIgraph
from botapad import Botapad

# parse response attributes
_key = lambda e,k : e.get(k)
_label = lambda e,k : e.get('title')
_abstract = lambda e,k : e.get('abstract')
_keywords = lambda e, k : ";".join(e['keywords']['teeft']) if 'keywords' in e else ""

def _list(e, k) :
    return  ";".join(e.get(k, []))

def _author_names( e, k ):
    s =  ";".join( [ v['name'] for v in  e['author'] ])
    return clean(s)
    
def _author_affs(e, k):
    s = ";".join( [ k for k in flatten([ v['affiliations'] for v in  e['author'] ]) if k is not None ] )
    return clean(s)
    
def _refBibAuteurs(article, k) :
    
    auteurs = []
    for e in article.get('refBibs', [] ):
        for a in e.get('author', [] ):
            auteurs.append( a['name'] )

    s =  ";".join( auteurs )
    return clean(s)

def _categories(article, k) :
    
    l = set()
    for e in article.get('categories', [] ):
        for a in article['categories'][e]:
            l.add( a[3:].strip().lower() )

    return clean( ";".join( l ) )
    
def clean(s):
    s = s.replace(',', '')
    return s
    
def flatten(l):

    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el


# csv cols
SCHEMA = [ 
        "@refBibAuteurs: #label, shape[triangle-top]".split(','),
        "@auteurs: #label, shape[triangle-bottom]".split(','),
        "@keywords: #label, shape[diamond]".split(','), 
        "@categories: #label, shape[diamond]".split(','),
        ]

        
COLS = [
    ('genre', _list , "@article: genre"),
    ('title', _key  ,  "title"),
    ('corpusName', _key ,  "corpusName" ),
    ('label', _label  ,  "label"),
    ('author_names', _author_names ,  "%+ auteurs"),
    ('abstract', _abstract ,  "abstract"),
    ('score', _key ,  "score"),
    ('keywords', _keywords ,  "%+ keywords"),
    ('originalGenre', _list  ,  "originalGenre"),
    ('pmid', _key  ,  "pmid"),
    ('refBibAuteurs', _refBibAuteurs, "%+ refBibAuteurs"),
    ('id', _key, "#id"),
    ('shape', lambda e,k: "square"  ,  "shape"),
    ('categories', _categories  ,  "%+categories"),
 ]

"""
    ('author_affiliations', _author_affs ,  "%+author_affiliations"),
    ('publicationDate', ),
    ('ark', ),
    ('namedEntities', ),
    ('annexes', ),
    ('metadata', ),
    ('fulltext', ),
    ('serie', ),
    ('host', ),
    ('enrichments', ),
    ('categories', ),
    ('qualityIndicators', ),
    ('doi', ),
    ('language', ),
    ('copyrightDate', ),
    ('arkIstex', ),
    ('refBibs', ),
"""

def get_schema():
    cols = [ e[2] for e in COLS  ]
    return SCHEMA + [cols]

def to_istex_url(q, field, size=10):
    q = q.encode("utf8")
    if field == "auteurs":
        qurl = "(%s)" % urllib.quote_plus("author.name:\"%s\"" % q )
    elif field == "refBibAuteurs":
        qurl = "(%s)" % urllib.quote_plus("refBibs.author.name:\"%s\"" % q )
    else:
        qurl = urllib.quote_plus( "%s" % q )

    
    url = "https://api.istex.fr/document/?q=%s&facet=corpusName[*]&size=%s&rankBy=qualityOverRelevance&output=*&stats" % ( qurl, size )

    if field == "istex":
        url = q

    return url


def request_api(url):
    if url :
        print "requesting %s" % url
        data = requests.get(url).json()
        headers = [ "%s" % (e[2]) for e in COLS ]
        rows = [ [  e[1](hit, e[0]) for e in COLS ] for hit in data['hits'] ]
        return headers, rows
    else :
        return [], []


def request_api_to_graph(gid, url):
    headers, rows = request_api(url)
    bot = BotaIgraph(directed=True)
    botapad = Botapad(bot , gid, "", delete=False, verbose=True, debug=False)
    botapad.parse_csvrows( [headers] + rows, separator='auto', debug=False)
    graph = bot.get_igraph(weight_prop="weight")
    
    return graph



def to_csv(headers, rows):
    out = StringIO()
    writer = csv.writer(out, quoting=csv.QUOTE_ALL)
    writer.writerows( headers )

    for row in rows :
        writer.writerow(row )

    return out.getvalue()


def graph_to_calc(graph):
    
    comments = [
            [ "! %s  V:%s E:%s" % ( graph['properties']['name'], graph.vcount(), graph.ecount())  ],
            [ ], ] + [  ["! %s" % json.dumps(graph['queries'])  ] ]
            
    nodetypes = [ e['name'] for e in graph['nodetypes']]

    headers = []        
    for k in nodetypes:
        if k != "article":
            headers.append(["@%s: #label" % k])

    headers = comments + headers + [[],[]]

    keys = []
    for i,col in enumerate(COLS):
        col = col[0]
        key = ""
        if i == 0 :
            key = "@article:"
        if col == "author_names" : col = "auteurs"
        isindex = col == "id"
        isproj = col in nodetypes
        key = "%s%s%s%s" % (key, "#" if isindex else "", "%+" if isproj else "", col)
        keys.append(key)

    headers = headers + [keys] 
    rows = []
    nodetypes_idx = { e['uuid']:e for e in graph['nodetypes'] }

    articles = [ v for v in graph.vs if nodetypes_idx[v['nodetype']]['name'] == "article" ]

    for v in articles:
        row = []
        for col in COLS:
            col = col[0]
            if col == "author_names" : col = "auteurs"
            isindex = col == "id"
            isproj = col in nodetypes
            
            #print col, isindex, isproj, nodetypes_idx[v['nodetype']]['name'], v["properties"]['label']

            if not isproj:
                row.append(v['properties'][col])
            else:
                cell = []
                for e in v.neighbors():
                    n = nodetypes_idx[e['nodetype']]['name']
                    if n == col :
                        cell.append(e['properties']['label'])
                row.append(';'.join(cell))
        rows.append(row)
    return headers, rows

    
def pad_to_graph(gid, url):
    bot = BotaIgraph(directed=True)
    botapad = Botapad(bot , gid, "", delete=False, verbose=True, debug=False)
    #botapad.parse(url, separator='auto', debug=app.config['DEBUG'])
    botapad.parse(url, separator='auto', debug=False)
    graph = bot.get_igraph(weight_prop="weight")
    graph['starred'] = []
    graph['queries'] = []
    
    return graph
    
    

