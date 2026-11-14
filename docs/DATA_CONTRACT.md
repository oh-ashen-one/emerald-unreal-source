# Data contract and fidelity gates

The authoritative source is pret/pokeemerald at the revision and file SHA-256 hashes in `data/source-lock.json`. The expansion fork is a source of prior notes only. No ROM is needed for this import pipeline.

`python3 tools/import_littleroot.py --references out/source-reference` generates the UE input at `unreal/Emerald/Content/Imported/Data/littleroot.json`. Install Pillow for optional reference PNGs. The importer itself needs only Python's standard library.

## Coordinates and map words

- Source `(x,y)` is an unpadded metatile index, positive east/south. Runtime map-buffer padding (`MAP_OFFSET = 7`) must never be added to authored events.
- One metatile is 16×16 original pixels and 200×200 UE centimeters. Its center is UE `(200*x,200*y,0)`. UE +X east, +Y south, +Z up. Engine cameras must honor this mapping.
- Original packed u16 words retain ID bits 0–9, collision bits 10–11 and elevation bits 12–15. Elevation is a gameplay collision layer, not a physical Z coordinate.
- Metatile attributes retain behavior bits 0–7 and layer bits 12–15. Both layers' eight source tile words retain tile ID, flip and palette bits. Primary banks start at 0, secondary banks at 512.
- All original event JSON fields are retained without rewriting. `warp_links` resolves **zero-based** destination warp indices against the actual destination map. Two exit tiles may point to one exterior door; reciprocal identity must not be assumed.

## Source anomalies and dynamic state

The alternate lab-with-table file contains 170 u16 words for a declared 13×13 layout. The importer preserves the final unused word in `trailing_block_words`; it does not turn it into an extra cell. Normal geometry has 169 cells.

The source houses are gender-dependent. Both floors retain all decoration slots and story-state NPC objects, including objects that are initially hidden. Importing every object does not mean displaying every object simultaneously. Initialization flags, variable graphics, scripted movement and map callbacks must be implemented before claiming NPC parity.

Map entry scripts, coordinate triggers, object interactions and background interactions seed a transitive source-label index. Raw instructions, text and movement records retain source paths and line numbers. **Retaining scripts does not implement their semantics.** A future runtime opcode coverage report must distinguish supported, tested and unresolved engine-special behavior.

The source-reference PNGs are static 2D tile composites. They omit actors, tile-animation callbacks, time-dependent palettes, script-mutated metatiles and original screen composition. They are layout/art references, not screenshots of original gameplay or proof of UE rendering.

## Required evidence

1. Differential raw-data tests for every cell, event, tileset definition, source hash and warp destination.
2. UE C++ compilation and deterministic runtime traversal of every interior and both directions of each warp.
3. Source-state scenarios for both house roles, clock/stair gate, rival interactions, lab transitions and town boundary triggers; record unsupported operations.
4. In-engine collision/furniture/NPC overlays compared to source; inspect matching renders at wide and close views.
5. Licensed professional assets, provenance, lighting/material/art iterations and independent visual critique.
6. Exterior plus every interior hero screenshot, 20–40-second actual walkthrough capture, and README/READY launch instructions with remaining limitations.

No data-only, build-only or screenshot-only result closes all six gates.
