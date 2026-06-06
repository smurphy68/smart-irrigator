import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
LATITUDE = os.getenv("LATITUDE")
LONGITUDE = os.getenv("LONGITUDE")

BED_AREA = 1.8 * 0.76
ABSORPTION_FACTOR = 0.8  # assumed high because it's a raised bed with angled sides


def notify(message):
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": f"🍓 Pi: {message}"})


def get_weather_data():
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": float(LATITUDE),
        "longitude": float(LONGITUDE),
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
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
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


def calculate_dispense(etc0_mm, rainfall_mm_yday, forecast_rain_probability):
    demand_l = etc0_mm * BED_AREA

    # rainfall credit for yesterday's rain
    effective_rainfall = rainfall_mm_yday * BED_AREA * ABSORPTION_FACTOR

    credit_l = 0
    if forecast_rain_probability > 80:
        credit_l = demand_l * 0.8
    elif forecast_rain_probability > 50:
        credit_l = demand_l * 0.5

    estimated_dispense = demand_l - effective_rainfall - credit_l
    dispense = max(0, estimated_dispense)

    return round(dispense, 2)


def schedule_dispense():
    return


notify("Service started")


if __name__ == "__main__":
    print("running")
    yesterday_result, today_result = get_weather_data()

    litres = calculate_dispense(
        today_result["et0"],
        yesterday_result["precipitation_mm"],
        today_result["precipitation_probability"]
    )

    notify(f"Scheduled to dispense {litres}L today")
