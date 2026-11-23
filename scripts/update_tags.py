# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Clean up tags in German and English content (idempotent).

Rules (German front matter is the source, English tags are derived via TAG_EN):
- drop tags without information value (DROP)
- the country from `location.country` is always tagged; existing country tags are kept
  (border crossings mention two countries)
- place tags for major stops: posts within PLACE_RADIUS_KM of the place, by province
  (Guangxi) or listed manually in PLACE_EXTRA
- tags in TAG_TO_CATEGORY become categories (merged with existing categories)
- all other tags are kept in their original order

Only the `tags:` and `categories:` lines are rewritten. Dry run by default, prints every change:

    uv run scripts/update_tags.py            # show changes
    uv run scripts/update_tags.py --apply    # write files
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DE, EN = ROOT / "content", ROOT / "content.en"
# "Blog" is kept: it marks public posts (vs. private diary entries)
DROP = {"Reise", "Reiseberichte"}
# these are kinds of posts, not topics: Blog = public post, Tagebuch = private diary
TAG_TO_CATEGORY = {
    "Blog": "Blog",
    "Tagebuch": "Tagebuch",
    "Orga": "Orga",
    "orga": "Orga",
    "fun": "Fun",
    "erfolg": "Meilenstein",
    "Essen": "Essen",
}
CATEGORY_EN = {
    "Tagebuch": "Diary",
    "Orga": "Planning",
    "Meilenstein": "Milestone",
    "Essen": "Food",
}
COUNTRIES = {  # location.country -> German tag
    "Germany": "Deutschland",
    "Austria": "Österreich",
    "Hungary": "Ungarn",
    "Czech Republic": "Tschechien",
    "Poland": "Polen",
    "Ukraine": "Ukraine",
    "Russia": "Russland",
    "Kyrgyzstan": "Kirgistan",
    "China": "China",
    "Hong Kong": "China",
    "Laos": "Laos",
    "Cambodia": "Kambodscha",
    "Thailand": "Thailand",
    "Malaysia": "Malaysia",
    "Singapore": "Singapur",
}
PLACE_RADIUS_KM = 30
PLACES = {  # German tag -> localityName whose posts define the centre
    "Dieburg": "Dieburg",
    "Wien": "Vienna",
    "Budapest": "Budapest",
    "Prag": "Prague",
    "Krakau": "Krakow",
    "Bischkek": "Bishkek",
    "Kaschgar": "Kashi",
    "Xining": "Xining",
    "Chengdu": "Chengdu",
    "Hongkong": "Hong Kong",
    "Guangzhou": "Guangzhou",
    "Kunming": "Kunming",
    "Phnom Penh": "Phnom Penh",
    "Bangkok": "Bangkok",
    "Kota Bharu": "Kota Bharu",
}
PLACE_AREAS = {"Guangxi": {"Guangxi", "Guangxi Zhuangzu Zizhiqu"}}
PLACE_EXTRA = {  # retrospective posts located elsewhere
    "Kaschgar": ["2009-10-28"],
    "Hongkong": ["2009-11-27"],
    "Guangxi": ["2010-01-05"],
}
TAG_EN = {
    "Tagebuch": "Diary",
    "Orga": "Planning",
    "orga": "planning",
    "Essen": "Food",
    "Meilenstein": "Milestone",
    "Deutschland": "Germany",
    "Österreich": "Austria",
    "Ungarn": "Hungary",
    "Tschechien": "Czech Republic",
    "Polen": "Poland",
    "Russland": "Russia",
    "Kirgistan": "Kyrgyzstan",
    "Kambodscha": "Cambodia",
    "Singapur": "Singapore",
    "Wien": "Vienna",
    "Prag": "Prague",
    "Krakau": "Kraków",
    "Bischkek": "Bishkek",
    "Kaschgar": "Kashgar",
    "Hongkong": "Hong Kong",
}
COUNTRY_TAGS = set(COUNTRIES.values())


def front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    return yaml.safe_load(text.split("---", 2)[1]) or {}


def distance_km(a: tuple, b: tuple) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, [*a, *b])
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371 * 2 * math.asin(math.sqrt(h))


def place_tags(pages: dict[Path, dict]) -> dict[Path, list[str]]:
    located = {p: fm["location"] for p, fm in pages.items() if fm.get("location")}
    result: dict[Path, list[str]] = {p: [] for p in pages}
    for tag, locality in PLACES.items():
        points = [
            (loc["latitude"], loc["longitude"])
            for loc in located.values()
            if loc.get("localityName") == locality
        ]
        centre = (
            sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points),
        )
        for page, loc in located.items():
            if (
                distance_km(centre, (loc["latitude"], loc["longitude"]))
                <= PLACE_RADIUS_KM
            ):
                result[page].append(tag)
    for tag, areas in PLACE_AREAS.items():
        for page, loc in located.items():
            if loc.get("administrativeArea") in areas:
                result[page].append(tag)
    for tag, stems in PLACE_EXTRA.items():
        for page in pages:
            if page.stem in stems and tag not in result[page]:
                result[page].append(tag)
    return result


def new_tags(fm: dict, places: list[str]) -> list[str]:
    old = [t for t in fm.get("tags") or [] if t not in DROP]
    country = COUNTRIES.get((fm.get("location") or {}).get("country", ""))
    rest = [
        t
        for t in old
        if t not in COUNTRY_TAGS and t not in places and t not in TAG_TO_CATEGORY
    ]
    countries = ([country] if country else []) + [t for t in old if t in COUNTRY_TAGS]
    return list(dict.fromkeys(countries + places + rest))


def english_file(de_file: Path, fm: dict, by_key: dict[str, Path]) -> Path | None:
    if key := fm.get("translationKey"):
        return by_key.get(key)
    candidate = EN / de_file.relative_to(DE)
    return candidate if candidate.exists() else None


def write_list(path: Path, key: str, values: list[str], apply: bool) -> bool:
    """Rewrite (or add) the `key: [...]` line in the front matter."""
    text = path.read_text()
    line = f"{key}: " + json.dumps(values, ensure_ascii=False).replace('","', '", "')
    pattern = re.compile(rf"^{key}:.*$", re.MULTILINE)
    head, sep, body = text.partition("\n---")
    if pattern.search(head):
        new = pattern.sub(line, head, count=1) + sep + body
    elif values:
        new = f"{head}\n{line}{sep}{body}"
    else:
        new = text
    if new != text and apply:
        path.write_text(new)
    return new != text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="write files")
    args = parser.parse_args()

    pages = {p: front_matter(p.read_text()) for p in sorted(DE.rglob("*.md"))}
    pages = {p: fm for p, fm in pages.items() if fm}
    by_key = {}
    for p in EN.rglob("*.md"):
        if key := front_matter(p.read_text()).get("translationKey"):
            by_key[key] = p
    places = place_tags(pages)

    changed = 0
    for page, fm in pages.items():
        old, old_cats = fm.get("tags") or [], fm.get("categories") or []
        tags = new_tags(fm, places[page])
        moved = [TAG_TO_CATEGORY[t] for t in old if t in TAG_TO_CATEGORY]
        cats = list(dict.fromkeys(old_cats + moved))
        if tags == old and cats == old_cats:
            continue
        en = english_file(page, fm, by_key)
        en_tags = [TAG_EN.get(t, t) for t in tags]
        en_cats = [CATEGORY_EN.get(c, c) for c in cats]
        results = [
            write_list(page, "tags", tags, args.apply),
            write_list(page, "categories", cats, args.apply),
        ]
        if en:
            results += [
                write_list(en, "tags", en_tags, args.apply),
                write_list(en, "categories", en_cats, args.apply),
            ]
        if any(results):
            changed += 1
            print(
                f"{page.relative_to(DE)}: tags {tags} categories {cats}  | en: {en_tags} {en_cats}"
            )
    print(f"{changed} pages {'updated' if args.apply else 'to update (dry run)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
