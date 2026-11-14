#!/usr/bin/env python3
"""Lossless pret/pokeemerald -> engine-neutral/UE JSON importer. No ROM input.

Source map coordinates are tile indices (no engine MAP_OFFSET padding).
A metatile is 16x16 source pixels; one metatile is 200 cm in UE.
UE +X points east, +Y south and +Z up. Elevation is a gameplay layer,
not a physical height. Retain the packed source words for independent audits.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MAP_NAMES = ('LittlerootTown', 'LittlerootTown_BrendansHouse_1F',
             'LittlerootTown_BrendansHouse_2F', 'LittlerootTown_MaysHouse_1F',
             'LittlerootTown_MaysHouse_2F', 'LittlerootTown_ProfessorBirchsLab')
EVENT_KEYS = ('object_events', 'warp_events', 'coord_events', 'bg_events')


def words(raw: bytes) -> list[int]:
    if len(raw) % 2:
        raise ValueError('Odd-length u16 source')
    return list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))


def unpack_block(word: int) -> dict:
    if not 0 <= word <= 0xffff:
        raise ValueError('Block must be u16')
    return {'metatile_id': word & 0x3ff, 'collision': (word >> 10) & 3,
            'elevation': word >> 12}


def definitions(text: str) -> dict[str, str]:
    """Resolve named C initializers/INCBINs without executing source."""
    return {m[0]: m[1] for m in re.findall(
        r'\b(\w+)\s*(?:\[[^\]]*\])*\s*=\s*(\{.*?\}|[^;]+);', text, re.S)}


class Importer:
    def __init__(self, source: Path):
        self.source = source
        self.inputs = {}
        self.headers = definitions(self.read('src/data/tilesets/headers.h'))
        self.graphics = definitions(self.read('src/graphics.c'))
        self.graphics.update(definitions(self.read('src/data/tilesets/graphics.h')))
        self.metatiles = definitions(self.read('src/data/tilesets/metatiles.h'))
        behavior_source = self.read('include/constants/metatile_behaviors.h')
        behavior_enum = re.search(r'enum\s*\{(.*?)\};', behavior_source, re.S)[1]
        behavior_enum = re.sub(r'//[^\n]*|/\*.*?\*/', '', behavior_enum, flags=re.S)
        self.behaviors = {}
        next_value = 0
        for entry in behavior_enum.split(','):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split('=')
            name = parts[0].strip()
            if len(parts) == 2:
                next_value = int(parts[1].strip(), 0)
            if name.startswith('MB_'):
                self.behaviors[next_value] = name
            next_value += 1
        self.labels_text = self.read('include/constants/metatile_labels.h')
        self.tilesets = {}

    def raw(self, name: str) -> bytes:
        path = (self.source / name).resolve()
        if not path.is_relative_to(self.source.resolve()):
            raise ValueError('Source path escapes repository')
        raw = path.read_bytes()
        self.inputs[name] = hashlib.sha256(raw).hexdigest()
        return raw

    def read(self, name: str) -> str:
        return self.raw(name).decode()

    def load_tileset(self, symbol: str) -> dict:
        if symbol in self.tilesets:
            return self.tilesets[symbol]
        fields = dict(re.findall(r'\.(\w+)\s*=\s*(\w+)', self.headers[symbol]))
        def path_for(table, key):
            return re.findall(r'"([^\"]+)"', table[fields[key]])[0]
        meta_path = path_for(self.metatiles, 'metatiles')
        attr_path = path_for(self.metatiles, 'metatileAttributes')
        tile_path = path_for(self.graphics, 'tiles')
        palette_paths = re.findall(r'"([^\"]+\.pal)"', self.graphics[fields['palettes']])
        meta_words = words(self.raw(meta_path))
        attrs = words(self.raw(attr_path))
        if len(meta_words) != len(attrs) * 8:
            raise ValueError(f'{symbol}: inconsistent metatile/attribute lengths')
        self.raw(tile_path)
        palettes = []
        for path in palette_paths:
            lines = self.read(path).splitlines()
            if lines[:3] != ['JASC-PAL', '0100', '16']:
                raise ValueError(f'Unexpected palette: {path}')
            palettes.append([list(map(int, line.split())) for line in lines[3:19]])
        label_prefix = fields['metatiles'].removeprefix('gMetatiles_')
        labels = {}
        for name, value in re.findall(r'#define\s+(METATILE_\w+)\s+(0x[0-9A-Fa-f]+|\d+)\b', self.labels_text):
            if name.startswith('METATILE_' + label_prefix + '_'):
                labels.setdefault(str(int(value, 0)), []).append(name)
        offset = 512 if fields['isSecondary'] == 'TRUE' else 0
        result = {'symbol': symbol, 'offset': offset, 'tile_path': tile_path,
                  'metatile_path': meta_path, 'attribute_path': attr_path,
                  'palette_paths': palette_paths, 'palettes': palettes,
                  'callback': fields.get('callback', 'NULL'), 'labels': labels,
                  'metatiles': []}
        for i, attr in enumerate(attrs):
            result['metatiles'].append({
                'id': i + offset, 'attribute_word': attr,
                'behavior': attr & 255, 'behavior_name': self.behaviors.get(attr & 255),
                'layer_type': (attr >> 12) & 15,
                'tile_words': meta_words[i*8:i*8+8]})
        self.tilesets[symbol] = result
        return result

    def load_layout(self, layout):
        primary = self.load_tileset(layout['primary_tileset'])
        secondary = self.load_tileset(layout['secondary_tileset'])
        blocks = words(self.raw(layout['blockdata_filepath']))
        declared_count = layout['width'] * layout['height']
        if len(blocks) < declared_count:
            raise ValueError(f"Bad block count: {layout['id']}")
        cells = []
        for i, block in enumerate(blocks[:declared_count]):
            cell = unpack_block(block)
            bank = primary if cell['metatile_id'] < 512 else secondary
            definition = bank['metatiles'][cell['metatile_id'] - bank['offset']]
            x, y = i % layout['width'], i // layout['width']
            cell.update(x=x, y=y, source_word=block, ue_center_cm=[x*200, y*200, 0],
                        behavior=definition['behavior'],
                        behavior_name=definition['behavior_name'],
                        layer_type=definition['layer_type'],
                        tile_words=definition['tile_words'])
            cells.append(cell)
        return {**layout, 'border_words': words(self.raw(layout['border_filepath'])),
                'trailing_block_words': blocks[declared_count:], 'cells': cells}

    def scripts(self, entrypoints):
        """Index labels and retain reachable instructions, movements and text.

        This is lossless ingestion, not a claim that all opcodes run in UE.
        Unresolved engine specials/macros are reported for the VM implementation.
        """
        labels = {}
        candidates = sorted(set((self.source / 'data/maps').glob('*/scripts.inc')) |
                            set((self.source / 'data/scripts').rglob('*.inc')) |
                            set((self.source / 'data/text').rglob('*.inc')) | {self.source/'data/event_scripts.s'})
        for path in candidates:
            text = path.read_text()
            found = list(re.finditer(r'^(\w+)::?[^\n]*\n', text, re.M))
            for i, match in enumerate(found):
                end = found[i+1].start() if i+1 < len(found) else len(text)
                body = text[match.end():end]
                next_label = found[i+1][1] if i+1 < len(found) else None
                labels[match[1]] = {'source': str(path.relative_to(self.source)),
                                   'line': text[:match.start()].count('\n')+1,
                                   'body': body, 'next_label': next_label}
        pending = list(entrypoints)
        selected = {}
        missing = set()
        while pending:
            name = pending.pop()
            if name in selected or name in missing or name in ('0x0', '0', 'NULL'):
                continue
            if name not in labels:
                missing.add(name)
                continue
            item = labels[name]
            self.raw(item['source'])
            selected[name] = item
            # Preserve implicit fallthrough, including movement/data blocks.
            code_lines = [line.split('@')[0].strip() for line in item['body'].splitlines()]
            code_lines = [line for line in code_lines if line and not line.startswith('.align')]
            last_op = code_lines[-1].split()[0] if code_lines else ''
            if item['next_label'] and last_op not in ('end', 'return', 'goto', 'end_movement', 'endmovement', '.string', '.byte'):
                pending.append(item['next_label'])
            # Only known label references are traversed; preserve every raw line.
            for line in item['body'].splitlines():
                code = line.split('@')[0]
                if '.string' in code:
                    continue
                pending.extend(token for token in re.findall(r'\b\w+\b', code)
                               if token in labels and token not in selected)
        return selected, sorted(missing)

    def run(self):
        layouts = json.loads(self.read('data/layouts/layouts.json'))['layouts']
        lookup = {item['id']: item for item in layouts}
        maps = []
        roots = []
        for name in MAP_NAMES:
            m = json.loads(self.read(f'data/maps/{name}/map.json'))
            m['geometry'] = self.load_layout(lookup[m['layout']])
            roots.append(name + '_MapScripts')
            for key in EVENT_KEYS:
                for event in m[key]:
                    if event.get('script'):
                        roots.append(event['script'])
            maps.append(m)
        variants = [self.load_layout(item) for item in layouts
                    if item['name'].startswith('Littleroot') and item['id'] not in {m['layout'] for m in maps}]
        by_id = {m['id']: m for m in maps}
        links = []
        for m in maps:
            for index, event in enumerate(m['warp_events']):
                target = by_id.get(event['dest_map'])
                if not target:
                    raise ValueError(f'External warp requires explicit treatment: {event}')
                dest_index = int(event['dest_warp_id'], 0)
                target_event = target['warp_events'][dest_index]
                links.append({'source_map': m['id'], 'source_warp': index,
                              'source_xy': [event['x'], event['y']],
                              'dest_map': target['id'], 'dest_warp': dest_index,
                              'dest_xy': [target_event['x'], target_event['y']]})
        scripts, missing = self.scripts(roots)
        revision = subprocess.check_output(['git','-C',str(self.source),'rev-parse','HEAD'], text=True).strip()
        return {'schema': 'emerald.littleroot/1', 'source_revision': revision,
                'coordinates': {'tile_cm': 200, 'x': 'east', 'y': 'south', 'z': 'up',
                                'source_grid_padding_applied': False,
                                'elevation_is_gameplay_layer': True},
                'maps': maps, 'layout_variants': variants, 'tilesets': self.tilesets,
                'warp_links': links, 'scripts': scripts, 'missing_entrypoints': missing,
                'source_hashes': self.inputs}


def render_references(source, data, output):
    """Render data-driven 2D reference sheets, never used as 3D completion proof."""
    from PIL import Image, ImageOps, ImageDraw
    output.mkdir(parents=True, exist_ok=True)
    cache = {}
    def tile_bank(symbol):
        if symbol not in cache:
            sheet = Image.open(source / data['tilesets'][symbol]['tile_path'])
            if sheet.mode != 'P':
                raise ValueError('Expected indexed 4bpp source PNG')
            cache[symbol] = sheet
        return cache[symbol]
    layouts = [m['geometry'] for m in data['maps']] + data['layout_variants']
    for layout in layouts:
        p, s = layout['primary_tileset'], layout['secondary_tileset']
        palettes = data['tilesets'][p]['palettes'][:6] + data['tilesets'][s]['palettes'][6:16]
        canvas = Image.new('RGBA', (layout['width']*16, layout['height']*16), (0,0,0,255))
        for cell in layout['cells']:
            for layer in range(2):
                for quadrant in range(4):
                    word = cell['tile_words'][layer*4+quadrant]
                    index, palette = word & 1023, word >> 12
                    symbol = p if index < 512 else s
                    index -= 512 if index >= 512 else 0
                    sheet = tile_bank(symbol)
                    tx, ty = (index % (sheet.width//8))*8, (index//(sheet.width//8))*8
                    tile = sheet.crop((tx,ty,tx+8,ty+8))
                    # GBA 5-bit channel quantization, expanded to 8-bit.
                    pal = palettes[palette]
                    pixels = [(int(c)//8*255//31) for rgb in pal for c in rgb]
                    tile.putpalette(pixels + [0]*(768-len(pixels)))
                    tile.info['transparency'] = 0
                    tile = tile.convert('RGBA')
                    if word & 1024: tile = ImageOps.mirror(tile)
                    if word & 2048: tile = ImageOps.flip(tile)
                    canvas.alpha_composite(tile, (cell['x']*16+(quadrant%2)*8,
                                                  cell['y']*16+(quadrant//2)*8))
        stem = layout['name'].removesuffix('_Layout')
        canvas.save(output / (stem+'.png'))
        # Separate collision overlay so the reference stays faithful.
        overlay = canvas.resize((canvas.width*3, canvas.height*3), Image.Resampling.NEAREST)
        draw = ImageDraw.Draw(overlay, 'RGBA')
        for c in layout['cells']:
            if c['collision']:
                x,y = c['x']*48,c['y']*48
                draw.rectangle((x,y,x+47,y+47), fill=(245,40,65,60))
        overlay.save(output / (stem+'-collision.png'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'pokeemerald')
    parser.add_argument('--out', type=Path, default=ROOT/'unreal/Emerald/Content/Imported/Data/littleroot.json')
    parser.add_argument('--references', type=Path)
    args = parser.parse_args()
    data = Importer(args.source).run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, indent=2)+'\n')
    temporary.replace(args.out)
    lock = {'repository': 'https://github.com/pret/pokeemerald',
            'revision': data['source_revision'], 'source_hashes': data['source_hashes']}
    (ROOT/'data/source-lock.json').write_text(json.dumps(lock, indent=2)+'\n')
    report = {'source_revision': data['source_revision'],
              'maps': [{'name': m['name'], 'width': m['geometry']['width'],
                        'height': m['geometry']['height'], 'cells': len(m['geometry']['cells']),
                        **{key: len(m[key]) for key in EVENT_KEYS}} for m in data['maps']],
              'layout_variants': [v['name'] for v in data['layout_variants']],
              'warp_links': len(data['warp_links']), 'reachable_script_labels': len(data['scripts']),
              'missing_entrypoints': data['missing_entrypoints'],
              'runtime_semantics_verified': False}
    (ROOT/'data/import-report.json').write_text(json.dumps(report, indent=2)+'\n')
    if args.references:
        render_references(args.source, data, args.references)
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
