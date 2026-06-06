import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
import schedule
import time

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
LATITUDE = os.getenv("LATITUDE")
LONGITUDE = os.getenv("LONGITUDE")

BED_AREA = 1.8 * 0.76
ABSORPTION_FACTOR = 0.8  # assumed high because it's a raised bed with angled sides
TICK_INTERVAL_MINS = 10

DISPENSED_L = 0
DAILY_L = 0


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
    notify(f"Scheduled to dispense {DAILY_L}L today")


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

    tick_amount = DAILY_L / (9 * 60 / TICK_INTERVAL_MINS)
    DISPENSED_L += tick_amount
    notify(f"Dispensing {tick_amount:.3f}L - total: {DISPENSED_L:.2f}/{DAILY_L}L")
    pump_it()


def pump_it():  # louder
    return


if __name__ == "__main__":
    notify("Service started")

    schedule.every().day.at("05:59").do(reset_daily)
    schedule.every().day.at("06:00").do(morning_fetch)

    schedule.every(TICK_INTERVAL_MINS).minutes.do(schedule_dispense)

    while True:
        schedule.run_pending()
        time.sleep(1)