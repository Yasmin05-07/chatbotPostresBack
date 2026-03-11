import fitz  # PyMuPDF
import os

def verificar_lectura():
    carpeta = "./data"
    print(f"--- Verificando archivos en: {carpeta} ---")
    
    archivos = [f for f in os.listdir(carpeta) if f.endswith('.pdf')]
    
    if not archivos:
        print(" No se encontraron archivos PDF en la carpeta /data")
        return

    for archivo in archivos:
        ruta = os.path.join(carpeta, archivo)
        try:
            doc = fitz.open(ruta)

            texto = doc[0].get_text()
            print(f"✅ {archivo}: Leído correctamente. (Caracteres encontrados: {len(texto)})")
            print(f"--- Vistazo al contenido de {archivo}: ---")
            print(texto[:100] + "...") 
            print("-" * 30)
        except Exception as e:
            print(f"Error al leer {archivo}: {e}")

if __name__ == "__main__":
    verificar_lectura()