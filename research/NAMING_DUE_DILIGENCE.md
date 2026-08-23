# Naming Due Diligence Sprint — 2026-08-23

Scope: find a clean name for the vendor-change-monitoring product currently titled "ModelSignal". 41 candidates generated and batch-screened; finalists deep-checked. **All domain and trademark findings are PRELIMINARY automated signals (DNS presence, archive.org history, npm/PyPI/GitHub/HN searches) — not guarantees. Owner must verify via a registrar WHOIS lookup and USPTO TESS / EUIPO search before purchase.**

## Method
1. Batch screen of 41 candidates: exact-name checks on npm registry, PyPI, DNS NS-records for `.com/.ai/.dev/.watch`, plus known-brand knowledge.
2. Survivors deep-dived: GitHub repo/org search API, HN Algolia full-text, npm fuzzy search (catches confusingly similar products), Wayback Machine CDX history per candidate domain, best-effort Reddit/X probes (both bot-limited → manual verification required).

## Rejected candidates and reasons

| Candidate | Reason for rejection |
|---|---|
| bellwether | npm + PyPI packages exist; all probed domains registered |
| weathervane | npm + PyPI taken |
| diffwatch | npm + PyPI taken |
| slippage | npm + PyPI taken |
| tokenledger | all domains taken |
| driftwatch | PyPI package exists |
| errata (standalone) | npm + PyPI taken; errata.dev registered |
| ratebook | PyPI package exists; .com/.ai registered |
| ratecard | .dev registered; generic industry term used by many billing tools |
| overage | PyPI package exists |
| specsheet | PyPI package exists |
| runrate | PyPI package exists |
| trueup | .dev registered |
| **vendordiff** | **Active product at vendordiff.com** — e-commerce restock/price tracker (Wayback capture 2025-07-16: "VendorDiff … Recent Restocks … SKU … Price") |
| **capwatch** | Existing product "CapWatch – Monitor Your Cryptoportfolio" (HN) |
| fineline | 138 GitHub repos; generic phrase |
| repricewatch | "repricing" is a large e-commerce software category (Amazon repricers) → adjacent-audience confusion |
| graceperiod | Generic dictionary term (weak TM distinctiveness); GitHub org taken; existing restaurant brand |
| stickerprice | Common finance phrase (2,397 HN hits); .com taken; GitHub user taken |
| quietchange | GitHub org/user already taken; headline-generic phrase |
| meterwatch | Multiple pre-existing same-name repos including a utility-metering app |
| sunsetwatch, quotascope | Pre-existing zero-star same-name repos; weak distinctiveness |
| eolwatch, planshift, softlimit, usagecap, listprice, billshock, pricetremor, fineprintwatch, lineitem, canarywatch, caveatalone* | Narrow scope, weak brandability, or partial registrations (*caveat standalone unscreened — superseded by CaveatWatch) |

## The five strongest candidates

| | **CaveatWatch** ⭐ recommended | **ErrataWatch** | **RateRegistry** | **ThrottleWatch** | **ModelManifest** |
|---|---|---|---|---|---|
| **Meaning & positioning** | Every AI price ships with an asterisk/caveat; we are the watchdog on those caveats — prices, limits, plan footnotes, terms | "Errata" = the official list of corrections vendors publish; we collect them into one authoritative feed | A permanent, citable registry of published rates & limits; the ledger-of-record angle | You get throttled without notice; we surface throttling/quota changes before they bite | The manifest of what AI vendors ship and change; models, plans, prices |
| **Memorability** | High — vivid word, obvious story, two-beat compound | High — unusual word sticks; slight spelling friction ("errata") | Medium-high — descriptive, less evocative | High — visceral developer pain word | Medium-high — nice alliteration; sounds model-centric only |
| **Collision findings** | npm/PyPI: none · GitHub: 0 repos, org `github.com/caveatwatch` unclaimed · HN: 1 unrelated hit (El Niño story) · Bing/DDG: zero meaningful results · [GH search](https://github.com/search?q=caveatwatch+in%3Aname&type=repositories) | npm/PyPI: none · GitHub: 0 repos, org unclaimed · HN: 0 hits · web: none · Flag: [Errata Security](https://erratasec.com/) (infosec firm) — different field, fuzzy tech-audience adjacency · [GH search](https://github.com/search?q=erratawatch+in%3Aname&type=repositories) | npm/PyPI: none (fuzzy search returns only irrelevant packages) · GitHub: 0 repos, org unclaimed · HN: 2 unrelated · [GH search](https://github.com/search?q=rateregistry+in%3Aname&type=repositories) | npm/PyPI: none · GitHub: 2 zero-star personal repos (noise-level) · HN: 0 · [GH search](https://github.com/search?q=throttlewatch+in%3Aname&type=repositories) | npm/PyPI: none · GitHub: 0 repos, org unclaimed · HN: 2 unrelated · [GH search](https://github.com/search?q=modelmanifest+in%3Aname&type=repositories) |
| **Plausible domains (PRELIMINARY — DNS-based)** | caveatwatch.com/.ai/.dev show no DNS records; caveat.watch has no archive history — verify all four at registrar | erratawatch.ai/.dev no DNS records; erratawatch.com registered (no archived content seen) — verify | rateregistry.dev/.ai no DNS records; .com registered since ≥2002 as dead placeholder (potentially acquirable later) — verify | throttlewatch.dev/.ai no DNS records; **.com status unprobed — verify first** | modelmanifest.dev/.ai no DNS records; .com status unprobed — verify |
| **Risks** | Two-word compound length; "caveat" legal connotation could feel lawyerly if copy is careless | Spelling/pronunciation friction; Errata Security adjacency should be monitored; plural-only word feels odd mid-sentence | Descriptive-but-dry; less story energy in launch posts | Scope reads narrower than product (rate limits ≠ pricing/terms); two trivial repos share the name | Name implies models-only while product covers plans/terms/billing; may need positioning discipline forever |
| **Recommended tagline** | *"Every AI price comes with an asterisk. We watch it."* | *"Official changes, officially recorded."* | *"Published rates, permanently on the record."* | *"Know you're throttled before your users do."* | *"What shipped, what changed, what it costs."* |

## Social handles
X/Twitter and Reddit serve bot-shells from this environment; handles could not be reliably verified automatically. Owner should check @handles for all five candidates on X, Reddit, YouTube, LinkedIn manually before purchase.

## Trademark status
No trademark databases were accessible programmatically (USPTO TESS requires interactive session). Web-search signals showed no same-class brands for any finalist, but this is NOT a clearance opinion. Before purchase, run TESS (tmsearch.uspto.gov) basic-word-mark search on each finalist in classes 9/42, optionally EUIPO TMview for EU.

## Recommendation
**CaveatWatch** — cleanest collision profile across every channel tested, memorable, and the positioning writes itself: AI vendors hide changes in the fine print; CaveatWatch watches the fine print. Backups, in order: **ErrataWatch**, **RateRegistry**.
