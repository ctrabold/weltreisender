# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Give the front matter of every page the same keys in the same order, and validate it.

Per page kind (German diary post, English diary post, section `_index.md`, other page) a set
of keys is always present: missing ones are added with a default (see DEFAULTS), existing
ones keep their value. Keys are sorted in ORDER. Each key moves together with its value (also
multi-line ones like `location` or `route`), its trailing `# comment` and, for `location`, the
`# CHECK location:` lines that follow it. Page bodies are not touched.

Afterwards every page is checked (types, allowed values, coordinates, date against file name,
German/English pairs) and problems are listed; the exit code is 1 if there are any.

    uv run scripts/normalize_frontmatter.py            # dry run: list changes and problems
    uv run scripts/normalize_frontmatter.py --apply    # rewrite files, then list problems

Re-running is safe: files already in order are skipped.
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DIRS = ["content", "content.en"]

# identity > status > description > place and route > day datasheet > taxonomy > layout/theme
ORDER = [
    "date",
    "title",
    "translationKey",
    "slug",
    "aliases",
    "draft",
    "summary",
    "location",
    "travelMode",
    "route",
    "mood",
    "sleeping",
    "costs",
    "events",
    "tags",
    "categories",
    "category",
    "layout",
    "build",
    "bookFlatSection",
    "bookCollapseSection",
    "bookToc",
    "noprevnext",
    "nodateline",
    "disable_comments",
]

TRAVEL_MODES = {
    "bike", "foot", "bus", "car", "kayak", "train", "boat", "plane", "unknown", "static",
}  # fmt: skip
MOODS = ["terrible", "bad", "neutral", "good", "great"]  # 1 to 5
SLEEPING = {"tent", "hostel", "hotel", "homestay", "vehicle", "misc"}
DATASHEET_DE_ONLY = {
    "location",
    "travelMode",
    "route",
    "mood",
    "sleeping",
    "costs",
}  # `events` may be translated

# keys that are always present; the value is written when the key is missing ("" = empty)
DEFAULTS = {
    "diary-de": {
        "draft": "false",
        "travelMode": "bike",
        "mood": "neutral",
        "sleeping": "",
        "costs": "",
        "events": "[]",
        "tags": "[]",
        "categories": "[]",
    },
    "diary-en": {"draft": "false", "tags": "[]", "categories": "[]"},
    "index": {"draft": "false"},
    "page": {"draft": "false", "tags": "[]", "categories": "[]"},
}
# keys that cannot have a default; a page without them is a problem
REQUIRED = {
    "diary-de": ["date", "title", "summary", "location"],
    "diary-en": ["date", "title", "summary"],
    "index": ["date", "title"],
    "page": ["date", "title"],
}

KEY = re.compile(r"([A-Za-z][A-Za-z0-9_]*):")
DIARY = re.compile(r"docs/(20\d\d/\d\d)/((20\d\d-\d\d-)(\d\d[a-z]?))\.md$")


DOCS = re.compile(r"^content(?:\.en)?/docs/(.+?)(?:/_index)?\.md$")


def diary_slug(rel: str) -> str:
    """Slug of a diary post: day plus suffix letter (`2009-05-21a.md` → `21a`)."""
    return DIARY.search(rel).group(4)


def old_urls(rel: str) -> list[str]:
    """Earlier URLs of a page below `docs/`, kept as redirects (`aliases`).

    `hugo.toml` [permalinks] drops `docs/` from the URL; before that a page lived at
    `/docs/<path>/`, a diary post first at `/docs/2009/05/2009-05-21/`, then
    `/docs/2009/05/21/`. Hugo puts aliases below the page's language root (`/en/…`).
    """
    m = DOCS.match(rel)
    if not m or m.group(1) == "_index":  # docs root: never rendered (build.render)
        return []
    d = DIARY.search(rel)
    if d:
        month, stem, _, day = d.groups()
        return [f"/docs/{month}/{stem}/", f"/docs/{month}/{day}/"]
    return [f"/docs/{m.group(1).lower()}/"]


def set_aliases(chunks: list[tuple[str, list[str]]], urls: list[str]) -> bool:
    """Make `aliases` start with `urls`, keep other aliases; return True if it was added."""
    chunk = next((c for c in chunks if c[0] == "aliases"), None)
    current = []
    if chunk:
        current = yaml.safe_load("\n".join(chunk[1])).get("aliases") or []
    wanted = urls + [a for a in current if a not in urls]
    line = "aliases: [" + ", ".join(f'"{a}"' for a in wanted) + "]"
    if not chunk:
        chunks.append(("aliases", [line]))
        return True
    if current != wanted:
        comments = [ln for ln in chunk[1][1:] if ln.lstrip().startswith("#")]
        chunk[1][:] = [line] + comments
    return False


def kind_of(rel: str) -> str:
    if DIARY.search(rel):
        return "diary-en" if rel.startswith("content.en/") else "diary-de"
    return "index" if rel.endswith("_index.md") else "page"


def split_chunks(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Group front matter lines into (key, lines) chunks; comments follow their key."""
    chunks: list[tuple[str, list[str]]] = []
    for line in lines:
        m = KEY.match(line)
        if m:
            chunks.append((m.group(1), [line]))
        elif chunks:
            chunks[-1][1].append(line)
        else:
            raise ValueError(f"line before the first key: {line!r}")
    # `# CHECK location:` lines usually end up after the last key: move them to `location`
    loc = next((c for c in chunks if c[0] == "location"), None)
    if loc:
        for key, chunk in chunks:
            if key == "location":
                continue
            moved = [ln for ln in chunk[1:] if ln.startswith("# CHECK location")]
            for ln in moved:
                chunk.remove(ln)
                loc[1].append(ln)
    return chunks


def normalize(text: str, kind: str, rel: str) -> tuple[str, list[str]]:
    """Return the text with filled and sorted front matter, and the keys that were added."""
    if not text.startswith("---\n"):
        return text, []
    _, front, body = text.split("---\n", 2)
    chunks = split_chunks(front.rstrip("\n").split("\n"))
    present = {k for k, _ in chunks}
    added = []
    defaults = dict(DEFAULTS[kind])
    if kind.startswith("diary"):
        defaults["slug"] = f'"{diary_slug(rel)}"'
    for key, value in defaults.items():
        if key not in present:
            chunks.append((key, [f"{key}: {value}" if value else f"{key}:"]))
            added.append(key)
    urls = old_urls(rel)
    if urls and set_aliases(chunks, urls):
        added.append("aliases")
    rank = {k: i for i, k in enumerate(ORDER)}
    ordered = sorted(chunks, key=lambda c: rank.get(c[0], len(ORDER)))  # stable
    new_front = "\n".join(line for _, chunk in ordered for line in chunk) + "\n"
    return "---\n" + new_front + "---\n" + body, added


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate(rel: str, kind: str, text: str) -> list[str]:
    """Return a list of problems with the front matter of one page."""
    if not text.startswith("---\n"):
        return ["no front matter"]
    front = text.split("---\n", 2)[1]
    try:
        data = yaml.safe_load(front) or {}
    except yaml.YAMLError as error:
        return [f"invalid YAML: {str(error).splitlines()[0]}"]
    problems = [f"missing required key `{k}`" for k in REQUIRED[kind] if k not in data]
    problems += [f"unknown key `{k}`" for k in data if k not in ORDER]
    if "draft" in data and not isinstance(data["draft"], bool):
        problems.append(f"`draft` must be true or false, not {data['draft']!r}")
    for key in ("tags", "categories"):
        value = data.get(key)
        if key in data and not (
            isinstance(value, list) and all(isinstance(v, str) for v in value)
        ):
            problems.append(f"`{key}` must be a list of strings, not {value!r}")
    if kind.startswith("diary"):
        match = DIARY.search(rel)
        day = match.group(3) + match.group(4)[:2]
        written = re.search(r"^date: (\d{4}-\d\d-\d\d)", front, re.MULTILINE)
        if not written or written.group(1) != day:
            problems.append(f"`date` does not match the file name day {day}")
        slug = diary_slug(rel)
        if data.get("slug") != slug:
            problems.append(f"`slug` must be {slug!r}, not {data.get('slug')!r}")
    for url in old_urls(rel):
        if url not in (data.get("aliases") or []):
            problems.append(f"`aliases` must contain {url!r} (old URL)")
    if kind == "diary-en":
        problems += [
            f"`{k}` belongs to the German page only"
            for k in DATASHEET_DE_ONLY & data.keys()
        ]
        if not (ROOT / rel.replace("content.en/", "content/", 1)).exists():
            problems.append("no German twin")
    if kind == "diary-de":
        if not (ROOT / rel.replace("content/", "content.en/", 1)).exists():
            problems.append("no English twin")
        if data.get("travelMode") not in TRAVEL_MODES:
            problems.append(
                f"`travelMode` {data.get('travelMode')!r} not in {sorted(TRAVEL_MODES)}"
            )
        if data.get("mood") not in MOODS:
            problems.append(f"`mood` {data.get('mood')!r} not in {MOODS}")
        if data.get("sleeping") not in SLEEPING | {None}:
            problems.append(
                f"`sleeping` {data.get('sleeping')!r} not in {sorted(SLEEPING)}"
            )
        costs = data.get("costs")
        if costs is not None and not (is_number(costs) and costs >= 0):
            problems.append(f"`costs` must be empty or a number (EUR), not {costs!r}")
        events = data.get("events")
        if events is not None and not (
            isinstance(events, list)
            and all(isinstance(e, str) and e.strip() for e in events)
        ):
            problems.append("`events` must be a list of non-empty strings")
        loc = data.get("location")
        if isinstance(loc, dict):
            lat, lon = loc.get("latitude"), loc.get("longitude")
            if not (is_number(lat) and -90 <= lat <= 90):
                problems.append(f"location.latitude invalid: {lat!r}")
            if not (is_number(lon) and -180 <= lon <= 180):
                problems.append(f"location.longitude invalid: {lon!r}")
            if not loc.get("name"):
                problems.append("location.name is empty")
        elif "location" in data:
            problems.append("`location` must be a mapping with latitude/longitude/name")
        route = data.get("route")
        if "route" in data and not (
            isinstance(route, list)
            and len(route) >= 2
            and all(
                isinstance(p, list) and len(p) == 2 and all(map(is_number, p))
                for p in route
            )
        ):
            problems.append("`route` must be a list of at least two [lat, lon] pairs")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply", action="store_true", help="rewrite files (default: dry run)"
    )
    args = parser.parse_args()

    changed = 0
    all_problems: list[str] = []
    for directory in DIRS:
        for path in sorted((ROOT / directory).rglob("*.md")):
            rel = str(path.relative_to(ROOT))
            kind = kind_of(rel)
            text = path.read_text()
            new, added = normalize(text, kind, rel)
            if new != text:
                changed += 1
                note = f" (adds {', '.join(added)})" if added else ""
                print(("rewrite " if args.apply else "would change ") + rel + note)
                if args.apply:
                    path.write_text(new)
            all_problems += [f"{rel}: {p}" for p in validate(rel, kind, new)]
    print(f"{changed} file(s) {'rewritten' if args.apply else 'would change'}")
    for problem in all_problems:
        print(f"PROBLEM {problem}")
    print(f"{len(all_problems)} problem(s)")
    return 1 if all_problems else 0


if __name__ == "__main__":
    sys.exit(main())
