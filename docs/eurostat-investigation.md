# Eurostat datasource investigation

Verified against the live Statistics API on 11 October 2026. These are observations from this investigation, not guarantees about future availability.

## Curated dataset mappings

| Measure | Dataset | Fixed dimensions | Article |
| --- | --- | --- | --- |
| Nominal GDP | `nama_10_gdp` | `freq=A`, `unit=CP_MEUR`, `na_item=B1GQ` | National accounts and GDP |
| Population on 1 January | `demo_gind` | `freq=A`, `indic_de=JAN` | Population and population change statistics |
| Annual unemployment rate | `une_rt_a` | `freq=A`, `unit=PC_ACT`, `age=Y15-74`, `sex=T` | Unemployment statistics |

Greece uses Eurostat geography code `EL`, not ISO `GR`. Dataset titles and article URLs live in `backend/app/catalog.py`. Article associations are curated; an article may discuss other datasets and units too. GDP directly references nama_10_gdp; the population article directly references demo_gind. The unemployment article currently references monthly une_rt_m: our annual une_rt_a is an explicitly labeled companion dataset, not an assertion that the article’s monthly figures are annual values.

## Working requests

Base: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/`

- `nama_10_gdp?geo=EL&unit=CP_MEUR&na_item=B1GQ&freq=A&sinceTimePeriod=2016`
- `demo_gind?geo=EL&indic_de=JAN&freq=A&sinceTimePeriod=2016`
- `une_rt_a?geo=EL&unit=PC_ACT&age=Y15-74&sex=T&freq=A&sinceTimePeriod=2016`

All three returned HTTP 200. GDP and unemployment returned ten annual observations for 2016–2025; demo_gind returned eleven observations for 2016–2026. The initially tested GDP, demo_pjan and unemployment responses reported update times of 9 October, 25 September, and 10 September 2026. Population was then switched to demo_gind to match the actual article reference. GDP uses million euros at current prices. Population counts persons. Unemployment measures percent of the labour force, ages 15–74, both sexes.

A live request for Greece GDP produced 174448.2 million euros in 2016 and 248353.7 million euros in 2025; the latter carried flag `p`. These examples are validation evidence and are not hardcoded application data.

## JSON-stat decoding

The response contains `id`, `size`, `dimension`, `value`, and optionally `status`. Dimension order determines row-major flattened positions. Category indexes may be objects mapping code to position, or arrays. Values and flags may be sparse objects or arrays. Missing values remain null; zero is a real value. Decode every dimension, check fixed filters, reject unresolved dimensions, and then select the requested years. Do not assume an observation's array position is its year.

“Last ten years” defaults to ten consecutive years ending in the latest non-missing annual observation. “Last ten calendar years” selects the ten complete calendar years before the current UTC year. Missing observations inside either interval remain gaps. Eurostat observations can be provisional or revised; raw flags and source update time are retained.

## Article ingestion

Fetch each article over HTTPS, select `.mw-parser-output`, remove scripts, navigation, and edit controls, then create overlapping text chunks. Keep article URL, dataset association, kind, chunk ID, and ingestion time. Live ingestion initially created 43 article chunks plus three metadata records. PostgreSQL stores text and provenance; Qdrant stores vectors and payloads. Dataset metadata and article chunks are retrieved separately so long articles cannot displace metadata.

The local semantic model is FastEmbed's published all-MiniLM-L6-v2 ONNX distribution (384 dimensions). It needs access to `storage.googleapis.com` for the initial download. Optional OpenAI embeddings use `text-embedding-3-small` with 1536 dimensions; separate indexes prevent mixing vector spaces. Explicit lexical mode exists for connectivity troubleshooting and is labeled in API/UI responses. It is not semantic search.

## Remaining investigation

The Statistics API was exercised. SDMX APIs for automatic codelist discovery and coverage enumeration have not been verified yet. The current prototype intentionally uses curated filters and a limited country set instead of claiming full Eurostat metadata discovery. Future work should verify SDMX metadata responses, version mappings, multilingual article ingestion, and dataset changes before broadening scope.
