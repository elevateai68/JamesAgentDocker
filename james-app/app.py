from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn, os, httpx, json, datetime
import traceback
import aiofiles

# --- Setup Data Directory ---
DATA_DIR = "james-data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
MEMORY_FILE = os.path.join(DATA_DIR, "memory.jsonl")

# --- Load Persona ---
SYSTEM_PROMPT = "You are a helpful assistant."
try:
    with open("james_personality.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
    print("INFO:     James persona loaded from file.")
except FileNotFoundError:
    print("WARNING:  james_personality.txt not found. Using default system prompt.")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

OLLAMA_API = os.getenv("OLLAMA_API_BASE", "http://ollama:11434/v1")


# --- UPDATED: Function to read all memories with better error logging ---
async def get_all_memories():
    try:
        all_memories = []
        async with aiofiles.open(MEMORY_FILE, "r", encoding="utf-8") as f:
            async for line in f:
                all_memories.append(json.loads(line))

        if not all_memories:
            return None

        formatted_memories = "\n".join([f"- {json.dumps(m)}" for m in all_memories])
        return f"For context, here is your long-term memory. Use it to answer the user's question if relevant:\n{formatted_memories}"
    except FileNotFoundError:
        print("INFO: Memory file not found. Skipping.")
        return None
    except Exception as e:
        print(f"--- ERROR: Could not read memory file ---")
        traceback.print_exc()  # <-- THIS IS THE NEW LINE
        return None


# --- API Endpoints ---
@app.get("/", response_class=FileResponse)
def serve_index():
    return FileResponse("static/index.html")


@app.post("/remember")
async def remember(
    what: str = Form(...), who: str = Form(...), file: UploadFile = File(None)
):
    try:
        memory_record = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "what": what,
            "who": who,
            "user_id": "guest",
        }
        if file:
            memory_record["original_filename"] = file.filename

        async with aiofiles.open(MEMORY_FILE, "a", encoding="utf-8") as f:
            await f.write(json.dumps(memory_record) + "\n")

        print(f"INFO: Memory saved for '{who}': '{what}'")
        return {"status": "ok", "message": "Memory successfully saved."}
    except Exception as e:
        print(f"ERROR: Could not save memory. Error: {e}")
        traceback.print_exc()
        return {"status": "error", "message": "Failed to save memory."}


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    try:
        data = json.loads(await ws.receive_text())
        user_prompt = data.get("prompt", "")

        memory_context = await get_all_memories()

        print(
            f"--- MEMORY CONTEXT ADDED TO PROMPT: ---\n{memory_context}\n------------------------------------"
        )

        final_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if memory_context:
            final_messages.append({"role": "system", "content": memory_context})
        final_messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": "qwen2.5:7b",
            "messages": final_messages,
            "stream": True,
            "temperature": 0.3,
        }

        async with httpx.AsyncClient(timeout=120) as c:
            async with c.stream(
                "POST", f"{OLLAMA_API}/chat/completions", json=payload
            ) as r:
                r.raise_for_status()
                async for chunk in r.aiter_text():
                    if not chunk.strip():
                        continue
                    try:
                        if chunk.startswith("data: "):
                            chunk = chunk[len("data: ") :]
                        if chunk.strip() == "[DONE]":
                            continue
                        pkt = json.loads(chunk)
                        content = (
                            pkt.get("choices", [{}])[0].get("delta", {}).get("content")
                        )
                        if content:
                            await ws.send_text(content)
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
