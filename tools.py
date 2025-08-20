import swisseph as swe
import datetime, requests, os
# from openai import OpenAI
from groq import Groq

from dotenv import load_dotenv, find_dotenv

# this finds .env in your project and loads it
load_dotenv(find_dotenv())
# def get_sidereal_positions(birth_date, birth_time, latitude, longitude, tz_offset=5.5):
#     """
#     Calculate Moon sign and Ascendant using sidereal zodiac (Lahiri ayanamsa).
#     """
#     # Convert datetime
#     dt = datetime.datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M")
#     jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60 - tz_offset)

    # # Set Lahiri ayanamsa
    # swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    # # Moon position
    # moon_calc = swe.calc_ut(jd, swe.MOON)   # returns (longitude, latitude, distance, speed_long, speed_lat, speed_dist)
    # moon_lon = moon_calc[0][0]              # first element, longitude
    # moon_sign = int(moon_lon // 30)

    # # Ascendant
    # houses, ascmc = swe.houses_ex(jd, latitude, longitude, b'A')
    # asc_lon = ascmc[0]                      # ascendant longitude
    # asc_sign = int(asc_lon // 30)

    # # Rashi list
    # rashis = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    #           "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

    # return {
    #     "moon_sign": rashis[moon_sign],
    #     "ascendant": rashis[asc_sign]
    # }

from geopy.geocoders import Nominatim

def get_chart_positions(birth_date, birth_time, city_name, tz_offset=5.5):
    # Parse birth date & time
    year, month, day = map(int, birth_date.split("-"))
    hour, minute = map(int, birth_time.split(":"))

    # Get latitude and longitude
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(city_name, timeout=10)
    if not location:
        raise ValueError(f"City '{city_name}' not found")
    latitude, longitude = location.latitude, location.longitude
    # Convert local time to UTC
    # utc_hour = hour - tz_offset
    # birth_datetime = datetime.datetime(year, month, day, int(utc_hour), minute)
    local_dt = datetime.datetime(year, month, day, hour, minute)

    # Convert to UTC by subtracting offset
    birth_datetime = local_dt - datetime.timedelta(hours=tz_offset)

    # Convert to Julian day
    jd = swe.julday(
        birth_datetime.year, birth_datetime.month, birth_datetime.day,
        birth_datetime.hour + birth_datetime.minute/60.0
    )

    # Set to Lahiri ayanamsha (sidereal zodiac)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Define zodiac signs
    zodiac_signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    results = {}

    # 🌙 Moon
    pos, _ = swe.calc_ut(jd, swe.MOON)
    lon = pos[0]
    sign_index = int(lon // 30)
    sign = zodiac_signs[sign_index]
    degree_in_sign = lon % 30
    results["Moon"] = {"longitude": lon, "sign": sign, "degree": round(degree_in_sign, 2)}

    # 🕉 Ascendant (Lagna)
    ascmc = swe.houses_ex(jd, latitude, longitude, b'A')  # Placidus system, can change
    asc_lon = ascmc[0][0]  # first value is Ascendant longitude
    sign_index = int(asc_lon // 30)
    sign = zodiac_signs[sign_index]
    degree_in_sign = asc_lon % 30
    results["Ascendant"] = {"longitude": asc_lon, "sign": sign, "degree": round(degree_in_sign, 2)}

    # (Optional) Add planets if needed
    planets = {
        "Sun": swe.SUN,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,
        "Ketu": swe.TRUE_NODE,
    }
    for planet, p_id in planets.items():
        pos, _ = swe.calc_ut(jd, p_id)
        lon = pos[0]
        sign_index = int(lon // 30)
        sign = zodiac_signs[sign_index]
        degree_in_sign = lon % 30
        results[planet] = {"longitude": lon, "sign": sign, "degree": round(degree_in_sign, 2)}

    return results

# Example call
# ans1 = get_chart_positions(
#     birth_date="2001-03-23",
#     birth_time="21:04",
#     latitude=26.9124,
#     longitude=75.7873
# )
# print(ans1['Ascendant']['sign'], ans1['Moon'])


def fetch_horoscope(sign: str, sign_type: str):
    """
    Fetch today's horoscope from Serper API for given sign.
    sign: e.g. "Leo"
    sign_type: "ascendant" or "moon"
    """
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": os.getenv("SERPER_API_KEY"), "Content-Type": "application/json"}
    query = f"Detailed today's {sign} {sign_type} horoscope, vedic astrology, Indian"
    payload = {"q": query, "num": 2}

    resp = requests.post(url, headers=headers, json=payload)
    print("resp Status:", resp.status_code)

    data = resp.json()
    results = [item["snippet"] for item in data.get("organic", [])[:2]]
    return " ".join(results) if results else f"No horoscope found for {sign_type} {sign}"

# res = fetch_horoscope("Libra", "Ascendant")
# print("res ", res)
# # client = OpenAI()

def generate_final_prediction(name, ascendant, moon_sign, asc_text, moon_text):
    """
    Combine horoscope texts into a single personalized prediction.
    """
    prompt = f"""
    Candidate: {name}
    Ascendant: {ascendant}
    Moon Sign: {moon_sign}

    Ascendant Horoscope Data: {asc_text}
    Moon Sign Horoscope Data: {moon_text}

    Task: Write a single, coherent, personalized prediction for today,
    blending both ascendant and moon sign influences.
    Keep it natural and insightful (4–5 sentences max).
    """
    

    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),)   

    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.7
    # )

    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
    model="openai/gpt-oss-20b",
    stream=False,
    )
    result = chat_completion.choices[0].message.content
    print("[INFO]: Result: ", result)
    return result



# text = generate_final_prediction(name= "s", ascendant= "libra", moon_sign= "aquarius", asc_text = "u ll have wonderful day", moon_text= "you are goin to be healthy!")


# print(text)
