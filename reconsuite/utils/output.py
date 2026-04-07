import json
from jinja2 import Template

HTML_TEMPLATE = """
<html><head><meta charset="utf-8"><title>ReconSuite Report - {{target}}</title></head><body>
<h1>ReconSuite Report - {{target}}</h1>
<pre>{{report|tojson(indent=2)}}</pre>
</body></html>
"""

def save_json(report, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

def save_html(report, filename):
    t = Template(HTML_TEMPLATE)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(t.render(target=report.get("target"), report=report))
