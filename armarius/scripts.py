import sys
import os
import os.path

from . import app, initdb

def run_server():
    try:
        config = os.path.abspath(sys.argv[1])
        app.config.from_pyfile(config)
    except:
        cwd = os.getcwd()
        app.config['DATABASE'] = 'sqlite:////' + os.path.join(cwd, 'wiki.db')

    with app.app_context():
        initdb()

    port = app.config.get('PORT', 5000)

    app.run(host='0.0.0.0', port=port)
