# References

## Authorship

Authored by Kai Schlüter (ChBrain) with AI-assisted drafting. The per-file workflow is:

1. A model proposes several drafts of a passage.
2. The facts are checked against authoritative sources.
3. The final voice is rewritten by hand.

The intent is to use facts (which are not copyrightable) carried in the author's own expression. Occasional close-paraphrase or factual drift may slip through; if you spot it, please open an issue and link the source.

`scripts/spotcheck_withheld.py` is a sampling helper for periodic review: it picks N random in-scope Withheld blocks (deterministic per seed) and prints them as a markdown brief with audit instructions. The audit itself is performed by whichever LLM session runs the script - no API key required.

---

## Primary sources

The Autobahn network data is drawn from publicly available infrastructure sources only. The list below names the sources used most often; it is not exhaustive.

**autobahn.de** - Federal motorway operator (Autobahn GmbH des Bundes). Exit numbers, road designations, construction status, service areas.

**bast.de** - Federal Highway Research Institute (Bundesanstalt fur Strassenwesen). Traffic data, road standards, Elbtunnel and Laermschutztunnel specifications.

**bmvi.de** - Federal Ministry for Digital and Transport. Planning documents for A20 western extension, A21 northern extension, Fehmarnbelt tunnel.

**autobahnatlas-online.de** - Independent Autobahn reference for kilometre values, exit numbering, and historical alignment.

**German Wikipedia** - Individual articles for motorways, exits, named infrastructure (bridges, tunnels, junctions), towns, persons, and events. Used for historical context and Withheld content; phrasing is the author's own.

**Local and regional reporting** - Nordkurier, schwerin.news, schwerin-lokal.de, IHK Schwerin, and equivalent local sources for current planning and construction status.

**Google Maps and direct observation** - Used for kilometre verification, alignment, and on-the-ground geometry.

Other regional sources (state archives, monastery websites, municipal heritage pages, individual museum and church sites) are consulted as needed.

---

## Notes on sources

All road and infrastructure data is factual as of April 2026. Construction statuses (Hamburg-Bahrenfeld closed, A21 northern extension planned for mid-2026, Westkreuz Hamburg future junction) are current at time of writing.

The personas, pieces, positions, and processes are fictional constructs built on the factual road architecture.

---

*v0.2.4 - KAI Worlds - Kai Schlueter - April 2026*
