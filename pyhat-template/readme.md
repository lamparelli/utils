# Abstract

It's a template for the PyHAT stack (Python HTMX ASGI Tailwind).
Info here: https://github.com/PyHAT-stack/awesome-python-htmx

HTML pages are served with a python ASGI server (fastapi + uvicorn).
The need for javascript is reduced by using HTMX.
An example can be seen in index.html:
- the form uses an HTMX submit action ("hx-post") that points to the python /add endpoint (instead of pointing to a JS function)
- thanks to jinja, the python endpoint can return a part of html (like a matrioska) to be embedded in the parent html
- the form defines were to place the result of the python endpoint ("hx-target" defines where to place the result; "hx-swap" defines HOW to place it, for example at the start/end of the element, or replace the current content) 

# Setup & Run

Install: `pip install -r requirements.txt`
Run: `uvicorn main:app`