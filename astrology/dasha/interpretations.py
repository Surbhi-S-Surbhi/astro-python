
MAHADASHA_INTERPRETATIONS = {

    "Surya":
        "Surya Mahadasha leadership aur authority ko strong karti hai.",

    "Chandra":
        "Chandra Mahadasha emotions, creativity aur mental growth laati hai.",

    "Mangal":
        "Mangal Mahadasha energy aur competition ko increase karti hai.",

    "Budh":
        "Budh Mahadasha communication aur intelligence ko strong karti hai.",

    "Guru":
        "Guru Mahadasha wisdom aur expansion deti hai.",

    "Shukra":
        "Shukra Mahadasha luxury aur relationships par focus karti hai.",

    "Shani":
        "Shani Mahadasha discipline aur karmic lessons laati hai.",

    "Rahu":
        "Rahu Mahadasha unexpected changes aur ambitions ko activate karti hai.",

    "Ketu":
        "Ketu Mahadasha spirituality aur detachment badhati hai."
}

def get_timeline_interpretation(graha):

    return MAHADASHA_INTERPRETATIONS.get(
        graha,
        f"{graha} Mahadasha jeevan mein mahatvapurna parivartan laati hai."
    )

def get_mahadasha_interpretation(
    lord
):

    return MAHADASHA_INTERPRETATIONS.get(
        lord,
        f"{lord} Mahadasha chal rahi hai."
    )