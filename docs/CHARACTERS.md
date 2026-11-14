# Licensed character presentation

The runtime uses four CC0 bases from Quaternius's Ultimate Animated Character Pack. Original files remain unchanged and ignored. Source-role palettes and relative sprite heights are compiled from the pinned pret PNGs; source object flags, positions and facing still drive the actors. These are staging silhouettes: caps, dresses, hair, body likeness, motion pacing and contacts still need refinement before final acceptance.

Acquisition metadata is in `data/character-lock.json`. The official pack page and included license both say CC0. Models were selected from the official public Drive folder, using the connected Drive workflow for metadata/license/raw-file reads. Public direct-download responses were HTML and were not treated as model files. Temporary connector file references were materialized via stdin with terminal echo disabled; signed URLs are not stored in the ledger or source.

The selected glTF documents embed their buffers. Packaging preserves skin joints, inverse bind data, weights, geometry, materials and animation keys, with bounded base64 decoding. Characters never pass through the static-scene baker. Existing Idle/Walk/Run/SitDown are selected; Casual_Bald has no Run and explicitly reuses Walk. Selected root-bone horizontal translation is constant, so source grid motion remains authoritative. No whole motion was authored.

On a fresh machine, download only the four files identified in the lock through the official folder/connector, then verify their SHA-256. No account signup, purchase or project upload is required. The runtime descriptor and native assets are generated:

```sh
./tools/build.sh
./tools/import_characters.sh
./tools/build_character_profiles.sh
./tools/build_levels.sh
./tools/render_baseline.sh
./tools/render_event_scenario.sh
```

The native importer requires exactly one complete skeletal mesh per source model and one selected sequence per source clip, with matching skeletons and positive lengths. It reports actual native paths/material slots/bounds. Profiles create a skeletal-compatible project material and read every assigned vector value back. UE5.8's installed SetMaterialInstanceVectorParameterValue implementation always returns false after setting/updating, so its return is not a validity test.

Figures use single-node playback of the existing sequences. World position/facing/visibility come from original source state, without capsule physics or animation root trajectories changing grid coordinates. Velocity selects locomotion; backwards source movement reverses the base clip. Chair occupancy is identified by original chair metatiles and uses the source SitDown end pose. This is adaptation of a sourced pose, not new animation.

Baseline captures include the post-clock source NPC snapshot, with frame-story progression paused for the sweep; idle skeletal pose updates continue. Geometry smoke remains story-independent. The renderer checks expected/configured human counts, explicit unmapped diagnostics, source map callback failures and time/pose readback. Pose verification excludes initial settling frames; a bind-to-idle transition alone is not accepted. Actual playability, foot contacts, broad state coverage and owner acceptance remain separate.

Character integration exposed a missing central helper in the event importer: Common_EventScript_NopReturn is in data/event_scripts.s. Central code labels and all branch-target resolution are now included, and native tests cover all six map callbacks in both genders. Source callback failure is an error in the capture verifier, not an empty-scene success.

The rival bedroom's item-ball marker uses the installed Epic `/Engine/BasicShapes/Sphere` as its geometric base. A project material adapts the original NPC3 palette (red/white/black indices11/14/15) and characteristic band/button; no copyrighted 3D game asset was downloaded. It remains subject to engine-content use terms; only a reference and recipe are in Git. Unknown nonhuman graphics still remain explicit diagnostics until covered.
