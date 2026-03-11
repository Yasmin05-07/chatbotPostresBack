import os
import fitz  # PyMuPDF
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv

# 1. Configuración de entorno
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

app = FastAPI(title="PostresBot API - Ingeniería Informática")

# 2. Configuración de CORS (CRÍTICO para conectar con Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite que Vercel y tu celular se conecten
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Función para extraer texto de los manuales PDF
def extraer_texto_pdfs():
    texto_total = ""
    carpeta_data = "./data"
    
    if not os.path.exists(carpeta_data):
        print(f"⚠️ Error: La carpeta {carpeta_data} no existe en el servidor.")
        return ""

    archivos = [f for f in os.listdir(carpeta_data) if f.endswith(".pdf")]
    
    if not archivos:
        print("⚠️ No se encontraron archivos PDF en la carpeta /data.")
        return ""

    for archivo in archivos:
        ruta = os.path.join(carpeta_data, archivo)
        try:
            with fitz.open(ruta) as doc:
                for pagina in doc:
                    texto_total += pagina.get_text()
            print(f"✅ PDF Cargado con éxito: {archivo}")
        except Exception as e:
            print(f"❌ Error leyendo {archivo}: {e}")
                
    return texto_total

# Cargamos el conocimiento al iniciar el servidor
CONOCIMIENTO_POSTRES = extraer_texto_pdfs()

# 4. Modelos de datos
class ChatRequest(BaseModel):
    message: str

# 5. Endpoint Principal
@app.post("/chat")
async def chat(request: ChatRequest):
    # Limitamos el contexto para no saturar la ventana de Groq (Llama 3.3 70B)
    contexto_limitado = CONOCIMIENTO_POSTRES[:25000] 

    prompt_sistema = f"""
    Eres un experto en cultura y repostería internacional (Venezuela, Japón y Corea).
    
    REGLA DE ORO: Responde basándote ÚNICAMENTE en la información técnica de los PDF.
    - Si la información no está en los PDF, responde: "Lo siento, esa información no se encuentra en mis manuales técnicos."
    - No inventes ingredientes. No digas que el quesillo lleva carne.
    - Sé profesional, directo y utiliza un tono académico de ingeniería.

    INFORMACIÓN TÉCNICA DE LOS MANUALES:
    {contexto_limitado}
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": request.message}
            ],
            temperature=0.1, # Muy baja para que no invente (sea determinista)
        )
        return {"response": completion.choices[0].message.content}
    
    except Exception as e:
        print(f"Error en Groq: {e}")
        return {"response": "Hubo un error técnico al procesar la consulta con la IA."}

# 6. Configuración de inicio para Render/Producción
if __name__ == "__main__":
    import uvicorn
    # Render usa la variable de entorno PORT, si no existe usamos 10000
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)