# Glossary German → British English

Reference for translating `content/` into `content.en/`. Tags are mapped 1:1 so they can be
reverted or changed with search and replace (e.g. `rg -l '"Travel"' content.en`).
Add new mappings here before using a new tag or term.

## Tags

Tags are maintained by `scripts/update_tags.py` (German source, English derived from its
`TAG_EN` table — keep that table and this one in sync). `Reise`/`Travel` and `Reiseberichte`/`Travel Reports` were
removed. `Blog` marks public posts (as opposed to private diary entries). Country tags follow `location.country`; place tags mark major stops
(posts within 30 km, Guangxi by province, plus a few retrospective posts).

| German      | English        | Kind    | Note                        |
| ----------- | -------------- | ------- | --------------------------- |
| Deutschland | Germany        | country |                             |
| Österreich  | Austria        | country | test ride 2007              |
| Ungarn      | Hungary        | country | test ride 2007              |
| Tschechien  | Czech Republic | country | name used in 2009           |
| Polen       | Poland         | country |                             |
| Ukraine     | Ukraine        | country |                             |
| Russland    | Russia         | country |                             |
| Kirgistan   | Kyrgyzstan     | country |                             |
| China       | China          | country | also for Hong Kong posts    |
| Laos        | Laos           | country |                             |
| Kambodscha  | Cambodia       | country |                             |
| Thailand    | Thailand       | country |                             |
| Malaysia    | Malaysia       | country |                             |
| Singapur    | Singapore      | country |                             |
| Dieburg     | Dieburg        | place   | start and finish            |
| Wien        | Vienna         | place   | test ride 2007              |
| Budapest    | Budapest       | place   | test ride 2007              |
| Prag        | Prague         | place   |                             |
| Krakau      | Kraków         | place   |                             |
| Bischkek    | Bishkek        | place   |                             |
| Kaschgar    | Kashgar        | place   |                             |
| Xining      | Xining         | place   |                             |
| Chengdu     | Chengdu        | place   |                             |
| Hongkong    | Hong Kong      | place   |                             |
| Guangzhou   | Guangzhou      | place   |                             |
| Guangxi     | Guangxi        | place   | province (Guilin, Yangshuo) |
| Kunming     | Kunming        | place   |                             |
| Phnom Penh  | Phnom Penh     | place   |                             |
| Bangkok     | Bangkok        | place   |                             |
| Kota Bharu  | Kota Bharu     | place   |                             |

Only country and place tags are in use. Topics (`Mindset`, `Essen`, `Meilenstein`) are categories.

## Categories

Kinds of posts, not topics (moved from tags by `scripts/update_tags.py`, `TAG_TO_CATEGORY` /
`CATEGORY_EN`).

| German      | English   | Note                                                 |
| ----------- | --------- | ---------------------------------------------------- |
| Blog        | Blog      | public post (was a tag)                              |
| Tagebuch    | Diary     | private diary entry (was a tag)                      |
| Orga        | Planning  | planning and organisation (tag `Orga`/`orga` merged) |
| Fun         | Fun       | was tag `fun`                                        |
| Meilenstein | Milestone | was tag `erfolg`                                     |
| Essen       | Food      | was tag `Essen`                                      |
| Mindset     | Mindset   |                                                      |
| equipment   | equipment |                                                      |
| travel      | –         | legacy, only `posts/2017-01-29-…` (German only)      |

## Datasheet and events

Labels and fixed values of the day datasheet (moods, accommodation, weather, compass, travel
modes) are translated once in `i18n/de.toml` / `i18n/en.toml`; keep both files key by key in
sync. Only `events` is free text in the front matter of both language versions, starting with
its emoji:

| German                           | English                         |
| -------------------------------- | ------------------------------- |
| 🕌 Ramadan                       | 🕌 Ramadan                      |
| 🌙 Ende des Ramadan (Id al-Fitr) | 🌙 End of Ramadan (Eid al-Fitr) |
| 🎄 Weihnachten                   | 🎄 Christmas                    |
| 🧧 Chinesisches Neujahr          | 🧧 Chinese New Year             |
| 🏮 Laternenfest                  | 🏮 Lantern Festival             |
| 🎉 Couchsurfing Meeting          | 🎉 Couchsurfing meetup          |

## Sections and file names

Non-date pages get English file and directory names. Both language versions share a
`translationKey` so Hugo links them as translations.

| German path                                 | English path                                   | `translationKey`         |
| ------------------------------------------- | ---------------------------------------------- | ------------------------ |
| `posts/2025-11-01-schlagworte.md`           | `posts/2025-11-01-tags.md`                     | `tags`                   |
| `docs/vorbereitung/_index.md`               | `docs/preparation/_index.md`                   | `preparation`            |
| `docs/vorbereitung/vorfahrt.md`             | `docs/preparation/before-departure.md`         | `vorfahrt`               |
| `docs/vorbereitung/risiko-management.md`    | `docs/preparation/risk-management.md`          | `risiko-management`      |
| `docs/rueckblick/_index.md`                 | `docs/looking-back/_index.md`                  | `looking-back`           |
| `docs/rueckblick/danke.md`                  | `docs/looking-back/thanks.md`                  | `danke`                  |
| `docs/rueckblick/elektronik-beim-reisen.md` | `docs/looking-back/electronics-on-the-road.md` | `elektronik-beim-reisen` |
| `docs/rueckblick/erfahrungen.md`            | `docs/looking-back/experiences.md`             | `erfahrungen`            |
| `docs/rueckblick/reise-faq.md`              | `docs/looking-back/travel-faq.md`              | `reise-faq`              |
| `docs/rueckblick/weiterfahrt.md`            | `docs/looking-back/moving-on.md`               | `weiterfahrt`            |

Diary posts keep their date-based file names (`2009-11-14`) in both languages and need no
`translationKey`.

Section titles of the 2007 test ride (same paths in both languages): `docs/2007/_index.md`
Vorgeschichte → Prequel, `docs/2007/09/_index.md` Testfahrt nach Budapest → Test ride to Budapest.

## Terms

| German                             | English                                                              | Note                                  |
| ---------------------------------- | -------------------------------------------------------------------- | ------------------------------------- |
| Ort / GPS                          | Place / GPS                                                          | rendered by template (`i18n/*.toml`)  |
| Rondolf                            | Rondolf                                                              | name of the bicycle, never translated |
| Radweg                             | cycle path                                                           |                                       |
| Zeltplatz/Campingplatz             | campsite                                                             |                                       |
| Nachtzug / Nachtbus                | night train / night bus                                              |                                       |
| Platten                            | puncture                                                             |                                       |
| Inbusschlüssel                     | Allen key                                                            |                                       |
| Westler                            | Westerner                                                            |                                       |
| Herberge, Hostel                   | hostel                                                               |                                       |
| Visum verlängern                   | extend the visa                                                      |                                       |
| Risikoliste                        | risk list                                                            | anchor `#risk-list`                   |
| Taschen (am Rad)                   | panniers                                                             |                                       |
| Klopapier                          | loo roll                                                             |                                       |
| Auslandskrankenkasse               | travel health insurance                                              |                                       |
| Auswärtiges Amt                    | German Foreign Office                                                |                                       |
| ADFC                               | ADFC (the German cyclists' association)                              | explain on first mention              |
| Selbstreise Handbuch               | Selbstreise Handbuch (a German handbook on independent travel)       |                                       |
| Deutsche Zentrale für Globetrotter | Deutsche Zentrale für Globetrotter (German centre for globetrotters) |                                       |
| sich einen Wolf fahren             | get saddle sore                                                      |                                       |
| Hup-Schutz                         | horn protection                                                      |                                       |

Links to German-only pages from English pages use `{{% relref path="…" lang="de" %}}`; drop
`lang="de"` once the target is translated.

## Diary terms

Collected while translating the diary (2009–2010). Proper names stay German with a short
explanation on first mention.

| German                           | English                                                |
| -------------------------------- | ------------------------------------------------------ |
| Weltenpummler                    | globe-pedaller                                         |
| Packtaschen / Low-Rider          | panniers / low-riders (front panniers)                 |
| Regenmontur, Regensachen         | rain gear, waterproofs                                 |
| Überschuhe                       | overshoes                                              |
| Kompressions-Beutel              | compression sack                                       |
| Hobo (Kocher)                    | hobo stove                                             |
| Platzwart                        | (campsite) warden                                      |
| Pension                          | guesthouse                                             |
| Herbergsvater                    | guesthouse owner                                       |
| Landstraße / Standstreifen       | country road / hard shoulder                           |
| LKW                              | lorry                                                  |
| Radwegnummer                     | (numbered) cycle route                                 |
| Bergwertung / gepunktetes Trikot | King of the Mountains / polka-dot jersey               |
| Mann mit dem Hammer              | hit the wall                                           |
| innerer Schweinehund             | inner couch potato                                     |
| Snakebite                        | snakebite (puncture)                                   |
| Schmodderwege                    | muddy tracks                                           |
| grüne Grenze                     | "green border" (open border)                           |
| Brotzeit                         | picnic                                                 |
| Radler                           | shandy                                                 |
| Schampus                         | bubbly                                                 |
| Rauchbier                        | smoked beer (_Rauchbier_, a Bamberg speciality)        |
| Schäufele                        | Schäufele (Franconian roast pork shoulder)             |
| Fleischpflanzerl                 | Fleischpflanzerl (Bavarian meatballs)                  |
| Schweinsöhrchen                  | palmiers (pig's-ear biscuits)                          |
| Kwas / квас                      | kvass                                                  |
| Kumis                            | kumis (fermented mare's milk)                          |
| Lagman, Manti                    | lagman, manti (dumplings)                              |
| Tea Tarik                        | teh tarik                                              |
| Gastiniza                        | gostinitsa (guesthouse)                                |
| Magazin (Laden)                  | magazin (shop)                                         |
| Babuschka                        | babushka (granny)                                      |
| STOI!                            | STOI! ("Stop!")                                        |
| SOM                              | som                                                    |
| Farang / Falang                  | farang (Westerner)                                     |
| Sabei-Dii                        | Sabaidee                                               |
| "*TAN"-Länder                    | "-stan" countries                                      |
| Hardsleeper / Sleeper-Bus        | hard sleeper / sleeper bus                             |
| Dschungel-Express                | Jungle Railway                                         |
| Fahrsteig                        | moving walkway / travelator                            |
| ORS-Lösung                       | rehydration salts                                      |
| Bankomat                         | cash machine                                           |
| Plumsklo                         | long-drop                                              |
| Altglascontainer                 | bottle bank                                            |
| Mundschutz                       | face mask                                              |
| Lichthupe                        | flashing headlights                                    |
| Junggesellenabschied             | stag do                                                |
| Silvester                        | New Year's Eve                                         |
| Weihnachtsmann / Nikolausstiefel | Father Christmas / St Nicholas boots                   |
| Tuba-Mukke                       | oompah music                                           |
| Tatort                           | _Tatort_ (Germany's cult Sunday-night crime series)    |
| Stromberg                        | Stromberg (a German TV comedy)                         |
| THW                              | THW (Germany's federal disaster relief agency)         |
| Globetrotter (Laden)             | Globetrotter (a German outdoor shop)                   |
| Kauderwelsch                     | Kauderwelsch (a German phrasebook series)              |
| Heidepark                        | Heide Park, the theme park in northern Germany         |
| Glasperlenspiel                  | Hesse's _The Glass Bead Game_                          |
| "et läuft!" (Kölsch)             | kept, glossed "as they say in Cologne … it's rolling!" |
| Hessisch ("ebbes Uffjerescht")   | kept, glossed ("a bit excited")                        |

### Test ride 2007

| German                      | English                                                       |
| --------------------------- | ------------------------------------------------------------- |
| Vesper                      | _Vesper_ (a hearty Swabian cold supper), glossed on first use |
| Kaiserschmarren             | _Kaiserschmarrn_ (shredded sweet pancake)                     |
| Tacho / KM Stand            | bike computer / odometer                                      |
| Schontag                    | rest day                                                      |
| Daten (section heading)     | Stats                                                         |
| Lipizaner                   | Lipizzaners                                                   |
| Touri-Hochburgen            | tourist hotspots                                              |
| West Bahnhof / Ostbahnhof   | Westbahnhof / Keleti, the East station                        |
| Gellért-Bad                 | Gellért Baths                                                 |
| "<3 lich" (herzlich)        | "<3-warming" (heart-warming)                                  |
| Regenfahrt (Regensburg pun) | kept as a pun, glossed: _Regen_ is German for rain            |
| SK                          | Slovakia (SK)                                                 |

### Place names

Krakau → Kraków, Karlsbad → Karlovy Vary (Karlsbad), Plzen → Plzeň, Eger → Ohře (Eger),
Moldawien → Moldova, Zywiec → Żywiec, Kerč' → Kerch, Bachčisaraj → Bakhchysarai,
Sebastopol → Sevastopol, Jalta → Yalta, Alušta → Alushta, Cimljansk → Tsimlyansk,
Jalalabat → Jalal-Abad, Guelchoe → Gulcha, Irkeschtam → Irkeshtam, Huatogou → Huatugou,
Gangcha → Gangca, Yuangsho → Yangshuo, Katie → Kratie.

## Style

- Write like a native British travel blogger, not a literal translation: idiomatic phrasing,
  natural word order, contractions ("I'm", "it's"), punchy short sentences where the German is
  punchy. Meaning and facts stay exact; wording may change freely (e.g. "Dank!" → "Cheers!",
  "verkatert" → "a bit worse for wear").
- British spelling and vocabulary (travelled, colour, organise, metres, puncture, mobile phone).
- Add the country to lesser-known towns on first mention in a post, e.g. "Dennis from Kiel,
  Germany". Not needed for well-known cities (Budapest, Bangkok) or places in the country the
  post is set in (Leshan in a China post).
- Briefly explain German-specific things where English readers would be lost (e.g. "Rondolf,
  my bike", "a proper German-style _Aufguss_").
- Dates: `Samstag, 14 November 2009` → `Saturday, 14 November 2009`; `14. November` → `14 November`.
- Keep the informal, ironic first-person voice and the present tense of the diary entries.
- German "Du/Dich/Dir" addressed to the reader becomes "you".
- Keep place names, Chinese/Cyrillic names, quotes in other languages, links, image paths and
  shortcodes unchanged. Local German references (e.g. Cologne's "Flotte") stay and keep the
  explanation the author gives.
- Author notes such as `TODO ct …` are copied verbatim, not translated.
- English files do not repeat `location`, `travelMode` or `# CHECK` comments (the German page is
  the single source) and do not include the hand-written `Ort:` / `GPS:` footer.
