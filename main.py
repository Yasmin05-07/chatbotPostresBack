import os
import fitz  
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def extraer_texto_pdfs():
    texto_total = ""
    carpeta_data = "./data"
 
    if not os.path.exists(carpeta_data):
        print(f"Error: La carpeta {carpeta_data} no existe.")
        return ""

    for archivo in os.listdir(carpeta_data):
        if archivo.endswith(".pdf"):
            ruta = os.path.join(carpeta_data, archivo)
            try:
                with fitz.open(ruta) as doc:
                    for pagina in doc:
                        texto_total += pagina.get_text()
                print(f" Cargado: {archivo}")
            except Exception as e:
                print(f" Error leyendo {archivo}: {e}")
                
    return texto_total

CONOCIMIENTO_POSTRES = extraer_texto_pdfs()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    
    contexto_limitado = CONOCIMIENTO_POSTRES[:40000] 

    prompt_sistema = f"""
    Eres un experto en cultura y repostería internacional (Venezuela, Japón y Corea).
    
    REGLA ESTRICTA: Tu respuesta debe basarse exclusivamente en la información proporcionada a continuación.
    - Si el usuario pregunta algo que NO está en el texto, responde: "Lo siento, esa información no se encuentra en mis manuales técnicos."
    - No inventes ingredientes ni tradiciones culturales.
    - Si mencionan el 'quesillo', asegúrate de usar la definición del PDF de Venezuela.

    INFORMACIÓN TÉCNICA DE LOS PDF:
    {contexto_limitado}
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": request.message}
            ],
            temperature=0.2, 
        )
        return {"response": completion.choices[0].message.content}
    
    except Exception as e:
        return {"response": f"Hubo un error en la conexión con Groq: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)