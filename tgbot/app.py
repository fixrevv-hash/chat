"""
Dashboard web (FastAPI) untuk memantau percakapan dan mengatur persona bot.
Berjalan bersamaan dengan worker Telegram dalam satu proses (lihat main.py).
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import db

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class PersonaUpdate(BaseModel):
    persona: str


class DelayUpdate(BaseModel):
    reply_delay_min: float
    reply_delay_max: float


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/state")
async def api_state():
    config = await db.get_config()
    stats = await db.get_stats()
    messages = await db.get_recent_messages(limit=60)
    return JSONResponse(
        {
            "active": config.get("active", "true") == "true",
            "persona": config.get("persona", ""),
            "reply_delay_min": float(config.get("reply_delay_min", 2)),
            "reply_delay_max": float(config.get("reply_delay_max", 5)),
            "stats": stats,
            "messages": messages,
        }
    )


@app.post("/api/toggle")
async def api_toggle():
    config = await db.get_config()
    current = config.get("active", "true") == "true"
    await db.set_config("active", "false" if current else "true")
    return {"active": not current}


@app.post("/api/persona")
async def api_persona(update: PersonaUpdate):
    await db.set_config("persona", update.persona)
    return {"ok": True}


@app.post("/api/delay")
async def api_delay(update: DelayUpdate):
    await db.set_config("reply_delay_min", str(update.reply_delay_min))
    await db.set_config("reply_delay_max", str(update.reply_delay_max))
    return {"ok": True}
