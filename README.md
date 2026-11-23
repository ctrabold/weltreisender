# Overview

Dieses Repository enthält den Reise-Blog von meiner Radreise von Deutschland nach Singapur in den Jahren 2009 und 2010.

## Setup

```shell
# for maximum cleanups and rebuilds, run where you checked out the repository
hugo server --printPathWarnings \
            --disableFastRender \
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

# ===

```shell
. "$HOME/.cargo/env"

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
