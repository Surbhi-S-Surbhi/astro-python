from flask import Flask, request, jsonify, send_file
import swisseph as swe
from PIL import Image, ImageDraw, ImageFont
from flask import send_file
import os
import threading
import time


app = Flask(__name__)

# set ephemeris path
swe.set_ephe_path('./ephe')


# -------------------------
# HOME ROUTE
# -------------------------
@app.route('/')
def home():
    return "Backend is running 🚀"


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
    "sun": "Su", "moon": "Mo", "mars": "Ma", "mercury": "Me",
    "jupiter": "Ju", "venus": "Ve", "saturn": "Sa",
    "rahu": "Ra", "ketu": "Ke"
}

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
def generate_chart(house_data, lagna_sign):
    SIZE = 900
    PAD  = 60
    G    = (SIZE - 2 * PAD) // 4   # cell size = 195
    O    = PAD                       # grid origin = 60

    img  = Image.new('RGB', (SIZE, SIZE), '#FFFDF5')
    draw = ImageDraw.Draw(img)

    try:
        fB = ImageFont.truetype("DejaVuSans-Bold.ttf", 19)
        fN = ImageFont.truetype("DejaVuSans.ttf", 13)
        fT = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
    except Exception:
        fB = fN = fT = ImageFont.load_default()

    DARK   = '#2C1810'
    ACCENT = '#8B1A1A'
    BG     = '#FFFDF5'   # matches image background
    LGBG   = '#FFF0E0'   # warm tint for Lagna house

    # ── 1. Outer border ───────────────────────────────────────────
    draw.rectangle([O, O, O+4*G, O+4*G], outline=DARK, width=3)

    # ── 2. Internal 4×4 grid lines ────────────────────────────────
    for i in range(1, 4):
        draw.line([O+i*G, O,     O+i*G, O+4*G], fill=DARK, width=2)
        draw.line([O,     O+i*G, O+4*G, O+i*G], fill=DARK, width=2)

    # ── 3. Diagonal lines in center 2×2 block ─────────────────────
    draw.line([O+G, O+G,   O+3*G, O+3*G], fill=DARK, width=2)   # \
    draw.line([O+3*G, O+G, O+G,   O+3*G], fill=DARK, width=2)   # /

    # ── 4. Fill all 4 center triangles ────────────────────────────
    # This erases the crossing lines INSIDE each triangle so planets
    # appear on a clean background (no lines running through text).
    tip = (O+2*G, O+2*G)       # center point (450, 450)
    TL  = (O+G,   O+G)         # (255, 255)
    TR  = (O+3*G, O+G)         # (645, 255)
    BR  = (O+3*G, O+3*G)       # (645, 645)
    BL  = (O+G,   O+3*G)       # (255, 645)

    # H1=top (Lagna, warm fill), H4=right, H7=bottom, H10=left (all BG)
    draw.polygon([TL, TR,  tip], fill=LGBG)   # H1  top
    draw.polygon([TR, BR,  tip], fill=BG)     # H4  right
    draw.polygon([BL, BR,  tip], fill=BG)     # H7  bottom
    draw.polygon([TL, BL,  tip], fill=BG)     # H10 left

    # ── 5. Redraw all center-block edges (fills covered them) ──────
    draw.line([TL,  TR ], fill=DARK, width=2)   # top edge
    draw.line([TR,  BR ], fill=DARK, width=2)   # right edge
    draw.line([BR,  BL ], fill=DARK, width=2)   # bottom edge
    draw.line([BL,  TL ], fill=DARK, width=2)   # left edge
    draw.line([TL,  tip], fill=DARK, width=2)   # \ top-left spoke
    draw.line([TR,  tip], fill=DARK, width=2)   # / top-right spoke
    draw.line([BR,  tip], fill=DARK, width=2)   # \ bottom-right spoke
    draw.line([BL,  tip], fill=DARK, width=2)   # / bottom-left spoke

    # ── 6. House text anchor positions ────────────────────────────
    # Outer rectangular cells: column/row centres.
    # Center triangles: pushed into the "fat" upper part of each triangle,
    # above the horizontal midline at y=450, to stay away from the center crossing.
    house_centers = {
        12: (157.5, 157.5),    # top-left corner cell
        1:  (450.0, 318.0),    # H1  top-triangle       (Lagna)
        2:  (742.5, 157.5),    # top-right corner cell
        3:  (742.5, 352.5),    # right col, upper cell
        4:  (600.0, 390.0),    # H4  right-triangle     (upper half)
        5:  (742.5, 547.5),    # right col, lower cell
        6:  (742.5, 742.5),    # bottom-right corner cell
        7:  (450.0, 610.0),    # H7  bottom-triangle    (lower half)
        8:  (157.5, 742.5),    # bottom-left corner cell
        9:  (157.5, 547.5),    # left col, lower cell
        10: (300.0, 390.0),    # H10 left-triangle      (upper half)
        11: (157.5, 352.5),    # left col, upper cell
    }

    LINE_H = 24   # px between planet lines
    NUM_H  = 16   # px for house number row

    # ── 7. Draw house numbers + planet abbreviations ───────────────
    for h, (hx, hy) in house_centers.items():
        planets = house_data.get(h, [])
        n       = len(planets)

        # Vertically centre the whole block (number + planets) around (hx, hy)
        total_h = NUM_H + n * LINE_H
        start_y = hy - total_h / 2

        # House number
        num_txt = str(h)
        nb  = draw.textbbox((0, 0), num_txt, font=fN)
        nw  = nb[2] - nb[0]
        col = ACCENT if h == 1 else '#AAAAAA'
        draw.text((hx - nw / 2, start_y), num_txt, fill=col, font=fN)

        # Planet abbreviations
        for i, pname in enumerate(planets):
            short = SHORT.get(pname, pname[:2].title())
            color = PLANET_COLORS.get(pname, '#1A1A2E')
            pb  = draw.textbbox((0, 0), short, font=fB)
            pw  = pb[2] - pb[0]
            px  = hx - pw / 2
            py  = start_y + NUM_H + i * LINE_H
            draw.text((px + 1, py + 1), short, fill='#D0C8B0', font=fB)   # shadow
            draw.text((px,     py    ), short, fill=color,      font=fB)

    # ── 8. Title ──────────────────────────────────────────────────
    title = f"Lagna: {lagna_sign}"
    tb = draw.textbbox((0, 0), title, font=fT)
    draw.text(((SIZE - (tb[2] - tb[0])) // 2, 16), title, fill=DARK, font=fT)

    # ── 9. Redraw outer border + corner accents ────────────────────
    draw.rectangle([O, O, O+4*G, O+4*G], outline=DARK, width=3)
    cs = 16
    for (ex, ey) in [(O, O), (O+4*G-cs, O), (O, O+4*G-cs), (O+4*G-cs, O+4*G-cs)]:
        draw.rectangle([ex, ey, ex+cs, ey+cs], fill=ACCENT)

    filename = f"chart_{int(time.time())}.png"
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
# RUN
# -------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)