#!/usr/bin/env python3
"""Generate standard header / connector schematic symbols (.SchLib).

Everything in this library is generated from first principles with
`altium-monkey`, not hand-drawn in Altium. Families produced:

  single      "Header N"            N pins, single row                 (300 mil)
  dual        "Header NX2"          2N pins, zig-zag numbering          (400 mil)
  angled      "Header NX2A"         2N pins, column-sequential numbers  (400 mil)
  socket      "Socket N"/"Socket NX2"   female receptacle counterparts  (cup cue)
  idc         "Header IDC T"        boxed/shrouded dual row, notch+pin1 (400 mil)
  jumper      "Jumper N"/"Jumper 2X2"   small select/link headers
  terminal    "Terminal Block N"    N-way screw terminal block         (400 mil)

Shared conventions (matching the legacy library so symbols drop in cleanly):
  * 100 mil grid, pins length 200 mil, electrical type Passive
  * the pin *name* shows the number; the pin designator is hidden
  * left pins point Left (180 deg) at x=0; right pins point Right (0 deg) at x=400
  * body rectangle (0, -100*(rows+1)) -> (width, 0), blue outline, pale-yellow
    fill (not solid); component designator "P?"; empty "Comment" parameter below

Usage
-----
    pip install -r tools/requirements.txt

    python tools/generate_symbols.py                  # full default set + SVGs + manifest
    python tools/generate_symbols.py --no-svg         # skip SVG previews
    python tools/generate_symbols.py --single 1-40 --dual 1-40 --angled "" \
        --socket-single 1-40 --socket-dual 1-40 --no-extras

Counts accept comma lists and A-B ranges, e.g. "1-100,128". An empty string
disables a family. By default the standard set is generated:
  single/dual/angled 1-100, socket single/dual 1-100, plus IDC / jumper /
  terminal families.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from altium_monkey import (
    AltiumSchLib,
    LineWidth,
    PinElectrical,
    Rotation90,
    SchPointMils,
    make_sch_pin,
)

# ── Geometry / style constants ────────────────────────────────────────────────
PITCH = 100
PIN_LEN = 200
ROW_GAP = 400          # right-column x for dual rows
W_SINGLE = 300
W_DUAL = 400
W_TERM = 400
LINE_COLOR = 0xFF0000  # blue outline   (Altium BGR-packed int)
FILL_COLOR = 0xB0FFFF  # pale-yellow fill
MARK_COLOR = 0x0000FF  # red  (pin-1 marker)
DESIGNATOR_TEXT = "P?"
DESIGNATOR_COLOR = 8388608
DESIGNATOR_FONT_ID = 1

SYMBOLS_DIR = Path("symbols")
SVG_DIR = Path("previews")

# Default counts. N is the number that appears in the symbol name (= rows; for
# dual families the real pin count is 2N).
DEFAULT_RANGE = "1-100"
IDC_TOTALS = [6, 10, 14, 16, 20, 26, 34, 40, 50, 60, 64]   # total pins (2 x rows)
JUMPER_SINGLE = [2, 3]
TERMINAL_WAYS = list(range(2, 13))                          # 2..12 way


# ── Low-level primitive helpers ───────────────────────────────────────────────
def _pin(sym, designator: int, name: int, x: int, row: int, orientation) -> None:
    sym.add_pin(
        make_sch_pin(
            designator=str(designator),
            name=str(name),
            location_mils=SchPointMils.from_mils(x, -PITCH * row),
            orientation=orientation,
            length_mils=PIN_LEN,
            electrical_type=PinElectrical.PASSIVE,
            name_visible=True,
            designator_visible=False,
        )
    )


def _pin_left(sym, designator: int, name: int, row: int) -> None:
    _pin(sym, designator, name, 0, row, Rotation90.DEG_180)


def _pin_right(sym, designator: int, name: int, row: int) -> None:
    _pin(sym, designator, name, ROW_GAP, row, Rotation90.DEG_0)


def _body(sym, rows: int, width: int) -> int:
    """Add the body rectangle; return its bottom Y (y1)."""
    y1 = -PITCH * (rows + 1)
    sym.add_rectangle(
        0, y1, width, 0,
        color=LINE_COLOR, area_color=FILL_COLOR,
        line_width=LineWidth.SMALL, is_solid=False,
    )
    return y1


def _finish(sym, y1: int) -> None:
    sym.add_designator(DESIGNATOR_TEXT, 0, 0,
                       color=DESIGNATOR_COLOR, font_id=DESIGNATOR_FONT_ID)
    sym.add_parameter("Comment", "", x=0, y=y1 - PITCH)


def _new(name: str, description: str):
    lib = AltiumSchLib()
    return lib, lib.add_symbol(name, description=description)


# ── Family builders ───────────────────────────────────────────────────────────
def build_single(n: int):
    lib, s = _new(f"Header {n}", f"Header, {n}-Pin")
    for i in range(1, n + 1):
        _pin_left(s, i, i, i)
    _finish(s, _body(s, n, W_SINGLE))
    return f"Header {n}", lib, f"{n}-Pin Header", "Header"


def build_dual(n: int):
    lib, s = _new(f"Header {n}X2", f"Header, {n}-Pin, Dual row")
    for i in range(1, n + 1):
        _pin_left(s, 2 * i - 1, 2 * i - 1, i)
        _pin_right(s, 2 * i, 2 * i, i)
    _finish(s, _body(s, n, W_DUAL))
    return f"Header {n}X2", lib, f"{n}×2 Pin Header", "Header"


def build_angled(n: int):
    lib, s = _new(f"Header {n}X2A", f"Header, {n}-Pin, Dual row")
    for i in range(1, n + 1):
        _pin_left(s, i, i, i)
    for i in range(1, n + 1):
        _pin_right(s, n + i, n + i, i)
    _finish(s, _body(s, n, W_DUAL))
    return f"Header {n}X2A", lib, f"{n}×2 Pin Header (Angled)", "Header"


def _socket_cup(sym, x: int, row: int, facing_left: bool) -> None:
    """A small semicircular 'cup' at a pin's inner end to read as a receptacle."""
    y = -PITCH * row
    if facing_left:   # left-column pin (enters from the west): ')' opening west
        sym.add_arc(x, y, 30, start_angle=-90, end_angle=90,
                    color=LINE_COLOR, line_width=LineWidth.SMALL)
    else:             # right-column pin (enters from the east): '(' opening east
        sym.add_arc(x, y, 30, start_angle=90, end_angle=270,
                    color=LINE_COLOR, line_width=LineWidth.SMALL)


def build_socket_single(n: int):
    lib, s = _new(f"Socket {n}", f"Socket (Female header), {n}-Pin")
    for i in range(1, n + 1):
        _pin_left(s, i, i, i)
    y1 = _body(s, n, W_SINGLE)
    for i in range(1, n + 1):
        _socket_cup(s, 0, i, facing_left=True)
    _finish(s, y1)
    return f"Socket {n}", lib, f"{n}-Pin Socket", "Socket"


def build_socket_dual(n: int):
    lib, s = _new(f"Socket {n}X2", f"Socket (Female header), {n}-Pin, Dual row")
    for i in range(1, n + 1):
        _pin_left(s, 2 * i - 1, 2 * i - 1, i)
        _pin_right(s, 2 * i, 2 * i, i)
    y1 = _body(s, n, W_DUAL)
    for i in range(1, n + 1):
        _socket_cup(s, 0, i, facing_left=True)
        _socket_cup(s, ROW_GAP, i, facing_left=False)
    _finish(s, y1)
    return f"Socket {n}X2", lib, f"{n}×2 Pin Socket", "Socket"


def build_idc(total: int):
    rows = total // 2
    name = f"Header IDC {total}"
    lib, s = _new(name, f"Boxed/shrouded header, 2×{rows}, {total}-Pin (IDC)")
    for i in range(1, rows + 1):
        _pin_left(s, 2 * i - 1, 2 * i - 1, i)
        _pin_right(s, 2 * i, 2 * i, i)
    y1 = _body(s, rows, W_DUAL)
    cx = W_DUAL // 2
    # polarizing notch dipping down from the top edge
    s.add_polyline(
        [(cx - 40, 0), (cx - 40, -50), (cx + 40, -50), (cx + 40, 0)],
        color=0, line_width=LineWidth.SMALL,
    )
    # pin-1 marker: small filled red triangle inside the body near pin 1
    s.add_polygon(
        [(40, -70), (40, -130), (90, -100)],
        color=MARK_COLOR, area_color=MARK_COLOR, is_solid=True,
    )
    _finish(s, y1)
    return name, lib, f"{total}-Pin Boxed Header (2×{rows})", "Boxed Header"


def build_jumper_single(n: int):
    lib, s = _new(f"Jumper {n}", f"Jumper / link header, {n}-Pin")
    for i in range(1, n + 1):
        _pin_left(s, i, i, i)
    _finish(s, _body(s, n, W_SINGLE))
    return f"Jumper {n}", lib, f"{n}-Pin Jumper", "Jumper"


def build_jumper_2x2():
    lib, s = _new("Jumper 2X2", "Jumper / select header, 2×2, 4-Pin")
    for i in range(1, 3):
        _pin_left(s, 2 * i - 1, 2 * i - 1, i)
        _pin_right(s, 2 * i, 2 * i, i)
    _finish(s, _body(s, 2, W_DUAL))
    return "Jumper 2X2", lib, "2×2 Pin Jumper", "Jumper"


def build_terminal(n: int):
    name = f"Terminal Block {n}"
    lib, s = _new(name, f"Screw terminal block, {n}-Way")
    for i in range(1, n + 1):
        _pin_left(s, i, i, i)
    y1 = _body(s, n, W_TERM)
    for i in range(1, n + 1):
        y = -PITCH * i
        s.add_arc(70, y, 30, color=0, line_width=LineWidth.SMALL)         # screw
        s.add_line(50, y + 20, 90, y - 20, color=0, line_width=LineWidth.SMALL)  # slot
    _finish(s, y1)
    return name, lib, f"{n}-Way Terminal Block", "Terminal Block"


# ── Plan assembly ─────────────────────────────────────────────────────────────
def _parse_counts(spec: str) -> list[int]:
    out: set[int] = set()
    for chunk in (spec or "").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            lo, hi = chunk.split("-", 1)
            out.update(range(int(lo), int(hi) + 1))
        else:
            out.add(int(chunk))
    return sorted(out)


def build_plan(args) -> list:
    """Return an ordered list of zero-arg builder thunks."""
    plan: list = []
    plan += [(build_single, n) for n in _parse_counts(args.single)]
    plan += [(build_dual, n) for n in _parse_counts(args.dual)]
    plan += [(build_angled, n) for n in _parse_counts(args.angled)]
    plan += [(build_socket_single, n) for n in _parse_counts(args.socket_single)]
    plan += [(build_socket_dual, n) for n in _parse_counts(args.socket_dual)]
    if not args.no_extras:
        plan += [(build_idc, t) for t in IDC_TOTALS]
        plan += [(build_jumper_single, n) for n in JUMPER_SINGLE]
        plan += [(build_jumper_2x2, None)]
        plan += [(build_terminal, n) for n in TERMINAL_WAYS]
    return plan


# ── Manifest ──────────────────────────────────────────────────────────────────
CATEGORY_ORDER = ["Header", "Socket", "Boxed Header", "Jumper", "Terminal Block"]


def write_manifest(path: Path, rows: list[tuple[str, str, str]]) -> None:
    """rows = [(file_rel, display_name, category), ...]; write a fresh manifest."""
    by_cat: dict[str, list[tuple[str, str]]] = {}
    for file_rel, name, cat in rows:
        by_cat.setdefault(cat, []).append((file_rel, name))

    lines = [
        "# Altium Headers & Connectors — Symbol Manifest",
        "# GENERATED by tools/generate_symbols.py — do not edit by hand.",
        "",
        "symbols:",
        "",
    ]
    cats = [c for c in CATEGORY_ORDER if c in by_cat]
    cats += [c for c in by_cat if c not in CATEGORY_ORDER]
    for cat in cats:
        lines.append(f"  # ── {cat} " + "─" * max(0, 60 - len(cat)))
        lines.append("")
        for file_rel, name in by_cat[cat]:
            lines.append(f'  - file: "{file_rel}"')
            lines.append(f"    name: {name}")
            lines.append(f"    category: {cat}")
            lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--single", default=DEFAULT_RANGE)
    ap.add_argument("--dual", default=DEFAULT_RANGE)
    ap.add_argument("--angled", default=DEFAULT_RANGE)
    ap.add_argument("--socket-single", default=DEFAULT_RANGE, dest="socket_single")
    ap.add_argument("--socket-dual", default=DEFAULT_RANGE, dest="socket_dual")
    ap.add_argument("--no-extras", action="store_true",
                    help="skip IDC / jumper / terminal-block families")
    ap.add_argument("--no-svg", action="store_true", help="do not render SVG previews")
    ap.add_argument("--no-manifest", action="store_true",
                    help="do not (re)write symbols.yaml")
    ap.add_argument("--out", default=str(repo_root / SYMBOLS_DIR))
    ap.add_argument("--svg-out", default=str(repo_root / SVG_DIR))
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    svg_dir = Path(args.svg_out)
    if not args.no_svg:
        svg_dir.mkdir(parents=True, exist_ok=True)

    plan = build_plan(args)
    rows: list[tuple[str, str, str]] = []
    for builder, arg in plan:
        name, lib, display, category = builder() if arg is None else builder(arg)
        path = out_dir / f"{name}.SchLib"
        lib.save(path)
        try:
            file_rel = path.resolve().relative_to(repo_root).as_posix()
        except ValueError:
            file_rel = (SYMBOLS_DIR / path.name).as_posix()
        rows.append((file_rel, display, category))
        if not args.no_svg:
            (svg_dir / f"{name}.svg").write_text(
                lib.symbol_to_svg(name), encoding="utf-8")

    print(f"Generated {len(rows)} symbols into {out_dir}")
    if not args.no_svg:
        print(f"Rendered {len(rows)} SVGs into {svg_dir}")
    if not args.no_manifest:
        write_manifest(repo_root / "symbols.yaml", rows)
        print(f"Wrote symbols.yaml ({len(rows)} entries)")


if __name__ == "__main__":
    main()
