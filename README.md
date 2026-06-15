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

| Family | Name pattern | Pins | Notes |
|---|---|---|---|
| Single row | `Header N` | N | one column, 1…N down the left (300 mil body) |
| Dual row | `Header NX2` | 2N | zig-zag numbering 1,2 / 3,4 / … (400 mil) |
| Dual row, angled | `Header NX2A` | 2N | column-sequential: left 1…N, right N+1…2N |
| Socket (female) | `Socket N`, `Socket NX2` | N / 2N | receptacle counterparts, cup cue per pin |
| Boxed / shrouded IDC | `Header IDC T` | T | dual row with polarizing notch + pin-1 marker |
| Jumper | `Jumper 2`, `Jumper 3`, `Jumper 2X2` | 2–4 | small link / select headers |
| Terminal block | `Terminal Block N` | N | N-way screw terminal (screw + slot per way) |

`Header`/`Socket` single, dual and angled families cover **1–100** in the name
(so dual/angled run up to 200 physical pins). Boxed IDC uses the standard sizes
(6, 10, 14, 16, 20, 26, 34, 40, 50, 60, 64); terminal blocks are 2–12 way.

Each family is stored in its own folder under `symbols/` (mirrored under
`previews/`):

```
symbols/
  Pin Headers - Single Row/        Header N
  Pin Headers - Dual Row/          Header NX2
  Pin Headers - Dual Row Angled/   Header NX2A
  Sockets/                         Socket N, Socket NX2
  Boxed Headers IDC/               Header IDC T
  Jumpers/                         Jumper 2/3/2X2
  Terminal Blocks/                 Terminal Block N
```

Shared conventions: 100 mil grid, 200 mil pins, electrical type *Passive*; the
visible number is the pin *name* (designator hidden); blue body outline with a
pale-yellow (non-solid) fill; component designator `P?`.

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
