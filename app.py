from flask import Flask, request, Response
from lxml import etree
import requests
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

XSLT_URL = "https://www.sat.gob.mx/sitio_internet/cfd/4/cadenaoriginal_4_0/cadenaoriginal_4_0.xslt"

# Cache del XSLT en MEMORIA (no en archivo)
xslt_cache = None

def get_xslt():
    global xslt_cache
    try:
        if xslt_cache is None:
            logger.info("📥 Descargando XSLT desde SAT...")
            response = requests.get(XSLT_URL, timeout=30)
            response.raise_for_status()
            
            logger.info("🔧 Parseando XSLT...")
            xslt_cache = etree.fromstring(response.content)
            logger.info("✅ XSLT cargado en memoria")
        
        return xslt_cache
        
    except Exception as e:
        logger.error(f"❌ Error cargando XSLT: {str(e)}")
        raise

@app.route("/cadena_original", methods=["POST"])
def cadena_original():
    try:
        logger.info("📥 Recibiendo petición...")
        
        # Parsear XML
        xml_doc = etree.fromstring(request.data)
        logger.info("✅ XML parseado")
        
        # Obtener XSLT
        xslt_doc = get_xslt()
        
        # Crear transformador y aplicar
        transform = etree.XSLT(xslt_doc)
        cadena = str(transform(xml_doc))
        
        logger.info(f"✅ Cadena generada: {len(cadena)} caracteres")
        return Response(cadena.strip(), mimetype="text/plain")

    except etree.XMLSyntaxError as e:
        logger.error(f"❌ Error de sintaxis XML: {str(e)}")
        return Response(f"Error XML: {str(e)}", status=400, mimetype="text/plain")

    except Exception as e:
        logger.error(f"❌ Error general: {str(e)}")
        return Response(f"Error: {str(e)}", status=500, mimetype="text/plain")

@app.route("/health", methods=["GET"])
def health():
    return "✅ Servicio activo"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Iniciando servidor en puerto {port}")
    app.run(host="0.0.0.0", port=port)