#!/bin/bash
# Pre-generates the web copies of all photos, in parallel (rush + ImageMagick + exiftool):
#
#   $SRC/<y>/<m>/<d>/<name>.jpg  ->  assets/images/<y>/<m>/<d>/<name>.webp        (1600 px, q80)
#                                    assets/images/thumb/<y>/<m>/<d>/<name>.webp  (400 px, q65, no metadata)
#
# The originals (print source) live outside the site, default ~/Pictures/hugo-assets-images.
# Hugo reads only the copies in assets/images (large copy = same path as the original, with .webp).
#
# The originals are never touched (source for print). The web copies are upright (rotated by
# Exif orientation, tag reset to 1). The large copies keep all metadata of the original: Exif, GPS, IPTC, XMP
# and the colour profile. WebP has no IPTC block: caption and keywords move to XMP (dc:Description,
# dc:Subject). Only the small preview image embedded in the Exif data is dropped.
# Existing copies that are newer than their original are skipped, so re-runs only take the new
# or changed photos. Copies of removed originals are only reported, never deleted.
#
#   scripts/make-web-images.sh            # all photos
#   scripts/make-web-images.sh --force    # regenerate everything
#   scripts/make-web-images.sh --check    # only report originals without a copy (exit 1), for CI
#   JOBS=4 SRC=... DEST=... scripts/make-web-images.sh
#
# Needs rush, magick (ImageMagick 7) and exiftool-rs (6x faster, same output; falls back to the
# Perl exiftool). Metadata warnings go to $DEST/exiftool-warnings.log, not to the console: minor
# ones (-m) are ignored, e.g. damaged Canon maker notes in some originals; the rest stay in the log.
set -euo pipefail

SRC=${SRC:-$HOME/Pictures/hugo-assets-images}
DEST=${DEST:-assets/images}
JOBS=${JOBS:-$(sysctl -n hw.ncpu 2>/dev/null || nproc)}
EXIFTOOL=${EXIFTOOL:-$(command -v exiftool-rs || command -v exiftool)}
WARNLOG=$DEST/exiftool-warnings.log

# worker: one original -> large + thumb (called by rush, once per photo)
if [[ ${1:-} == --one ]]; then
	src=$2
	base=${src#"$SRC"/}
	base=${base%.*}
	large=$DEST/$base.webp
	thumb=$DEST/thumb/$base.webp
	if [[ ${FORCE:-} != 1 && $large -nt $src && $thumb -nt $src ]]; then exit 0; fi
	mkdir -p "$(dirname "$large")" "$(dirname "$thumb")"
	# written under a temporary name and renamed at the end, so an interrupted run never leaves a
	# copy without metadata that the next run would take for finished
	tmp_large=$large.partial.webp
	tmp_thumb=$thumb.partial.webp
	# one decode for both sizes; the JPEG decoder already shrinks while reading (jpeg:size)
	MAGICK_THREAD_LIMIT=1 magick -define jpeg:size=1400x1400 "$src" -auto-orient -resize '1600x1600>' \
		-quality 80 -define webp:method=4 -write "$tmp_large" \
		-resize '400x400>' -strip -quality 65 -define webp:method=6 "$tmp_thumb"
	# magick does not carry everything over: copy all tags again, pixels are already upright
	# (large copy only: Hugo reads the capture date from it; metadata would double the thumbnail size)
	"$EXIFTOOL" -q -m -overwrite_original -TagsFromFile "$src" -all:all --IFD1:all -Orientation#=1 \
		"-XMP-dc:Description<IPTC:Caption-Abstract" "-XMP-dc:Subject<IPTC:Keywords" "$tmp_large" 2>>"$WARNLOG"
	mv "$tmp_thumb" "$thumb" && mv "$tmp_large" "$large"
	exit 0
fi

# --check: a photo without a copy would silently be missing on the site
if [[ ${1:-} == --check ]]; then
	missing=0
	while read -r f; do
		rel=${f#"$SRC"/}
		rel=${rel%.*}
		if [[ ! -f $DEST/$rel.webp || ! -f $DEST/thumb/$rel.webp ]]; then
			echo "no web copy: $f"
			missing=$((missing + 1))
		fi
	done < <(find "$SRC" -type f \( -iname '*.jpg' -o -iname '*.jpeg' \) | sort)
	echo "$missing photos without web copy"
	[[ $missing == 0 ]]
	exit
fi

FORCE=0
[[ ${1:-} == --force ]] && FORCE=1
export SRC DEST FORCE EXIFTOOL WARNLOG
mkdir -p "$DEST"
touch "$WARNLOG"
warned=$(wc -l <"$WARNLOG")
RUSH=${RUSH:-$(command -v rush || mise which rush)}
SELF=$(cd "$(dirname "$0")" && pwd)/$(basename "$0")

total=$(find "$SRC" -type f \( -iname '*.jpg' -o -iname '*.jpeg' \) | wc -l | tr -d ' ')
echo "$total photos in $SRC, $JOBS parallel jobs$([[ $FORCE == 1 ]] && echo ', --force')"
find "$SRC" -type f \( -iname '*.jpg' -o -iname '*.jpeg' \) | sort | "$RUSH" -j "$JOBS" "'$SELF' --one {}"

echo "web copies: $(find "$DEST" -name '*.webp' -not -path "$DEST/thumb/*" | wc -l | tr -d ' ') large, $(find "$DEST/thumb" -name '*.webp' | wc -l | tr -d ' ') thumb, $(du -sh "$DEST" | cut -f1)"
echo "metadata warnings this run: $(($(wc -l <"$WARNLOG") - warned)) (see $WARNLOG)"
# report copies without original (renamed or deleted photos)
find "$DEST" -name '*.webp' -not -path "$DEST/thumb/*" | while read -r f; do
	rel=${f#"$DEST"/}
	rel=${rel%.webp}
	compgen -G "$SRC/$rel.[jJ][pP]*[gG]" >/dev/null || echo "orphan (original gone): $f"
done
