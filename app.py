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
# from flask import Flask, request
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
# from generate_chart import generate_chart

# path = generate_chart(
#     house_data={
#         1:  ["Jupiter"],
#         4:  ["Moon", "Mars"],
#         6:  ["Sun", "Venus", "Ketu"],
#         7:  ["Mercury"],
#         9:  ["Moon", "Mars"],
#         12: ["Saturn", "Rahu"],
#     },
#     lagna_sign="Cancer"
# )
# path = "chart_abc123.png"  ← the saved image file

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


SHORT_HI = {
    "sun": "सू", "moon": "चं", "mars": "मं", "mercury": "बु",
    "jupiter": "गु", "venus": "शु", "saturn": "श", "rahu": "रा",
    "ketu": "के", "lagna": "ल.", "ascendant": "ल.",
}
SHORT_EN = {
    "sun": "सू",
    "moon": "चं",
    "mars": "मं",
    "mercury": "बु",
    "jupiter": "गु",
    "venus": "शु",
    "saturn": "श",
    "rahu": "रा",
    "ketu": "के",
    "lagna": "ल",
}
print("NEW VERSION RUNNING")
BG_COLOR = "#FFFDF5"
LINE_COLOR = "#2C1810"
NUM_COLOR = "#8B6F47"
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
        "NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/NotoSansDevanagari-Bold.ttf",
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



PURPLE = "#6A0DAD"
BLACK  = "#111111"
BG     = "#fffdf8"

DEVA_BOLD = "fonts/NotoSansDevanagari-Bold.ttf"
LAT_BOLD  = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _try_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return None

def generate_chart(house_data: dict, lagna_sign: str) -> str:
    SIZE    = 1000
    TITLE_H = 55
    PAD     = 70

    img  = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)

    fTitle  = _try_font(LAT_BOLD, 30) or ImageFont.load_default()
    fNum    = _try_font(LAT_BOLD, 22) or ImageFont.load_default()
    fPlanet = _try_font(DEVA_BOLD, 26) or _try_font(LAT_BOLD, 26) or ImageFont.load_default()
    has_deva = _try_font(DEVA_BOLD, 10) is not None
    SHORT    = SHORT_HI if has_deva else SHORT_EN

    L=PAD; T=PAD+TITLE_H; R=SIZE-PAD; B=SIZE-PAD
    cx=(L+R)//2; cy=(T+B)//2; sq=R-L; q=sq//4

    tl=(L,T); tr=(R,T); br=(R,B); bl=(L,B)
    top=(cx,T); right=(R,cy); bottom=(cx,B); left=(L,cy)
    P_TL=(cx-q,T+q); P_TR=(cx+q,T+q)
    P_BR=(cx+q,cy+q); P_BL=(cx-q,cy+q)
    LW=3

    # Draw lines
    draw.rectangle([L,T,R,B], outline=BLACK, width=4)
    draw.line([tl,br], fill=BLACK, width=LW)
    draw.line([tr,bl], fill=BLACK, width=LW)
    draw.line([top,right],    fill=BLACK, width=LW)
    draw.line([right,bottom], fill=BLACK, width=LW)
    draw.line([bottom,left],  fill=BLACK, width=LW)
    draw.line([left,top],     fill=BLACK, width=LW)

    # weighted point: w% from tip toward base midpoint
    def wp(b1, b2, tip, w=0.58):
        bx=(b1[0]+b2[0])//2; by=(b1[1]+b2[1])//2
        return (int(tip[0]+w*(bx-tip[0])), int(tip[1]+w*(by-tip[1])))

    # For bottom-corner houses (H6, H8) and right-corner (H5) and left-corner (H9),
    # bias MORE toward the inner chord to stay away from the outer boundary
    centers = {
        1:  wp(P_TL, P_TR,  top,    0.62),
        2:  wp(P_TR, top,   tr,     0.54),
        3:  wp(P_TR, right, tr,     0.54),
        4:  wp(P_TR, P_BR,  right,  0.62),
        5:  wp(P_BR, right, br,     0.50),
        6:  wp(P_BR, bottom,br,     0.50),
        7:  wp(P_BL, P_BR,  bottom, 0.62),
        8:  wp(P_BL, bottom,bl,     0.50),
        9:  wp(P_BL, left,  bl,     0.50),
        10: wp(P_TL, P_BL,  left,   0.62),
        11: wp(P_TL, left,  tl,     0.54),
        12: wp(P_TL, top,   tl,     0.54),
    }

    LINE_H = 32

    def draw_house(h, hx, hy):
        planets = list(house_data.get(h, []))
        extra   = [SHORT.get("lagna","As")] if h==1 else []
        abbrs   = extra + [SHORT.get(p.lower(), p[:2]) for p in planets]

        total_h = LINE_H * (1 + len(abbrs))
        # For bottom-corner houses, shift anchor UP by half the planet block height
        # so planets don't overflow below the border
        y_offset = 0
        if h in (6, 8):    # bottom-corner houses
            y_offset = -LINE_H * len(abbrs) // 2
        elif h in (5, 9):  # side-bottom houses, mild shift
            y_offset = -LINE_H * len(abbrs) // 3

        start_y = hy - total_h//2 + y_offset

        num_str = str(h)
        bb = draw.textbbox((0,0), num_str, font=fNum)
        draw.text((hx-(bb[2]-bb[0])//2, start_y), num_str, fill=PURPLE, font=fNum)

        for i, abbr in enumerate(abbrs):
            py = start_y + LINE_H*(i+1)
            bb = draw.textbbox((0,0), abbr, font=fPlanet)
            draw.text((hx-(bb[2]-bb[0])//2, py), abbr, fill=PURPLE, font=fPlanet)

    for h,(hx,hy) in centers.items():
        draw_house(h, hx, hy)

    # Title
    title = f"Lagna: {lagna_sign}"
    bb = draw.textbbox((0,0), title, font=fTitle)
    draw.text(((SIZE-(bb[2]-bb[0]))//2, 14), title, fill=BLACK, font=fTitle)

    # Redraw lines clean on top
    draw.rectangle([L,T,R,B], outline=BLACK, width=4)
    draw.line([tl,br], fill=BLACK, width=LW)
    draw.line([tr,bl], fill=BLACK, width=LW)
    draw.line([top,right],    fill=BLACK, width=LW)
    draw.line([right,bottom], fill=BLACK, width=LW)
    draw.line([bottom,left],  fill=BLACK, width=LW)
    draw.line([left,top],     fill=BLACK, width=LW)

    filename = f"chart_{uuid.uuid4().hex}.png"
    img.save(filename, dpi=(150,150))
    return filename

# Cancer test
p1 = generate_chart({
    1:["Jupiter"], 6:["Sun","Venus","Ketu"],
    7:["Mercury"], 9:["Moon","Mars"], 12:["Saturn","Rahu"]
}, "Cancer")
print(f"Cancer: {p1}")

# Stress test
p2 = generate_chart({
    1:["Jupiter","Saturn"], 2:["Sun","Moon"], 3:["Mars"],
    4:["Mercury","Venus","Rahu"], 5:["Ketu"],
    6:["Sun","Venus","Ketu"], 8:["Moon","Mars"],
    11:["Saturn","Rahu"], 12:["Mars","Moon"]
}, "Aries")
print(f"Stress: {p2}")


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