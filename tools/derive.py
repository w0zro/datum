#!/usr/bin/env python3
"""datum palette derivation + verification.

OKLCH -> sRGB hex, WCAG 2.x contrast ratio, APCA Lc (W3 0.1.9),
CVD simulation (Machado 2009, severity 1.0), and xterm-256 quantization.
Pure stdlib.
"""
import math

# ---------------------------------------------------------------- OKLab / OKLCH
def oklch_to_linear_srgb(L, C, H):
    h = math.radians(H)
    a = C * math.cos(h)
    b = C * math.sin(h)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l = l_ ** 3
    m = m_ ** 3
    s = s_ ** 3
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return [r, g, bb]

def linear_to_srgb_channel(c):
    if c <= 0.0031308:
        v = 12.92 * c
    else:
        v = 1.055 * (max(c, 0.0) ** (1 / 2.4)) - 0.055
    return v

def srgb_to_linear_channel(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

def clamp01(x):
    return max(0.0, min(1.0, x))

def oklch_to_hex(L, C, H):
    lin = oklch_to_linear_srgb(L, C, H)
    srgb = [clamp01(linear_to_srgb_channel(c)) for c in lin]
    return "#%02x%02x%02x" % tuple(round(c * 255) for c in srgb), any(
        c < -0.001 or c > 1.001 for c in lin
    )

def hex_to_rgb01(hx):
    hx = hx.lstrip("#")
    return [int(hx[i : i + 2], 16) / 255 for i in (0, 2, 4)]

def hex_to_oklab(hx):
    r, g, b = (srgb_to_linear_channel(c) for c in hex_to_rgb01(hx))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, a, bb

# ---------------------------------------------------------------- WCAG 2.x
def wcag_lum(hx):
    r, g, b = (srgb_to_linear_channel(c) for c in hex_to_rgb01(hx))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def wcag_ratio(fg, bg):
    l1, l2 = wcag_lum(fg), wcag_lum(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)

# ---------------------------------------------------------------- APCA W3 0.1.9
def _apca_Y(hx):
    r, g, b = hex_to_rgb01(hx)
    return 0.2126729 * r ** 2.4 + 0.7151522 * g ** 2.4 + 0.0721750 * b ** 2.4

def apca_lc(txt, bg):
    Yt, Yb = _apca_Y(txt), _apca_Y(bg)
    if Yt < 0.022:
        Yt += (0.022 - Yt) ** 1.414
    if Yb < 0.022:
        Yb += (0.022 - Yb) ** 1.414
    if abs(Yb - Yt) < 0.0005:
        return 0.0
    if Yb > Yt:  # normal polarity: dark text on light bg
        S = (Yb ** 0.56 - Yt ** 0.57) * 1.14
        out = 0.0 if S < 0.1 else S - 0.027
    else:  # reverse: light text on dark bg
        S = (Yb ** 0.65 - Yt ** 0.62) * 1.14
        out = 0.0 if S > -0.1 else S + 0.027
    return abs(out * 100)

# ---------------------------------------------------------------- CVD (Machado 2009, sev 1.0)
_MACHADO = {
    "protan": [
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [-0.003882, -0.048116, 1.051998],
    ],
    "deutan": [
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ],
    "tritan": [
        [1.255528, -0.076749, -0.178779],
        [-0.078411, 0.930809, 0.147602],
        [0.004733, 0.691367, 0.303900],
    ],
}

def simulate_cvd(hx, kind):
    lin = [srgb_to_linear_channel(c) for c in hex_to_rgb01(hx)]
    M = _MACHADO[kind]
    out_lin = [sum(M[i][j] * lin[j] for j in range(3)) for i in range(3)]
    srgb = [clamp01(linear_to_srgb_channel(c)) for c in out_lin]
    return "#%02x%02x%02x" % tuple(round(c * 255) for c in srgb)

def oklab_dist(h1, h2):
    a = hex_to_oklab(h1)
    b = hex_to_oklab(h2)
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))

# ---------------------------------------------------------------- xterm-256
def _cube_levels():
    return [0, 95, 135, 175, 215, 255]

def nearest_xterm256(hx):
    r, g, b = (round(c * 255) for c in hex_to_rgb01(hx))
    best_i, best_d = None, 1e18
    levels = _cube_levels()
    for i in range(216):
        ri = levels[(i // 36) % 6]
        gi = levels[(i // 6) % 6]
        bi = levels[i % 6]
        d = (ri - r) ** 2 + (gi - g) ** 2 + (bi - b) ** 2
        if d < best_d:
            best_d, best_i = d, 16 + i
    for i in range(24):
        v = 8 + i * 10
        d = (v - r) ** 2 + (v - g) ** 2 + (v - b) ** 2
        if d < best_d:
            best_d, best_i = d, 232 + i
    return best_i

# ---------------------------------------------------------------- palette spec
# Anchors: (name, hue_angle_oklch). Hue identity is shared across modes.
# Anchored on Okabe-Ito hue angles (CVD-safe qualitative set); 'cyan' is a
# teal placed to sit maximally between string-green and keyword-blue.
# OI sky-blue (236) is deliberately unused: it sits 8 deg from OI blue and the
# two are barely separable even with normal vision (measured 0.065 Oklab), so
# it would add noise, not information.
HUES = {
    "red": 47,       # OI vermillion    -> errors
    "orange": 77,    # OI orange        -> numbers
    "yellow": 105,   # OI yellow        -> constants (warm = values)
    "green": 165,    # OI bluish-green  -> strings
    "cyan": 200,     # teal             -> types
    "blue": 244,     # OI blue          -> keywords
    "purple": 346,   # OI reddish-purple-> functions / specials
}

# Second tier: the ubiquitous glue. Saturated like everything else, but
# split from its full-chroma sibling on the SAME hue by lightness -- the one
# channel that survives every kind of CVD. Glue sits nearer fg0 (it is the
# body text), accents keep the saturated mid-tones.
EXTRAS = {
    "dark":  {"var": (0.91, 0.070, 77), "op": (0.87, 0.062, 244),
              "call": (0.85, 0.080, 346), "param": (0.92, 0.078, 200)},
    "light": {"var": (0.36, 0.055, 77), "op": (0.42, 0.060, 244),
              "call": (0.40, 0.070, 346), "param": (0.38, 0.055, 200)},
}

# Per-mode design targets. Neutrals tuned for soft near-black / off-white.
# Co-occurring token pairs are given a lightness gap so they survive CVD:
#   keyword(blue) vs constant(purple); string(green) vs type(cyan).
DARK = {
    "neutral_h": 256, "neutral_c": 0.012,
    "bg0": 0.185, "bg1": 0.225, "bg2": 0.305,
    "fg1": 0.675, "fg1_c": 0.020,     # comments / muted (legible, faint hue)
    "fg0": 0.905, "fg0_c": 0.012,
    # Lightness raised so every accent clears the APCA body-text aim (Lc 60) on
    # bg0 -- purple used to sit at 46.7 and red at 50.9, passing the WCAG floor
    # while falling well short of the perceptual one. Chroma is held at its
    # original value everywhere except red: at C 0.15 the hue physically cannot
    # reach Lc 60 inside sRGB (it clips at 58.4), so it gives up 0.01 of chroma.
    "accent_L": {"red":0.775,"orange":0.834,"yellow":0.889,"green":0.808,"cyan":0.855,"blue":0.759,"purple":0.789},
    "accent_C": {"red":0.140,"orange":0.130,"yellow":0.140,"green":0.140,"cyan":0.110,"blue":0.120,"purple":0.140},
}
LIGHT = {
    "neutral_h": 256, "neutral_c": 0.010,
    "bg0": 0.972, "bg1": 0.940, "bg2": 0.865,
    "fg1": 0.520, "fg1_c": 0.022,
    "fg0": 0.300, "fg0_c": 0.014,
    # Light-mode lightness was originally bunched into L 0.49-0.55. Hue is what
    # CVD collapses, so a 0.06 spread left co-occurring accents nearly identical
    # to a protanope (orange/yellow measured 0.007 apart). These values are the
    # result of searching L/C -- hue anchors held fixed -- for the assignment
    # that maximises the worst-case separation across all three simulations
    # while keeping every accent inside sRGB and above the WCAG floor.
    "accent_L": {"red":0.506,"orange":0.550,"yellow":0.481,"green":0.497,"cyan":0.527,"blue":0.545,"purple":0.482},
    "accent_C": {"red":0.140,"orange":0.115,"yellow":0.082,"green":0.105,"cyan":0.087,"blue":0.134,"purple":0.154},
}

def build(mode):
    spec = DARK if mode == "dark" else LIGHT
    pal = {}
    nh, nc = spec["neutral_h"], spec["neutral_c"]
    for k in ("bg0", "bg1", "bg2"):
        pal[k] = oklch_to_hex(spec[k], nc, nh)[0]
    pal["fg1"] = oklch_to_hex(spec["fg1"], spec["fg1_c"], nh)[0]
    pal["fg0"] = oklch_to_hex(spec["fg0"], spec["fg0_c"], nh)[0]
    for name, h in HUES.items():
        L = spec["accent_L"][name]
        C = spec["accent_C"][name]
        hx, oog = oklch_to_hex(L, C, h)
        pal[name] = hx
        if oog:
            pal[name] += "*"  # out-of-gamut flag
    return pal

def report(mode):
    pal = build(mode)
    bg0 = pal["bg0"].rstrip("*")
    bg1 = pal["bg1"].rstrip("*")
    print(f"\n===== {mode.upper()} =====  bg0={bg0}")
    print(f"{'role':8} {'hex':9} {'cterm':5} {'L':5} {'C':5} {'H':5} "
          f"{'WCAG/bg0':9} {'APCA/bg0':8}")
    for name, (L, C, h) in EXTRAS[mode].items():
        hx, oog = oklch_to_hex(L, C, h)
        pal[name] = hx + ("*" if oog else "")
    order = ["bg0","bg1","bg2","fg1","fg0","var","op","call","param",
             "red","orange","yellow","green","cyan","blue","purple"]
    for k in order:
        hx = pal[k].rstrip("*")
        oog = "*" if pal[k].endswith("*") else " "
        L, a, b = hex_to_oklab(hx)
        C = math.sqrt(a*a + b*b)
        H = (math.degrees(math.atan2(b, a))) % 360
        ct = nearest_xterm256(hx)
        wc = wcag_ratio(hx, bg0)
        ap = apca_lc(hx, bg0)
        print(f"{k:8} {hx}{oog} {ct:<5} {L:.2f}  {C:.3f} {H:5.0f} "
              f"{wc:6.2f}   {ap:6.1f}")
    # accent-vs-bg1 for popups/statusline sanity
    # CVD separability: min pairwise oklab distance among accents
    accents = ["red","orange","yellow","green","cyan","blue","purple"]
    print(f"  min pairwise Oklab dist among accents:")
    for kind in ("none","protan","deutan","tritan"):
        hexes = {a: (pal[a].rstrip("*") if kind=="none"
                     else simulate_cvd(pal[a].rstrip("*"), kind)) for a in accents}
        mind, pair = 1e9, None
        for i in range(len(accents)):
            for j in range(i+1, len(accents)):
                d = oklab_dist(hexes[accents[i]], hexes[accents[j]])
                if d < mind:
                    mind, pair = d, (accents[i], accents[j])
        print(f"    {kind:7} {mind:.3f}  (closest: {pair[0]}/{pair[1]})")
    return pal

ROLES = ["bg0", "bg1", "bg2", "fg1", "fg0",
         "red", "orange", "yellow", "green", "cyan", "blue", "purple",
         "var", "call", "param", "op"]

def palette(mode):
    """Full derived palette for one mode: role -> measured values.

    This is the single source of truth every port is generated from -- keeping
    a port hand-written is how a stale color sneaks in."""
    pal = build(mode)
    extras = {k: oklch_to_hex(L, C, H)[0] for k, (L, C, H) in EXTRAS[mode].items()}
    bg0 = pal["bg0"].rstrip("*")
    out = {}
    for name in ROLES:
        hx = (pal.get(name) or extras.get(name)).rstrip("*")
        L, a, b = hex_to_oklab(hx)
        out[name] = {
            "hex": hx,
            "cterm": nearest_xterm256(hx),
            "L": round(L, 3),
            "C": round(math.sqrt(a * a + b * b), 4),
            "H": round(math.degrees(math.atan2(b, a)) % 360, 1),
            "wcag": round(wcag_ratio(hx, bg0), 2),
            "apca": round(apca_lc(hx, bg0), 1),
        }
    return out

def palette_json():
    return {m: palette(m) for m in ("dark", "light")}

def fingerprint():
    """Stable hash of the whole derived palette.

    Stamped into the preview PNGs so a stale render can be detected without
    re-rendering (which needs Chrome + Monaspace and only runs on a Mac)."""
    import hashlib, json
    blob = json.dumps(palette_json(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]

# ---------------------------------------------------------------- verification
# datum's pitch is that the colors are verified, not eyeballed -- so the claims
# are asserted here and run in CI. Without this, editing a hue angle keeps every
# port perfectly in sync (gen_ports --check still passes) while the palette
# silently drops below its contrast floor.
#
# FLOORS are hard: they encode what the docs promise, and a regression fails CI.
# TARGETS are the original design aims; where the palette falls short today it
# is reported as a warning rather than pretended away.
WCAG_TEXT = 4.5        # WCAG 2.2 AA body text, every text role on bg0
APCA_TEXT = 60.0       # APCA body-text contrast for every accent, on bg0
APCA_MUTED = 45.0      # comments/muted must stay readable
TIER_SPLIT = 0.05      # min Oklab L gap between a tier-1 accent and its tier-2 sibling
CVD_FLOOR = 0.02       # min Oklab separation for a co-occurring pair under any CVD

# Roles rendered as text on bg0.
TEXT_ROLES = ["red", "orange", "yellow", "green", "cyan", "blue", "purple",
              "var", "call", "param", "op", "fg0"]
# Same-hue tier-1 -> tier-2 siblings. This lightness split IS the scheme's
# signature mechanism, and it is the separation that survives every kind of CVD.
TIER_PAIRS = [("orange", "var"), ("blue", "op"), ("purple", "call"), ("cyan", "param")]
# Accent pairs that plausibly sit next to each other in real code.
COOCCUR = [("blue", "purple"), ("green", "cyan"), ("orange", "yellow"),
           ("red", "orange"), ("red", "yellow")]

def check(verbose=True):
    """Assert the palette still meets its published claims. Returns (fails, warns)."""
    fails, warns = [], []

    def emit(ok, label, detail, level="FAIL"):
        if verbose:
            print(f"  {'PASS' if ok else level:4}  {label:44} {detail}")

    for mode in ("dark", "light"):
        p = palette(mode)
        bg0 = p["bg0"]["hex"]
        if verbose:
            print(f"\n{mode.upper()}  (bg0={bg0})")

        # -- contrast: every text role clears WCAG AA on the canvas
        worst = min((p[r]["wcag"], r) for r in TEXT_ROLES)
        ok = worst[0] >= WCAG_TEXT
        emit(ok, f"WCAG >= {WCAG_TEXT} for all text roles",
             f"worst {worst[0]:.2f} ({worst[1]})")
        if not ok:
            fails.append(f"{mode}: {worst[1]} at WCAG {worst[0]:.2f} < {WCAG_TEXT}")

        ok = p["fg1"]["wcag"] >= WCAG_TEXT and p["fg1"]["apca"] >= APCA_MUTED
        emit(ok, f"comments readable (WCAG >= {WCAG_TEXT}, APCA >= {APCA_MUTED:.0f})",
             f"WCAG {p['fg1']['wcag']:.2f}, APCA {p['fg1']['apca']:.1f}")
        if not ok:
            fails.append(f"{mode}: fg1 WCAG {p['fg1']['wcag']:.2f} / APCA {p['fg1']['apca']:.1f}")

        # -- no clipped colors: an out-of-gamut request means the rendered hex
        #    is not the color the OKLCH spec actually asked for.
        clipped = [k for k, v in build(mode).items() if v.endswith("*")]
        clipped += [k for k, (L, C, H) in EXTRAS[mode].items() if oklch_to_hex(L, C, H)[1]]
        emit(not clipped, "all colors inside sRGB gamut", clipped or "none clipped", "WARN")
        if clipped:
            warns.append(f"{mode}: {', '.join(clipped)} clipped to fit sRGB")

        # -- the chroma-tiering mechanism itself
        worst_split = min((abs(hex_to_oklab(p[a]["hex"])[0] - hex_to_oklab(p[b]["hex"])[0]), a, b)
                          for a, b in TIER_PAIRS)
        ok = worst_split[0] >= TIER_SPLIT
        emit(ok, f"tier-1/tier-2 lightness split >= {TIER_SPLIT}",
             f"worst {worst_split[0]:.3f} ({worst_split[1]}/{worst_split[2]})")
        if not ok:
            fails.append(f"{mode}: {worst_split[1]}/{worst_split[2]} split {worst_split[0]:.3f}")

        # -- CVD: co-occurring pairs must stay apart under all three simulations
        worst_cvd = (1e9, None, None, None)
        for a, b in COOCCUR:
            for kind in ("protan", "deutan", "tritan"):
                d = oklab_dist(simulate_cvd(p[a]["hex"], kind), simulate_cvd(p[b]["hex"], kind))
                if d < worst_cvd[0]:
                    worst_cvd = (d, a, b, kind)
        d, a, b, kind = worst_cvd
        ok = d >= CVD_FLOOR
        emit(ok, f"co-occurring pairs separable under CVD >= {CVD_FLOOR}",
             f"worst {d:.3f} ({a}/{b} under {kind})")
        if not ok:
            fails.append(f"{mode}: {a}/{b} only {d:.3f} apart under {kind}")

        # -- APCA: perceptual contrast, where WCAG is unreliable on dark grounds
        worst_apca = min((p[r]["apca"], r) for r in TEXT_ROLES)
        ok = worst_apca[0] >= APCA_TEXT
        emit(ok, f"APCA Lc >= {APCA_TEXT:.0f} for all text roles",
             f"worst {worst_apca[0]:.1f} ({worst_apca[1]})")
        if not ok:
            fails.append(f"{mode}: {worst_apca[1]} at APCA Lc {worst_apca[0]:.1f} < {APCA_TEXT:.0f}")

    if verbose:
        if warns:
            print("\nwarnings (design aims not met; not blocking):")
            for w in warns:
                print(f"  ! {w}")
        print("\n" + ("PALETTE FAILS:\n  " + "\n  ".join(fails)
                      if fails else "palette meets every published claim"))
    return fails, warns

if __name__ == "__main__":
    import sys, json
    if "--json" in sys.argv:
        print(json.dumps(palette_json(), indent=2))
    elif "--fingerprint" in sys.argv:
        print(fingerprint())
    elif "--check" in sys.argv:
        sys.exit(1 if check()[0] else 0)
    else:
        for m in ("dark", "light"):
            report(m)
