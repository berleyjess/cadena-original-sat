from flask import Flask, request, Response
from lxml import etree
import requests
import os
import requests
import locale
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
print("🔄 Configurando locale...")
try:
    locale.setlocale(locale.LC_ALL, 'es_MX.UTF-8')
    print("🎉 Locale configurado exitosamente: es_MX.UTF-8")
except locale.Error as e:
    print(f"⚠️  No se pudo configurar es_MX.UTF-8: {e}")
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        print("🎉 Locale configurado: C.UTF-8")
    except locale.Error as e:
        print(f"⚠️  No se pudo configurar C.UTF-8: {e}")
        # Forzar variables de entorno como último recurso
        os.environ['LANG'] = 'C.UTF-8'
        os.environ['LC_ALL'] = 'C.UTF-8'
        os.environ['PYTHONIOENCODING'] = 'utf-8'

@app.route("/cadena_original", methods=["POST"])
def cadena_original_local():
    try:
        xml_data_bytes = request.data
        xml_data_string = xml_data_bytes.decode('utf-8')
        
        # Usar XSLT local
        xslt_path = descargar_xslt_local()
        
        with PySaxonProcessor(license=False) as proc:
            xslt_proc = proc.new_xslt30_processor()
            
            # Cargar desde archivo local
            with open(xslt_path, 'r', encoding='utf-8') as f:
                xslt_content = f.read()
            
            xslt_executable = xslt_proc.compile_stylesheet(stylesheet_text=xslt_content)
            xml_doc = proc.parse_xml(xml_text=xml_data_string)
            cadena = xslt_executable.transform_to_string(xdm_node=xml_doc)

            return Response(cadena.strip(), mimetype="text/plain")

    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

# Descargar el XSLT una vez al iniciar la aplicación
def descargar_xslt_local():
    xslt_url = "https://www.sat.gob.mx/sitio_internet/cfd/4/cadenaoriginal_4_0/cadenaoriginal_4_0.xslt"
    local_path = "cadenaoriginal_4_0.xslt"
    
    if not os.path.exists(local_path):
        response = requests.get(xslt_url)
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
    
    return local_path
    
@app.route("/")
def root():
    return "Servicio XSLT SAT activo ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
