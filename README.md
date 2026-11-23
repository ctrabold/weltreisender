# Overview

Dieses Repository enthält den Reise-Blog von meiner Radreise von Deutschland nach Singapur in den Jahren 2009 und 2010.

## Setup

```shell
# for maximum cleanups and rebuilds, run where you checked out the repository
hugo server --disableFastRender \
	--cleanDestinationDir=true \
	--logLevel=debug \
	--gc \
	-M
```

## Thanks

- <https://github.com/alex-shpak/hugo-book?tab=readme-ov-file>

## License

The structure, design, and layout of this site is licensed under the **MIT License**.

The content of the site (blog posts and page content) is licensed under a **Creative Commons Attribution** license (you may use it, but must give attribution).

See the [About page](http://christian-trabold.de/about/#content-on-this-site) for details.

```text
Copyright 2026, Christian Trabold
Licensed under CC BY-NC-ND 4.0 License
see <https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en> for details.
```

## FAQ

### How do I fix file dates (to reflect pictures taken dates)

```shell
exiftool -r -d %s -tagsfromfile "%d/%F.json" \
	"-AllDates<photoTakenTimeTimestamp" \
	"-FileCreateDate<photoTakenTimeTimestamp" \
	"-FileModifyDate<photoTakenTimeTimestamp" \
	"-Description<description" \
	"-Caption-Abstract<description" \
	"-GPSLatitude<geoDataLatitude" \
	"-GPSLatitudeRef<geoDataLatitude" \
	"-GPSLongitude<geoDataLongitude" \
	"-GPSLongitudeRef<geoDataLongitude" \
	"-GPSAltitude<geoDataAltitude" \
	-overwrite_original \
	-ext jpg -ext jpeg -ext png -ext mp4 -ext mov .
```

## ===

```shell
exiftool-rs -r -d %s -tagsfromfile "%d/%F.json" \
	"-AllDates<photoTakenTimeTimestamp" \
	"-FileCreateDate<photoTakenTimeTimestamp" \
	"-FileModifyDate<photoTakenTimeTimestamp" \
	"-Description<description" \
	"-Caption-Abstract<description" \
	"-GPSLatitude<geoDataLatitude" \
	"-GPSLatitudeRef<geoDataLatitude" \
	"-GPSLongitude<geoDataLongitude" \
	"-GPSLongitudeRef<geoDataLongitude" \
	"-GPSAltitude<geoDataAltitude" \
	-overwrite_original \
	-ext jpg -ext jpeg -ext png -ext mp4 -ext mov .
```

### How do I update maps after adding or editing location in a post?

1. **Edit the German post's front matter** (`content/docs/...`). The English page takes `location` and `travelMode` from it automatically.
   - New or corrected coordinates: set `location.latitude` / `location.longitude`, plus `name` etc.
   - Travel mode: set `travelMode:` to one of:
     - routed along roads: `bike` (the default), `foot`, `bus`, `car`
     - routed along rivers: `kayak`
     - dashed straight line: `train`, `boat`, `plane`, `unknown`
     - no leg at all: `static`
2. **Recalculate the legs:** `uv run scripts/build_routes.py`.
   - Only legs whose input changed are fetched again from BRouter. That includes the changed post and the **next** post, because its leg starts at the changed location.
   - To check first, use `--dry-run`. To recalculate a single leg, use `--only 2009/06/2009-06-18`.
   - Legs that previously failed are retried automatically.
3. **Watch for stale files:** if a post changes **to** `static`, or now has the same place as the previous post, the script only reports `stale leg file data/routes/...json`. It never deletes anything, so delete that file yourself.
4. **Rebuild or reload:** `hugo server` picks up the change. All three map types use the same data: the post map with its elevation profile, the route map of the whole trip (`/karte/`, `/en/map/`), and the tag page maps.

Posts without `location` don't appear on any map. They get a marker and a leg as soon as you add coordinates and run step 2.
