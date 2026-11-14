# Original event runtime — current scope

The runtime consumes `Content/Imported/Data/source-events.json`, compiled from the pinned pret source by `tools/compile_events.py`. No ROM or guessed event placement is involved. The compiler retains source paths/lines, arguments, label fallthrough, map callback tables, local IDs, numeric constants and original messages. Central `data/event_scripts.s` and C string constants are included; all referenced message labels resolve.

## Implemented source-logic slice

- Canonical numeric variables/flags, including aliases, initial reset flags and original male/female truck-intro flag functions.
- An explicit post-clock exploration checkpoint, derived from the source clock/broadcast path. It starts with intro state 7, clock set, moved-in trucks hidden and movers removed. This is a checkpoint, not an implementation of the complete truck arrival.
- Immediate map-load/transition callbacks, predicate warp/frame tables, conditional call/goto, call stack, label fallthrough and return/end.
- Current-map object position/home/facing/movement type, original flag-based map-entry visibility, temporary add/remove visibility and variable rival graphics. Unused decoration slots remain hidden in the empty new-game inventory.
- Original background/coordinate event selection by tile, elevation, facing and variable predicate; NPC occupancy and interaction target selection.
- Source messages/pages, player/rival and selected gender-string substitutions, yes/no result and clock hour/minute state.
- Source grid movement paths, normal 16-frame/fast 8-frame steps, delays, facing and facing-lock/unlock for backward scripted movement. These port original authored grid commands, not newly authored skeletal animation.
- Logical metatile and layout state. Dynamic visual replacements for those changes remain incomplete.
- Unknown script opcode/special errors are explicit; script state, queued effects and requested warp are transactionally rolled back. Unsupported movement actions are logged as errors; general movement-error recovery still needs completion.

## Presentation and integration limits

Normal play uses licensed skeletal source-role figures, with source palette/height adaptation and acquired Idle/Walk/Run/SitDown; likeness, pacing and contacts remain staging. Source-driven wandering/look-around and in-flight occupancy reservations are now implemented with a conservative global script lock; see docs/AUTONOMOUS_NPCS.md for exact coverage and gaps.

Sound/BGM, door, fade, emote and related effect commands are emitted to an explicit effect list. Their original output and `waitse`/`waitdooranim`/fanfare timing are not bridged yet. Do not call a correct final state an exact cutscene/timing reproduction. Ordinary warp transitions are still immediate.

The native HUD displays original text and a diagnostic clock selection screen. It does not reproduce every original PC/menu/clock confirmation behavior or original UI art. Menus, party/Pokedex systems, decoration customization, remaining special helpers, original arrival and postgame state paths remain incomplete. Unsupported interactions must not be accepted as 1:1 behavior.

Geometry smoke disables story. Fixed baseline captures include a paused post-clock NPC snapshot, while the separate wander capture ticks the actual story. These remain scoped checks. Story/input scenarios are separate, so they cannot silently inherit a geometry-mode pass.

## Verification

- Python: `python3 -m unittest discover -s tests -v` (32 checks including source movement-contract extraction).
- Native: `tools/ue_data_test.sh` runs `Emerald.*`, verified from a fresh report, including source callbacks/visibility, both genders' original clock-script state/mom sequence, source trigger predicates/sign text and transactional rollback. The latest report contains seven passing tests, including autonomous movement/reservations, all-map callbacks and the original guard/facing lock. `data/native-event-test-report.json` is the tracked summary.
- Real key path: `tools/event_input_test.sh` injects E/W through `APlayerController::InputKey`, exercising the actual binding/polling path. Fixture setup positions the player; traversal through the trigger is a real key-driven step. The corrected scenario passed after the earlier harness/unsupported-facing failures, which are logged and not counted as passes. `data/native-event-input-report.json` records the actual player/twin endpoints.
- Rendered scenario: `tools/render_event_scenario.sh` saves actual sign/guard images, verifies the engine log and requires scenario success. Current rendered scenario passed at out/event-render/20261113-201714; both images were opened after increasing dialogue text scale. Native HUD and staging character art are not final.

The full GOAL.md requirements remain open until all source behavior, character art/motion, visual quality, final captures and performance/acceptance gates are verified.
