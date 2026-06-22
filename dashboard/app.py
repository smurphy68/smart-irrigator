from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
import redis, json, os
from datetime import datetime, timedelta

load_dotenv()

REDIS_URL: str = os.getenv("REDIS_URL", "")
OBSCURE_ENDPOINT: str = os.getenv("OBSCURE_ENDPOINT", "")
BED_AREA = float(os.getenv("BED_AREA", "1.368"))
ABSORPTION_FACTOR = float(os.getenv("ABSORPTION_FACTOR", "0.8"))
TICK_INTERVAL_MINS = int(os.getenv("TICK_INTERVAL_MINS", "10"))
PUMP_RATE_LS = float(os.getenv("PUMP_RATE_LS", "0.1"))

app = Flask(__name__)


def get_redis():
    return redis.from_url(REDIS_URL)


def get_history():
    r = get_redis()
    cutoff = datetime.now() - timedelta(days=30)
    entries = r.lrange("irrigator:history", 0, -1)

    result = []

    for i in range(len(entries)):
        entry = json.loads(entries[i])

        if datetime.fromisoformat(entry["date"]) < cutoff:
            continue

        if i == 0:
            entry["yday_rain"] = None
        else:
            prev_entry = json.loads(entries[i - 1])
            entry["yday_rain"] = prev_entry["rainfall"]

        result.append(entry)

    return result


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


@app.post("/" + OBSCURE_ENDPOINT)
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


@app.get("/api/config")
def api_config():
    return jsonify({
        "tick_interval_mins": os.getenv("TICK_INTERVAL_MINS", "60"),
        "bed_area": os.getenv("BED_AREA", "1.368"),
        "absorption_factor": os.getenv("ABSORPTION_FACTOR", "0.8"),
        "pump_rate_ls": os.getenv("PUMP_RATE_LS", "0.1"),
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
