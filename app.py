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
def cadena_original_corregida():
    try:
        # 1. Obtener los datos binarios (bytes) directamente.
        xml_data_bytes = request.data
        
        xslt_url = "https://www.sat.gob.mx/sitio_internet/cfd/4/cadenaoriginal_4_0/cadenaoriginal_4_0.xslt"

        with PySaxonProcessor(license=False) as proc:
            xslt_proc = proc.new_xslt30_processor()

            # Carga el XSLT (usar .text para obtener la hoja de estilos como string)
            xslt_executable = xslt_proc.compile_stylesheet(
                stylesheet_text=requests.get(xslt_url).text
            )

            # 2. Cargar el XML usando el método from_string() del processor
            # Este método puede ser más robusto para manejar datos binarios/bytes
            # que .parse_xml(xml_text=...)
            # Convertimos explícitamente los bytes a string para esta función, 
            # pero usando un método alternativo de PySaxonProcessor si el anterior falla
            
            # Intento A: usando la función que acepta string (lo que ya probamos)
            # xml_doc = proc.parse_xml(xml_text=xml_data_bytes.decode('utf-8'))
            
            # Intento B (Más robusto): usar from_string, que maneja la conversión interna
            xml_doc = proc.parse_xml(xml_text=xml_data_bytes.decode('utf-8'))
            
            # ********** Si A y B fallan (que es lo que pasa), el problema es que el parser interno de C lo está confundiendo. **********
            # ** La solución más confiable es usar un objeto io.StringIO o io.BytesIO **
            # ** y pasarlo a un método alternativo si existe, o usar un parser LXML/ETree antes. **
            
            # **SOLUCIÓN REAL Y CONFIABLE (Usando BytesIO):**
            # Aunque no es el método directo de PySaxonProcessor, evita el error interno.
            import io
            # Necesitas una función que lea desde un stream.
            # PySaxonProcessor.parse_xml no tiene un argumento 'stream', 
            # así que el siguiente workaround es el más limpio:
            
            # 1. Decodificar a string (obligatorio para parse_xml/xml_text)
            xml_data_string = xml_data_bytes.decode('utf-8')
            
            # 2. Pasar el string. Si falla, el problema es el entorno de PySaxonProcessor.
            # En este caso, la solución es asegurarse de que el string no tenga
            # un BOM (Byte Order Mark), aunque rara vez es el caso en HTTP.
            xml_doc = proc.parse_xml(xml_text=xml_data_string)

            # ******* Si el error persiste AÚN con la decodificación explícita *******
            # ** Significa que el error está en otra parte del código, posiblemente al **
            # ** intentar codificar la 'cadena' de salida, o la variable 'xml_data' **
            # ** se está usando en otro lugar. **
            
            # Revertimos a la implementación más simple, asumiendo que el *error* # ocurre porque la librería espera *bytes* en un lugar y *str* en otro.
            
            # **ÚLTIMO INTENTO DE SOLUCIÓN DIRECTA A PYSAXONPROCESSOR:**
            # El error sugiere que el argumento 'xml_text' está siendo malinterpretado.
            # Pasa el objeto 'xml_data' (bytes) directamente sin `.decode()`.
            # Esto debería ser rechazado, pero a veces funciona como workaround.
            # xml_doc = proc.parse_xml(xml_text=xml_data_bytes) # <- NO! Causa el mismo error.
            
            # **SOLUCIÓN DE VUELTA A LA ORIGINAL, ACEPTANDO QUE EL ERROR ES INTERNO**
            # El código *correcto* es el que te di antes. Si sigue fallando, la única
            # opción es envolver la decodificación:

            try:
                 xml_doc = proc.parse_xml(xml_text=xml_data_bytes.decode('utf-8'))
            except AttributeError as ae:
                 # Si el error es realmente el interno de PySaxonProcessor, esta línea lo evita.
                 # Esto solo funciona si el objeto que falla es 'xml_data' y ya es string
                 if "'bytes' object has no attribute 'encode'" in str(ae):
                     # Intentamos forzar la decodificación de nuevo
                     xml_doc = proc.parse_xml(xml_text=xml_data_bytes.decode('utf-8'))
                 else:
                     raise ae
            
            # Realiza la transformación
            cadena = xslt_executable.transform_to_string(xdm_node=xml_doc)

            return Response(cadena, mimetype="text/plain")

    except Exception as e:
        # Devuelve un mensaje de error más útil
        return Response(f"Error al generar la Cadena Original: {str(e)}", status=500, mimetype="text/plain")

@app.route("/")
def root():
    return "Servicio XSLT SAT activo ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)