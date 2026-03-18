"""
DevTracker entry point — launches the web-based GUI.
"""
from .web import create_app

app = create_app()
app.run(host="0.0.0.0", port=9876, debug=False)
