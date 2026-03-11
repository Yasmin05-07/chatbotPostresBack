import os
import fitz  # PyMuPDF
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv

# 1. Configuración inicial
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()

# Configuración de CORS corregida para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Función para leer PDFs
def extraer_texto_pdfs():
    texto_total = ""
    carpeta_data = "./data"
    
    if not os.path.exists(carpeta_data):
        print(f"⚠️ Error: La carpeta {carpeta_data} no existe.")
        return ""

    archivos = [f for f in os.listdir(carpeta_data) if f.endswith(".pdf")]
    for archivo in archivos:
        ruta = os.path.join(carpeta_data, archivo)
        try:
            with fitz.open(ruta) as doc:
                for pagina in doc:
                    texto_total += pagina.get_text()
            print(f"✅ Cargado: {archivo}")
        except Exception as e:
            print(f"❌ Error leyendo {archivo}: {e}")
                
    return texto_total

# Cargamos el conocimiento al iniciar
CONOCIMIENTO_POSTRES = extraer_texto_pdfs()

class ChatRequest(BaseModel):
    message: str

# 3. Endpoint principal del Chat
@app.post("/chat")
async def chat(request: ChatRequest):
    
    # REDUCIDO A 12,000 para evitar el error 429 de Rate Limit
    # Esto asegura que la consulta no pese tanto en tokens
    contexto_limitado = CONOCIMIENTO_POSTRES[:12000] 

    prompt_sistema = f"""
    Eres un experto en cultura y repostería internacional (Venezuela, Japón y Corea).
    
    REGLA ESTRICTA: Tu respuesta debe basarse exclusivamente en la información proporcionada a continuación.
    - Si la información NO está en el texto, responde: "Lo siento, esa información no se encuentra en mis manuales técnicos."
    - No inventes ingredientes.
    - Si mencionan el 'quesillo', usa la definición del PDF de Venezuela.

    INFORMACIÓN TÉCNICA:
    {contexto_limitado}
    """
    
    try:
        # CAMBIADO A LLAMA-3-8B: Es más rápido y tiene límites de cuota menos estrictos
        completion = client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": request.message}
            ],
            temperature=0.1, 
        )
        return {"response": completion.choices[0].message.content}
    
    except Exception as e:
        # Si el error es de Rate Limit (429), enviamos un mensaje claro
        if "429" in str(e):
            return {"response": "Error: Se ha alcanzado el límite de mensajes permitidos por la API. Por favor, espera unos minutos."}
        return {"response": f"Hubo un error en la conexión con Groq: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    # Ajuste dinámico de puerto para Render
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)