# seed.py
import redis, json
from datetime import datetime, timedelta

r = redis.from_url("redis://localhost:6379")

for i in range(14):
    date = (datetime.now() - timedelta(days=13-i)).isoformat()
    r.rpush("irrigator:history", json.dumps({
        "date": date,
        "et0": round(1.5 + i * 0.2, 2),
        "rainfall": round(2.0 if i % 4 == 0 else 0, 1),
        "dispensed": round(3.0 + i * 0.1, 2),
        "forecast_prob": 20,
        "moisture": round(55 + (i % 5) * 3, 1)
    }))

for i in range(30):
    date = (datetime.now().replace(hour=6, minute=0) + timedelta(minutes=i*10)).isoformat()
    r.rpush("irrigator:ticks", json.dumps({
        "date": date,
        "tick_amount": 0.06,
        "dispensed_total": round(i * 0.06, 2)
    }))

print("Seeded.")