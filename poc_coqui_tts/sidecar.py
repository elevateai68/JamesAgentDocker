from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from TTS.api import TTS
import io
import soundfile as sf
import traceback

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Let the TTS library manage model downloads to a persistent volume
try:
    print("Loading TTS models... This may take a while on first run.")

    # VITS model (self-contained)
    james_tts = TTS(model_name="tts_models/en/vctk/vits", gpu=False)

    # Tacotron2 model (the library will find the default vocoder automatically)
    julia_tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", gpu=False)
    startup_error = None
    print("TTS models loaded successfully.")

except Exception as e:
    james_tts = None
    julia_tts = None
    startup_error = str(e)
    print("--- FATAL: Could not load TTS models ---")
    traceback.print_exc()
    print("-----------------------------------------")


@app.get("/health")
async def health():
    if not james_tts or not julia_tts:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": f"TTS models failed to load: {startup_error}",
            },
        )
    return {"status": "ok", "models": ["james", "julia"]}


@app.post("/tts")
async def synthesize(request: Request):
    if not james_tts or not julia_tts:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": "TTS models failed to load on startup.",
            },
        )
    try:
        body = await request.json()
        text = body.get("text", "")
        speaker = body.get("speaker", "james").lower()

        if speaker == "julia":
            wav = julia_tts.tts(text=text)
            rate = julia_tts.synthesizer.output_sample_rate
        else:
            speaker_id = body.get("speaker_id", "p236")
            wav = james_tts.tts(text=text, speaker=speaker_id)
            rate = james_tts.synthesizer.output_sample_rate

        buf = io.BytesIO()
        sf.write(buf, wav, rate, format="WAV")
        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/wav")

    except Exception as e:
        print("--- ERROR: Exception during TTS synthesis ---")
        traceback.print_exc()
        print("-------------------------------------------")
        return JSONResponse(
            status_code=500, content={"status": "error", "detail": str(e)}
        )
