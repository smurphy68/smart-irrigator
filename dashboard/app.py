from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
import redis, json, os
from datetime import datetime, timedelta

load_dotenv()

REDIS_URL: str = os.getenv("REDIS_URL", "")
OBSCURE_ENDPOINT: str = os.getenv("OBSCURE_ENDPOINT", "")

app = Flask(__name__)


def get_redis():
    return redis.from_url(REDIS_URL)


def get_history():
    r = get_redis()
    cutoff = datetime.now() - timedelta(days=30)
    entries = r.lrange("irrigator:history", 0, -1)
    return [
        json.loads(e) for e in entries
        if datetime.fromisoformat(json.loads(e)["date"]) >= cutoff
    ]


def get_today_ticks():
    r = get_redis()
    today = datetime.now().strftime("%Y-%m-%d")
    entries = r.lrange("irrigator:ticks", 0, -1)
    return [
        json.loads(e) for e in entries
        if json.loads(e).get("date", "").startswith(today)
    ]


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/history")
def api_history():
    return jsonify(get_history())


@app.get("/api/ticks")
def api_ticks():
    return jsonify(get_today_ticks())


@app.post(OBSCURE_ENDPOINT)
def ingest():
    r = get_redis()
    data = request.json
    event = data.get("event")

    if event == "dispense_tick":
        data["date"] = datetime.now().isoformat()
        r.rpush("irrigator:ticks", json.dumps(data))
        r.ltrim("irrigator:ticks", -288, -1)
    else:
        data["date"] = datetime.now().isoformat()
        r.rpush("irrigator:history", json.dumps(data))
        r.ltrim("irrigator:history", -30, -1)

    return {"ok": True}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
