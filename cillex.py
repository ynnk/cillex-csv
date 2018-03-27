#-*- coding:utf-8 -*-

import os
import sys
import requests
import codecs
import random
import json
import datetime
import logging

from flask import Flask, Response, make_response, g, current_app, request
from flask import render_template, render_template_string, abort, redirect, url_for,  jsonify

import istex2csv as istex

# Flask,Login , cors
DEBUG = os.environ.get('APP_DEBUG', "").lower() == "true"
app = Flask(__name__)
app.config['DEBUG'] = DEBUG

from reliure.utils.log import get_app_logger_color
log_level = logging.INFO if app.config['DEBUG'] else logging.WARN
logger = get_app_logger_color("cillex", app_log_level=log_level, log_level=log_level)

from flask_login import LoginManager, current_user, login_user, login_required

login_manager = LoginManager()
login_manager.init_app(app)

from flask_cors import CORS
CORS(app)



from pdgapi.explor import prepare_graph, export_graph, layout_api, clustering_api

from botapi import BotaIgraph
from botapad import Botapad

from pdglib.graphdb_ig import IGraphDB, engines
from cello.graphs import pedigree

graphdb = IGraphDB({})
graphdb.open_database()
print "Graphdb", graphdb 

CALC_URL = "http://calc.padagraph.io/export-cillex-csv-Y"
#ENGINES_HOST = "http://localhost:5004"
#STATIC_HOST = "http://localhost:5000"
ENGINES_HOST = ""
STATIC_HOST = ""

from cillexapi import db_graph

@app.route('/', methods=['GET', 'POST'])
def readme():
    return render_template('home.html' )

@app.route('/graphsearch', methods=['GET'])
@app.route('/graphsearch/<string:gid>', methods=['GET'])
def graphsearch(gid=None):

    if gid is None :
        gid = hex(random.randint(10000,10000000000))[2:]

    query, graph = db_graph(graphdb, { 'graph':gid })
    
    routes = "%s/engines" % ENGINES_HOST
    sync = "%s/graphs/g/%s" % (ENGINES_HOST, gid)
    data = {}
    
    error = None
    
    #args
    args = request.args
     
    color = "#" + args.get("color", "249999" )    
    options = {
        #
        'wait' : 4,
        #template
        'zoom'  : args.get("zoom", 1200 ),
        'buttons': 0, # removes play/vote buttons
        'labels' : 1 if not args.get("no-labels", None ) else 0,  # removes graph name/attributes 
        # gviz
        'el': "#viz",
        'background_color' : color,
        'initial_size' : 16,
        'user_font_size' : 2,
        'user_vtx_size' : 1,
        'vtx_size' : args.get("vertex_size", 2 ),
        'show_text'  : 0 if args.get("no_text"  , None ) else 1,     # removes vertex text 
        'show_nodes' : 0 if args.get("no_nodes" , None ) else 1,   # removes vertex only 
        'show_edges' : 0 if args.get("no_edges" , None ) else 1,   # removes edges 
        'show_images': 0 if args.get("no_images", None ) else 1, # removes vertex images
        
        'auto_rotate': 0,
        'adaptive_zoom': True,
            
    }
    
    return render_template('istex.html',
        static_host=STATIC_HOST, color=color,
        routes=routes, data=data, options=json.dumps(options),
        sync=sync )
     
from pdgapi import graphedit
 
edit_api = graphedit.graphedit_api("graphs", app, graphdb, login_manager, None )
app.register_blueprint(edit_api)

from pdglib.graphdb_ig import engines
from pdgapi.explor import layout_api
from cillexapi import explore_api, clustering_api

api = explore_api(engines, graphdb)
api = layout_api(engines, api)
api = clustering_api(graphdb, engines, api)

app.register_blueprint(api)

from pdgapi import get_engines_routes



@app.route('/engines', methods=['GET'])
def _engines():
    host = ENGINES_HOST
    return jsonify({'routes': get_engines_routes(app, host)})

from flask_runner import Runner
def main():
    ## run the app
    print "running main"

    #build_app()

    runner = Runner(app)
    runner.run()

if __name__ == '__main__':
    sys.exit(main())



