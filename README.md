# Altium Headers & Connectors

Generated pin-header and connector schematic symbols for Altium Designer, every
one produced from first principles by [tools/generate_symbols.py](tools/generate_symbols.py)
using [altium-monkey](https://pypi.org/project/altium-monkey/) — nothing is
hand-drawn. Symbol metadata (display name + category) lives in
[symbols.yaml](symbols.yaml), which the generator also writes.

## Browse

**[Browse & import on Sideband →](https://getsideband.com/libraries/altium-headers)**

Preview every symbol, then import the ones you need straight into Sideband.

## Families

Pin headers, sockets and jumpers all share the same nomenclature and geometry —
single (`N`), dual zig-zag (`NX2`), and dual column-sequential (`NX2A`):

| Family | Name pattern | Range | Notes |
|---|---|---|---|
| Pin header | `Header N` / `NX2` / `NX2A` | N = 1…100 | blue outline body, numbered pins |
| Socket (female) | `Socket N` / `NX2` / `NX2A` | N = 1…100 | same as headers + receptacle cup per pin |
| Jumper / link | `Jumper N` / `NX2` / `NX2A` | N = 1…100 | same as headers, jumper/select naming |
| Boxed / shrouded IDC | `Header IDC T` | T = 2…100 even | dual row + polarizing notch + pin-1 marker |
| Terminal block | `Terminal Block N` | N = 1…100 | N-way screw terminal (screw + slot per way) |

**Full sweeps, no curation** — every size in range is generated (dual/angled run
to 200 physical pins; IDC `T` is total pins, even only = 2×rows). 1050 symbols,
each with an SVG preview.

Shared conventions: 100 mil grid, 200 mil pins, electrical type *Passive*; the
visible number is the pin *name* (designator hidden); blue body outline with a
pale-yellow (non-solid) fill; component designator `P?`.

Each family/variant is stored in its own folder under `symbols/` (mirrored under
`previews/`):

```
symbols/
  Pin Headers - Single Row/        Header N
  Pin Headers - Dual Row/          Header NX2
  Pin Headers - Dual Row Angled/   Header NX2A
  Sockets - Single Row/            Socket N
  Sockets - Dual Row/              Socket NX2
  Sockets - Dual Row Angled/       Socket NX2A
  Jumpers - Single Row/            Jumper N
  Jumpers - Dual Row/              Jumper NX2
  Jumpers - Dual Row Angled/       Jumper NX2A
  Boxed Headers IDC/               Header IDC T
  Terminal Blocks/                 Terminal Block N
```

## Previews

An SVG of every symbol is rendered into [previews/](previews/) for quick visual
inspection on GitHub. They are build artifacts — the catalog previews on Sideband
are rendered server-side from the `.SchLib` files.

## Generating

```bash
pip install -r tools/requirements.txt

python tools/generate_symbols.py                  # full set + SVGs + symbols.yaml
python tools/generate_symbols.py --no-svg         # skip previews
python tools/generate_symbols.py --single 1-40 --dual 1-40 --angled "" \
    --socket-single 1-40 --socket-dual 1-40 --no-extras
```

Counts accept comma lists and `A-B` ranges (e.g. `"1-100,128"`); an empty string
disables a family. `symbols.yaml` is regenerated every run unless `--no-manifest`.

## Publishing

This repo **self-publishes** to the Sideband catalog. On every push to `main`, the
[Publish workflow](.github/workflows/publish.yml) sends the raw `.SchLib` files and
the `symbols.yaml` metadata to Sideband, which renders previews server-side and
publishes the catalog entry.

```bash
pip install -r requirements.txt
export SIDEBAND_API_URL=https://…
export SIDEBAND_CATALOG_URL=https://getsideband.com
export SIDEBAND_PUBLISH_TOKEN=…
python publish.py
```
