# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Compute the route from the previous diary location to each post's location.

Reads the German diary posts (content/docs/<year>/<month>/20*.md) in chronological order
and writes one leg per post to data/routes/<year>/<month>/<post>.json. Legs are routed
with BRouter (https://brouter.de) depending on the post's `travelMode` front matter
(default: bike); non-routable modes (train, boat, plane, unknown) and failed requests
are stored as a straight line with `routed: false`. Posts at the same place as the previous
one (< SAME_PLACE_KM) or with `travelMode: static` get no leg. A `route:` list of [lat, lon]
waypoints in the front matter replaces the automatic leg with the route of the day (start,
via points, finish) - also for the first post, which has no previous location. `routeProfile:` sets
another BRouter profile for that leg (e.g. car-fast to stay on main roads). Legs never cross
trips (`params.trips` in hugo.toml): the first post of a trip is treated like the first post.
Existing legs with unchanged
input are not requested again; stale leg files are reported, never deleted. `--check` (no network)
lists leg files no post needs (stale or orphaned) and exits 1 if there are any (hk hook, CI).

    uv run scripts/build_routes.py              # compute missing/changed legs
    uv run scripts/build_routes.py --dry-run    # only list legs
    uv run scripts/build_routes.py --check      # fail on leg files no post needs
"""

import argparse
import itertools
import json
import math
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content/docs"
CONFIG = ROOT / "hugo.toml"
TARGET = ROOT / "data/routes"
BROUTER = "https://brouter.de/brouter"
PROFILES = {
    "bike": "trekking",
    "foot": "hiking-mountain",
    "bus": "car-vario",
    "car": "car-vario",
    "kayak": "river",
}
# bus/car profiles of brouter.de each fail on some corridors ("no track found",
# "error re-tracking track"): try these in turn, trekking (roads) as the last resort
PROFILE_FALLBACKS = {"car-vario": ["car-fast", "car-eco", "trekking"]}
# brouter.de refuses (403) very long requests: custom routes are routed in pieces
MAX_POINTS = 4
MAX_PIECE_KM = 900  # straight-line length of a piece (1,500 km was refused)
MODES = {*PROFILES, "train", "boat", "kayak", "plane", "unknown", "static"}
SAME_PLACE_KM = 1.0
SIMPLIFY_DEG = 0.0001  # ~10 m, keeps files small without visible loss
REQUEST_DELAY_S = 1.0
RETRIES = 2
RETRY_DELAY_S = 60.0
ELEVATION_MODES = {"bike", "foot"}  # legs that get an elevation profile
PROFILE_POINTS = 200


def front_matter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    return yaml.safe_load(text.split("---", 2)[1]) or {}


def trip_key(date: str, trips: list[dict]) -> str:
    """Key of the trip whose months ('YYYY-MM', inclusive) contain date, or "" (as docs/trip-key)."""
    month = date[:7]
    return next((t["key"] for t in trips if t["from"] <= month <= t["to"]), "")


def posts() -> list[dict]:
    trips = tomllib.loads(CONFIG.read_text()).get("params", {}).get("trips", [])
    result = []
    for path in CONTENT.glob("20*/*/20*.md"):
        fm = front_matter(path)
        loc = fm.get("location") or {}
        if "latitude" not in loc:
            continue
        result.append(
            {
                "key": path.relative_to(CONTENT).with_suffix(""),
                "date": str(fm.get("date")),
                "trip": trip_key(str(fm.get("date")), trips),
                "point": [float(loc["latitude"]), float(loc["longitude"])],
                "mode": fm.get("travelMode", "bike"),
                "waypoints": [[float(a), float(b)] for a, b in fm.get("route") or []],
                "routeProfile": fm.get("routeProfile", ""),
            }
        )
    return sorted(result, key=lambda p: (p["date"], str(p["key"])))


def distance_km(a: list[float], b: list[float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, [*a, *b])
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371 * 2 * math.asin(math.sqrt(h))


def simplify(points: list[list[float]], tolerance: float) -> list[list[float]]:
    """Ramer-Douglas-Peucker line simplification."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        (y1, x1), (y2, x2) = points[start], points[end]
        length = math.hypot(x2 - x1, y2 - y1) or 1e-12
        index, dmax = start, 0.0
        for i in range(start + 1, end):
            y0, x0 = points[i]
            d = abs((x2 - x1) * (y1 - y0) - (x1 - x0) * (y2 - y1)) / length
            if d > dmax:
                index, dmax = i, d
        if dmax > tolerance:
            keep[index] = True
            stack += [(start, index), (index, end)]
    return [p for p, k in zip(points, keep) if k]


def elevation_profile(points: list[list[float]], ascent: int) -> dict:
    """Downsample [lon, lat, ele] points to PROFILE_POINTS [km, metres] pairs."""
    km, total = [0.0], 0.0
    for (lon1, lat1, *_), (lon2, lat2, *_) in itertools.pairwise(points):
        total += distance_km([lat1, lon1], [lat2, lon2])
        km.append(total)
    elevations = [p[2] if len(p) > 2 else 0 for p in points]
    step = max(1, len(points) // PROFILE_POINTS)
    indices = sorted({*range(0, len(points), step), len(points) - 1})
    samples = [[round(km[i], 2), round(elevations[i])] for i in indices]
    descent = ascent - (elevations[-1] - elevations[0])
    return {
        "points": samples,
        "ascent": ascent,
        "descent": round(descent),
        "min": round(min(elevations)),
        "max": round(max(elevations)),
    }


def route_piece(points: list[list[float]], profile: str) -> tuple[list, dict]:
    """One BRouter request: return its [lon, lat, ele] points and GeoJSON properties."""
    query = urllib.parse.urlencode(
        {
            "lonlats": "|".join(f"{lon},{lat}" for lat, lon in points),
            "profile": profile,
            "alternativeidx": 0,
            "format": "geojson",
        },
        safe=",|",
    )
    for attempt in range(RETRIES + 1):
        try:
            with urllib.request.urlopen(f"{BROUTER}?{query}", timeout=120) as response:
                feature = json.load(response)["features"][0]
            break
        except urllib.error.HTTPError as error:
            # 403 = rate limited by brouter.de, wait and retry
            if error.code != 403 or attempt == RETRIES:
                raise
            time.sleep(RETRY_DELAY_S)
    return feature["geometry"]["coordinates"], feature["properties"]


def route(points: list[list[float]], profile: str) -> tuple[list, int, dict]:
    """Return ([[lat, lon], ...], length in metres, elevation profile) from BRouter.

    Routes longer than MAX_POINTS waypoints or MAX_PIECE_KM are routed in overlapping pieces
    and joined.
    """
    pieces, piece = [], [points[0]]
    for point in points[1:]:
        too_long = sum(
            distance_km(x, y) for x, y in itertools.pairwise(piece + [point])
        )
        if len(piece) >= 2 and (len(piece) >= MAX_POINTS or too_long > MAX_PIECE_KM):
            pieces.append(piece)
            piece = [piece[-1]]  # pieces overlap in one waypoint
        piece.append(point)
    pieces.append(piece)
    track: list = []
    length = ascent = 0
    for number, piece in enumerate(pieces):
        if number:
            time.sleep(REQUEST_DELAY_S)
        part, properties = route_piece(piece, profile)
        track += part if not track else part[1:]  # the join point is in both pieces
        length += int(properties["track-length"])
        ascent += int(properties.get("filtered ascend", 0))
    coords = [[round(lat, 5), round(lon, 5)] for lon, lat, *_ in track]
    return simplify(coords, SIMPLIFY_DEG), length, elevation_profile(track, ascent)


def route_with_fallback(points: list[list[float]], profile: str) -> tuple:
    """Like route(), but a 400 ("no track") tries PROFILE_FALLBACKS; also returns the profile used."""
    error: Exception | None = None
    for candidate in [profile, *PROFILE_FALLBACKS.get(profile, [])]:
        try:
            return (*route(points, candidate), candidate)
        except urllib.error.HTTPError as caught:
            if caught.code != 400:
                raise
            error = caught
            time.sleep(REQUEST_DELAY_S)
    raise error  # type: ignore[misc]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="only list legs")
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if a leg file is not needed by any post (stale or orphaned), no network",
    )
    parser.add_argument(
        "--only", action="append", help="only compute this leg, e.g. 2009/05/2009-05-12"
    )
    args = parser.parse_args()
    args.dry_run = args.dry_run or args.check

    counts: dict[str, int] = {}
    wanted: set[Path] = set()  # leg files the posts need
    items = posts()
    for previous, current in zip([None, *items], items, strict=False):
        if previous is not None and previous["trip"] != current["trip"]:
            previous = None  # a new trip starts without a leg from the last one
        mode = current["mode"]
        points = current["waypoints"]
        if not points:
            if previous is None:
                continue  # first post without a custom route
            points = [previous["point"], current["point"]]
        start, end = points[0], points[-1]
        target = TARGET / current["key"].with_suffix(".json")
        km = sum(distance_km(a, b) for a, b in itertools.pairwise(points))
        if mode not in MODES:
            print(f"{current['key']}: unknown travelMode '{mode}', using straight line")
        if args.only and str(current["key"]) not in args.only:
            continue
        if km < SAME_PLACE_KM or mode == "static":
            status = "same-place" if km < SAME_PLACE_KM else "static"
            if target.exists():
                print(f"{current['key']}: stale leg file {target.relative_to(ROOT)}")
        else:
            wanted.add(target)
            leg = {
                "from": start,
                "to": end,
                "fromPost": str(previous["key"]) if previous else "",
                "mode": mode,
                # `routeProfile` overrides the BRouter profile of the mode, e.g. car-fast for a bike
                # leg on main roads that the trekking profile avoids (2010-02-06); mode stays as is
                "profile": current["routeProfile"] or PROFILES.get(mode, ""),
            }
            if current["waypoints"]:  # only custom routes store their waypoints
                leg["waypoints"] = current["waypoints"]
            cached = json.loads(target.read_text()) if target.exists() else {}
            # failed routing requests (profile set but not routed) are retried
            # routed bike/foot legs without elevation (older files) are refreshed
            missing_elevation = mode in ELEVATION_MODES and "elevation" not in cached
            if (
                all(cached.get(k) == v for k, v in leg.items())
                and (cached.get("routed") or not leg["profile"])
                and not (cached.get("routed") and missing_elevation)
            ):
                status = "cached"
            elif args.dry_run:
                status = "to-compute"
            else:
                leg |= {
                    "routed": False,
                    "distance": int(km * 1000),
                    "coordinates": points,
                }
                status = "straight"
                if leg["profile"]:
                    try:
                        coords, length, elevation, used = route_with_fallback(
                            points, leg["profile"]
                        )
                        leg |= {
                            "routed": True,
                            "distance": length,
                            "coordinates": coords,
                        }
                        if used != leg["profile"]:
                            leg["usedProfile"] = (
                                used  # profile that worked, not the intended one
                            )
                        if mode in ELEVATION_MODES:
                            leg["elevation"] = elevation
                        status = "routed"
                    except (
                        urllib.error.URLError,
                        KeyError,
                        IndexError,
                        ValueError,
                    ) as error:
                        status = "failed"
                        print(f"{current['key']}: {km:.0f} km, routing failed: {error}")
                    time.sleep(REQUEST_DELAY_S)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(leg, separators=(",", ":")) + "\n")
        counts[status] = counts.get(status, 0) + 1
        if not args.check:
            print(f"{current['key']}: {mode}, {km:.0f} km, {status}")

    if args.check:
        unneeded = sorted(set(TARGET.rglob("*.json")) - wanted)
        for path in unneeded:
            print(
                f"leg file no post needs (stale or orphaned): {path.relative_to(ROOT)}"
            )
        print(f"{len(unneeded)} unneeded leg file(s)")
        return 1 if unneeded else 0
    print(f"{len(items)} posts with location: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
