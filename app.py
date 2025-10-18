from flask import Flask, request, Response
import requests
from saxonche import PySaxonProcessor
import sys

app = Flask(__name__)

# Cache del XSLT
xslt_cache = None

def log(message):
    print(f"[LOG] {message}", file=sys.stderr, flush=True)

def get_xslt():
    global xslt_cache
    try:
        if xslt_cache is None:
            log("📥 Descargando XSLT desde SAT...")
            xslt_url = "https://www.sat.gob.mx/sitio_internet/cfd/4/cadenaoriginal_4_0/cadenaoriginal_4_0.xslt"
            response = requests.get(xslt_url, timeout=30)
            response.raise_for_status()
            xslt_cache = response.content.decode('utf-8')  # ← Convertir bytes a string
            log(f"✅ XSLT cargado - Tamaño: {len(xslt_cache)} caracteres")
        return xslt_cache
    except Exception as e:
        log(f"❌ Error cargando XSLT: {str(e)}")
        raise

@app.route("/cadena_original", methods=["POST"])
def cadena_original():
    try:
        log("🟡 Iniciando procesamiento...")
        
        # Asegurar que xml_data sea string
        xml_data = request.data
        if isinstance(xml_data, bytes):
            xml_content = xml_data.decode('utf-8')
        else:
            xml_content = xml_data
            
        log(f"📦 XML recibido: {len(xml_content)} caracteres")
        
        # Obtener XSLT
        xslt_content = get_xslt()
        
        # Procesar con Saxon
        with PySaxonProcessor(license=False) as proc:
            log("🔧 Compilando XSLT...")
            xslt_proc = proc.new_xslt30_processor()
            xslt_executable = xslt_proc.compile_stylesheet(stylesheet_text=xslt_content)
            
            log("🔧 Cargando XML...")
            xml_doc = proc.parse_xml(xml_text=xml_content)
            
            log("🔄 Aplicando transformación...")
            cadena = xslt_executable.transform_to_string(xdm_node=xml_doc)
            
            log(f"✅ Cadena generada: {len(cadena)} caracteres")
            return Response(cadena.strip(), mimetype="text/plain")

    except Exception as e:
        log(f"❌ ERROR COMPLETO: {str(e)}")
        return Response(f"Error: {str(e)}", status=500, mimetype="text/plain")

@app.route("/health", methods=["GET"])
def health():
    log("🏥 Health check")
    return "✅ Servicio Saxon activo"

@app.route("/")
def root():
    return "Servicio XSLT SAT con Saxon activo ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    log(f"🚀 Iniciando servidor en puerto {port}")
    app.run(host="0.0.0.0", port=port)