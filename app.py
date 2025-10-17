from flask import Flask, request, Response
from lxml import etree
import requests
import os

app = Flask(__name__)

XSLT_URL = "https://www.sat.gob.mx/sitio_internet/cfd/4/cadenaoriginal_4_0/cadenaoriginal_4_0.xslt"
LOCAL_XSLT = "/tmp/cadenaoriginal_4_0.xslt"

def get_xslt():
    # Guarda una copia local en /tmp (permite más velocidad y evita fallas de red)
    if not os.path.exists(LOCAL_XSLT):
        xslt_data = requests.get(XSLT_URL).content
        with open(LOCAL_XSLT, "wb") as f:
            f.write(xslt_data)
    return etree.parse(LOCAL_XSLT)

@app.route("/cadena_original", methods=["POST"])
def cadena_original():
    try:
        xml_data = request.data
        xml_doc = etree.fromstring(xml_data)

        xslt_doc = get_xslt()
        transform = etree.XSLT(xslt_doc)
        cadena = str(transform(xml_doc))

        return Response("Error en el sat!" + cadena, mimetype="text/plain")
    except etree.XMLSyntaxError as e:
        logger.error(f"❌ Error de sintaxis XML: {str(e)}")
        return Response(f"Error: XML mal formado - {str(e)}", status=400, mimetype="text/plain")

    except Exception as e:
        return Response("Error: " + str(e), status=500, mimetype="text/plain")

@app.route("/")
def home():
    return "Servicio XSLT SAT activo ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)