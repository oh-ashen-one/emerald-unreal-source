# Asset and method provenance

Public source release: third-party raw/native assets, generated content and private evidence are excluded. Historical acquisition/adaptation notes below credit the separately acquired inputs used in the local demo; they do not imply those inputs are redistributed here. The MIT license applies only to original project code and documentation. Third-party content retains its own license. The concept image and local reports referenced below are not included.

## Source data

- pret/pokeemerald — https://github.com/pret/pokeemerald — pinned in `data/source-lock.json`. Referenced by the local layout/event research importer. This public repository includes only original implementation and provenance metadata, not ROMs, extracted game graphics/audio, source checkouts or generated game data. It grants no rights to Pokémon content.
- Owner's expansion fork — https://github.com/oh-ashen-one/pokemon-emerald-ai-slop — pre-Rustboro audit consulted for cast/context; no geometry or gameplay changes copied into the vanilla map data.

## Acquired free asset candidates, 2026-11-13

- Kenney Furniture Kit 2.0 — https://kenney.nl/assets/furniture-kit — CC0, verified in the original listing and included `License.txt`. Acquired the documented mirror's `furniturekit_updated` subtree after the original archive returned HTTP 403. Mirror: https://github.com/ETdoFresh/kenney.nl . Candidate beds, tables, chairs, kitchen cabinets, TV and small interior props. No modifications or engine imports yet.
- Kenney Nature Kit 2.1 — https://kenney.nl/assets/nature-kit — CC0, verified in original listing and included `License.txt`. Same mirror, `kenney_natureKit_2.1` subtree. Candidate broadleaf trees, grass and flowers. No modifications or engine imports yet.
- Exact mirror revision and selected-file hashes will be written to the asset acquisition manifest before import. Packs remain in ignored `.references/kenney`.

## Required source checks and access/fit results

- Epic/Fab checked first: https://www.fab.com/listings/a467507b-e5a6-4b37-b878-93fe3ffe856f — Epic Games Stylized Lake Village, free, 59 assets, UEFN referenced format only; not a native editable UE5 cottage kit. No acquisition/license assertion beyond that listing.
- Local UE 5.8 feature packs inspected: first/third-person, top-down, vehicle, VR and AR templates available. No matching furnished village pack found in this location. Engine basic assets may serve diagnostic scenes, not final art acceptance.
- Sand3D first check for secondary props: https://huggingface.co/spaces/Sandflow/sand3d-explorer — host page reachable; interactive explorer failed through the web reader. Candidate/rights inspection incomplete, not proof no matching prop exists.
- NVIDIA SimReady: https://huggingface.co/datasets/nvidia/simready-assets — dataset identifies simulation-oriented USD assets and CC BY 4.0; examples skew industrial/medical. No pack downloaded; per-package license checks still required if selected.
- ThreeJS Assets free collection: https://threejsassets.com/assets/free — direct reads timed out; search index identifies low-poly trees/props. No account created or model downloaded. Per-model license and fit remain unverified.
- Free web-fetch service returned HTTP 401; used available built-in web reading for the checks above. No paid web calls or account changes.

## Original concept art

The private authoring workflow used a generated concept reference. Concept/reference imagery and its source arrangement are excluded from this public release. It was never represented as an Unreal screenshot.

## Methods

Bully Remake's documented local source importer → generated manifest → CLI C++ build → headless runtime smoke → inspected capture pipeline informed the architecture. Its frame-driven door-fade guidance and real-input smoke distinction are references for later implementation; no Bully game assets acquired. Decompiling-games, Free Assets First, Claude Code Game Builder archive, shared Unreal and Epic MCP/skill guidance were loaded. This session uses Codex; it does not claim Claude-specific model/tool access.

## Additional architectural candidates checked after native baseline

- Kenney 3D Modular Buildings — https://github.com/ETdoFresh/kenney.nl/tree/master/kenney_modularbuildings_updated — included CC0 notice checked and Preview.png opened. Plain modular wall/window/door/roof pieces; promising editable base, still far below final material/detail target. No selected file imported yet.
- Kenney Fantasy Town Kit 1.0 — https://github.com/ETdoFresh/kenney.nl/tree/master/fantasy-town-kit-1.0 — included CC0 notice checked and Preview.png opened. Descriptive GLB roof-gable/window/pillar modules available. Candidate for source-footprint adaptation; no selected file imported yet. These two subtrees are acquired under the same pinned mirror revision; add exact selected hashes/triangle counts to asset-lock before import.

## Selected art pass 2 inputs, 2026-11-13

- Selected Kenney Fantasy Town roofGable, roofGableTop, roof, wallWindowGlass and pillarWood from the already inspected CC0 pack; plus Furniture Kit stove, table, doorway and lamps. Exact GLB hashes and triangle counts are now in asset-lock (36 total mesh inputs). Planned adaptations are source-derived dimensions/transforms and source palette overrides; native import/render fit still needs the next run.
- Poly Haven Wood Floor, Dimitrios Savva — https://polyhaven.com/a/wood_floor — original asset page and https://polyhaven.com/license explicitly identify CC0. Acquired only 2K JPEG diffuse, DX normal and packed AO/roughness/metal maps through the public file API/direct asset endpoints. Physical reference width 1.7 m. Hashes, direct URLs and sizes in `data/pbr-lock.json`; color/UV adaptation will be recorded in the builder.
- Poly Haven Spruit Sunrise, Greg Zaal — https://polyhaven.com/a/spruit_sunrise — CC0 on original listing. Selected 1K Radiance HDR (1.5 MB) for physical ambient fill/reflections; no site screenshots or preview art copied. Hash/provenance in pbr-lock. No account, purchase or paid call.

## Verified adaptations in art pass 2

- Added Furniture Kit chairModernCushion to the pinned input ledger (38 total complete static assemblies). Original source files remain unchanged. The new bake converts every static node/mesh into one complete glTF mesh, applying source hierarchy transforms and inverse-transpose normals, preserving materials/UVs, and correcting mirrored winding. Bed now includes frame, cover and pillow; earlier first-mesh selection was incomplete. Per-model converted hashes, original instance/primitive counts and bounds are in art-bake-report.
- Native actors fit these complete licensed bases to source-derived furnishing/building footprints. Palette overrides are sampled from original map references: Brendan blue rugs, May pink rugs, green chair cushions, pink/yellow tabletops and blue bedding. The unchanged-source-image sampling code and values are in source_style.py/source-style.json. No asset is represented as original authorship.
- Reused project palette parent as parameterized material instances; reused Epic's installed WorldAlignedTexture function for sourced PBR floor color. Selected Poly Haven HDR is used as ambient/reflection input. Original materials/functions in engine/plugin content were not edited.
- Tiny imported bases keep complete LOD0 geometry with no reduction; Nanite disabled per imported asset to avoid inappropriate usage fallback. Shared project materials explicitly support Nanite. Latest actual game log has no material compilation/default-material/Python startup errors; this is not final visual acceptance or performance proof.

## Lab furnishing inputs, 2026-11-13

- Previewed Furniture Kit desk and cardboardBoxClosed isometric renders; selected their complete GLBs under the same pinned mirror revision/included CC0 notice. Added exact source hashes/triangle counts to asset-lock (40 static inputs total). Source models unchanged. Source-compound transforms and existing computer/bookshelf/books/chair/plant assemblies adapt them to lab desks, storage and shelves; the circular machine is still diagnostic, not a substituted unrelated appliance. Prior Sand3D/SimReady/Fab/ThreeJS checks and access limits above still apply.

## Wall-fixture inputs, 2026-11-13

- Poly Haven Wall Clock, PierreB3D — https://polyhaven.com/a/wall_clock — CC0 at listing and https://polyhaven.com/license. Selected1K glTF plus its exact buffer/texture dependencies (3,658 triangles, four source nodes); public API self-identifying request succeeded after default client403. No authentication/account workaround. Source bytes unmodified, packed into GLB with images embedded, then complete static scene bake; source-derived size/placement recorded. Static acquired hand pose retained, no new motion authored.
- Poly Haven Hanging Picture Frame01, James Ray Cock — https://polyhaven.com/a/hanging_picture_frame_01 — CC0. Selected1K glTF/dependencies,2,586 triangles. Original files unchanged; source pixels from pinned Brendan bedroom map replace the staging artwork material in engine, and frame fitted to the mirrored original map-poster anchor. Provider preview images used only for private inspection, not game art.
- Exact URLs, MD5/byte checks, SHA-256 and packaging hashes in data/prop-lock.json; combined42-input ledger in asset-lock. Poly Haven Gaming Console rejected: curved black console is not original purple GameCube. Poly Pizza clock https://poly.pizza/m/dwZRvbXlAus and console https://poly.pizza/m/7jHiQIMZkRs were read but not acquired; actual asset fit/download/CC-BY terms not fully verified. Fab search unavailable through reader and Sand3D interactive results unavailable; these limits do not prove absence of suitable assets.

- Native preview correction: imported transmission glass was dark in actual Metal rendering; project transparent fixture-glass material now preserves readable faces without changing source geometry. The original map pixels appear inside the licensed frame at source columns. All six final-source frames were inspected; clock hand pose remains static. Source-style samples/print generation are reproducible from pinned original reference data.

## Roof surface inputs, 2026-11-13

- Poly Haven Clay Roof Tiles02, Amal Kumar — https://polyhaven.com/a/clay_roof_tiles_02 — CC0 verified at listing/license. Selected only2K JPEG diffuse, DirectX normal and packed ARM; exact bytes/hashes in exterior-surface-lock. Original images unchanged. World-aligned texture/normal functions reused from installed Epic content; project tint/desaturation instances adapt terracotta/olive roof roles.
- Tree Small02(https://polyhaven.com/a/tree_small_02) preview/metadata inspected but not acquired:2.06M triangles and sparse crown did not fit current source silhouette/performance needs without further adaptation. Roof14/CeramicRoof01/GreyRoofTiles02 previews inspected; selected clay curved-tile base better fits the intended roof style. All provider previews used only for private inspection. Original lab floor pixels derive pinned source metatile202; grayscale relief is a staging adaptation, not new original art.

## Skeletal character bases, 2026-11-13

- Quaternius Ultimate Animated Character Pack — https://quaternius.com/packs/ultimatedanimatedcharacter.html — CC0 on primary listing and included license. Official folder https://drive.google.com/drive/folders/1sNi1AfenfPRrvRt5yfaj5QMMd6KKcUJ5 . Selected Doctor_Male_Young, Casual_Male, Casual_Female and Casual_Bald; exact Drive IDs/bytes/SHA-256 in character-lock. Included license snapshot uses normalized line endings.
- Original source files unchanged. Embedded buffers packed into GLB with skin/weights/keys preserved, existing Idle/Walk/Run/SitDown selected; Bald's missing Run explicitly aliases Walk. Original root horizontal translations constant. Source PNG palette indices/heights drive role materials/proportions. Runtime timing/reversal, footprint/facing/visibility and held seated end pose are documented adaptations; no whole motion authored. Silhouette/outfit likeness and motion/contact polish remain incomplete.
- Mixamo/Fab/SimReady/ThreeJS source checks and Kenney candidate previews recorded in LOG. No claim blocked access means no asset exists. Kenney candidates were not integrated. Official Quaternius preview was used only for selection, not game art. Connected Drive operations were read-only; no account changes/signup/purchase or external generation.

## Quality-pass candidates and installed Examples

- Installed UE5.8.3 ArchVis Template HillTree_02 and complete12-file material/texture dependencies: Epic Engine Examples under https://www.unrealengine.com/eula/unreal (Templates are defined as Examples). Original installed bytes unchanged, private native authoring copies only; data/epic-quality-lock.json and tools/acquire_engine_quality.py. Two native LODs, original bark/leaf normal and leaf roughness/opacity bindings verified; runtime quality acceptance pending.
- Poly Haven CC0 2K PBR sets: Leafy Grass (Charlotte Baglioni), Brown Mud Leaves01 and White Planks Clean (Rob Tuytel). Canonical source/creator/license/API URLs and exact bytes/MD5/SHA-256 in data/quality-surface-lock.json; reproduction tools/acquire_quality_surfaces.py. Original acquired bytes unchanged. Candidate diffuse images inspected; integrated rendered acceptance remains separate.

## Adult character candidate — CC BY4.0

“Free Cartoon Game Man Character (Rigged)” by **Canino3d Studio**, https://www.fab.com/listings/d2d871a0-50ea-4041-9889-3f27e5377bb3 . Licensed under **Creative Commons Attribution4.0 International**, https://creativecommons.org/licenses/by/4.0/ . Original downloaded bytes are unchanged. Native import, texture lookup staging, retargeting and any later material/role adaptations are recorded in the asset ledger. Currently an evaluation candidate; preserve this credit in rendered study captions and final game credits if used. No endorsement by the creator is implied.

Quixel Megascans **Kikuyu Grass** (https://www.fab.com/listings/4a7f5036-b879-4910-a5f2-271ccff93b32) and **Lawn Grass** (https://www.fab.com/listings/f50d1f4a-d91a-41c2-86ad-10c4ffe7f658), acquired freeNovember14 under Fab Standard License (https://www.fab.com/eula). CompleteLOD0 grass variants adapted with masked two-sided foliage/explicitORT channel binding and cosmetic source-cell scattering;4K lawn color/normal/roughness/AO blended with retained source-connected paths at200cm. Original hash-pinned archives unchanged and ignored; no standalone redistribution.

**Cartoon Young Boy Rigged**, giyas3dartist — https://www.fab.com/listings/cb88681d-f0d3-4f6c-bfa6-ee38d2734f7f , free under Fab Standard License (https://www.fab.com/eula). Original eleven-part skin/rig/morph/PBR source retained; duplicate facial-test names made unique; existing CC0 male motions retargeted. Eye-export materials adapted with existing transparent project material and engine flat iris normal. Original source files unchanged and ignored; no standalone redistribution. Native/world/final-quality evidence has separate scope.

Interior fixtures: **Gaming Console**, Sean Buckley (https://polyhaven.com/a/gaming_console), and **Electric Stove**, Kuutti Siitonen (https://polyhaven.com/a/electric_stove), CC0-1.0. Complete static scenes/PBR maps retained, adapted to original source furniture footprints. **Metal Plate02**, Rob Tuytel (https://polyhaven.com/a/metal_plate_02), CC0-1.0, supplies4Kdiffuse/normal/ARM to original project specimen-analyzer/controller geometry. Generator: tools/build_original_lab_analyzer.py; no Nintendo artwork/mesh inputs. Surface license: https://polyhaven.com/license . Raw sources and generated native assets stay ignored.


## Expanded furnishing sources — November14

| Asset | Creator and primary URL | License | Adaptation / verification scope |
|---|---|---|---|
| Retrofuturistic Computer | crow — https://www.fab.com/listings/7304fe63-018f-464f-b7ac-b544ed9285d6 | CC BY4.0 — https://creativecommons.org/licenses/by/4.0/ | Free listing/license/download verified in signed-in browser. Complete11-part25,320-triangle monitor, base, keyboard and cables (native25,288 after exactly32coincident-corner faces collapse at float32/cm conversion); original real color/normal/metallic-roughness maps. Source-sized placement adapters, no Nintendo art. Native usable geometry/PBR verified; all7actual041839source-world views inspected. |
| Fridge | Toss — https://www.fab.com/listings/4c8ac069-4587-4325-a39f-5ab8bf129966 | CC BY4.0 — https://creativecommons.org/licenses/by/4.0/ | Free listing/license/download verified in signed-in browser. Complete clean8,596-triangle variant selected with original ancestors/materials; presentation ground and separate worn alternative excluded. Source bytes unchanged; native/world041839fit inspected; yaw-90/local dimension swap faces doors into both kitchens. |
| Book Encyclopedia Set01 | John Malcolm — https://polyhaven.com/a/book_encyclopedia_set_01 | CC0-1.0 — https://polyhaven.com/license | Complete20-book67,306-triangle source with4Kmaps.24 exactly zero-area source faces are removed by native import; all usable geometry remains required. Separate derivative stacks six complete volumes20,210tri; raw input unchanged. |
| Cardboard Box01 | Rahul Chaudhary — https://polyhaven.com/a/cardboard_box_01 | CC0-1.0 | Complete16,952-triangle scan,4Kmaps; source storage-box anchors. |
| Metal Office Desk | Ulan Cabanilla — https://polyhaven.com/a/metal_office_desk | CC0-1.0 | All9parts/6,898tri with4Kmaps; original desk centers/footprints. |
| Television02 | Benny Weimer — https://polyhaven.com/a/television_02 | CC0-1.0 | Complete2,310tri4Kscan; original television anchors. |
| Painted Wooden Cabinet02 | Kirill Sannikov — https://polyhaven.com/a/painted_wooden_cabinet_02 | CC0-1.0 | All3parts/966tri4Kscan; kitchen cupboard anchors. |
| Small Wooden Table01 | Ulan Cabanilla — https://polyhaven.com/a/small_wooden_table_01 | CC0-1.0 | Complete3,410tri4Kscan; living/notebook desk anchors. |

All six selected Poly Haven glTF exports and both Fab models contain no skins or animation; none were silently discarded. All source URLs, hashes and dependencies are pinned in quality-fixture-lock, fab-computer-lock and fab-fridge-lock. Adaptations use complete scene baking, positioning/scaling and a clean variant or complete-book arrangement where stated. Models/materials adapted; no endorsement implied. Fab sources here use CC BY4.0, not Fab Standard. No purchase or signup. All13native fixture assemblies pass usable geometry/PBR checks; all7actual041839world views opened, floor albedo UV corrected and121input/13warp traversal041945passes. Full quality gate remains open.


## Interior detail sources — November14

| Asset | Creator / URL | License | Adaptation and current scope |
|---|---|---|---|
| Bathroom Sink Cabinet | Jimbogies — https://www.fab.com/listings/f9018670-caa2-4fc3-8059-6dbfe0227097 | CC BY4.0 — https://creativecommons.org/licenses/by/4.0/ | Original glTF archive/license.txt retained;68triangle-surface parts/20,538tri, real wood/stone color/normal/metallic-roughness maps. Three line-only meshes38/39/40(46segments) explicitly excluded by triangle-only native conversion; no triangle surfaces, skins or animations discarded. Original source attribution: https://sketchfab.com/3d-models/bathroom-sink-cabinet-e5cf10304ffb4c11bc7841b584ccd706 . Native usable geometry/PBR and043416native study inspection pass; source front+Y. All7source-world043816views opened;044030credits creator/source/license/adaptation notice inspected/readable. |
| Modern Staircase Collection 3D Model Pack | 3dShowdown — https://www.fab.com/listings/84f06084-d96f-4ce0-8254-811d544f9570 | Fab Standard License — https://www.fab.com/eula | Free/Standard listing and original glTF/texture downloads verified. Complete straight variant roots4+24 and all8children,10parts/27,648tri. Original stone/wood color/normal/roughness maps supplied separately and reattached in owned derivative; roughness packed into G, metallic0/AO1. Other independent variants/raw archives unchanged. Native geometry/PBR and043416native study inspection pass; all10parts/facing+Y. All4source stair anchors/facing/fit inspected in043816; source warps regression043922passes. |
| Potted Plant01 | Rico Cilliers — https://polyhaven.com/a/potted_plant_01 | CC0-1.0 — https://polyhaven.com/license | All4parts/176,226source faces; native176,094 after exactly132coincident-corner triangles collapse.4Kpot/leaves diffuse/normal/ARM and source alpha retained.0skins/0animations. Native usable geometry/PBR and043416native study inspection pass; foliage/soil/contact visible. All3source lab plants/floor contact inspected in043816. |

Source-first checks: free Metal Sinks by Sousinho Games is too wide/industrial for a single source sink cell;102tri Kitchen Sink Unit01 and texture-free Free Stylized Sinks do not meet the detail target. No paid sink/stair asset acquired. Poly Haven model catalog has no sink/stair match; its full potted plant fits the existing source plant footprint. No purchase/signup/ROM/Nintendo art. Hashes in fab-sink-lock/fab-stairs-lock/quality-fixture-lock; selected surface/scene derivation in prepare_interior_details.py and interior-detail-report.json. These are import-stage facts; the full quality gate remains open.


## Original lab materials and scanned pickup — November14

No new external asset acquired. Existing CC0 Poly Haven CardboardBox01 (Rahul Chaudhary, https://polyhaven.com/a/cardboard_box_01) now supplies the generic static pickup descriptor at the prior110cm contract, all16,952tri/native PBR materials retained. Original source graphic identity, position, visibility and interaction script are unchanged; actual May2F054547floor/scale inspected, native static ready=1.

Original project analyzer/controller geometry is unchanged. Native audit proved imported color factors and inherited translucent blend were already present; the old dominant weathered-metal albedo was a poor glass treatment. Project-owned original_lab_materials.py now uses the existing CC0 MetalPlate02 maps as subtle glass/display microdetail, explicit translucent glass(.18opacity) and brighter emissive panels under physical scene exposure. Actual static material slots/texture/scalar readbacks and real-RHI compile gate each build. ARM uses the actual existing linear-color texture sampler. Native front study045915opened: blue dome/internal canisters and front panels visible. Actual source lab054547blue dome/canisters/front panels inspected; full gate open.


## Full room presentation — November14

No new external acquisition. Full upper walls/ceilings/crown profiles extend existing source room footprints using existing licensed WhitePlanksClean PBR and source trim; all original grid/collision/warp/event data retained. Complete CC0 Kenney FurnitureKit lampSquareCeiling (https://kenney.nl/assets/furniture-kit), already SHA-pinned/imported60tri, supplies ceiling fixtures. Project material adaptation adds the existing licensed scanned microdetail emitter and warm/cool emission. Local rectangular lights provide4000Khouse/6500Klab lighting. Geometry/local lights activate in third-person view while overhead cutaways retain their exposure. Room shell query collision blocks CAMERA only, ignores every pawn/physics channel; front camera guard is visually hidden. Native readbacks/all7locked054547+6perspective054653images inspected; five interior near-wall cases054756pass. Exterior tree occlusion remains open; full gate open.


## Riya candidate and clothing maps — November14, resumed after restart

| Fab asset | Publisher | Source | License | Current use/status |
|---|---|---|---|---|
| Riya-Realistic girl | giyas3dartist | https://www.fab.com/listings/40fcda7b-ca5b-4d0a-a8d1-eef4d79867e7 | Fab Standard License — https://www.fab.com/eula | Free signed-in download verified before restart; source archive SHA256 pinned in data/fab-riya-character-lock.json and reverified after restart. Complete primary native mesh144550tri/112bones/76morphs/31materials; modular alternatives excluded from assembly. Existing CC0 female Idle/Walk/Run/SitDown retargeted. Candidate only: not installed in gameplay. |

Missing package references repaired using six compatibility aliases of INCLUDED licensed assets only; no external IdaFaber asset acquired. Original source bytes preserved. Supplied demo maps/controllers/animations excluded. Project clothing adapter explicitly connects the creator Business_Suit, Pencil_skirt and shirt diffuse/normal/roughness maps. Only project-owned roughness copies converted to linear mask compression. No source mesh, weights or original source texture modified.

Actual native073133 and073553studies opened after restart. Strict112bone/31material complete-assembly checks and real Idle/Walk/Run bone/time samples pass; seated frozen pose present. Material compilation/fallback/ensure/fatal counts zero. Jacket roughness visibly improved in073553, skirt burgundy detail restored. Running skirt deformation and seated chair contact are rejected/pending. These frames do not establish final quality, motion contact or cast integration. Native capture guard logs no-exclusive-lock contamination, so no exclusive performance claim.


## Detailed cast variants — November14 after restart

No new asset acquired. Existing free Fab Cartoon Young Boy (giyas3dartist, https://www.fab.com/listings/cb88681d-f0d3-4f6c-bfa6-ee38d2734f7f , Fab Standard License) now also supplies the source boy and sibling profiles. Existing free Fab Free Cartoon Game Man Character (Rigged) (Canino3d Studio, https://www.fab.com/listings/d2d871a0-50ea-4041-9889-3f27e5377bb3 , CC BY4.0 https://creativecommons.org/licenses/by/4.0/) now also supplies birch, fat_man and norman. Attribution remains available through C Credits.

Project-owned shirt color variants preserve the original adult color graph and its previously verified real normal/roughness maps; boy instances use the native BaseColorFactor parameter, preserving all original PBR texture bindings. No geometry, skeleton, source keys or original licensed source files changed. Source height/width/graphics metadata retained exactly. Complete native073844preview opened: three22-material/101bone adults and two11-part/556bone children; native idle time/bone motion and all faces/material/floor contact inspected. Shared adult face/shape is an interim limitation. No final identity/quality acceptance. Five descriptors installed with source mappings unchanged; source-world074006sevenviews and074103sixperspectives opened after installation. Riya and remaining female roles are unchanged.


Measured Riya seated preview075355now opened: pelvis-centered chair with corrected front+Y facing exposes the full seated body/legs/shoes and plausible preview contact. Native112bone/31material assembly and four-state guard pass, no shader fallback/ensure/fatal. This250cmhigh chair and pelvis-centered placement differ from current source-world chairs; source-world visual-root/contact adaptation is still required. Running skirt deformation remains rejected, so Riya stays uninstalled. No NPC/source position changed. Native pose report saved in data/native-riya-seat-pose-report.json.


## Riya supplied locomotion and parent variants — November14

No new external download. Original free Fab Standard Riya-Realistic girl archive (giyas3dartist, https://www.fab.com/listings/40fcda7b-ca5b-4d0a-a8d1-eef4d79867e7) includes native MF_Idle/MF_Walk_Fwd/MF_Run_Fwd already bound to the same112bone skeleton. Initial intake excluded all Animation files. Supplemental prepare_riya_supplied_motion.py now stages ONLY those three hash-pinned AnimSequences from that original archive; source controllers/ABPs/BlendSpaces/demo maps remain excluded and unexecuted. Original228base files and three supplemental original sequence files are preserved. Native inspector verifies actual AnimSequence class/skeleton/durations and samples16poses; project-owned duplicates force root lock with root motion disabled, source keys unmodified.

Source-first fit correction: CC0-retargeted walking/running on the tight skirt was rejected. Original supplied native locomotion in081918and parent082039previews has visibly better clothing/limb fit. Existing CC0-retargeted SitDown remains, with measured mesh-only seat offset; source actor/chair anchors stay unchanged. Parent outfit variants use project material-instance tint with creator albedo luminance/detail and unchanged real normal/roughness bindings. Burgundy mom/navy rival_mom retain source role heights/widths/graphics. Actual native5.04s/48frame parent-motion082212was played in QuickTime through its end and scrubbed midway; static seats and complete Idle/Walk cycles inspected. This is a source-motion preview, not the required final20–40s gameplay walkthrough. A final idle-foot-height seating adjustment is pending fresh preview/world verification before parent installation. Full AAA gate remains open.


## Installed parent/gait checkpoint — November14

Both existing source mother roles now use complete Riya112bone/31material Fab Standard models with burgundy/navy clothing variants, original source300cmheight/width/graphics/tiles/facing/flags retained. Original supplied MF_Idle/MF_Walk_Fwd/MF_Run_Fwd sequence copies use native Riya skeleton and root lock; existing CC0-retargeted SitDown retained. Only three original sequence files additionally selected from already acquired free Fab archive. All228base+3supplemental source hashes unchanged; no ABP/BlendSpace/demo/controller execution, purchase/account/ROM/art acquisition. Profile regeneration reinstalls both reviewed descriptors.

Seated visual offset[-.159,73.696,-7.509]cm centers the pelvis on its original source chair and aligns foot height to original supplied idle; source actor/chair anchors and horizontal footprints are unchanged. Full scanned chair height250cm replaces vertically squashed150cm. **Contact remains unaccepted:** native closeups084240reveal hands intersect cushions; taller backs enter first-floor camera foreground. Next correction is sourced seated-pose arm/contact adaptation, with camera/foreground review. Do not mark the full seating or AAA gate passed.

Native48frame motion preview082934encodes49frames(last repeated)/5.2s/H2641280x800 with frame durations from actual engine animation time. Played to end in QuickTime. It shows supplied walks fitting clothing better than rejected CC0 full-stride retarget. This is a scoped studio QA film, not the required final20–40s gameplay walkthrough. Native source gait now distinguishes authored walk/delay/in-place states and avoids choosing Run solely from world speed. Actual original route-guard twin logs Walk at native time/bone samples; source timing/positions unchanged.

Fresh source-world7views083504and6perspectives083612all opened; native8tests083416and32Python checks pass. Both121input/13warp runs083716/083824pass, third-person initializes across6maps. Rendered V/C/Esc/E/W083931passes; all3PNG opened/readable, guard still foliage-occluded. Supplementary two source-room copies084240add only contact cameras; original level bytes, source map/parent tiles and seated offsets verified. Both closeups opened, rejected as final contact. Source locks/import report unchanged. No representative performance or owner acceptance claim. Current gallery refreshed; full GOAL remains active.


## Sourced seated hand correction — November14 verified checkpoint

Existing CC0 sourced SitDown retarget now has a separate project-owned SitDown_LapHands derivative. A native AnimSequencerController updates only six upper-arm/forearm/wrist tracks over the final eight source keys, preserving original translations/scales, other tracks, skeleton/duration and original source fileSHA3369ce0a... No whole motion authored. Analytic two-bone IK preserves limb lengths/bend side; anatomical hand orientation keeps palms down toward knees. Native frozen-pose readback reaches wrists[+/-18,45,126]cm; pelvis/feet/head unchanged within.001nativecm. Source actor/chair anchors, heights/widths/graphics/flags and source layouts/collision/13warps unchanged.

Native100445six-state preview opened and100526actual5.24s/48frame movie played to end in QuickTime. Candidate installed; matching source-room101235closeups opened: prior cushion penetration is removed, hands visible over lap. Fine finger/cloth spacing, complete seated contact and owner acceptance remain open. All7matched101347and6perspective101456images opened, zero shader/fallback/ensure/fatal checks. First-floor chair foreground and outdoor occlusion remain.39Python checks pass, including three analytic contact tests. Gameplay C++/source data are unchanged from prior8native093423/dual-mode121input-13warp083716+083824and V/C/Esc/E/W083931proof; this animation-only pass adds actual native pose/clip/room readbacks. No new native admission after the rolling counter reached10/10; shared cap/flags/watchdog untouched.

Reproduce with guarded_level_build.py build_parent_contact_pass.py (one shared-FIFO/hourly admission batches correction + Riya + parent studio), then render_parent_gallery.sh/render_parent_motion.sh and actual inspection before install_parent_characters.py. Existing copied source-room cameras use render_parent_contacts.sh; original source scene bytes are unchanged. Raw licensed inputs/native assets/media remain ignored. No new model download/purchase/signup/ROM. ASSETS lists original free Fab Riya and CC0 source motion, modifications and limits.

Female-player source-first research: official free Canino3d Studio Free Stylized Cartoon Girl Rigged Character listing fe501f98-a9bb-4acb-b96e-e5b65d8f0d00 and its public preview were read; detailed stylized face is a candidate, but full body/rig/PBR/license remain unverified. Existing Cartoon Asian Girl preview has large child proportions and is not preferred; no model acquired or imported. data/female-player-fab-candidates.json keeps reference/candidate claims separate from actual Unreal renders. Full GOAL/AAA gate remains active.
