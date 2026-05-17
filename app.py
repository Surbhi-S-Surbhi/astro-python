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


def generate_chart(house_data, lagna_sign):

    from PIL import Image, ImageDraw, ImageFont
    import uuid

    SIZE = 900
    MARGIN = 60

    img = Image.new("RGB", (SIZE, SIZE), "#fffdf8")
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
        planet_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
        number_font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        planet_font = ImageFont.load_default()
        number_font = ImageFont.load_default()

    PURPLE = "#6A0DAD"
    BLACK = "#111111"

    left = MARGIN
    top = MARGIN + 40
    right = SIZE - MARGIN
    bottom = SIZE - MARGIN

    center_x = SIZE // 2
    center_y = (top + bottom) // 2

    # Outer square
    draw.rectangle(
        [left, top, right, bottom],
        outline=BLACK,
        width=3
    )

    # Main diagonals
    draw.line((left, top, right, bottom), fill=BLACK, width=3)
    draw.line((right, top, left, bottom), fill=BLACK, width=3)

    # Middle diamond
    draw.line((center_x, top, right, center_y), fill=BLACK, width=3)
    draw.line((right, center_y, center_x, bottom), fill=BLACK, width=3)
    draw.line((center_x, bottom, left, center_y), fill=BLACK, width=3)
    draw.line((left, center_y, center_x, top), fill=BLACK, width=3)

    # House positions
    house_positions = {
        1:  (center_x, top + 120),
        2:  (right - 140, top + 120),
        3:  (right - 80, center_y - 90),
        4:  (right - 150, center_y + 30),
        5:  (right - 80, bottom - 180),
        6:  (right - 140, bottom - 80),
        7:  (center_x, bottom - 120),
        8:  (left + 140, bottom - 80),
        9:  (left + 80, bottom - 180),
        10: (left + 150, center_y + 30),
        11: (left + 80, center_y - 90),
        12: (left + 140, top + 120),
    }

    # Draw house numbers + planets
    for house_num, (x, y) in house_positions.items():

        draw.text(
            (x, y),
            str(house_num),
            fill=PURPLE,
            font=number_font,
            anchor="mm"
        )

        planets = house_data.get(house_num, [])

        py = y + 40

        for p in planets:

            short = SHORT_EN.get(p.lower(), p[:2])

            draw.text(
                (x, py),
                short.lower(),
                fill=PURPLE,
                font=planet_font,
                anchor="mm"
            )

            py += 28

    # Lagna title
    draw.text(
        (SIZE // 2, 35),
        f"Lagna: {lagna_sign}",
        fill=BLACK,
        font=title_font,
        anchor="mm"
    )

    # Save image
    filename = f"chart_{uuid.uuid4().hex}.png"

    img.save(filename)

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