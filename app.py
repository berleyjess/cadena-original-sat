from flask import Flask, request, Response
from lxml import etree
import requests

app = Flask(__name__)

@app.route("/cadena_original", methods=["POST"])
def cadena_original():
    try:
        xml_data = request.data
        # XSLT oficial del SAT CFDI 4.0
        xslt_url = "https://www.sat.gob.mx/sitio_internet/cfd/4/cadenaoriginal_4_0/cadenaoriginal_4_0.xslt"
        xslt_doc = etree.parse(requests.get(xslt_url).content)
        transform = etree.XSLT(xslt_doc)

        xml_doc = etree.fromstring(xml_data)
        cadena = str(transform(xml_doc))

        return Response(cadena, mimetype="text/plain")

    except Exception as e:
        return Response("Error: " + str(e), status=500, mimetype="text/plain")

@app.route("/")
def root():
    return "Servicio XSLT SAT activo ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)