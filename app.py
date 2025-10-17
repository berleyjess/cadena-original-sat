from flask import Flask, request, Response
from lxml import etree
import requests
import sys
import os

app = Flask(__name__)

XSLT_URL = "https://www.sat.gob.mx/sitio_internet/cfd/4/cadenaoriginal_4_0/cadenaoriginal_4_0.xslt"
xslt_cache = None

def log(message):
    print(f"[LOG] {message}", file=sys.stderr, flush=True)

def get_xslt():
    global xslt_cache
    try:
        if xslt_cache is None:
            log("Descargando XSLT...")
            response = requests.get(XSLT_URL, timeout=30)
            response.raise_for_status()
            xslt_cache = etree.fromstring(response.content)
            log("XSLT cargado en memoria")
        return xslt_cache
    except Exception as e:
        log(f"ERROR XSLT: {str(e)}")
        raise

@app.route("/cadena_original", methods=["POST"])
def cadena_original():
    try:
        log("Procesando XML...")
        xml_doc = etree.fromstring(request.data)
        xslt_doc = get_xslt()
        transform = etree.XSLT(xslt_doc)
        cadena = str(transform(xml_doc))
        log("Cadena generada exitosamente")
        return Response(cadena.strip(), mimetype="text/plain")
    except Exception as e:
        log(f"ERROR: {str(e)}")
        return Response(f"Error: {str(e)}", status=500, mimetype="text/plain")

@app.route("/health")
def health():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)