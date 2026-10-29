# How wrong is your clock?

The gap between legal clock time and solar time for the world's people under the time zone rules of {{meta.year|raw}}: a world map you can tap for any place's sunrise, solar noon and sunset through the year, with stories on Spain and Galicia, western China, India, Argentina, Russia and the UK.

**Interactive version:** https://maps.tristanhotham.com/clock-vs-sun/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23757706

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- Averaged over {{meta.year|raw}}, {{population.e_ann.ahead|pct}} of the world's {{v.world_people_bn|raw}} billion people live where the clock runs ahead of the sun; {{population.e_ann.ahead_30|pct}} by more than half an hour and {{population.e_ann.ahead_60|pct1}} (about {{v.ahead_60_people_m|int}} million) by more than an hour. Only {{population.e_ann.behind_30|pct1}} live where it runs more than half an hour behind. The median gap is {{population.e_ann.median|dur}}.
- Without daylight saving, {{population.e_std.ahead|pct}} would still be ahead; only {{population.dst_share|pct}} of people changed their clocks in {{meta.year|raw}}. On 21 June, {{population.e_jun.ahead_60|pct1}} are more than an hour ahead.
- Of {{countries.n_1m|int}} countries of a million people or more, {{countries.n_1m_ahead|int}} run ahead of the sun on average and {{countries.n_1m_ahead_60|int}} by more than an hour. Spain is furthest ahead ({{country.Spain.e_ann|dur}}), then France ({{country.France.e_ann|dur}}).
- Galicia: the latest sunrise of {{meta.year|raw}} is {{stories.galicia_places.A Coruña.rise_late|raw}} in A Coruña ({{stories.galicia_places.A Coruña.rise_late_date|raw}}), {{stories.galicia_places.Santiago de Compostela.rise_late|raw}} in Santiago de Compostela and {{stories.galicia_places.Vigo.rise_late|raw}} in Vigo, against {{stories.galicia_places.London.rise_late|raw}} in London, {{stories.galicia_places.Madrid.rise_late|raw}} in Madrid and {{stories.galicia_places.Barcelona.rise_late|raw}} in Barcelona. The sun rises after 9:00 on {{stories.galicia_places.A Coruña.days_rise_after_9|int}} days in A Coruña. Among {{stories.europe_s55_n|int}} European cities of 100,000 or more south of 55 degrees north, only Brest has a later winter sunrise. Porto, at Vigo's longitude on UK time, has its latest sunrise at {{stories.galicia_places.Porto.rise_late|raw}}.
- Single national clocks give the biggest city gaps: Kashgar {{stories.china.kashgar.e_std|dur}} ahead on Beijing time ({{stories.china.kashgar_xinjiang_time_e_std|dur}} on informal Xinjiang time); Tinsukia, Assam, {{stories.india.east.e_std|dur}} behind on India Standard Time.
- UK: from {{stories.uk.lowestoft.e_std|dur}} behind the sun in Lowestoft to {{stories.uk.west_ni.e_std|dur}} ahead in Enniskillen (winter clock).

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page (Leaflet). Loads `data/page.json`, `data/zgrid.png`, `data/borders.json`, `data/tzlines.json`, `data/hills.png`. |
| `header.png` | Social card (1200 by 630). |
| `data/zgrid.png` | Time zone index on a 0.1 degree grid, 85N to 60S (3600 by 1450 pixels; index + 1 = red + 256 × green, 0 = no zone). ODbL. |
| `data/page.json` | Zone list with the clock offset on each change date of {{meta.year|raw}}, the place list for search and names, and the Galicia chart series. |
| `data/tzlines.json` | Simplified lines where the clock changes between neighbouring zones. ODbL. |
| `data/borders.json` | Natural Earth 1:50m country outlines, simplified. |
| `data/hills.png` | Hill shading (AWS Terrain Tiles), shared with other studies on the site. |
| `data/places.csv` | GeoNames places of 10,000 or more (the full {{meta.places_used|int}} places of 1,000 or more are in `data/places_1000.csv.gz`): zone (boundaries and GeoNames), standard offset, gap in minutes (no daylight saving, year average, 21 June, 21 December) and {{meta.year|raw}} sun times (latest and earliest sunrise with day of year, sunset, solar noon, days with sunrise after 9:00 and 8:30, sunset after 22:00). Times are minutes after local midnight. |
| `data/countries.csv` | Population-weighted gaps by country (Kontur hexagons), with ranges from places. |
| `data/zones.csv` | Each zone's standard and official offset, offsets on 21 June and 21 December, and whether it changes in {{meta.year|raw}}. ODbL. |
| `data/population_by_offset.csv` | Share of the world's people in 15 minute bands of the gap. |
| `data/results.json` | Every number used anywhere. |
| `code/common.py` | Paths and the NOAA sun equations. |
| `code/01_prepare.py` | Reads the zone polygons, the IANA rules for every day, Kontur population and GeoNames places; writes `work/` intermediates (zone offsets, 0.1 degree grid, hexagons and places with zones). |
| `code/02_analyse.py` | All statistics, sun times for every place and day, stories and rankings. |
| `code/03_page_data.py` | Page data files. |
| `code/04_build_site.py` | Derived numbers, checks of facts stated in words, and `index.html` from `code/page_template.html`. |
| `code/05_figures.py`, `code/06_header.py` | Figures for the paper and blog; social card. |
| `code/07_paper.py` | Paper PDF from `code/paper_template.tex` with xelatex. |
| `code/08_release.py` | Blog post, blog and Zenodo metadata, Zenodo folder, this README. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Gap.** Clock offset from UTC minus 4 minutes per degree of longitude east (mean solar time), folded into plus or minus 12 hours. Year average: mean of the offset in force at local midday on each day of {{meta.year|raw}}. No daylight saving: the smaller of the offsets on 15 December {{meta.year|raw}} and 15 June 2027 (rules as at the end of {{meta.year|raw}}).
- **Legal time.** Xinjiang (tz `Asia/Urumqi`, UTC+6, informal Xinjiang time) is given Beijing time, China's legal time; the informal alternative is reported.
- **Sun times.** NOAA solar calculator equations (Meeus), upper limb on a flat horizon (sun centre 0.833 degrees below), including the equation of time; within a minute of the astral package.
- **People.** Kontur Population H3 resolution 4 hexagons (about 22 km), placed in the zone containing their centre. Countries from Natural Earth 1:10m.

## Known limits

- Clock gaps, not lived time: schools, shops and offices may adapt their hours. Informal local times (Xinjiang above all) are not the main measure.
- Zone polygons follow OpenStreetMap and can be wrong in detail. On the page they are stored on a 0.1 degree grid, so taps within a few km of a zone boundary can land in the neighbouring zone.
- Hexagons on borders take their centre's zone. GeoNames coordinates and populations contain errors and duplicate districts.
- Flat horizon at sea level. Rules describe {{meta.year|raw}} only; Morocco and some Canadian provinces changed during the year.

## Sources and licences

- Time zone boundaries: Evan Siroky, timezone-boundary-builder, release 2026a, https://github.com/evansiroky/timezone-boundary-builder. Open Database License 1.0, built from OpenStreetMap data © OpenStreetMap contributors.
- Time zone rules: IANA time zone database {{meta.tz_version|raw}} (public domain), via the Python `tzdata` package.
- Population: Kontur Population, 22 km H3 hexagons, release 1 November 2023, https://data.humdata.org/dataset/kontur-population-dataset-22km. CC BY 4.0.
- Places: GeoNames cities1000, retrieved {{meta.geonames_retrieved|raw}}, https://download.geonames.org/export/dump/. CC BY 4.0.
- Country outlines: Natural Earth 1:10m and 1:50m (public domain).
- Solar equations: NOAA Global Monitoring Laboratory solar calculator, https://gml.noaa.gov/grad/solcalc/ ; Meeus, J. (1998) Astronomical Algorithms.
- Page base map tiles (optional) © Esri; hill shading from AWS Terrain Tiles.

Text, figures and derived data: CC BY 4.0, except `data/zgrid.png`, `data/tzlines.json` and `data/zones.csv` (ODbL 1.0, derived from timezone-boundary-builder). Code: MIT (see `LICENSE`).

## How to rerun

Inputs are read in place from `CVS_SRC` (default `/home/claude/hist/_data18/clock-vs-sun`: `timezones.geojson.zip`, `kontur_population_20231101_r4.gpkg.gz`, `cvs_geonames_cities1000.json.gz`, a reduced copy of GeoNames cities1000 with id, name, coordinates, feature code, country, admin1, population and time zone) and `NE_DIR` (Natural Earth GeoJSON). Python 3 with numpy, pandas, shapely 2, h3, tzdata, Pillow and matplotlib; xelatex for the paper.

```
python3 code/01_prepare.py
python3 code/02_analyse.py
python3 code/03_page_data.py
python3 code/04_build_site.py
python3 code/05_figures.py
python3 code/06_header.py
python3 code/07_paper.py
python3 code/08_release.py
```

## Citation

Hotham, T. (2026) How wrong is your clock? Clock time against solar time for the world's people in 2026. https://doi.org/10.5281/zenodo.23757706

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
