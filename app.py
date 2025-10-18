from flask import Flask, request, Response
from lxml import etree
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from OpenSSL import crypto
import base64
import requests
import os
import locale
from saxonche import PySaxonProcessor

app = Flask(__name__)

@app.route("/cadena_original", methods=["POST"])
def cadena_original_local():
    try:
        xml_data_bytes = request.data
        xml_data_string = xml_data_bytes.decode('utf-8')
        
        # Usar XSLT local
        xslt_path = descargar_xslt_local()
        with PySaxonProcessor(license=False) as proc:
            xslt_proc = proc.new_xslt30_processor()
            
            # 💥 CAMBIO: Leer como bytes y decodificar el string XSLT explícitamente
            with open(xslt_path, 'rb') as f: # Abrir en modo de lectura de bytes ('rb')
                xslt_bytes = f.read()
            
            # Decodificar el contenido asegurando que sea UTF-8
            xslt_content = xslt_bytes.decode('utf-8')

            xslt_content_clean = xslt_content.replace('Ã±', 'ñ')
            
            xslt_executable = xslt_proc.compile_stylesheet(stylesheet_text=xslt_content_clean)
            
            # ... (el resto del código sigue igual)
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
# =======================================================================
# 💥 ENDPOINT 2: SELLADO DE LA CADENA ORIGINAL (NUEVO)
# =======================================================================

def sellar_cadena_sha256(cadena_original: str, key_path: str, password: str) -> str:
    """
    Firma criptográficamente la cadena original con la llave privada y devuelve
    el sello codificado en Base64.
    """
    
    # 1. Leer y desencriptar la llave privada (.key)
    # El archivo .key del SAT está en formato DER, y se convierte a PEM
    
    # Leer el archivo .key en formato DER (binario)
    with open(key_path, "rb") as key_file:
        key_der = key_file.read()
    
    # Convertir de DER a PEM (requiere pyOpenSSL)
    key_pem_bytes = crypto.dump_privatekey(crypto.FILETYPE_PEM, 
                                           crypto.load_privatekey(crypto.FILETYPE_ASN1, key_der, password.encode('utf-8')))

    # Cargar la llave privada PEM desencriptada (requiere cryptography)
    private_key = load_pem_private_key(
        key_pem_bytes,
        password=None, # La llave ya está desencriptada en PEM
        backend=None
    )

    # 2. Generar el Hash y Firmar (SHA-256 + RSA)
    signer = private_key.signer(
        padding.PKCS1v15(), # El padding requerido por el SAT
        hashes.SHA256()      # El algoritmo de hash requerido
    )
    
    # La cadena original debe ser firmada en bytes
    signer.update(cadena_original.encode('utf-8'))
    signature = signer.finalize()
    
    # 3. Codificar la firma a Base64
    sello_base64 = base64.b64encode(signature).decode('utf-8')
    
    return sello_base64


@app.route("/sellar_cfdi", methods=["POST"])
def sellar_cfdi():
    """Recibe la cadena original y devuelve el sello digital."""
    try:
        data = request.get_json()
        cadena_original = data.get("cadena_original")

        if not cadena_original:
            return jsonify({"error": "Falta 'cadena_original' en el cuerpo JSON."}), 400
        
        if not all([KEY_PATH, PASSWD]):
             return jsonify({"error": "Faltan rutas o contraseña de la llave de sellado."}), 500

        sello = sellar_cadena_sha256(cadena_original, KEY_PATH, PASSWD)
        
        return jsonify({"sello": sello})

    except Exception as e:
        # Añade logging en Render para depuración
        print(f"Error en /sellar_cfdi: {str(e)}")
        return jsonify({"error": f"Error al generar el sello: {str(e)}"}), 500
        
@app.route("/")
def root():
    return "Servicio XSLT SAT activo ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
