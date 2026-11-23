# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Fetch the weather of the day for every German diary post that has a location.

Data comes from the Open-Meteo historical archive (https://open-meteo.com, ERA5 reanalysis,
CC BY 4.0): daily values for the post's coordinates, not measurements on the spot. One file per
post is written to data/weather/<year>/<month>/<post>.json. Existing files whose date and
coordinates are unchanged are not requested again; stale files are reported, never deleted.

    uv run scripts/build_weather.py              # fetch missing/changed days
    uv run scripts/build_weather.py --dry-run    # only list what would be fetched
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content/docs"
TARGET = ROOT / "data/weather"
API = "https://archive-api.open-meteo.com/v1/archive"
DAILY = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "sunshine_duration",
    "wind_speed_10m_max",
    "wind_direction_10m_dominant",
    "weather_code",
]
REQUEST_DELAY_S = 0.4
RETRIES = 3
RETRY_DELAY_S = 60.0


def front_matter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    return yaml.safe_load(text.split("---", 2)[1]) or {}


def posts() -> list[dict]:
    result = []
    for path in sorted(CONTENT.glob("20*/*/20*.md")):
        loc = front_matter(path).get("location") or {}
        if "latitude" not in loc:
            continue
        result.append(
            {
                "key": path.relative_to(CONTENT).with_suffix(""),
                "date": path.stem[:10],  # the file name day is the local calendar day
                "latitude": round(float(loc["latitude"]), 4),
                "longitude": round(float(loc["longitude"]), 4),
            }
        )
    return result


def fetch(post: dict) -> dict:
    query = urllib.parse.urlencode(
        {
            "latitude": post["latitude"],
            "longitude": post["longitude"],
            "start_date": post["date"],
            "end_date": post["date"],
            "daily": ",".join(DAILY),
            "timezone": "auto",
        }
    )
    for attempt in range(RETRIES + 1):
        try:
            with urllib.request.urlopen(f"{API}?{query}", timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == RETRIES:
                raise
            print(f"  rate limited, waiting {RETRY_DELAY_S:.0f} s", file=sys.stderr)
            time.sleep(RETRY_DELAY_S)
    raise RuntimeError("unreachable")


def first(daily: dict, name: str, digits: int | None = None):
    value = (daily.get(name) or [None])[0]
    return (
        None
        if value is None
        else (round(value, digits) if digits is not None else value)
    )


def day_from(post: dict, response: dict) -> dict:
    daily = response["daily"]
    sunshine = first(daily, "sunshine_duration")
    return {
        "date": post["date"],
        "latitude": post["latitude"],
        "longitude": post["longitude"],
        "gridElevation": response.get("elevation"),
        "temperatureMax": first(daily, "temperature_2m_max", 1),
        "temperatureMin": first(daily, "temperature_2m_min", 1),
        "precipitation": first(daily, "precipitation_sum", 1),
        "sunshineHours": None if sunshine is None else round(sunshine / 3600, 1),
        "windMax": first(daily, "wind_speed_10m_max", 0),
        "windDirection": first(daily, "wind_direction_10m_dominant", 0),
        "weatherCode": first(daily, "weather_code"),
        "source": "Open-Meteo (ERA5)",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="only list the days")
    args = parser.parse_args()

    wanted = {}
    fetched = failed = cached = 0
    for post in posts():
        path = TARGET / post["key"].with_suffix(".json")
        wanted[path] = post
        if path.exists():
            old = json.loads(path.read_text())
            if "windDirection" in old and all(
                old.get(k) == post[k] for k in ("date", "latitude", "longitude")
            ):
                cached += 1
                continue
        if args.dry_run:
            print(f"would fetch {post['key']} ({post['date']})")
            continue
        try:
            day = day_from(post, fetch(post))
        except (urllib.error.URLError, KeyError, ValueError) as error:
            print(f"{post['key']}: failed: {error}")
            failed += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(day, ensure_ascii=False, indent=1) + "\n")
        fetched += 1
        print(
            f"{post['key']}: {day['temperatureMin']}..{day['temperatureMax']} °C, {day['precipitation']} mm"
        )
        time.sleep(REQUEST_DELAY_S)

    for stale in sorted(set(TARGET.rglob("*.json")) - set(wanted)):
        print(f"stale (post gone), kept: {stale.relative_to(ROOT)}")
    print(f"{len(wanted)} posts: {fetched} fetched, {cached} cached, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
