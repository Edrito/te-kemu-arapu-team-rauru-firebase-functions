class TIMES:
    choosing_category = 15
    choosing_player = 5
    letter_selection = 15
    end = 15


# Generate hints based on the category, and the starting letter of a maori word
HINTS = {
    "food": {
        "a": {"āwenewene": "sickly sweet"},
        "e": {
            "E WORD": "E WORD",
        },
        "h": {"hēki": "egg"},
        "i": {
            "īnanga": "whitebait",
        },
        "k": {
            "kūmara": "sweet potato",
        },
        "m": {
            "mīti": "meat",
        },
        "n": {
            "nāti": "nut",
        },
        "o": {"ōti": "oats"},
        "p": {"pea": "pear"},
        "r": {"rīwai": "potato"},
        "t": {"tī": "tea"},
        "u": {"uhi": "yam"},
        "w": {"witi": "wheat"},
    },
    "locations": {
        "a": {
            "Akaroa": "Akaroa is a small town on Banks Peninsula in the Canterbury Region of the South Island of New Zealand"
        },
        "e": {
            "Eketāhuna": "Eketāhuna is a small rural settlement, in the south of the Tararua District and the Manawatū-Whanganui region of New Zealand's North Island"
        },
        "h": {
            "Hāwera": "Hāwera is the second-largest centre in the Taranaki region of New Zealand's North Island"
        },
        "i": {
            "Ihumātao": "Ihumātao is an archeological site of historic importance in the suburb of Māngere, Auckland"
        },
        "k": {
            "Kaikōura": "Kaikōura is a town on the east coast of the South Island of New Zealand"
        },
        "m": {"Manukau": "Manukau, or Manukau Central, is a suburb of South Auckland"},
        "n": {
            "Ngongotahā": "Ngongotahā is a small settlement on the western shores of Lake Rotorua in the North Island"
        },
        "o": {
            "Ōtaki": "Ōtaki is a town in the Kāpiti Coast District of the North Island"
        },
        "p": {
            "Paeroa": "Paeroa is a town in the Hauraki District of the Waikato Region in the North Island"
        },
        "r": {
            "Rangiora": "Rangiora is the largest town and seat of the Waimakariri District, in Canterbury"
        },
        "t": {
            "Taupō": "Taupō, sometimes written Taupo, is a town located in the central North Island"
        },
        "u": {"Urupukapuka": "Urupukapuka Island"},
        "w": {"Waihi": "Waihi is a town in Hauraki District in the North Island"},
    },
    "nature": {
        "a": {"awa": "river"},
        "e": {"eke": "ride, mount, overcome"},
        "h": {"hau": "(TEMP) wind"},
        "i": {"iwi": "(TEMP) bone"},
        "k": {"kai": "(TEMP) food"},
        "m": {"mahi": "(TEMP) work"},
        "n": {"ngahere": "(TEMP) forest"},
        "o": {"one": "(TEMP) sand"},
        "p": {"pā": "(TEMP) fortified village"},
        "r": {"roto": "(TEMP) lake"},
        "t": {"tāwhai": "(TEMP) tree"},
        "u": {"uru": "(TEMP) feather"},
        "w": {"wai": "(TEMP) water"},
    },
}


CATEGORIES = ["food", "locations", "nature"]


DIFFICULTY_TIMES = {"Beginner": 30, "Intermediate": 15, "Pro": 5}

MAORI_ALPHABET = "aehikmnoprutuw"

MAORI_ALPHABET_LIST = ["a", "e", "h", "i", "k", "m", "n", "o", "p", "r", "t", "u", "w"]
