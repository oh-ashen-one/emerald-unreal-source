# Emerald Unreal — Littleroot source

An experimental Unreal Engine 5.8 C++ recreation of Littleroot Town and its five building interiors, with grid movement, door warps, dialogue/event tooling, third-person and overhead cameras, and licensed environment/character integration.

This is the **source release**, not a downloadable game. It contains the original C++ project, Python authoring/import tools, tests and asset provenance. ROMs, extracted Nintendo graphics/audio, generated map/event data, third-party models/textures, Unreal binaries and packaged builds are not included. The private demo opened successfully and passed a 30-second packaged town launch test; that build is not distributed here. Visual polish and full behavior parity remain unfinished.

## How to play

You need your own Unreal Engine 5.8 installation, appropriately licensed source inputs, and the separately acquired assets listed in [ATTRIBUTION.md](ATTRIBUTION.md) and [asset credits](docs/ASSETS.md). Asset locks in `data/` contain source URLs and hashes, not the assets. Free Fab content still requires its applicable license/account entitlement.

This is an authoring snapshot, not a one-command setup: some tools expect the original workstation's shared GPU guard and local asset paths. Set `UE_ROOT` to your engine installation and inspect the acquisition/preparation tools before running them. Generate the local manifests with `tools/import_littleroot.py` and `tools/compile_events.py`, compile the native project, acquire/import the licensed assets, and generate levels with `tools/build_levels.py`. The editor workflow uses Python/editor scripting and the original author's native MCP plugins; none are required by a finished standalone. Generated graphics, maps and source checkouts must stay local.

After preparing the content, package with Unreal AutomationTool `BuildCookRun -platform=Mac -clientconfig=Development -build -cook -stage -pak -package -archive` and your project/archive paths. All four content phases are required. Open the resulting `Emerald.app`; it runs without Unreal Editor. No binary release is attached to this repository.

| Control | Action |
| --- | --- |
| WASD / arrow keys | Move |
| E / Enter / Space | Interact, confirm, advance dialogue |
| V | Toggle third person / overhead |
| C / Esc | Open credits / close or cancel |
| Cmd+Q (Mac) | Quit |

Enter a door tile to use a warp. If the clock prompt appears, adjust with the arrows and confirm with E.

## Credits and license

Original code and documentation: [MIT](LICENSE). Third-party assets are separately licensed and are **not** relicensed by this repository. Credits include Kenney, Poly Haven contributors, Quaternius, Epic Games, StyleHex Studio, Tidal Flask Studios, Quixel and the Fab creators listed in [ATTRIBUTION.md](ATTRIBUTION.md). The local research importer references [pret/pokeemerald](https://github.com/pret/pokeemerald); no rights to Nintendo game content are granted here.

Pokémon and related names belong to their respective owners. This independent fan project is **not affiliated with or endorsed by Nintendo, Game Freak or The Pokémon Company**.
