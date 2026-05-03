# ARCHITECTURE.md

*Autobahn world architecture. Based on [KAI HACKS AI Architecture](https://kaihacks.ai/architecture.html).*

*This document describes the architecture decisions for the Autobahn world.*

---

## General

### Title

Each file opens with a `# Title` - the name of the place, road, or construct it represents.

---

### Owner

Each file has a `## Owner` block. It anchors the file to the world and identifies its structural parent.

---

### Sections

Every file contains the following sections in this fixed order: `Owner`, `Shown`, `Holds`, `Offers`, `Withheld`. No section may be omitted or reordered.

---

### Footer

Every file closes with a version footer: `vX.Y.Z - KAI Worlds`.

---

### Version

Versioning follows semantic versioning: `major.minor.patch`.

File footer versions and release tag versions are separate concerns:

- **File footer patch** - incremented by an LLM for content edits to a single file (corrections, additions, rewrites within one place). Does not require a release.
- **Patch release** - a GitHub release tag bump (`v0.1.X`). No file footer changes. User-triggered.
- **Minor release** - bumps all file footers world-wide via `scripts/bump_version.py --minor`, then PR + tag.
- **Major release** - bumps all file footers world-wide via `scripts/bump_version.py --major` for structural changes, then PR + tag.

All releases (patch, minor, major) are user-triggered.

---

### Encoding

Files are UTF-8, no byte-order mark.

---

### Filenames

All filenames use ASCII characters only. Underscores separate words. No hyphens or special characters (ü, ö, ä, etc.). Every file basename in the world is unique.

**Pattern:** `{type}_{descriptor}.md` where descriptor uses underscores to separate words and ASCII characters only:
- `place_a1_hamburg_zentrum.md` ✓ (ASCII lowercase, underscores)
- `piece_federal_motorway_network.md` ✓ (ASCII lowercase, underscores)
- `persona_hans_christoph_seebohm.md` ✓ (ASCII lowercase, underscores)
- `place_a1_hamburg-zentrum.md` ✗ (hyphen not allowed)
- `piece_federal-motorway-network.md` ✗ (hyphen not allowed)
- `place_strasse_muenchen.md` ✗ (ü/ö/ä not allowed; use ascii equivalents or spell out)

The deployer (`scripts/deploy.py`) asserts uniqueness of basenames across the entire bundle and resolves all links by basename. Filename validation is enforced by `scripts/validate_general.py`.

---

## Roads

A road and all its child places are modelled using the Place component from KAI HACKS AI Architecture. The road index is a Place that holds Places.

Every road has its own folder at `roads/<road>/`. The road index file lives in this folder alongside its nodes, rest stops, and passages.

It holds child places in sequence along a kilometre chain. Each child place is a specific point or stretch on the road, connected to its neighbours and to the road that contains it. The result is a directed graph - each Place a node, the kilometre chain the edge set, direction encoded in the sequence.

Road index files carry only `- Project: Autobahn` in Owner. Node files carry: `- Place: [Road](place_road.md) in [Bundesland](place_bundesland.md)` - the road index as structural parent, the bundesland as geographic container.

### Index

A road index is the parent file for a motorway. It holds the complete kilometre chain - every stop type in sequence, each entry linking to its child file.

**Shown** is what the driver experiences without leaving - the road as a physical whole.

**Holds** is the kilometre chain. Each entry carries the kilometre marker and a link to the child place. Order follows the road's defined direction from its starting terminus.

**Offers** is what the road makes available - its connections and destinations.

**Withheld** is what requires leaving the road to find - what the road passes but does not show.

**Naming:** `roads/{road}/place_{road}.md`

---

### Exit

The stretch of motorway between two adjacent stops, experienced from the carriageway.

**Shown** is what the driver sees without leaving - the road, the sign, the landscape passing.

**Holds** carries the kilometerstein position and navigation links to the adjacent stops on the same road.

**Offers** is the exit ramp - the active choice to leave the motorway.

**Withheld** is what requires seeking - specific, geographical, not visible from the carriageway.

**Naming:** `place_{road}_{name}.md`. Where the exit has an official number, it precedes the name: `place_{road}_{number}_{name}.md`

---

### Junction

A point where two or more motorways meet.

A junction connecting N motorways is described in N files - one per road, from that road's vantage. Each road owns its own view of the junction. Filenames are road-prefixed and unique by basename; cross-links between the per-road junction files are not required.

**Shown** is what the driver sees approaching - the junction infrastructure, the signs, the branching ahead.

**Holds** carries the kilometerstein position and navigation links to the adjacent stops on the same road.

**Offers** is the connecting motorways - the active choice to switch roads.

**Withheld** is what requires seeking - specific, geographical, not visible from the carriageway. Most junctions have no direct exit to the ordinary road; what is withheld requires leaving at an adjacent stop.

**Naming:** `place_{road}_{name}.md`. Where the junction has an official number, it precedes the name: `place_{road}_{number}_{name}.md`

---

## Rest Stop

### Motorway Rest Area

Rastplatz. Parking and basic facilities only. No fuel, no food. Directly on the motorway.

**Shown** is what the driver sees from the carriageway - the sign and the pull-off.

**Holds** carries the kilometerstein position and navigation links to the adjacent stops on the same road.

**Offers** is parking and basic facilities.

**Withheld** is what requires seeking - specific, geographical, not visible from the carriageway.

**Naming:** `place_{road}[_{NN}]_rest_{name}.md` — road prefix mandatory; exit number `NN` (zero-padded two digits) included only if an official AS-number exists for this stop.

---

### Motorway Service Area

Raststätte. Restaurant and hotel complex. No fuel. Directly on the motorway. In practice typically modelled as part of a Roadhouse rather than as a standalone type.

**Shown** is what the driver sees from the carriageway - the sign and the pull-off.

**Holds** carries the kilometerstein position and navigation links to the adjacent stops on the same road.

**Offers** is food, accommodation, and parking.

**Withheld** is what requires seeking - specific, geographical, not visible from the carriageway.

**Naming:** `place_{road}[_{NN}]_service_{name}.md` — road prefix mandatory; exit number `NN` (zero-padded two digits) included only if an official AS-number exists for this stop.

---

### Roadhouse

Rasthof. Full services directly on the motorway. Fuel, food, parking.

**Shown** is what the driver sees from the carriageway - the sign and the pull-off.

**Holds** carries the kilometerstein position and navigation links to the adjacent stops on the same road.

**Offers** is fuel, food, and parking.

**Withheld** is what requires seeking - specific, geographical, not visible from the carriageway.

**Naming:** `place_{road}[_{NN}]_roadhouse_{name}.md` — road prefix mandatory; exit number `NN` (zero-padded two digits) included only if an official AS-number exists for this stop.

---

### Truck Stop

Autohof. Full services off the motorway, accessed via an exit.

**Shown** is what the driver sees at the adjacent exit - the sign indicating the truck stop.

**Holds** carries the position reference and a link to the adjacent exit.

**Offers** is fuel, food, parking, and typically overnight facilities.

**Withheld** is what requires seeking - specific, geographical, not visible from the carriageway.

**Naming:** `place_{road}_truckstop_{name}.md`

---

## Passage

### Tunnel

The motorway passes underground. No exits within. Entry and exit are the only choices.

**Shown** is what the driver sees and experiences inside - walls, lighting, the changed acoustics, the length.

**Holds** carries the kilometerstein position and navigation links to the adjacent stops on the same road.

**Offers** is the passage. No alternative exists from within.

**Withheld** is what lies above - specific, geographical, not visible from the carriageway.

**Naming:** `place_{road}_tunnel_{name}.md`

---

### Bridge

A significant crossing where the motorway passes over (or under) an obstacle. Water, rail, or another road.

**Shown** is what the driver sees from the carriageway - the crossing, the height, what is briefly visible below or above.

**Holds** carries the kilometerstein position and navigation links to the adjacent stops on the same road.

**Offers** is the passage.

**Withheld** is what the crossing reveals briefly and then removes - what is visible only at the moment of crossing.

**Naming:** `place_{road}_bridge_{name}.md`

---

### Border Crossing

The point where the motorway crosses a national border. The road continues; the number changes.

**Shown** is what the driver sees at the transition - signage, former control infrastructure, the unmarked line.

**Holds** carries the kilometerstein position, the link to the first stop on the same road, and the reference to the continuing road across the border.

**Offers** is entry to the connecting road network across the border.

**Withheld** is what the border historically meant - what crossed here before Schengen, what the infrastructure was built for.

**Naming:** `place_{road}_border_{name}.md`

---

## Deployment

The world deploys flat to Claude.ai: every file lands in one folder. Build a deployable bundle with `scripts/deploy.py <manifest>`:

```
python scripts/deploy.py autobahn.md                            # all-bundle
python scripts/deploy.py roads/a7/place_a7.md                   # per-road bundle
python scripts/deploy.py states/place_schleswig_holstein.md     # per-state bundle
```

The bundle is exactly the manifest plus every `*.md` file linked from it. Single-hop closure: links from inside bundled files are not followed. The manifest is the source of truth - if a deployment needs the world frame (`instructions.md`, `stack.md`, the engine pieces, personas, vehicles, props), the manifest must link to them. The frame is a choice.

The deployer asserts every basename in the bundle is unique, rewrites every internal link to its bare filename, and emits `dist/<derived>.zip`. Cross-bundle links (a bundled file linking to a target outside the bundle) are warned by default; `--strict` upgrades the warning to a failure.

The road index files in `roads/<road>/`, the state files in `states/`, and `autobahn.md` at the repo root are the manifests authors maintain. Adding a new deployment scope means adding a new manifest file at the appropriate path.

The single author-facing rule: **every file basename in the world is unique**.

---

## To document

- **Geographic coordinates** - each place node to carry latitude, longitude, and altitude (from OSM or BASt sources). Enables geographic validation: compass directions verified against bearing, distances against geodetic calculations, elevation changes detected. Lookup table vs. per-file embedding still open. Proposed: validate directions against bearing; validate distances against haversine; detect anomalies (altitude spikes, direction contradictions). Requires authoritative source identification and accuracy tolerance definition.
- **State files** - the 16 federal state files in `states/`, their structure, subtitle tagline pattern, and how they aggregate roads and nodes. Needs its own `## State` chapter and `validate_states.py` script.
- **Naming conventions in use** - CONVERTED: German infixes replaced with English (`_bruecke_` → `_bridge_`, `_raststaette_` → `_service_`). Road-tied stops (service/rest/roadhouse) now require road prefix: `place_{road}_service_*`, `place_{road}_rest_*`, `place_{road}_roadhouse_*`; optional exit numbers if official AS-number exists. ✅ Migration complete. Tunnel naming still pending.
- **Navigation links placement** - FIXED: neighbour links (distance + direction markers) moved from `## Shown` to `## Holds` across 51 files (A1, A7, A20, A23, A24, A25, A210, A215). Validator `validate_navigation_links.py` enforces rule; all 187 files pass.
- **Engine files** - `instructions.md`, `stack.md`, and the pieces in `engine/` (kilometerstein, driver seat, infotainment, etc.)
- **People** - persona files in `people/`
- **Vehicles** - vehicle files in `vehicles/`
- **Props** - prop files in `props/`
- **Processes and positions** - process and position files used in the world
