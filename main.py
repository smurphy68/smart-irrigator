import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
import schedule
import time
from gpiozero import OutputDevice

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
LATITUDE = os.getenv("LATITUDE")
LONGITUDE = os.getenv("LONGITUDE")
OBSCURE_URL = os.getenv("OBSCURE_URL")

BED_AREA = 1.8 * 0.76
ABSORPTION_FACTOR = 0.8  # assumed high because it's a raised bed with angled sides
TICK_INTERVAL_MINS = int(os.getenv("TICK_INTERVAL_MINS", "60"))

DISPENSED_L = 0
DAILY_L = 0

PUMP_RATE_LS = 0.1  # litres per second - to be configured
PUMP_PIN = 4

pump = OutputDevice(PUMP_PIN, active_high=True)  # invert this when connected to the pump as relays are active


def notify(message):
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": f"🍓 Pi: {message}"})


def get_weather_data():
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": [
            "precipitation_sum",
            "et0_fao_evapotranspiration",
            "precipitation_probability_max"
        ],
        "timezone": "Europe/London",
        "start_date": yesterday,
        "end_date": today
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    daily = data["daily"]
    yesterday_data = {
        "date": daily["time"][0],
        "precipitation_mm": daily["precipitation_sum"][0],
        "et0": daily["et0_fao_evapotranspiration"][0],
    }
    today_data = {
        "date": daily["time"][1],
        "precipitation_probability": daily["precipitation_probability_max"][1],
        "et0": daily["et0_fao_evapotranspiration"][1],
    }

    return yesterday_data, today_data


def _post(payload: dict):
    if not OBSCURE_URL:
        return
    try:
        requests.post(OBSCURE_URL, json=payload)
    except requests.exceptions.RequestException as e:
        notify(f"Dashboard post failed: {e}")


def post_daily_schedule(et0: float, rainfall: float, dispensed: float, forecast_prob: float):
    _post({
        "event": "daily_schedule",
        "et0": et0,
        "rainfall": rainfall,
        "dispensed": dispensed,
        "forecast_prob": forecast_prob
    })


def post_dispense_tick(tick_amount: float, dispensed_total: float):
    _post({
        "event": "dispense_tick",
        "tick_amount": tick_amount,
        "dispensed_total": dispensed_total
    })


def post_moisture_reading(moisture: float):
    _post({
        "event": "moisture_reading",
        "moisture": moisture
    })


def reset_daily():
    global DISPENSED_L
    DISPENSED_L = 0

    global DAILY_L
    DAILY_L = 0


def morning_fetch():
    yesterday, today = get_weather_data()
    calculate_dispense(
        today["et0"],
        yesterday["precipitation_mm"],
        today["precipitation_probability"]
    )

    notify_schedule()

    post_daily_schedule(
        et0=today["et0"],
        rainfall=yesterday["precipitation_mm"],
        dispensed=DAILY_L,
        forecast_prob=today["precipitation_probability"]
    )


def calculate_dispense(et0_mm, rainfall_mm_yday, forecast_rain_probability):
    demand_l = et0_mm * BED_AREA

    # rainfall credit for yesterday's rain
    effective_rainfall = rainfall_mm_yday * BED_AREA * ABSORPTION_FACTOR

    credit_l = 0
    if forecast_rain_probability > 80:
        credit_l = demand_l * 0.8
    elif forecast_rain_probability > 50:
        credit_l = demand_l * 0.5

    estimated_dispense = demand_l - effective_rainfall - credit_l
    dispense = max(0, estimated_dispense)

    global DAILY_L
    DAILY_L = round(dispense, 2)

    return round(dispense, 2)


def schedule_dispense():
    global DISPENSED_L

    hour = datetime.now().hour
    if hour < 6 or (11 <= hour < 14) or hour >= 18:
        return

    if DISPENSED_L >= DAILY_L:
        return

    dispense_l = DAILY_L / (9 * 60 / TICK_INTERVAL_MINS)
    DISPENSED_L += dispense_l
    notify(f"Dispensing {dispense_l:.3f}L - total: {DISPENSED_L:.2f}/{DAILY_L}L")
    pump_it(dispense_l)
    post_dispense_tick(dispense_l, DISPENSED_L)


def pump_it(dispense_l: float):
    duration = round(dispense_l / PUMP_RATE_LS)
    duration = min(duration, 60)  # safety cap
    pump.on()
    time.sleep(duration)
    pump.off()


def notify_schedule():
    morning_ticks = int((5 * 60) / TICK_INTERVAL_MINS)
    afternoon_ticks = int((4 * 60) / TICK_INTERVAL_MINS)
    total_ticks = morning_ticks + afternoon_ticks
    tick_amount = round(DAILY_L / total_ticks, 3) if total_ticks > 0 else 0
    tick_duration = max(round(tick_amount / PUMP_RATE_LS), 3)

    message = (
        f"**Watering schedule for {datetime.now().strftime('%A %d %B')}**\n"
        f"Total to dispense: {DAILY_L}L\n\n"
        f"**Morning** 06:00–11:00\n"
        f"{morning_ticks} ticks × {tick_amount}L every {TICK_INTERVAL_MINS} mins ({tick_duration}s pump)\n\n"
        f"**Pause** 11:00–14:00\n"
        f"Peak evaporation — pump off\n\n"
        f"**Afternoon** 14:00–18:00\n"
        f"{afternoon_ticks} ticks × {tick_amount}L every {TICK_INTERVAL_MINS} mins ({tick_duration}s pump)"
    )
    notify(message)


if __name__ == "__main__":
    notify("Service started")

    reset_daily()
    morning_fetch()

    schedule.every().day.at("05:59").do(reset_daily)
    schedule.every().day.at("06:00").do(morning_fetch)
    schedule.every(TICK_INTERVAL_MINS).minutes.do(schedule_dispense)

    while True:
        schedule.run_pending()
        time.sleep(1)