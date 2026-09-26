#!/usr/bin/env python3
"""Gera os banners SVG do perfil. Texto convertido em contornos (sem depender de fonte instalada).

Uso: cd assets/gen && uv run --with fonttools --with uharfbuzz python gen.py && cp b-fetch.svg ../banner.svg
Requer JetBrains Mono Nerd Font instalada (fonte do Omarchy). O banner do perfil é o b-fetch.
"""
import io

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

MONO = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf"
MONO_B = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Bold.ttf"

# Tokyo Night (tema padrão do Omarchy)
C = dict(
    bg0="#16161e", bg="#1a1b26", bg2="#24283b", hl="#292e42", line="#3b4261",
    fg="#c0caf5", fg2="#a9b1d6", dim="#737aa2", comment="#565f89",
    blue="#7aa2f7", cyan="#7dcfff", magenta="#bb9af7", green="#9ece6a",
    orange="#ff9e64", red="#f7768e", yellow="#e0af68", teal="#1abc9c",
)

ICON = dict(arch="", pad="\U000f02b4", wifi="\U000f05a9", batt="\U000f0079",
            clock="\U000f0150", pin="\U000f034e", shield="\U000f0565", console="\U000f018d",
            whats="\U000f05a3", robot="\U000f06a9")


def num(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


class Font:
    def __init__(self, path, features=None):
        tt = TTFont(path)
        tt.flavor = None
        b = io.BytesIO()
        tt.save(b)
        data = b.getvalue()
        self.tt = TTFont(io.BytesIO(data))
        self.gs = self.tt.getGlyphSet()
        self.upm = self.tt["head"].unitsPerEm
        self.hb = hb.Font(hb.Face(hb.Blob(data)))
        self.features = features or {}

    def run(self, text, size, x, y, tracking=0.0):
        """Contorno do texto com baseline em y. Retorna (d, largura, bordas-por-glifo)."""
        s = size / self.upm
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, self.features)
        cx, parts, edges = x, [], []
        for inf, p in zip(buf.glyph_infos, buf.glyph_positions):
            name = self.tt.getGlyphName(inf.codepoint)
            pen = SVGPathPen(self.gs, ntos=num)
            self.gs[name].draw(TransformPen(pen, (s, 0, 0, -s, cx + p.x_offset * s, y - p.y_offset * s)))
            d = pen.getCommands()
            if d:
                parts.append(d)
            cx += p.x_advance * s + tracking * size
            edges.append(cx - x)
        width = cx - x - (tracking * size if edges else 0)
        return " ".join(parts), width, edges

    def width(self, text, size, tracking=0.0):
        return self.run(text, size, 0, 0, tracking)[1]


mono = Font(MONO, {"calt": False, "liga": False})
mono_b = Font(MONO_B, {"calt": False, "liga": False})
inter8 = Font("fonts/inter-800.woff", {"kern": True})
inter6 = Font("fonts/inter-600.woff", {"kern": True})


def text(font, s, size, x, y, fill, anchor="start", tracking=0.0, attrs=""):
    w = font.width(s, size, tracking)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    d, w, _ = font.run(s, size, x, y, tracking)
    return f'<path d="{d}" fill="{fill}"{attrs}/>', w


def spans(font, segs, size, x, y, tracking=0.0):
    """Segmentos coloridos numa linha. Retorna (svg, largura, bordas absolutas relativas a x)."""
    out, edges, cx = [], [], x
    for s, fill in segs:
        d, w, e = font.run(s, size, cx, y, tracking)
        if d:
            out.append(f'<path d="{d}" fill="{fill}"/>')
        edges += [cx - x + v for v in e]
        cx += w + (tracking * size if s else 0)
    return "".join(out), cx - x, edges


# ---------- animação (SMIL: roda dentro de <img> no GitHub) ----------

def kt(points, T):
    """points: [(t, valor)] -> keyTimes/values para calcMode discreto."""
    pts = sorted(points)
    if pts[0][0] != 0:
        pts.insert(0, (0, pts[0][1]))
    kts = ";".join(f"{t / T:.4f}" for t, _ in pts)
    vals = ";".join(str(v) for _, v in pts)
    return kts, vals


def discrete(attr, points, T):
    k, v = kt(points, T)
    return (f'<animate attributeName="{attr}" dur="{T}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{k}" values="{v}"/>')


def fade(t_in, t_out, T, d_in=0.35, d_out=0.4):
    """Opacidade 0 -> 1 em t_in, 1 -> 0 em t_out, ciclo T."""
    pts = [(0, 0), (t_in, 0), (t_in + d_in, 1), (t_out, 1), (t_out + d_out, 0), (T, 0)]
    k = ";".join(f"{t / T:.4f}" for t, _ in pts)
    v = ";".join(str(x) for _, x in pts)
    return (f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" '
            f'keyTimes="{k}" values="{v}"/>')


def typing_clip(cid, x, y_top, h, edges, t0, t1, t_hide, T):
    n = len(edges)
    pts = [(0, 0), (t0, 0)]
    for i, e in enumerate(edges, 1):
        pts.append((t0 + (t1 - t0) * i / n, round(e + 1, 1)))
    pts.append((t_hide, 0))
    full = round(edges[-1] + 1, 1)
    return (f'<clipPath id="{cid}"><rect x="{num(x)}" y="{y_top}" width="{full}" height="{h}">'
            f'{discrete("width", pts, T)}</rect></clipPath>')


def frame(w, h, r=18):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="Atos Lins">')


def gradient_border(gid, x, y, w, h, colors, dur=10):
    cx, cy = x + w / 2, y + h / 2
    stops = "".join(f'<stop offset="{i / (len(colors) - 1):.2f}" stop-color="{c}"/>' for i, c in enumerate(colors))
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x}" y1="{cy}" x2="{x + w}" y2="{cy}">{stops}'
            f'<animateTransform attributeName="gradientTransform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" '
            f'dur="{dur}s" repeatCount="indefinite"/></linearGradient>')


# =====================================================================
# A: mini desktop do Omarchy (barra + janelas em tiling)
# =====================================================================

def banner_desktop():
    W, H, T = 1200, 400, 14
    defs, body = [], []
    defs.append(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>')
    defs.append(f'<radialGradient id="g1" cx="1040" cy="40" r="520" gradientUnits="userSpaceOnUse">'
                f'<stop offset="0" stop-color="{C["magenta"]}" stop-opacity=".30"/><stop offset="1" stop-color="{C["magenta"]}" stop-opacity="0"/></radialGradient>')
    defs.append(f'<radialGradient id="g2" cx="120" cy="420" r="560" gradientUnits="userSpaceOnUse">'
                f'<stop offset="0" stop-color="{C["blue"]}" stop-opacity=".26"/><stop offset="1" stop-color="{C["blue"]}" stop-opacity="0"/></radialGradient>')
    defs.append(f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
                f'<circle cx="1" cy="1" r="1" fill="{C["fg2"]}" fill-opacity=".07"/></pattern>')
    defs.append(gradient_border("active", 16, 56, 600, 328, [C["cyan"], C["blue"], C["magenta"], C["cyan"]]))
    defs.append(f'<linearGradient id="name" x1="0" x2="1" y1="0" y2="0">'
                f'<stop offset="0" stop-color="{C["fg"]}"/><stop offset=".55" stop-color="{C["blue"]}"/>'
                f'<stop offset="1" stop-color="{C["magenta"]}"/></linearGradient>')
    defs.append('<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5"/></filter>')

    body.append(f'<rect width="{W}" height="{H}" fill="{C["bg0"]}"/>')
    body.append(f'<rect width="{W}" height="{H}" fill="url(#dots)"/>')
    body.append(f'<rect width="{W}" height="{H}" fill="url(#g1)"/><rect width="{W}" height="{H}" fill="url(#g2)"/>')

    # --- barra (estilo waybar) ---
    body.append(f'<rect x="16" y="14" width="1168" height="30" rx="9" fill="{C["bg"]}" fill-opacity=".9" stroke="{C["hl"]}"/>')
    p, _ = text(mono, ICON["arch"], 15, 32, 35, C["blue"])
    body.append(p)
    wx = 60
    for i in range(1, 6):
        if i == 1:
            body.append(f'<rect x="{wx - 6}" y="21" width="22" height="16" rx="8" fill="{C["blue"]}"/>')
            p, _ = text(mono_b, str(i), 12, wx + 5, 33.5, C["bg"], "middle")
        else:
            p, _ = text(mono, str(i), 12, wx + 5, 33.5, C["comment"], "middle")
        body.append(p)
        wx += 26
    p, _ = text(mono, "atoslins@omarchy", 13, W / 2, 34, C["fg2"], "middle")
    body.append(p)
    rx = 1168
    right = [(ICON["pad"] + " 82%", C["magenta"]), (ICON["wifi"], C["blue"]), (ICON["batt"], C["green"])]
    for s, fill in reversed(right):
        p, w = text(mono, s, 13, rx, 34, fill, "end")
        body.append(p)
        rx -= w + 18

    # --- janelas ---
    def win(x, y, w, h, active=False):
        stroke = "url(#active)" if active else C["line"]
        sw = 2 if active else 1.2
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="11" fill="{C["bg"]}" fill-opacity=".94" '
                f'stroke="{stroke}" stroke-width="{sw}"/>')

    body.append(win(16, 56, 600, 328, True))
    body.append(win(628, 56, 556, 160))
    body.append(win(628, 228, 272, 156))
    body.append(win(912, 228, 272, 156))

    # janela principal: identidade
    p, _ = text(mono, "HELLO, I'M  ·  OLÁ, EU SOU", 12.5, 48, 104, C["cyan"], tracking=0.14)
    body.append(p)
    p, nw = text(inter8, "Atos Lins", 84, 44, 186, "url(#name)", tracking=-0.025)
    body.append(p)
    cx = 48
    for label, col in [("Linux desktop", C["blue"]), ("Claude Code plugins", C["magenta"]), ("Automation", C["green"])]:
        w = mono.width(label, 13.5) + 26
        body.append(f'<rect x="{num(cx)}" y="212" width="{num(w)}" height="30" rx="15" fill="{col}" fill-opacity=".12" '
                    f'stroke="{col}" stroke-opacity=".45"/>')
        p, _ = text(mono, label, 13.5, cx + 13, 232, col)
        body.append(p)
        cx += w + 10
    p, _ = text(inter6, "Ferramentas para Linux, plugins para Claude Code e automação.", 15.5, 48, 286, C["fg2"])
    body.append(p)
    body.append(f'<line x1="48" y1="318" x2="584" y2="318" stroke="{C["hl"]}"/>')
    p, _ = spans(mono, [(ICON["pin"] + " ", C["red"]), ("Araraquara, SP · Brasil", C["dim"])], 13, 48, 352)[:2]
    body.append(p)
    p, _ = text(mono, "Python · TypeScript · PHP · Go · QML", 13, 584, 352, C["comment"], "end")
    body.append(p)

    # terminal: digitação
    X0, LH = 650, 26
    ys = [92, 118, 144, 170, 196]
    prompt = [("❯ ", C["green"])]
    l1 = [("omarchy", C["blue"]), (" plugin add atoslins.dualsense", C["fg"])]
    l2 = [("claude", C["blue"]), (" plugin install dod-guard", C["fg"])]
    pw = mono.width("❯ ", 15)

    t1a, t1b, o1, p2, t2a, t2b, o2, p3, HIDE = 0.8, 2.8, 3.2, 3.7, 4.0, 5.6, 6.0, 6.4, 12.4

    s, _, _ = spans(mono, prompt, 15, X0, ys[0])
    body.append(s)
    s, w1, e1 = spans(mono, l1, 15, X0 + pw, ys[0])
    defs.append(typing_clip("ty1", X0 + pw, ys[0] - 16, 22, e1, t1a, t1b, HIDE + 0.3, T))
    body.append(f'<g clip-path="url(#ty1)">{s}</g>')
    s, _, _ = spans(mono, [("  ✓ ", C["green"]), ("battery, lightbar, triggers", C["fg2"])], 15, X0, ys[1])
    body.append(f'<g opacity="1">{s}{fade(o1, HIDE, T)}</g>')
    s, _, _ = spans(mono, prompt, 15, X0, ys[2])
    body.append(f'<g>{s}{fade(p2, HIDE, T, 0.01)}</g>')
    s, w2, e2 = spans(mono, l2, 15, X0 + pw, ys[2])
    defs.append(typing_clip("ty2", X0 + pw, ys[2] - 16, 22, e2, t2a, t2b, HIDE + 0.3, T))
    body.append(f'<g clip-path="url(#ty2)">{s}</g>')
    s, _, _ = spans(mono, [("  ✓ ", C["green"]), ("definition of done enforced", C["fg2"])], 15, X0, ys[3])
    body.append(f'<g>{s}{fade(o2, HIDE, T)}</g>')
    s, _, _ = spans(mono, prompt, 15, X0, ys[4])
    body.append(f'<g>{s}{fade(p3, HIDE, T, 0.01)}</g>')

    # cursor: segue a digitação
    cw, ch = mono.width("M", 15), 19
    cur = [(0, X0 + pw, ys[0])]
    for i, e in enumerate(e1, 1):
        cur.append((t1a + (t1b - t1a) * i / len(e1), X0 + pw + e, ys[0]))
    cur.append((p2, X0 + pw, ys[2]))
    for i, e in enumerate(e2, 1):
        cur.append((t2a + (t2b - t2a) * i / len(e2), X0 + pw + e, ys[2]))
    cur.append((p3, X0 + pw, ys[4]))
    cur.append((HIDE + 0.4, X0 + pw, ys[0]))
    xs = [(t, round(x, 1)) for t, x, _ in cur]
    yv = [(t, y - 15) for t, _, y in cur]
    body.append(f'<rect x="{num(X0 + pw)}" y="{ys[4] - 15}" width="{num(cw)}" height="{ch}" rx="1.5" fill="{C["fg"]}">'
                f'{discrete("x", xs, T)}{discrete("y", yv, T)}'
                f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.05s" repeatCount="indefinite"/></rect>')

    # DualSense
    ox, oy = 764, 306
    defs.append(f'<linearGradient id="lb"><stop offset="0" stop-color="{C["cyan"]}">'
                f'<animate attributeName="stop-color" values="{C["cyan"]};{C["magenta"]};{C["red"]};{C["green"]};{C["cyan"]}" dur="7s" repeatCount="indefinite"/></stop>'
                f'<stop offset="1" stop-color="{C["magenta"]}">'
                f'<animate attributeName="stop-color" values="{C["magenta"]};{C["red"]};{C["green"]};{C["cyan"]};{C["magenta"]}" dur="7s" repeatCount="indefinite"/></stop></linearGradient>')
    pad = ("M-58,-40 C-28,-47 28,-47 58,-40 C77,-36 87,-26 91,-9 L100,33 C104,52 96,62 84,62 C74,62 66,55 60,46 "
           "L47,29 C38,25 -38,25 -47,29 L-60,46 C-66,55 -74,62 -84,62 C-96,62 -104,52 -100,33 L-91,-9 C-87,-26 -77,-36 -58,-40 Z")
    g = [f'<g transform="translate({ox} {oy}) scale(.86)">']
    g.append(f'<path d="{pad}" fill="{C["bg2"]}" stroke="{C["line"]}" stroke-width="1.6"/>')
    g.append('<g filter="url(#glow)" opacity=".9"><path d="M-37,-40 L-37,-8 M37,-40 L37,-8" stroke="url(#lb)" stroke-width="5" stroke-linecap="round"/></g>')
    g.append('<path d="M-37,-40 L-37,-8 M37,-40 L37,-8" stroke="url(#lb)" stroke-width="2.4" stroke-linecap="round"/>')
    g.append(f'<rect x="-32" y="-43" width="64" height="37" rx="6" fill="{C["hl"]}" stroke="{C["line"]}"/>')
    for i, dx in enumerate([-8, -4, 0, 4, 8]):
        g.append(f'<circle cx="{dx}" cy="1" r="1.3" fill="{C["fg"] if i == 2 else C["line"]}"/>')
    for dx, dy in [(0, -9), (0, 9), (-9, 0), (9, 0)]:
        g.append(f'<rect x="{-58 + dx - 3.5}" y="{-8 + dy - 3.5}" width="7" height="7" rx="1.5" fill="{C["comment"]}"/>')
    for dx, dy, col in [(0, -10, C["teal"]), (10, 0, C["red"]), (0, 10, C["blue"]), (-10, 0, C["magenta"])]:
        g.append(f'<circle cx="{58 + dx}" cy="{-8 + dy}" r="4.2" fill="none" stroke="{col}" stroke-width="1.6"/>')
    for sx in (-27, 27):
        g.append(f'<circle cx="{sx}" cy="20" r="12" fill="{C["bg0"]}" stroke="{C["line"]}"/>'
                 f'<circle cx="{sx}" cy="20" r="7" fill="{C["hl"]}"/>')
    g.append("</g>")
    body.append("".join(g))
    s, _, _ = spans(mono, [(ICON["pad"] + " ", C["magenta"]), ("dualsense", C["fg2"]), ("  82%", C["green"])], 12.5, 646, 255)
    body.append(s)

    # DoD-Guard
    s, _, _ = spans(mono, [(ICON["shield"] + " ", C["green"]), ("/dod:verify", C["fg2"])], 12.5, 930, 255)
    body.append(s)
    checks = ["tests actually run", "no stubs or TODOs", "proof attached"]
    for i, c in enumerate(checks):
        y = 284 + i * 23
        s, _, _ = spans(mono, [("✓ ", C["green"]), (c, C["fg"])], 13.5, 932, y)
        body.append(f'<g>{s}{fade(6.8 + i * 0.7, HIDE, T)}</g>')
    bw = mono_b.width("PASS", 12) + 24
    badge = (f'<rect x="932" y="344" width="{num(bw)}" height="22" rx="11" fill="{C["green"]}"/>'
             + text(mono_b, "PASS", 12, 932 + bw / 2, 359.5, C["bg"], "middle")[0])
    body.append(f'<g>{badge}{fade(9.2, HIDE, T, 0.25)}</g>')

    svg = frame(W, H) + "<defs>" + "".join(defs) + "</defs>" + '<g clip-path="url(#card)">' + "".join(body) + "</g></svg>"
    return svg


# =====================================================================
# B: fastfetch no terminal
# =====================================================================

def banner_fetch():
    W, H, T = 1200, 400, 16
    HIDE = 14.6
    defs, body = [], []
    # sem moldura externa: a janela ocupa o SVG inteiro e se funde ao fundo escuro do GitHub
    defs.append(f'<clipPath id="card"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>')
    defs.append(gradient_border("active", 1, 1, W - 2, H - 2, [C["cyan"], C["blue"], C["magenta"], C["cyan"]], 12))
    defs.append(f'<radialGradient id="g1" cx="190" cy="220" r="420" gradientUnits="userSpaceOnUse">'
                f'<stop offset="0" stop-color="{C["blue"]}" stop-opacity=".16"/><stop offset="1" stop-color="{C["blue"]}" stop-opacity="0"/></radialGradient>')
    defs.append(f'<linearGradient id="px" gradientUnits="userSpaceOnUse" x1="56" y1="92" x2="326" y2="352">'
                f'<stop offset="0" stop-color="{C["cyan"]}"/><stop offset=".5" stop-color="{C["blue"]}"/><stop offset="1" stop-color="{C["magenta"]}"/></linearGradient>')

    body.append(f'<rect width="{W}" height="{H}" fill="{C["bg"]}"/>')
    body.append(f'<rect width="{W}" height="{H}" fill="url(#g1)"/>')

    X0, Y0 = 44, 60
    prompt = [("~ ", C["cyan"]), ("❯ ", C["green"])]
    s, pw, _ = spans(mono, prompt, 16, X0, Y0)
    body.append(s)
    s, _, e = spans(mono, [("fastfetch", C["blue"])], 16, X0 + pw, Y0)
    defs.append(typing_clip("ty", X0 + pw, Y0 - 17, 23, e, 0.5, 1.4, HIDE + 0.3, T))
    body.append(f'<g clip-path="url(#ty)">{s}</g>')
    cw = mono.width("M", 16)
    cur = [(0, X0 + pw)] + [(0.5 + 0.9 * i / len(e), X0 + pw + v) for i, v in enumerate(e, 1)]
    xs = [(t, round(x, 1)) for t, x in cur]
    body.append(f'<rect x="{num(X0 + pw)}" y="{Y0 - 16}" width="{num(cw)}" height="20" rx="1.5" fill="{C["fg"]}">'
                f'{discrete("x", xs, T)}'
                f'{discrete("visibility", [(0, "visible"), (1.7, "hidden"), (HIDE + 0.4, "visible")], T)}'
                f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.05s" repeatCount="indefinite"/></rect>')

    # logo do Omarchy, o mesmo ASCII que o fastfetch imprime (célula de terminal 1:2)
    lines = open("omarchy-logo.txt", encoding="utf-8").read().rstrip("\n").split("\n")
    RH = 10
    CW = RH / 2
    lx, ly = 56, 92
    shapes = []
    for r, row in enumerate(lines):
        runs, c = [], 0
        while c < len(row):
            if row[c] == "█":
                start = c
                while c < len(row) and row[c] == "█":
                    c += 1
                runs.append(f"M{num(lx + start * CW)} {num(ly + r * RH)}h{num((c - start) * CW)}v{RH}h{num(-(c - start) * CW)}z")
            else:
                c += 1
        shapes.append("".join(runs))
    # um path só (sem emenda entre linhas) revelado linha a linha, como o terminal imprime
    logo_d = "".join(shapes)
    reveal = [(0, 0), (1.7, 0)] + [(1.7 + (r + 1) * 0.035, round((r + 1) * RH, 1)) for r in range(len(lines))] + [(HIDE + 0.4, 0)]
    defs.append(f'<clipPath id="rows"><rect x="{lx}" y="{ly}" width="300" height="{num(len(lines) * RH)}">'
                f'{discrete("height", reveal, T)}</rect></clipPath>')
    body.append(f'<path d="{logo_d}" fill="url(#px)" clip-path="url(#rows)"/>')
    # brilho passando pelo logo
    lw, lh = max(map(len, lines)) * CW, len(lines) * RH
    defs.append(f'<linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="{lx - 170}" y1="{ly}" x2="{lx}" y2="{ly + 70}">'
                f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".45"/>'
                f'<stop offset="1" stop-color="#fff" stop-opacity="0"/>'
                f'<animateTransform attributeName="gradientTransform" type="translate" values="0 0;0 0;{num(lw + 240)} 0;{num(lw + 240)} 0" '
                f'keyTimes="0;.2;.45;1" dur="{T}s" repeatCount="indefinite"/></linearGradient>')
    body.append(f'<path d="{logo_d}" fill="url(#shine)" clip-path="url(#rows)"/>')

    # informações
    IX, IY, LH = 360, 108, 27
    key = C["blue"]
    rows = [
        [("atoslins", C["cyan"]), ("@", C["fg2"]), ("omarchy", C["magenta"])],
        [("─" * 16, C["line"])],
        [("os     ", key), ("Omarchy · Arch Linux", C["fg"])],
        [("wm     ", key), ("Hyprland", C["fg"])],
        [("home   ", key), ("Araraquara, SP · Brasil", C["fg"])],
        [("focus  ", key), ("Linux desktop tools · Claude Code plugins · automation", C["fg"])],
        [("langs  ", key), ("Python · TypeScript · PHP · Go · QML", C["fg"])],
        [("ships  ", key), ("whatsapp · dualsense · dod-guard · metodo", C["fg"])],
        [("pt-br  ", key), ("Ferramentas para Linux, plugins para Claude Code e automação.", C["fg2"])],
    ]
    for i, segs in enumerate(rows):
        s, _, _ = spans(mono, segs, 16, IX, IY + i * LH)
        body.append(f'<g>{s}{fade(1.9 + i * 0.13, HIDE, T, 0.25)}</g>')
    palette = [C["bg2"], C["red"], C["green"], C["yellow"], C["blue"], C["magenta"], C["cyan"], C["fg"]]
    sw = []
    for i, col in enumerate(palette):
        sw.append(f'<rect x="{IX + i * 34}" y="{IY + 9 * LH - 10}" width="28" height="14" rx="3" fill="{col}"/>')
    body.append(f'<g>{"".join(sw)}{fade(1.9 + 9 * 0.13, HIDE, T, 0.25)}</g>')

    border = f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="none" stroke="url(#active)" stroke-width="2"/>'
    return (frame(W, H) + "<defs>" + "".join(defs) + "</defs>" + '<g clip-path="url(#card)">' + "".join(body)
            + "</g>" + border + "</svg>")


# =====================================================================
# C: aurora + tipografia grande + ícones em vidro
# =====================================================================

def banner_aurora():
    W, H = 1200, 400
    defs, body = [], []
    defs.append(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>')
    defs.append('<filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="70"/></filter>')
    defs.append('<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
                '<path d="M40 0H0V40" fill="none" stroke="#fff" stroke-opacity=".05"/></pattern>')
    defs.append('<radialGradient id="fadeG" cx=".72" cy=".45" r=".6"><stop offset="0" stop-color="#fff"/>'
                '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>')
    defs.append(f'<mask id="gm"><rect width="{W}" height="{H}" fill="url(#fadeG)"/></mask>')
    defs.append(f'<linearGradient id="name" x1="0" x2="1"><stop offset="0" stop-color="#ffffff"/>'
                f'<stop offset="1" stop-color="{C["fg"]}"/></linearGradient>')

    body.append(f'<rect width="{W}" height="{H}" fill="#0c0d14"/>')
    blobs = [(930, 90, 190, C["magenta"], "0 0;-70 40;0 0", 19),
             (1080, 330, 200, C["blue"], "0 0;50 -40;0 0", 23),
             (720, 400, 170, C["cyan"], "0 0;60 -30;0 0", 17),
             (180, -40, 150, C["blue"], "0 0;40 30;0 0", 21)]
    for x, y, r, col, vals, dur in blobs:
        body.append(f'<g filter="url(#blur)"><circle cx="{x}" cy="{y}" r="{r}" fill="{col}" fill-opacity=".55">'
                    f'<animateTransform attributeName="transform" type="translate" values="{vals}" dur="{dur}s" '
                    f'repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" keyTimes="0;.5;1"/></circle></g>')
    body.append(f'<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gm)"/>')

    p, _ = text(mono, "HELLO, I'M  ·  OLÁ, EU SOU", 13, 76, 118, C["cyan"], tracking=0.2)
    body.append(p)
    p, _ = text(inter8, "Atos Lins", 108, 70, 228, "url(#name)", tracking=-0.03)
    body.append(p)
    p, _ = text(inter6, "Linux desktop tools · Claude Code plugins · automation", 22, 76, 276, C["fg"])
    body.append(p)
    p, _ = text(inter6, "Ferramentas para Linux, plugins para Claude Code e automação.", 16.5, 76, 308, "#8f97bf")
    body.append(p)
    s, _, _ = spans(mono, [(ICON["pin"] + " ", C["red"]), ("Araraquara, SP · Brasil", C["dim"])], 13.5, 76, 354)
    body.append(s)

    tiles = [(880, 64, ICON["pad"], C["magenta"], 0), (1010, 136, ICON["shield"], C["green"], 1.3),
             (890, 212, ICON["console"], C["cyan"], 2.1)]
    for x, y, ic, col, ph in tiles:
        size = 108
        g = (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="26" fill="#ffffff" fill-opacity=".06" '
             f'stroke="#ffffff" stroke-opacity=".16"/>'
             f'<rect x="{x + 1}" y="{y + 1}" width="{size - 2}" height="{size / 2}" rx="25" fill="#ffffff" fill-opacity=".04"/>')
        p, _ = text(mono, ic, 54, x + size / 2, y + size / 2 + 19, col, "middle")
        body.append(f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -8;0 0" '
                    f'dur="6s" begin="-{ph}s" repeatCount="indefinite" calcMode="spline" '
                    f'keySplines=".45 0 .55 1;.45 0 .55 1" keyTimes="0;.5;1"/>{g}{p}</g>')

    return frame(W, H) + "<defs>" + "".join(defs) + "</defs>" + '<g clip-path="url(#card)">' + "".join(body) + "</g></svg>"


if __name__ == "__main__":
    for name, fn in [("a-desktop", banner_desktop), ("b-fetch", banner_fetch), ("c-aurora", banner_aurora)]:
        svg = fn()
        with open(f"{name}.svg", "w") as f:
            f.write(svg)
        print(name, f"{len(svg) / 1024:.0f} KB")
