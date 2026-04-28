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

**Naming:** `place_{road}_rest_{name}.md`

---

### Motorway Service Area

Raststätte. Restaurant and hotel complex. No fuel. Directly on the motorway. In practice typically modelled as part of a Roadhouse rather than as a standalone type.

**Shown** is what the driver sees from the carriageway - the sign and the pull-off.

**Holds** carries the kilometerstein position and navigation links to the adjacent stops on the same road.

**Offers** is food, accommodation, and parking.

**Withheld** is what requires seeking - specific, geographical, not visible from the carriageway.

**Naming:** `place_{road}_service_{name}.md`

---

### Roadhouse

Rasthof. Full services directly on the motorway. Fuel, food, parking.

**Shown** is what the driver sees from the carriageway - the sign and the pull-off.

**Holds** carries the kilometerstein position and navigation links to the adjacent stops on the same road.

**Offers** is fuel, food, and parking.

**Withheld** is what requires seeking - specific, geographical, not visible from the carriageway.

**Naming:** `place_{road}_roadhouse_{name}.md`

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

## To document

- **Bundesland files** - the 16 federal state files in `bundeslaender/`, their structure, subtitle tagline pattern, and how they aggregate roads and nodes. Needs its own `## Bundesland` chapter and `validate_bundeslaender.py` script.
- **Naming conventions in use** - actual files use German-language infixes that do not match the English spec: `_bruecke_` and compound forms (e.g. `place_a1_volmebruecke.md`) instead of `_bridge_`; `_raststaette_` instead of `_rest_` / `_service_`; compound tunnel names (e.g. `place_a7_elbtunnel.md`) instead of `_tunnel_`
- **Standalone Raststätte files** - files like `place_raststaette_aalbek.md` carry no road prefix; naming rule not yet defined
- **Numbered rest stop pattern** - Raststätten can carry an exit number mid-chain (e.g. `place_a1_28_raststaette_buddikate_ost.md`); not covered by the current spec
- **Navigation links in Shown** - some files (notably A23 nodes) carry neighbour links with distance markers inside `## Shown` rather than `## Holds`; placement convention not yet ruled on
- **Engine files** - `instructions.md`, `stack.md`, and the pieces in `engine/` (kilometerstein, driver seat, infotainment, etc.)
- **People** - persona files in `people/`
- **Vehicles** - vehicle files in `vehicles/`
- **Props** - prop files in `props/`
- **Processes and positions** - process and position files used in the world
