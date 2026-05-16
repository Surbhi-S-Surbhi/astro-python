# dasha/engine.py

import swisseph as swe
from datetime import datetime, timedelta
from datetime import datetime, timedelta
NAKSHATRA_SIZE = 13.3333333333
VIMSHOTTARI_SEQUENCE = [
    "Ketu",
    "Shukra",
    "Surya",
    "Chandra",
    "Mangal",
    "Rahu",
    "Guru",
    "Shani",
    "Budh"
]

NAKSHATRA_LORDS = [
    "Ketu",
    "Shukra",
    "Surya",
    "Chandra",
    "Mangal",
    "Rahu",
    "Guru",
    "Shani",
    "Budh"
] * 3

DASHA_YEARS = {
    "Ketu": 7,
    "Shukra": 20,
    "Surya": 6,
    "Chandra": 10,
    "Mangal": 7,
    "Rahu": 18,
    "Guru": 16,
    "Shani": 19,
    "Budh": 17,
}
def get_moon_longitude(dt):

    jd = swe.julday(
        dt.year,
        dt.month,
        dt.day,
        dt.hour + dt.minute / 60
    )

    moon = swe.calc_ut(jd, swe.MOON)

    return moon[0][0]


def get_nakshatra(longitude):

    return int(
        longitude / NAKSHATRA_SIZE
    )


def get_dasha_lord(nakshatra_index):

    return NAKSHATRA_LORDS[nakshatra_index]

def calculate_balance_years(
    longitude,
    dasha_lord
):

    nakshatra_start = (
        int(longitude / NAKSHATRA_SIZE)
        * NAKSHATRA_SIZE
    )

    degrees_passed = (
        longitude - nakshatra_start
    )

    degrees_remaining = (
        NAKSHATRA_SIZE - degrees_passed
    )

    total_dasha_years = DASHA_YEARS[dasha_lord]

    balance_years = (
        degrees_remaining
        / NAKSHATRA_SIZE
    ) * total_dasha_years

    return balance_years


def generate_mahadasha_timeline(
    birth_date,
    first_lord,
    balance_years
):

    timeline = []

    # FIRST MAHADASHA
    current_start = birth_date

    first_end = (
        birth_date
        + timedelta(days=balance_years * 365.25)
    )

    timeline.append({
        "lord": first_lord,
        "start": current_start,
        "end": first_end
    })

    current_start = first_end

    # REMAINING SEQUENCE
    start_index = VIMSHOTTARI_SEQUENCE.index(
        first_lord
    )

    remaining_sequence = (
        VIMSHOTTARI_SEQUENCE[start_index + 1:]
        + VIMSHOTTARI_SEQUENCE[:start_index]
    )

    for lord in remaining_sequence:

        years = DASHA_YEARS[lord]

        end_date = (
            current_start
            + timedelta(days=years * 365.25)
        )

        timeline.append({
            "lord": lord,
            "start": current_start,
            "end": end_date
        })

        current_start = end_date

    return timeline


def get_current_mahadasha(timeline):

    now = datetime.now()

    for dasha in timeline:

        if (
            dasha["start"]
            <= now
            <= dasha["end"]
        ):

            return dasha

    return None

def generate_antardashas(mahadasha):

    maha_lord = mahadasha["lord"]

    maha_years = DASHA_YEARS[
        maha_lord
    ]

    start = mahadasha["start"]

    antardashas = []

    start_index = VIMSHOTTARI_SEQUENCE.index(
        maha_lord
    )

    sequence = (
        VIMSHOTTARI_SEQUENCE[start_index:]
        + VIMSHOTTARI_SEQUENCE[:start_index]
    )

    current_start = start

    for antar_lord in sequence:

        antar_years = (
            maha_years
            * DASHA_YEARS[antar_lord]
        ) / 120

        antar_end = (
            current_start
            + timedelta(days=antar_years * 365.25)
        )

        antardashas.append({

            "lord": antar_lord,

            "start": current_start,

            "end": antar_end

        })

        current_start = antar_end

    return antardashas

def get_current_antardasha(
    antardashas
):

    now = datetime.now()

    for antar in antardashas:

        if (
            antar["start"]
            <= now
            <= antar["end"]
        ):

            return antar

    return None

def generate_mahadasha_timeline(birth_date):

    moon_longitude = get_moon_longitude(
        birth_date
    )

    nakshatra = get_nakshatra(
        moon_longitude
    )

    first_lord = get_dasha_lord(
        nakshatra
    )

    balance_years = calculate_balance_years(
        moon_longitude,
        first_lord
    )

    dasha_order = [
        "Ketu",
        "Shukra",
        "Surya",
        "Chandra",
        "Mangal",
        "Rahu",
        "Guru",
        "Shani",
        "Budh"
    ]

    dasha_years = {
        "Ketu": 7,
        "Shukra": 20,
        "Surya": 6,
        "Chandra": 10,
        "Mangal": 7,
        "Rahu": 18,
        "Guru": 16,
        "Shani": 19,
        "Budh": 17
    }

    start_index = dasha_order.index(
        first_lord
    )

    timeline = []

    current_start = birth_date

    remaining = balance_years

    first_end = current_start + timedelta(
        days=int(remaining * 365.25)
    )

    timeline.append({

        "lord": first_lord,

        "start": current_start,

        "end": first_end
    })

    current_start = first_end

    for i in range(1, 9):

        lord = dasha_order[
            (start_index + i) % 9
        ]

        years = dasha_years[lord]

        end_date = current_start + timedelta(
            days=int(years * 365.25)
        )

        timeline.append({

            "lord": lord,

            "start": current_start,

            "end": end_date
        })

        current_start = end_date

    return timeline