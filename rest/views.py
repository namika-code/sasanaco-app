from flask import Blueprint, render_template, request
from flask_login import login_required
from concurrent.futures import ThreadPoolExecutor
import requests

# グローバル変数
game_process = None

# stockのBlueprint
rest_bp = Blueprint('rest', __name__, url_prefix='/rest')

# =======================
# 一覧
# =======================
@rest_bp.route('/')
@login_required
def index():
    # 画面遷移
    return render_template('rest/index.html')

# =======================
# 天気
# =======================
@rest_bp.route('/weather')
@login_required
def weather():
    # =======================
    # Open-Meteo
    # =======================
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 36.2381,
        "longitude": 137.9717,
        "current": ["temperature_2m", "weather_code"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min"],
        "timezone": "Asia/Tokyo"
    }

    response = requests.get(url, params=params)
    weather = response.json()

    weather_icons = {
        0: "bi-brightness-high",
        1: "bi-brightness-high",
        2: "bi-cloud-sun",
        3: "bi-cloud",
        45: "bi-cloud-fog",
        48: "bi-cloud-fog",
        51: "bi-cloud-drizzle",
        53: "bi-cloud-drizzle",
        55: "bi-cloud-drizzle",
        61: "bi-cloud-rain",
        63: "bi-cloud-rain-heavy",
        65: "bi-cloud-rain-heavy",
        71: "bi-cloud-snow",
        73: "bi-cloud-snow",
        75: "bi-cloud-snow",
        80: "bi-cloud-rain",
        81: "bi-cloud-rain-heavy",
        82: "bi-cloud-rain-heavy",
        95: "bi-cloud-lightning",
        96: "bi-cloud-lightning",
        99: "bi-cloud-lightning",
    }

    today_code = weather["daily"]["weather_code"][0]
    today_icon = weather_icons.get(today_code, "bi-question-circle")

    # =======================
    # 気象庁
    # =======================
    code = "200000"
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"
    data = requests.get(url).json()

    areas = data[0]["timeSeries"][0]["areas"]
    target_area = next(
        (a for a in areas if "中部" in a["area"]["name"]),
        areas[0]
    )

    weather_code = target_area["weatherCodes"][0]

    icon_map = {
        "1": "bi-sun",
        "2": "bi-cloud",
        "3": "bi-cloud-rain",
        "4": "bi-cloud-snow",
    }
    icon_class = icon_map.get(weather_code[0], "bi-question-circle")

    temps_series = data[0]["timeSeries"][2]
    temps_area = next(
        (a for a in temps_series["areas"] if a["area"]["code"] == target_area["area"]["code"]),
        temps_series["areas"][0]
    )
    temps = temps_area["temps"]

    min_temp = temps[0] if len(temps) >= 1 else None
    max_temp = temps[1] if len(temps) >= 2 else None

    # アメダス
    real_temp = None
    try:
        latest_time = requests.get(
            "https://www.jma.go.jp/bosai/amedas/data/latest_time.txt"
        ).text.strip()

        amedas_url = f"https://www.jma.go.jp/bosai/amedas/data/map/{latest_time}.json"
        amedas = requests.get(amedas_url).json()

        station = "47610"
        temp_raw = amedas.get(station, {}).get("temp", [None])[0]
        if temp_raw is not None:
            real_temp = temp_raw / 10
    except Exception:
        real_temp = None

    return render_template(
        "rest/weather.html",
        weather=weather,
        today_icon=today_icon,
        icon_class=icon_class,
        min_temp=min_temp,
        max_temp=max_temp,
        real_temp=real_temp
    )

# =======================
# NASA
# =======================
NASA_KEY = "DEMO_KEY"  # NASA_学習用はこれでOK

@rest_bp.route('/nasa')
@login_required
def nasa():

    with ThreadPoolExecutor() as executor:

        future_apod = executor.submit(get_apod)
        future_iss = executor.submit(get_iss)

        data = future_apod.result()
        position = future_iss.result()

    return render_template(
        "rest/nasa.html",
        data=data,
        pos=position
    )


# 日付指定で過去の宇宙画像も取得
# URLに ?date=YYYY-MM-DD を追加するだけ
@rest_bp.route("/apod/<date>")
def apod_by_date(date):
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": NASA_KEY, "date": date}
    data = requests.get(url, params=params).json()
    return render_template("rest/nasa.html", data=data)

# gallery
@rest_bp.route("/gallery", defaults={"keyword": "nebula"})
@rest_bp.route("/gallery/<keyword>")
def gallery(keyword):
    keyword = request.args.get("keyword", keyword)

    url = f"https://images-api.nasa.gov/search?q={keyword}&media_type=image"
    data = requests.get(url).json()

    items = data["collection"]["items"]

    return render_template(
        "rest/gallery.html",
        items=items,
        keyword=keyword
    )


def get_apod():
    nasa_url = "https://api.nasa.gov/planetary/apod"
    nasa_params = {"api_key": NASA_KEY}

    try:
        res = requests.get(
            nasa_url,
            params=nasa_params,
            timeout=5
        )

        res.raise_for_status()

        return res.json()

    except requests.exceptions.RequestException:
        return None


def get_iss():
    iss_url = "http://api.open-notify.org/iss-now.json"

    try:
        res = requests.get(
            iss_url,
            timeout=5
        )

        res.raise_for_status()

        return res.json().get("iss_position", {})

    except requests.exceptions.RequestException:
        return {
            "latitude": "取得失敗",
            "longitude": "取得失敗"
        }

# ============================
# ブロック崩し(実行ファイルからFlask用に変更)
# ============================
@rest_bp.route("block")
def block_game():
    return render_template("rest/block_game.html")


# =======================
# 動物園
# =======================
@rest_bp.route("/zoo")
def zoo():
    animals = [
        {"file": "くま.webp", "size": 80, "like": "meat"},
        {"file": "ぞう.webp","size": 170, "like": "apple"},
        {"file": "きりん.webp", "size": 100, "like": "apple"},
        {"file": "ごりら正面.webp", "size": 50, "like": "apple"},
        {"file": "いんこ.webp","size": 30, "like": "apple"},
        {"file": "うさぎ.webp", "size": 30, "like": "apple"},
        {"file": "ステゴサウルス.webp", "size":150, "like": "meat"},
        {"file": "ティラノサウルス.webp", "size": 150, "like": "meat"},
        {"file": "トリケラトプス.webp", "size": 150, "like": "apple"},
        {"file": "プテラノドン.webp", "size": 150, "like": "meat"},
        {"file": "ブラキオサウルス.webp", "size": 150, "like": "meat"},
        {"file": "ぺんぎん.webp", "size": 30}, 
        {"file": "ねこ長沢.webp", "size": 100, "like": "apple"},
        {"file": "ぱんだ.webp", "size": 50},
        {"file": "メスライオン.webp", "size": 70, "like": "meat"},
        {"file": "オスライオン.webp", "size": 80, "like": "meat"},
       
    ]
    foods = [
        {"file": "apple.webp", "size": 50},
        {"file": "meat.webp", "size": 50}    
    ]
    
    return render_template('rest/zoo.html', animals=animals)