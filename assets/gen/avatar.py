#!/usr/bin/env python3
"""Gera as opções de foto de perfil (SVG + PNG 1024) no mesmo tema do banner.

Uso: cd assets/gen && python3 avatar.py   (precisa de rsvg-convert)
O GitHub recorta em círculo: o desenho fica no miolo, longe da borda.
"""
import subprocess

S = 1024
C = dict(bg="#1a1b26", bg2="#24283b", panel="#1f2335", line="#3b4261", comment="#565f89",
         fg="#c0caf5", blue="#7aa2f7", cyan="#7dcfff", magenta="#bb9af7", green="#9ece6a",
         red="#f7768e", teal="#1abc9c", yellow="#e0af68")


def base(extra_defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}">'
            f'<defs>'
            f'<radialGradient id="bgG" cx=".5" cy=".42" r=".75"><stop offset="0" stop-color="{C["bg2"]}"/>'
            f'<stop offset="1" stop-color="#13141c"/></radialGradient>'
            f'<linearGradient id="acc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C["cyan"]}"/>'
            f'<stop offset=".5" stop-color="{C["blue"]}"/><stop offset="1" stop-color="{C["magenta"]}"/></linearGradient>'
            f'<linearGradient id="ring" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C["cyan"]}"/>'
            f'<stop offset=".5" stop-color="{C["blue"]}"/><stop offset="1" stop-color="{C["magenta"]}"/></linearGradient>'
            f'<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="28"/></filter>'
            f'{extra_defs}</defs>'
            f'<rect width="{S}" height="{S}" fill="url(#bgG)"/>'
            f'<circle cx="512" cy="512" r="488" fill="none" stroke="url(#ring)" stroke-width="10" stroke-opacity=".55"/>')


def cells_path(rows, x0, y0, cw, ch, char="#"):
    """Blocos contíguos de cada linha viram um retângulo; um path só, sem emendas."""
    d = []
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            if row[c] == char:
                s = c
                while c < len(row) and row[c] == char:
                    c += 1
                d.append(f"M{x0 + s * cw} {y0 + r * ch}h{(c - s) * cw}v{ch}h{-(c - s) * cw}z")
            else:
                c += 1
    return "".join(d)


def fit(rows, cell, cy=512):
    w, h = max(map(len, rows)) * cell, len(rows) * cell
    return (S - w) / 2, cy - h / 2


# A: prompt "❯_" em blocos, como o logo do banner
def opt_prompt():
    rows = [
        "###............",
        "###............",
        "..###..........",
        "..###..........",
        "....###........",
        "....###........",
        "..###..........",
        "..###..........",
        "###......######",
        "###......######",
    ]
    cell = 44
    x0, y0 = fit(rows, cell, 512)
    d = cells_path(rows, x0, y0, cell, cell)
    return (base() + f'<path d="{d}" fill="url(#acc)" filter="url(#glow)" opacity=".55"/>'
            f'<path d="{d}" fill="url(#acc)"/></svg>')


# B: janelas em tiling (Hyprland), a ativa com a borda em degradê e o prompt dentro
def opt_tiling():
    out = [base()]
    g, r = 22, 30
    L, T, R, B = 222, 232, 802, 792
    mid = 512 - g / 2 + 40
    wins = [(L, T, mid - L, B - T, True),
            (mid + g, T, R - mid - g, 250, False),
            (mid + g, T + 250 + g, (R - mid - g - g) / 2, B - T - 250 - g, False),
            (mid + g + (R - mid - g - g) / 2 + g, T + 250 + g, (R - mid - g - g) / 2, B - T - 250 - g, False)]
    for x, y, w, h, active in wins:
        if active:
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="none" stroke="url(#acc)" '
                       f'stroke-width="14" filter="url(#glow)" opacity=".7"/>')
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{C["panel"]}" '
                       f'stroke="url(#acc)" stroke-width="9"/>')
        else:
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{C["panel"]}" '
                       f'fill-opacity=".85" stroke="{C["line"]}" stroke-width="6"/>')
    # prompt na janela ativa
    rows = ["##....", ".##...", "..##..", ".##...", "##.###"]
    cell = 30
    ax, ay, aw, ah = wins[0][:4]
    x0 = ax + (aw - 6 * cell) / 2
    y0 = ay + (ah - 5 * cell) / 2
    out.append(f'<path d="{cells_path(rows, x0, y0, cell, cell)}" fill="url(#acc)"/>')
    # "linhas de texto" nas outras
    x, y, w, h, _ = wins[1]
    for i, (ww, col) in enumerate([(.62, C["blue"]), (.8, C["comment"]), (.45, C["comment"])]):
        out.append(f'<rect x="{x + 34}" y="{y + 52 + i * 52}" width="{(w - 68) * ww}" height="18" rx="9" fill="{col}" fill-opacity=".8"/>')
    x, y, w, h, _ = wins[2]
    out.append(f'<circle cx="{x + w / 2}" cy="{y + h / 2}" r="{w * .22}" fill="none" stroke="{C["green"]}" stroke-width="12"/>')
    x, y, w, h, _ = wins[3]
    for i, col in enumerate([C["red"], C["yellow"], C["green"]]):
        out.append(f'<rect x="{x + 30}" y="{y + 60 + i * 56}" width="{w - 60}" height="22" rx="11" fill="{col}" fill-opacity=".75"/>')
    out.append("</svg>")
    return "".join(out)


# C: DualSense em pixel art, lightbar em degradê
def opt_gamepad():
    body = [
        "...#####......#####...",
        "..##################..",
        ".####################.",
        "######################",
        "######################",
        "######################",
        "######################",
        "########......########",
        "#######........#######",
        "######..........######",
        ".####............####.",
        "..##..............##..",
    ]
    cell = 34
    x0, y0 = fit(body, cell, 520)
    out = [base()]
    d = cells_path(body, x0, y0, cell, cell)
    out.append(f'<path d="{d}" fill="url(#acc)" filter="url(#glow)" opacity=".45"/>')
    out.append(f'<path d="{d}" fill="url(#acc)"/>')

    def px(c, r, col, w=1, h=1):
        out.append(f'<rect x="{x0 + c * cell}" y="{y0 + r * cell}" width="{w * cell}" height="{h * cell}" fill="{col}"/>')

    # touchpad, com a lightbar acesa nas laterais
    px(7, 1, C["cyan"], 1, 3)
    px(14, 1, C["magenta"], 1, 3)
    px(8, 1, C["panel"], 6, 3)
    # d-pad
    for c, r in [(3, 3), (2, 4), (3, 4), (4, 4), (3, 5)]:
        px(c, r, C["panel"])
    # botões
    for c, r, col in [(18, 3, C["teal"]), (17, 4, C["magenta"]), (19, 4, C["red"]), (18, 5, C["cyan"])]:
        px(c, r, C["panel"])
        out.append(f'<rect x="{x0 + c * cell + 7}" y="{y0 + r * cell + 7}" width="{cell - 14}" height="{cell - 14}" rx="3" fill="{col}"/>')
    # analógicos
    for c in (6, 14):
        px(c, 5, C["panel"], 2, 2)
        out.append(f'<rect x="{x0 + c * cell + 12}" y="{y0 + 5 * cell + 12}" width="{2 * cell - 24}" height="{2 * cell - 24}" rx="4" fill="{C["line"]}"/>')
    # LEDs do jogador
    for c in (9, 10, 11, 12):
        px(c, 5, C["panel"])
    px(10, 5, C["fg"], 2, 1)
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    for name, fn in [("avatar-a-prompt", opt_prompt), ("avatar-b-tiling", opt_tiling), ("avatar-c-gamepad", opt_gamepad)]:
        with open(f"{name}.svg", "w") as f:
            f.write(fn())
        subprocess.run(["rsvg-convert", "-w", str(S), "-h", str(S), f"{name}.svg", "-o", f"{name}.png"], check=True)
        print(name)
