from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn, os, platform, psutil, subprocess, httpx, json
import traceback

# --- Load Persona ---
SYSTEM_PROMPT = "You are a helpful assistant."
try:
    with open("james_personality.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
    print("INFO:     James persona loaded from file.")
except FileNotFoundError:
    print("WARNING:  james_personality.txt not found. Using default system prompt.")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Define Pydantic Models ---
class SystemInfo(BaseModel):
    cpu: str; ram_gb: float; gpu: str; active_model: str

class ChatReq(BaseModel):
    message: str

# --- API Endpoints ---
@app.get("/", response_class=FileResponse)
def serve_index():
    return FileResponse("static/index.html")

@app.post("/remember")
async def remember(what: str = Form(...), who: str = Form(...), file: UploadFile = File(None)):
    print("INFO: /remember endpoint called but is not yet fully implemented.")
    return {"status": "ok", "message": "Memory feature is under development."}

OLLAMA_API = os.getenv("OLLAMA_API_BASE", "http://ollama:11434/v1")

@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    try:
        data = json.loads(await ws.receive_text())
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}, 
                {"role": "user", "content": data.get('prompt', '')}]
        
        payload = { "model":"qwen2.5:7b", "messages":msgs, "stream": True, "temperature": 0.3 }
        
        async with httpx.AsyncClient(timeout=120) as c:
            async with c.stream("POST", f"{OLLAMA_API}/chat/completions", json=payload) as r:
                r.raise_for_status()
                async for chunk in r.aiter_text():
                    if not chunk.strip(): continue
                    try:
                        if chunk.startswith("data: "): chunk = chunk[len("data: "):]
                        if chunk.strip() == "[DONE]": continue
                        pkt = json.loads(chunk)
                        content = pkt.get("choices", [{}])[0].get("delta", {}).get("content")
                        if content: await ws.send_text(content)
                    except json.JSONDecodeError:
                        print(f"Warning: Skipping non-JSON chunk: {chunk}")
                        continue
        await ws.send_text("[Done]")
    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        tb_str = traceback.format_exc()
        error_message = f"[Error] A server-side error occurred:\n\n{tb_str}"
        print(error_message)
        await ws.send_text(error_message)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
