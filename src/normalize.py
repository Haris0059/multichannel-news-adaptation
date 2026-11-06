import re
from decimal import Decimal

FOLD = str.maketrans("čćšžđ", "ccszd")

MONTH_FORMS = {
    1: "january jan januar januara januaru januarom "
    "sijecanj sijecnja sijecnju sijecnjem",
    2: "february feb februar februara februaru februarom "
    "veljaca veljace veljaci veljacu veljacom",
    3: "march mar mart marta martu martom ozujak ozujka ozujku ozujkom",
    4: "april apr aprila aprilu aprilom travanj travnja travnju travnjem",
    5: "may maj maja maju majem svibanj svibnja svibnju svibnjem",
    6: "june jun juni juna junu junom lipanj lipnja lipnju lipnjem",
    7: "july jul juli jula julu julom srpanj srpnja srpnju srpnjem",
    8: "august aug augusta augustu augustom avgust avg avgusta avgustu avgustom "
    "kolovoz kolovoza kolovozu kolovozom",
    9: "september sep sept septembar septembra septembru septembrom "
    "rujan rujna rujnu rujnom",
    10: "october oct oktobar okt oktobra oktobru oktobrom "
    "listopad listopada listopadu listopadom",
    11: "november nov novembar novembra novembru novembrom "
    "studeni studenog studenoga studenom",
    12: "december dec decembar decembra decembru decembrom "
    "prosinac prosinca prosincu prosincem",
}
MONTHS = {form: month for month, forms in MONTH_FORMS.items() for form in forms.split()}
DATE_FILLERS = {"st", "nd", "rd", "th", "of", "from", "od"}

# "bilion" is left out: in Bosnian it means 10^12, not the English billion.
NUMBER_FORMS = {
    0: "zero nula",
    1: "one jedan jedna jedno jednu jednog jednoj jednom",
    2: "two dva dvije dvoje dvojica",
    3: "three tri troje trojica",
    4: "four cetiri cetvoro cetvero cetvorica",
    5: "five pet petoro petero petorica",
    6: "six sest sestoro sestero sestorica",
    7: "seven sedam sedmoro sedmero sedmorica",
    8: "eight osam osmoro osmero osmorica",
    9: "nine devet devetoro devetero devetorica",
    10: "ten deset desetoro desetero desetorica",
    11: "eleven jedanaest",
    12: "twelve dvanaest",
    13: "thirteen trinaest",
    14: "fourteen cetrnaest",
    15: "fifteen petnaest",
    16: "sixteen sesnaest",
    17: "seventeen sedamnaest",
    18: "eighteen osamnaest",
    19: "nineteen devetnaest",
    20: "twenty dvadeset",
    30: "thirty trideset",
    40: "forty cetrdeset",
    50: "fifty pedeset",
    60: "sixty sezdeset",
    70: "seventy sedamdeset",
    80: "eighty osamdeset",
    90: "ninety devedeset",
    100: "hundred hundreds sto stotina stotinu stotine stotini",
    200: "dvjesto dvjesta dvesta",
    300: "tristo trista",
    400: "cetiristo",
    500: "petsto",
    600: "seststo",
    700: "sedamsto",
    800: "osamsto",
    900: "devetsto",
    1_000: "thousand thousands hiljada hiljadu hiljade hiljadi "
    "tisuca tisucu tisuce tisuci",
    1_000_000: "million millions milion miliona milione milioni "
    "milijun milijuna milijune milijuni",
    1_000_000_000: "billion billions milijarda milijarde milijardu milijardi",
}
NUMBER_WORDS = {
    form: value for value, forms in NUMBER_FORMS.items() for form in forms.split()
}
NUMBER_CONNECTORS = {"i", "and", "a"}

CASE_ENDINGS = ("om", "em", "og", "oj", "a", "e", "i", "u", "o")

ORG_ALIASES = {
    "ibu": [
        "IBU",
        "International Burch University",
        "Internacionalni univerzitet Burch",
        "Internacionalni Burch univerzitet",
    ],
    "unsa": ["UNSA", "University of Sarajevo", "Univerzitet u Sarajevu"],
    "eu": ["EU", "European Union", "Evropska unija", "Europska unija"],
}


def fold(text):
    return text.lower().translate(FOLD)


def parse_date_part(text, month_known=False):
    numbers = []
    month = None
    for token in re.findall(r"\d+|[^\W\d_]+", fold(text)):
        if token.isdigit():
            numbers.append(token)
        elif token in MONTHS:
            month = MONTHS[token]
        elif token not in DATE_FILLERS:
            return None

    small = [int(n) for n in numbers if len(n) <= 2]
    years = [int(n) for n in numbers if len(n) == 4]
    if len(small) + len(years) != len(numbers) or len(years) > 1:
        return None

    year = years[0] if years else None
    day = None
    if month is None and not (month_known and len(small) == 1):
        if len(small) == 3 and year is None:
            day, month, year = small[0], small[1], 2000 + small[2]
        elif len(small) == 2:
            day, month = small
        elif len(small) == 1 and year is not None:
            month = small[0]
        elif len(small) == 1:
            day = small[0]
        elif small:
            return None
    elif len(small) == 1:
        day = small[0]
    elif small:
        return None

    if year is None and month is None and day is None:
        return None
    if (month and not 1 <= month <= 12) or (day and not 1 <= day <= 31):
        return None
    return year, month, day


def normalize_date(text):
    text = text.strip()

    academic = re.fullmatch(r"(\d{4})\s*[/–—-]\s*(\d{4}|\d{2})\.?", text)
    if academic:
        start = int(academic[1])
        end = int(academic[2])
        if end < 100:
            end += start - start % 100
        if end > start:
            return {"start": (start, None, None), "end": (end, None, None)}

    iso = re.fullmatch(r"(\d{4})-(\d{2})(?:-(\d{2}))?", text)
    if iso:
        day = int(iso[3]) if iso[3] else None
        parsed = (int(iso[1]), int(iso[2]), day)
        return {"start": parsed, "end": parsed}

    parts = re.split(r"\s*[-–—]\s*|\s+(?:to|do)\s+", text)
    if len(parts) == 1:
        parsed = parse_date_part(text)
        return {"start": parsed, "end": parsed} if parsed else None
    if len(parts) != 2:
        return None

    left = parse_date_part(parts[0])
    if left is None:
        return None
    right = parse_date_part(parts[1], month_known=left[1] is not None)
    if right is None:
        return None

    start = (left[0] or right[0], left[1] or right[1], left[2])
    end = (right[0] or left[0], right[1] or left[1], right[2])
    return {"start": start, "end": end}


def parse_digits(text, lang):
    text = re.sub(r"\s", "", text)
    if "," in text and "." in text:
        decimal = text[max(text.rfind(","), text.rfind("."))]
    else:
        decimal = "," if lang == "bs" else "."

    whole, fraction = text, "0"
    if text.count(decimal) == 1:
        whole, fraction = text.split(decimal)
    return Decimal(f"{re.sub(r'[.,]', '', whole)}.{fraction or '0'}")


def parse_number_words(text):
    tokens = [t for t in re.split(r"[\s-]+", text) if t not in NUMBER_CONNECTORS]
    if not tokens or not all(t in NUMBER_WORDS for t in tokens):
        return None

    total = current = 0
    for token in tokens:
        value = NUMBER_WORDS[token]
        if value >= 1_000:
            total += (current or 1) * value
            current = 0
        elif value == 100:
            current = (current or 1) * value
        else:
            current += value
    return Decimal(total + current)


def normalize_number(text, lang):
    text = fold(text).strip().rstrip(".").strip()

    match = re.fullmatch(r"(\d[\d.,\s]*?)\s*([^\d]*)", text)
    if match:
        value = parse_digits(match[1], lang)
        for word in match[2].split():
            if NUMBER_WORDS.get(word, 0) < 100:
                return None
            value *= NUMBER_WORDS[word]
    else:
        value = parse_number_words(text)
        if value is None:
            return None

    return int(value) if value == value.to_integral_value() else float(value)


# Strips suffixes only, so a real spelling change still differs: Skeledzija is not
# Skeledžija. Repeated because stems like Adem end in a suffix themselves.
def stem_word(word):
    while True:
        for ending in CASE_ENDINGS:
            if word.endswith(ending) and len(word) - len(ending) >= 2:
                word = word[: -len(ending)]
                break
        else:
            return word


def name_forms(text):
    exact = " ".join(text.lower().split())
    return {"exact": exact, "stem": " ".join(stem_word(w) for w in exact.split())}


ORG_IDS = {
    name_forms(alias)["stem"]: org_id
    for org_id, aliases in ORG_ALIASES.items()
    for alias in aliases
}


def normalize_org(text):
    text = re.sub(r"\b([A-ZČĆŠŽĐ]{2,})-[a-zčćšžđ]+\b", r"\1", text)
    forms = name_forms(text)
    org_id = ORG_IDS.get(forms["stem"])
    return {"exact": org_id, "stem": org_id} if org_id else forms


def normalize(text, fact_type, lang):
    if fact_type == "DATE":
        return normalize_date(text)
    if fact_type == "NUMBER":
        return normalize_number(text, lang)
    if fact_type == "PERSON":
        return name_forms(text)
    if fact_type == "ORG":
        return normalize_org(text)
    raise ValueError(f"unknown fact type: {fact_type}")
