# Smart Irrigator

A personal project to automate watering my raised bed vegetable garden using a Raspberry Pi. Instead of a fixed watering schedule, it pulls real weather data each morning and works out how much water the plants actually need that day.
The variables that control the watering system will be tweaked depending on the health of the plants, and soil moisture sensors will intervene if soil moisture becomes too high.

## The Idea

I wanted something smarter than a timer — something that would skip watering if it rained yesterday, or water less if the forecast looks wet. The system fetches data from [Open-Meteo](https://open-meteo.com/) each morning and calculates a daily water amount based on:

- **ET₀ (evapotranspiration)** — a standard agronomic measure of how much water the environment is drawing out of the soil. It accounts for temperature, wind, humidity and solar radiation in one number.
- **Yesterday's rainfall** — credited against today's demand so the plants aren't overwatered after rain
- **Today's forecast** — if rain is likely, it reduces the amount dispensed proactively

## How Dispensing Works

Rather than dumping all the water at once, it spreads it across two windows to improve absorption:

- **06:00 – 11:00** — morning watering
- **11:00 – 14:00** — pause during peak evaporation (midday sun would just evaporate it)
- **14:00 – 18:00** — afternoon watering

The daily amount is calculated as:

```
dispense (L) = max(0, ET₀ × bed_area - effective_rainfall - forecast_credit)
```

## Running It

The whole thing runs on a Raspberry Pi as a pair of systemd services — one that runs the irrigation logic, and one that polls this repo every 5 minutes and redeploys automatically when I push changes.

### Environment Variables

I made a local `.env` file in the project root (gitignored, so secrets are local to the Pi):

```
DISCORD_WEBHOOK_URL
LATITUDE
LONGITUDE
```

I'm using a Discord webhook for notifications — it pings me when the service starts, when the daily amount is calculated, and on each watering cycle.

## Configuration

The main values to tweak are at the top of `main.py`:

| Constant | Default | Description                                      |
|---|---|--------------------------------------------------|
| `BED_AREA` | `1.8 × 0.76` | My raised bed dimensions in m²                   |
| `ABSORPTION_FACTOR` | `0.8` | How much rainfall is assumed to actually soak in |
| `TICK_INTERVAL_MINS` | `10` | How often the pump triggers                      |
| `MORNING_HOURS` | `5` | Length of morning watering window                |
| `AFTERNOON_HOURS` | `4` | Length of afternoon watering window              |

## What's Not Done Yet

- Actual pump control via GPIO (currently `pump_it()` is a placeholder)
- Soil moisture sensor integration
- Logging dispensed amounts over time to tune the model

## Project Structure

```
smart-irrigator/
├── main.py           # Main irrigation logic
├── git-sync.sh       # Repo polling and auto-redeploy
├── setup.sh          # One-time setup script
├── requirements.txt  # Python dependencies
├── .env              # Local secrets (gitignored)
└── .gitignore
```

## Weather Data

All weather data comes from [Open-Meteo](https://open-meteo.com/) which is free and requires no API key. It provides historical and forecast data including the ET₀ value calculated using the Penman-Monteith formula.
