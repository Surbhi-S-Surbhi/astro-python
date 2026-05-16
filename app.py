from flask import Flask, request, jsonify, send_file
import swisseph as swe
from PIL import Image, ImageDraw, ImageFont
from flask import send_file
import os
import threading
import time
import uuid
from datetime import datetime
import json
from astrology.dasha.interpretations import (
    get_mahadasha_interpretation,
    get_timeline_interpretation
)
from flask import Flask, request
from astrology.dasha.engine import get_moon_longitude
from astrology.dasha.engine import (
    get_moon_longitude,
    get_nakshatra,
    get_dasha_lord,
    calculate_balance_years,
    generate_mahadasha_timeline,
    get_current_mahadasha,
    generate_antardashas,
    get_current_antardasha
)
app = Flask(__name__)
# set ephemeris path
swe.set_ephe_path('./ephe')


# -------------------------
# HOME ROUTE
# -------------------------
# -------------------------
# CURRENT DASHA API
# -------------------------
@app.route('/dasha/current', methods=['POST'])
def home():

    print("API HIT")

    data = request.json

    birth = datetime(
        data["year"],
        data["month"],
        data["day"],
        data.get("hour", 0),
        data.get("minute", 0)
    )

    # Moon longitude
    moon_longitude = get_moon_longitude(
        birth
    )

    # Nakshatra
    nakshatra = get_nakshatra(
        moon_longitude
    )

    # Dasha lord
    dasha_lord = get_dasha_lord(
        nakshatra
    )

    # Remaining years
    balance_years = calculate_balance_years(
        moon_longitude,
        dasha_lord
    )

    # Full Mahadasha timeline
    timeline = generate_mahadasha_timeline(
        birth
    )

    # Current Mahadasha
    current_mahadasha = get_current_mahadasha(
        timeline
    )

    # Antardashas
    antardashas = generate_antardashas(
        current_mahadasha
    )

    # Current Antardasha
    current_antardasha = get_current_antardasha(
        antardashas
    )

    return jsonify({

        "vartaman_mahadasha": {

            "graha":
                current_mahadasha["lord"],

            "shuru_tithi":
                current_mahadasha["start"].strftime(
                    "%d %B %Y"
                ),

            "samapt_tithi":
                current_mahadasha["end"].strftime(
                    "%d %B %Y"
                ),

            "vivaran":
                get_mahadasha_interpretation(
                    current_mahadasha["lord"]
                )
        },

        "vartaman_antardasha": {

            "graha":
                current_antardasha["lord"],

            "shuru_tithi":
                current_antardasha["start"].strftime(
                    "%d %B %Y"
                ),

            "samapt_tithi":
                current_antardasha["end"].strftime(
                    "%d %B %Y"
                )
        }
    })


# -------------------------
# MAHADASHA TIMELINE API
# -------------------------
@app.route('/dasha/mahadashas', methods=['POST'])
def mahadasha_timeline():

    data = request.json

    birth = datetime(
        data["year"],
        data["month"],
        data["day"],
        data.get("hour", 0),
        data.get("minute", 0)
    )

    moon_longitude = get_moon_longitude(
        birth
    )

    nakshatra = get_nakshatra(
        moon_longitude
    )

    dasha_lord = get_dasha_lord(
        nakshatra
    )

    balance_years = calculate_balance_years(
        moon_longitude,
        dasha_lord
    )

    timeline = generate_mahadasha_timeline(
        birth
    )

    formatted = []

    for item in timeline:

        formatted.append({

            "mahadasha_graha":
                item["lord"],

            "shuru_tithi":
                item["start"].strftime(
                    "%d %B %Y"
                ),

            "samapt_tithi":
                item["end"].strftime(
                    "%d %B %Y"
                ),

            "avadhi_varsh":
                round(
                    (item["end"] - item["start"]).days / 365.25,
                    2
                ),

            "vivaran":
                get_timeline_interpretation(
                    item["lord"]
                )
        })

    return jsonify(formatted)


# -------------------------
# UTILITY FUNCTIONS
# -------------------------
def get_zodiac(degree):
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return signs[int(degree // 30)]


def get_house_mapping(lagna_sign):
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    lagna_index = signs.index(lagna_sign)
    houses = {}
    for i in range(12):
        sign = signs[(lagna_index + i) % 12]
        houses[sign] = i + 1
    return houses


SHORT = {
    "Sun":     "सू",
    "Moon":    "चं",
    "Mars":    "मं",
    "Mercury": "बु",
    "Jupiter": "गु",
    "Venus":   "शु",
    "Saturn":  "श",
    "Rahu":    "रा",
    "Ketu":    "के",
    "Lagna":   "ल.",
}
SHORT_EN = {
    "Sun":     "Su",
    "Moon":    "Mo",
    "Mars":    "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus":   "Ve",
    "Saturn":  "Sa",
    "Rahu":    "Ra",
    "Ketu":    "Ke",
    "Lagna":   "As",
}
print("NEW VERSION RUNNING")
BG_COLOR = "#FFFDF5"
LINE_COLOR = "#2C1810"
PLANET_COLORS = {
    "sun":     "#E65C00",
    "moon":    "#4A90D9",
    "mars":    "#CC0000",
    "mercury": "#2E8B57",
    "jupiter": "#8B4513",
    "venus":   "#9B59B6",
    "saturn":  "#2C3E50",
    "rahu":    "#666666",
    "ketu":    "#888888",
}

# NOTE: Only 7 real planets + rahu. Ketu is derived from rahu, NOT fetched separately.
PLANETS = {
    "sun":     swe.SUN,
    "moon":    swe.MOON,
    "mars":    swe.MARS,
    "mercury": swe.MERCURY,
    "jupiter": swe.JUPITER,
    "venus":   swe.VENUS,
    "saturn":  swe.SATURN,
    "rahu":    swe.MEAN_NODE,
}


# -------------------------
# CHART GENERATOR
# -------------------------

def _load_fonts(size_bold, size_normal, size_num):
    """Try to load a font that supports Hindi Devanagari, else fall back."""
    candidates_devanagari = [
        "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "NotoSansDevanagari-Regular.ttf",
        "Lohit-Devanagari.ttf",
    ]
    candidates_latin = [
        "DejaVuSans-Bold.ttf",
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    hindi_font_bold   = None
    hindi_font_normal = None

    for path in candidates_devanagari:
        try:
            hindi_font_bold   = ImageFont.truetype(path, size_bold)
            hindi_font_normal = ImageFont.truetype(path, size_normal)
            break
        except Exception:
            continue

    latin_bold   = None
    latin_normal = None
    for path in candidates_latin:
        try:
            latin_bold   = ImageFont.truetype(path, size_bold)
            latin_normal = ImageFont.truetype(path, size_normal)
            break
        except Exception:
            continue

    default = ImageFont.load_default()

    # If we have a Devanagari font, use it; otherwise fall back to Latin
    fBold   = hindi_font_bold   or latin_bold   or default
    fNormal = hindi_font_normal or latin_normal or default
    fNum    = latin_bold or default   # numbers are always Latin

    use_hindi = hindi_font_bold is not None
    return fBold, fNormal, fNum, use_hindi


def generate_chart(house_data: dict, lagna_sign: str, use_hindi: bool = True) -> str:
    """
    Generate a North Indian Kundli chart image.

    Parameters
    ----------
    house_data : dict
        Keys are house numbers 1-12 (int).
        Values are lists of planet name strings, e.g. ["Sun", "Mars"].
        House 1 is the Lagna house (top-center diamond).
    lagna_sign : str
        Name of the sign in the Lagna (e.g. "Aries").
    use_hindi : bool
        If True, use Hindi abbreviations; otherwise English.

    Returns
    -------
    str  – path to the saved PNG file.
    """

    # ── Canvas setup ─────────────────────────────────────────────────────────
    SIZE = 900
    PAD  = 50
    G    = (SIZE - 2 * PAD) // 4   # cell size ≈ 200
    O    = PAD                      # grid origin

    img  = Image.new('RGB', (SIZE, SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img)

    fBold, fNormal, fNum, detected_hindi = _load_fonts(22, 14, 14)
    SHORT_MAP = SHORT if (use_hindi and detected_hindi) else SHORT_EN

    # ── Helper: draw text centred at (cx, cy) ────────────────────────────────
    def draw_centered(text, cx, cy, font, color):
        bb = draw.textbbox((0, 0), text, font=font)
        w  = bb[2] - bb[0]
        h  = bb[3] - bb[1]
        draw.text((cx - w / 2, cy - h / 2), text, fill=color, font=font)

    # ── Grid corners / key points ─────────────────────────────────────────────
    # Outer square corners
    TL_out = (O,       O)
    TR_out = (O+4*G,   O)
    BR_out = (O+4*G,   O+4*G)
    BL_out = (O,       O+4*G)

    # Inner square corners (centre 2×2 block)
    TL = (O+G,   O+G)
    TR = (O+3*G, O+G)
    BR = (O+3*G, O+3*G)
    BL = (O+G,   O+3*G)
    C  = (O+2*G, O+2*G)   # dead center

    # ── 1. White fill ─────────────────────────────────────────────────────────
    draw.rectangle([O, O, O+4*G, O+4*G], fill=BG_COLOR)

    # ── 2. Outer border ───────────────────────────────────────────────────────
    draw.rectangle([O, O, O+4*G, O+4*G], outline=LINE_COLOR, width=3)

    # ── 3. Internal 4×4 grid lines ────────────────────────────────────────────
    for i in range(1, 4):
        draw.line([(O+i*G, O),     (O+i*G, O+4*G)], fill=LINE_COLOR, width=2)
        draw.line([(O,     O+i*G), (O+4*G, O+i*G)], fill=LINE_COLOR, width=2)

    # ── 4. Diagonals in centre 2×2 block ──────────────────────────────────────
    draw.line([TL, BR], fill=LINE_COLOR, width=2)   # \
    draw.line([TR, BL], fill=LINE_COLOR, width=2)   # /

    # ── 5. House number & planet anchor points ────────────────────────────────
    #
    # North Indian layout (fixed houses, Lagna = house 1 = top diamond):
    #
    #   [12]  [1/Lag] [2]
    #   [11]  [10][4] [3]
    #   [10]  [7]     [4]  ← triangles; corners are rect cells
    #   [9]   [8]     [5]
    #   [8]   [7/bot] [6]
    #
    # Actual cell mapping for a 4×4 grid (0-indexed col, row):
    #   Corner cells  → plain rectangles
    #   Edge-centre cells → plain rectangles (but only 3 per side, skip corner cols)
    #   Centre 4 triangles → diamonds
    #
    # House positions in the North Indian chart (standard):
    # Top row    : H12(col0,row0)  H1-top-tri  H2(col3,row0)
    # 2nd row    : H11(col0,row1)  H10-left-tri / H4-right-tri  H3(col3,row1)
    # 3rd row    : H9(col0,row2)   H7-bot-tri                   H5(col3,row2)
    # Bot row    : H8(col0,row3)   H8-bot?     H6(col3,row3)
    #
    # Simpler: each house has a "label point" and a "planet list start point".
    #
    # We store (center_x, center_y) for the block, and nudge number to top-left
    # corner of that block.

    # Half-cell convenience
    h = G / 2   # half cell = 100

    # Centers of the 12 houses (number label positions)
    # For rectangular outer cells: center of that cell
    # For triangular inner houses: geometric centroid of the triangle
    #   Top triangle    centroid y = O+G + (O+2*G - (O+G))/3 = O+G + G/3
    #   Right triangle  centroid x = O+3*G + G/3
    #   Bottom triangle centroid y = O+3*G - G/3   (counted from BL corner downward... let's compute properly)

    # Triangle centroids (average of 3 vertices):
    # H1  top:    TL=(O+G,O+G)  TR=(O+3*G,O+G)  C=(O+2*G,O+2*G)
    #   cx = (O+G + O+3G + O+2G)/3 = O+2G,  cy = (O+G + O+G + O+2G)/3 = O+4G/3
    h1_cx = O + 2*G
    h1_cy = O + G + G//3   # a bit above center

    # H4  right:  TR=(O+3*G,O+G)  BR=(O+3*G,O+3*G)  C=(O+2*G,O+2*G)
    h4_cx = O + 3*G - G//3
    h4_cy = O + 2*G

    # H7  bottom: BL=(O+G,O+3*G)  BR=(O+3*G,O+3*G)  C=(O+2*G,O+2*G)
    h7_cx = O + 2*G
    h7_cy = O + 3*G - G//3

    # H10 left:   TL=(O+G,O+G)  BL=(O+G,O+3*G)  C=(O+2*G,O+2*G)
    h10_cx = O + G + G//3
    h10_cy = O + 2*G

    house_centers = {
        12: (O +   h,       O +   h),       # top-left  corner
        1:  (h1_cx,         h1_cy),          # top  triangle  (Lagna)
        2:  (O + 3*G + h,   O +   h),        # top-right corner
        3:  (O + 3*G + h,   O + G + h),      # right-upper rect
        4:  (h4_cx,         h4_cy),          # right triangle
        5:  (O + 3*G + h,   O + 2*G + h),    # right-lower rect
        6:  (O + 3*G + h,   O + 3*G + h),    # bottom-right corner
        7:  (h7_cx,         h7_cy),          # bottom triangle
        8:  (O +   h,       O + 3*G + h),    # bottom-left corner
        9:  (O +   h,       O + 2*G + h),    # left-lower rect
        10: (h10_cx,        h10_cy),         # left triangle
        11: (O +   h,       O + G + h),      # left-upper rect
    }

    LINE_H = 26   # vertical spacing between planet lines
    NUM_H  = 18   # space reserved for the house number row

    # ── 6. Draw each house ────────────────────────────────────────────────────
    for house_num, (hx, hy) in house_centers.items():
        planets = house_data.get(house_num, [])
        n = len(planets)

        # Lagna marker: add "ल." as a pseudo-planet in house 1 if not already there
        extra = []
        if house_num == 1:
            lagna_abbr = SHORT_MAP.get("Lagna", "As")
            extra = [lagna_abbr]

        all_items = extra + [SHORT_MAP.get(p, p[:2]) for p in planets]
        total_h = NUM_H + len(all_items) * LINE_H
        start_y = hy - total_h / 2

        # House number (small, purple, top of block)
        num_txt = str(house_num)
        bb  = draw.textbbox((0, 0), num_txt, font=fNum)
        nw  = bb[2] - bb[0]
        draw.text((hx - nw / 2, start_y), num_txt, fill=NUM_COLOR, font=fNum)

        # Planet abbreviations
        for i, abbr in enumerate(all_items):
            py = start_y + NUM_H + i * LINE_H
            draw_centered(abbr, hx, py + LINE_H // 2, fBold, PLANET_COLOR)

    # ── 7. Title bar at top ───────────────────────────────────────────────────
    title = f"Lagna: {lagna_sign}"
    bb = draw.textbbox((0, 0), title, font=fBold)
    tw = bb[2] - bb[0]
    draw.text(((SIZE - tw) // 2, 14), title, fill='#2C1810', font=fBold)

    # ── 8. Redraw borders (planets may have painted over edges) ───────────────
    draw.rectangle([O, O, O+4*G, O+4*G], outline=LINE_COLOR, width=3)
    for i in range(1, 4):
        draw.line([(O+i*G, O),     (O+i*G, O+4*G)], fill=LINE_COLOR, width=2)
        draw.line([(O,     O+i*G), (O+4*G, O+i*G)], fill=LINE_COLOR, width=2)
    draw.line([TL, BR], fill=LINE_COLOR, width=2)
    draw.line([TR, BL], fill=LINE_COLOR, width=2)

    # ── 9. Save ───────────────────────────────────────────────────────────────
    filename = f"chart_{uuid.uuid4().hex}.png"
    img.save(filename, dpi=(150, 150))
    return filename
# -------------------------
# KUNDLI API
# -------------------------
@app.route('/kundli', methods=['POST'])
def kundli():
    try:
        data   = request.get_json()
        year   = data['year']
        month  = data['month']
        day    = data['day']
        hour   = data['hour']
        minute = data['minute']
        lat    = data['lat']
        lon    = data['lon']

        time_decimal = hour + minute / 60.0
        jd = swe.julday(year, month, day, time_decimal)

        houses       = swe.houses(jd, lat, lon)
        lagna_degree = houses[0][0]
        lagna_sign   = get_zodiac(lagna_degree)

        result = {}

        # ── Fetch 7 planets + Rahu ────────────────────────────────
        for name, planet_id in PLANETS.items():
            p_data = swe.calc_ut(jd, planet_id)
            degree = p_data[0][0]
            result[name] = {
                "degree": round(degree, 2),
                "sign":   get_zodiac(degree)
            }

        # ── Derive Ketu from Rahu (always exactly 180° opposite) ──
        # FIX: Ketu is NOT fetched separately from swe (which would give
        # Rahu's position again). Instead we compute it from stored rahu degree.
        rahu_degree  = result["rahu"]["degree"]
        ketu_degree  = round((rahu_degree + 180) % 360, 2)
        result["ketu"] = {
            "degree": ketu_degree,
            "sign":   get_zodiac(ketu_degree)
        }

        # ── Place planets into houses ─────────────────────────────
        house_map  = get_house_mapping(lagna_sign)
        house_data = {i: [] for i in range(1, 13)}

        for name, info in result.items():
            house = house_map[info["sign"]]
            house_data[house].append(name)

        filename = generate_chart(house_data, lagna_sign)
        file_path = os.path.join(os.getcwd(), filename)
        def delete_file_later(path):
            time.sleep(600)  # 10 minutes
            if os.path.exists(path):
                os.remove(path)
                print("Deleted:", path)

        threading.Thread(
            target=delete_file_later,
            args=(file_path,),
            daemon=True   # 🔥 add this
        ).start()
        base_url = request.host_url.rstrip('/')
        return jsonify({
            "planets": result,
            "lagna":   {"degree": lagna_degree, "sign": lagna_sign},
            "chartUrl": base_url + "/" + filename,
            "message": "Kundli + chart generated"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------
# CHART ROUTE
# -------------------------
@app.route('/<filename>')
def get_chart(filename):
    if not filename.startswith("chart_"):
        return "Invalid file", 400

    file_path = os.path.join(os.getcwd(), filename)

    if os.path.exists(file_path):
        return send_file(file_path, mimetype='image/png')
    else:
        return "Chart expired", 404

# -------------------------
# TEST MOON ROUTE
# -------------------------
@app.route("/test-moon")
def test_moon():

    dt = datetime(1999, 8, 11, 10, 30)

    moon = get_moon_longitude(dt)

    return {
        "moon_longitude": moon
    }

@app.route('/test-dasha')
def test_dasha():

    birth = datetime(
        1999,
        8,
        11,
        10,
        30
    )

    moon_longitude = get_moon_longitude(birth)

    nakshatra = get_nakshatra(
        moon_longitude
    )

    dasha_lord = get_dasha_lord(
        nakshatra
    )

    return {
        "moon_longitude": round(moon_longitude, 4),
        "nakshatra": nakshatra,
        "dasha_lord": dasha_lord
    }
# -------------------------
# RUN
# -------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)