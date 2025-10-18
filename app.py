from flask import Flask, request, Response
from lxml import etree
import requests
from saxonche import PySaxonProcessor

app = Flask(__name__)

"""@app.route("/cadena_original", methods=["POST"])
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
        return Response("Error: " + str(e), status=500, mimetype="text/plain")"""

@app.route("/cadena_original", methods=["POST"])
def cadena_original():
    try:
        xml_data = request.data
        xslt_url = "https://www.sat.gob.mx/sitio_internet/cfd/4/cadenaoriginal_4_0/cadenaoriginal_4_0.xslt"

        with PySaxonProcessor(license=False) as proc:
            xslt_response = requests.get(xslt_url)
            xslt_content = xslt_response.content.decode('utf-8')  # ← DECODIFICAR bytes a string
            # Carga el XSLT desde la URL
            xslt_proc = proc.new_xslt30_processor()
            xslt_executable = xslt_proc.compile_stylesheet(stylesheet_text=requests.get(xslt_url).content)

            # Carga el XML desde los datos de la solicitud
            xml_content = xml_data.decode('utf-8')  # ← Asegurar que sea string
            #xml_doc = proc.parse_xml(xml_text=xml_data.decode('utf-8'))
            #xml_doc = proc.parse_xml(xml_text=xml_data.decode('utf-8'))
            xml_doc = proc.parse_xml(xml_text=xml_content)

            # Realiza la transformación
            cadena = xslt_executable.transform_to_string(xdm_node=xml_doc)

            return Response(cadena.strip(), mimetype="text/plain")#sin .strip()

    except Exception as e:
        return Response("Error: " + str(e), status=500, mimetype="text/plain")

@app.route("/")
def root():
    return "Servicio XSLT SAT activo ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)