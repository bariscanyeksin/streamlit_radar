import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import ssl
import io
from matplotlib import font_manager as fm
from matplotlib.colors import to_rgba
import requests
from urllib.request import urlopen
import streamlit as st
from datetime import datetime
from urllib.error import HTTPError
import base64
import os

st.set_page_config(
    page_title="FotMob Radar",
    initial_sidebar_state="expanded"
)

plt.rcParams['figure.dpi'] = 300
current_dir = os.path.dirname(os.path.abspath(__file__))

# Poppins fontunu yükleme
font_path = os.path.join(current_dir, 'fonts', 'Poppins-Regular.ttf')
prop = fm.FontProperties(fname=font_path)

bold_font_path = os.path.join(current_dir, 'fonts', 'Poppins-SemiBold.ttf')
bold_prop = fm.FontProperties(fname=bold_font_path)

# SSL sertifika doğrulamasını devre dışı bırakma
ssl._create_default_https_context = ssl._create_unverified_context

player1_id = 0
player2_id = 0

def fetch_players(search_term):
    if not search_term.strip():
        return {}

    headers = {
        'accept': '*/*',
        'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'if-none-match': '"ye9k3y5smr9ux"',
        'priority': 'u=1, i',
        'referer': 'https://www.fotmob.com',
        'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'x-fm-req': 'eyJib2R5Ijp7ImNvZGUiOjE3MjM5ODgxMDg3OTB9LCJzaWduYXR1cmUiOiIxMDY3ODRDNkZGRjg1MUJCN0REOTc5RDg5QzdBMUUzMCJ9',
    }

    params = {
        'hits': '50',
        'lang': 'tr,en',
        'term': search_term,
    }

    response = requests.get('https://www.fotmob.com/api/search/suggest', params=params, headers=headers)
    
    try:
        data = response.json()
    except ValueError:
        st.error("API yanıtı JSON formatında değil veya boş.")
        return {}

    if not isinstance(data, list) or len(data) == 0 or 'suggestions' not in data[0]:
        st.error("Beklenen JSON yapısı bulunamadı.")
        return {}

    suggestions = data[0]['suggestions']
    
    player_options = {f"{player['name']} ({player['teamName']})": player['id'] for player in suggestions if player['type'] == 'player'}
    
    return player_options

# Kullanıcıdan iki oyuncu için arama terimlerini alma
search_term1 = st.sidebar.text_input("Oyuncu 1 Arama", placeholder="Örneğin: Ferdi", help="Birinci oyuncunun ismini buraya girin.")
search_term2 = st.sidebar.text_input("Oyuncu 2 Arama", placeholder="Örneğin: Osayi", help="İkinci oyuncunun ismini buraya girin.")

# Apply the custom class to the input elements
st.markdown(
    """
    <style>
        /* Tüm sidebar text inputlarını hedef almak için */
         input .st-bb {
            background-color: #242C3A;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Boş arama terimleri durumunda kullanıcıyı bilgilendirme
if not search_term1.strip() and not search_term2.strip():
    st.sidebar.warning("Her iki oyuncu ismi de boş. Lütfen arama terimlerini girin.")
elif not search_term1.strip():
    st.sidebar.warning("Oyuncu 1 ismi boş. Lütfen arama terimini girin.")
elif not search_term2.strip():
    st.sidebar.warning("Oyuncu 2 ismi boş. Lütfen arama terimini girin.")
else:
    # Her iki oyuncu için de verileri çekme
    players1 = fetch_players(search_term1)
    players2 = fetch_players(search_term2)

    # Oyuncu 1 ve Oyuncu 2 seçimleri için seçeneklerin birleştirilmesi
    if players1 and players2:
        all_players_1 = {**players1}
        all_players_2 = {**players2}
        selected_player1 = st.sidebar.selectbox("Oyuncu 1 Seçimi", options=list(all_players_1.keys()), help="Listeden karşılaştırmak istediğiniz birinci oyuncuyu seçin.")
        selected_player2 = st.sidebar.selectbox("Oyuncu 2 Seçimi", options=list(all_players_2.keys()), help="Listeden karşılaştırmak istediğiniz ikinci oyuncuyu seçin.")

        player1_id = all_players_1.get(selected_player1)
        player2_id = all_players_2.get(selected_player2)
    else:
        st.sidebar.write("Aramanızla eşleşen oyuncu bulunamadı.")
        
# Oyuncu sezon bilgilerini çeken fonksiyon
def get_player_season_infos(player_id):
    headers = {
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'Referer': f'https://www.fotmob.com/players/{player_id}',
        'x-fm-req': 'eyJib2R5Ijp7ImNvZGUiOjE3MjExMjU1NTE2NDh9LCJzaWduYXR1cmUiOiI3MEJDRDc3MDRCMjRGQzI5NEQ3Mzc5N0IyMTE5N0FDOSJ9',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'id': str(player_id)
    }

    response = requests.get('https://www.fotmob.com/api/playerData', params=params, headers=headers)
    data = response.json()
    return data["statSeasons"]

# Kullanıcıya sezon ve ligleri göster ve entryId'yi seçtir
def select_season_and_league(player_seasons, player_num):
    options = []
    option_to_entryid = {}

    for season in player_seasons:
        season_name = season['seasonName']
        for tournament in season['tournaments']:
            display_name = f"{season_name} - {tournament['name']}"
            entry_id = tournament['entryId']
            options.append(display_name)
            option_to_entryid[display_name] = entry_id

    selected_option = st.sidebar.selectbox(f"Oyuncu {player_num} | Sezon - Lig", options, help="Karşılaştırılmak istenilen sezonu ve ligi seçin.")
    return option_to_entryid[selected_option]

def get_player_primary_position(player_id):
    headers = {
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'Referer': f'https://www.fotmob.com/players/{player_id}',
        'x-fm-req': 'eyJib2R5Ijp7ImNvZGUiOjE3MjExMjU1NTE2NDh9LCJzaWduYXR1cmUiOiI3MEJDRDc3MDRCMjRGQzI5NEQ3Mzc5N0IyMTE5N0FDOSJ9',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'id': str(player_id)
    }

    response = requests.get('https://www.fotmob.com/api/playerData', params=params, headers=headers)
    data = response.json()

    primary_position = data.get('positionDescription', {}).get('primaryPosition', {}).get('label')
    return primary_position
    
translation_dict = {
    'Tackles won': 'Başarılı Top Çalma',
    'Tackles won %': 'Başarılı Top Çalma Yüzdesi',
    'Duels won': 'Kazanılan İkili Mücadele',
    'Duels won %': 'Kazanılan İkili Mücadele Yüzdesi',
    'Aerials won': 'Kazanılan Hava Topu',
    'Aerials won %': 'Kazanılan Hava Topu Yüzdesi',
    'Interceptions': 'Top Kapma',
    'Recoveries': 'Top Kazanma',
    'Accurate passes': 'Başarılı Pas',
    'Pass accuracy': 'Başarılı Pas Yüzdesi',
    'Successful crosses': 'Başarılı Orta',
    'Cross accuracy': 'Başarılı Orta Yüzdesi',
    'Accurate long balls': 'Başarılı Uzun Top',
    'Long ball accuracy': 'Başarılı Uzun Top Yüzdesi',
    'Chances created': 'Gol Şansı Yaratma',
    'Touches': 'Topla Buluşma',
    'Dribbles': 'Başarılı Çalım',
    'Dribbles success rate': 'Başarılı Çalım Yüzdesi',
    'Saves': 'Kurtarışlar',
    'Save percentage': 'Kurtarış Yüzdesi',
    'Goals prevented': 'Gol Kurtarma',
    'Clean sheets': 'Gol Yemeden Bitirilen Maçlar',
    'Penalty goals saves': 'Penaltı Kurtarma',
    'Blocked scoring attempt': 'Gol Engelleme',
    'Possession won final 3rd': 'Rakip Alanda Top Çalma',
    'Fouls committed': 'Yapılan Faul',
    'Fouls won': 'Kazanılan Faul',
    'xG': 'Gol Beklentisi (xG)',
    'xGOT': 'İsabetli Şutta xG (xGOT)',
    'Shots': 'Şut',
    'Shots on target': 'İsabetli Şut',
    'xA': 'Asist Beklentisi (xA)',
    'Touches in opposition box': 'Rakip Ceza Sahasında Topla Buluşma'
}

def translate_stats(stat_titles, translation_dict):
    return [translation_dict.get(stat, stat) for stat in stat_titles]

# Oyuncu verilerini çekme fonksiyonu
def fetch_player_data(player_id, season_id):
    headers = {
        'accept': '*/*',
        'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'priority': 'u=1, i',
        'referer': 'https://www.fotmob.com/tr/players/' + str(player_id),
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    params = {'playerId': str(player_id), 'seasonId': str(season_id)}
    response = requests.get('https://www.fotmob.com/api/playerStats', params=params, headers=headers)
    response.raise_for_status()
    return response.json()

# DataFrame oluşturma fonksiyonu
def create_player_df(player_data):  
    if 'statsSection' not in player_data:
        return pd.DataFrame()  # Boş bir DataFrame döndürüyoruz
    
    top_stats = player_data['statsSection']['items']
    dfs = [pd.DataFrame(stat['items']).assign(category=stat['title']) for stat in top_stats]
    return pd.concat(dfs, ignore_index=True)

# İstatistik değerlerini çıkarma fonksiyonu
def extract_stat_values(df, stat_titles):
    stat_values = []
    for title in stat_titles:
        value = df.loc[df['title'] == title, 'per90'].values
        if len(value) > 0:
            stat_values.append(round(value[0], 2))  # Yuvarlama işlemi
        else:
            stat_values.append(0)  # Eğer başlık yoksa 0 ekle
    return stat_values

def extract_stat_values_percentage(df, stat_titles):
    stat_values = []
    for title in stat_titles:
        value = df.loc[df['title'] == title, 'percentileRankPer90'].values
        if len(value) > 0:
            stat_values.append(round(value[0], 2))  # Yuvarlama işlemi
        else:
            stat_values.append(0)  # Eğer başlık yoksa 0 ekle
    return stat_values

def get_player_name(player_id):
    headers = {
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'Referer': f'https://www.fotmob.com/players/{player_id}',
        'x-fm-req': 'eyJib2R5Ijp7ImNvZGUiOjE3MjExMjU1NTE2NDh9LCJzaWduYXR1cmUiOiI3MEJDRDc3MDRCMjRGQzI5NEQ3Mzc5N0IyMTE5N0FDOSJ9',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'id': str(player_id)
    }

    response = requests.get('https://www.fotmob.com/api/playerData', params=params, headers=headers)
    data = response.json()
    name = data["name"]
    return name

def get_last_shot_team_id(player_data):
    # Shotmap listesindeki son şutu al
    if player_data != None:
        if 'shotmap' in player_data:
            if player_data['shotmap'] != None:
                last_shot = player_data['shotmap'][-1]
                # Son şutun teamId değerini döndür
                return last_shot['teamId']
            else:
                return 0
        else:
            return 0
    else:
        return 0

def get_minutes(player_data, specific_stat_name):
    items = player_data['topStatCard']['items']
    
    # Belirli bir istatistik adını arayın
    for item in items:
        if item.get('title') == specific_stat_name:
            return item.get('statValue')
    
    return None

def get_matches_count(player_data, specific_stat_name):
    items = player_data['topStatCard']['items']
    
    # Belirli bir istatistik adını arayın
    for item in items:
        if item.get('title') == specific_stat_name:
            return item.get('statValue')
    
    return None

def get_started_matches_count(player_data, specific_stat_name):
    items = player_data['topStatCard']['items']
    
    # Belirli bir istatistik adını arayın
    for item in items:
        if item.get('title') == specific_stat_name:
            return item.get('statValue')
    
    return None

def fetch_player_season_and_league(player_id, season_id):
    headers = {
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'Referer': f'https://www.fotmob.com/players/{player_id}',
        'x-fm-req': 'eyJib2R5Ijp7ImNvZGUiOjE3MjExMjU1NTE2NDh9LCJzaWduYXR1cmUiOiI3MEJDRDc3MDRCMjRGQzI5NEQ3Mzc5N0IyMTE5N0FDOSJ9',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'id': str(player_id)
    }

    response = requests.get('https://www.fotmob.com/api/playerData', params=params, headers=headers)
    data = response.json()

    # Sezon bilgilerini içeren yapı
    stat_seasons = data.get('statSeasons', [])
    
    season_text = None
    league_name = None

    for season in stat_seasons:
        tournaments = season.get('tournaments', [])
        for tournament in tournaments:
            entry_id = tournament.get('entryId')
            if entry_id == season_id:
                season_text = season.get('seasonName')  # Sezon tarihi
                league_name = tournament.get('name')  # Lig adı
                break
        if season_text and league_name:
            break

    return season_text, league_name

def get_team_name(teamId):
    headers = {
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'Referer': f'https://www.fotmob.com/',
        'x-fm-req': 'eyJib2R5Ijp7ImNvZGUiOjE3MjExMjU1NTE2NDh9LCJzaWduYXR1cmUiOiI3MEJDRDc3MDRCMjRGQzI5NEQ3Mzc5N0IyMTE5N0FDOSJ9',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'id': str(teamId)
    }

    response = requests.get('https://www.fotmob.com/api/teams', params=params, headers=headers)
    data = response.json()
    teamName = data['details']['name']
    return teamName

def get_current_team_name(playerId):
    headers = {
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'Referer': f'https://www.fotmob.com/players/{playerId}',
    'x-fm-req': 'eyJib2R5Ijp7ImNvZGUiOjE3MjExMjU1NTE2NDh9LCJzaWduYXR1cmUiOiI3MEJDRDc3MDRCMjRGQzI5NEQ3Mzc5N0IyMTE5N0FDOSJ9',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'id': str(playerId)
    }

    response = requests.get('https://www.fotmob.com/api/playerData', params=params, headers=headers)
    data = response.json()
    if data["primaryTeam"] != None:
        return data["primaryTeam"]["teamName"]
    else:
        return "-"

def get_birthday(playerId):
    headers = {
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'Referer': f'https://www.fotmob.com/players/{playerId}',
    'x-fm-req': 'eyJib2R5Ijp7ImNvZGUiOjE3MjExMjU1NTE2NDh9LCJzaWduYXR1cmUiOiI3MEJDRDc3MDRCMjRGQzI5NEQ3Mzc5N0IyMTE5N0FDOSJ9',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'id': str(playerId)
    }

    response = requests.get('https://www.fotmob.com/api/playerData', params=params, headers=headers)
    data = response.json()
    birthday = data["birthDate"]["utcTime"]

    # Tarihi datetime nesnesine dönüştür
    date_obj = datetime.fromisoformat(birthday.replace("Z", "+00:00"))

    # Yeni formata çevir
    formatted_date = date_obj.strftime("%d.%m.%Y")
    return formatted_date

def get_age(playerId):
    headers = {
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'Referer': f'https://www.fotmob.com/players/{playerId}',
    'x-fm-req': 'eyJib2R5Ijp7ImNvZGUiOjE3MjExMjU1NTE2NDh9LCJzaWduYXR1cmUiOiI3MEJDRDc3MDRCMjRGQzI5NEQ3Mzc5N0IyMTE5N0FDOSJ9',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'id': str(playerId)
    }

    response = requests.get('https://www.fotmob.com/api/playerData', params=params, headers=headers)
    data = response.json()
    # playerInformation listesini al
    player_information = data.get('playerInformation', [])
    
    # Yaşı bulmak için döngü
    for item in player_information:
        if item.get('title') == 'Age':
            # Yaş bilgisini döndür
            return item['value'].get('numberValue')
    
    # Yaş bulunamazsa None döndür
    return None

st.markdown("""
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

                    html, body, [class*="cache"], [class*="st-"]  {
                        font-family: 'Poppins', sans-serif;
                    }
                    </style>
                    """, unsafe_allow_html=True
                )

if int(player1_id) > 0 and int(player2_id) > 0:
    # Oyuncu isimlerini almak için gerekli fonksiyonu çağırma
    player1_name = str(get_player_name(int(player1_id)))
    player2_name = str(get_player_name(int(player2_id)))

    # Sezon ve Lig bilgilerini çek
    player1_seasons = get_player_season_infos(player1_id)
    player2_seasons = get_player_season_infos(player2_id)

    if player1_seasons != None and player2_seasons != None:
        # Seçilen entryId'ler
        player1_season_id = select_season_and_league(player1_seasons, 1)
        player2_season_id = select_season_and_league(player2_seasons, 2)
    
    else:
        player1_season_id = "0-0"
        player2_season_id = "0-0"

    # Pozisyonları Türkçeye çeviren dict
    position_translation_dict = {
        "Goalkeeper": "Kaleci",
        "Keeper": "Kaleci",
        "Right Back": "Sağ Bek",
        "Left Back": "Sol Bek",
        "Center Back": "Stoper",
        "Right Midfielder": "Sağ Orta Saha",
        "Left Midfielder": "Sol Orta Saha",
        "Central Midfielder": "Merkez Orta Saha",
        "Attacking Midfielder": "Ofansif Orta Saha",
        "Defensive Midfielder": "Defansif Orta Saha",
        "Right Winger": "Sağ Kanat",
        "Left Winger": "Sol Kanat",
        "Striker": "Forvet",
        "Forward": "Hücumcu",
        "Center Forward": "Santrafor"
    }

    player1_primary_position = get_player_primary_position(player1_id)
    player2_primary_position = get_player_primary_position(player2_id)

    # Oyuncu pozisyonlarını Türkçeye çevirme
    player1_primary_position_tr = position_translation_dict.get(player1_primary_position, player1_primary_position)
    player2_primary_position_tr = position_translation_dict.get(player2_primary_position, player2_primary_position)

    selectbox_index = 0

    if player1_primary_position == "Goalkeeper":
        selectbox_index = 0
    if player1_primary_position == "Center Back":
        selectbox_index = 1
    if player1_primary_position == "Left Back" or player1_primary_position == "Right Back":
        selectbox_index = 2
    if player1_primary_position == "Defensive Midfielder" or player1_primary_position == "Central Midfielder":
        selectbox_index = 3
    if player1_primary_position == "Left Winger" or player1_primary_position == "Right Winger" or player1_primary_position == "Attacking Midfielder":
        selectbox_index = 4
    if player1_primary_position == "Striker":
        selectbox_index = 5

    radar_template = st.sidebar.selectbox("Radar Şablonu", ["Kaleci", "Stoper", "Sağ Bek - Sol Bek", 
                                                            "Merkez Orta Saha", "Kanat - Ofansif Orta Saha", 
                                                            "Santrafor"], index=selectbox_index, help="Seçilen ilk oyuncunun pozisyonuna göre radar şablonu otomatik olarak belirlense de istediğiniz radar şablonunu seçebilirsiniz.")

    if (radar_template == "Kaleci"):
        stat_titles = ["Saves", "Save percentage", "Goals prevented", "Clean sheets", "Penalty goals saves",
                    "Pass accuracy", "Accurate long balls", "Long ball accuracy"]

    if (radar_template == "Stoper"):
        stat_titles = ['Tackles won', 'Tackles won %', 'Duels won', 'Duels won %', 'Interceptions', 'Recoveries', 'Blocked scoring attempt',
                    'Accurate passes', 'Accurate long balls',  'Long ball accuracy']

    if (radar_template == "Sağ Bek - Sol Bek"):
        stat_titles = ['Tackles won', 'Duels won', 'Duels won %', 'Interceptions', 'Recoveries',
                    'Accurate passes', 'Chances created', 'Successful crosses', 'Cross accuracy',
                    'Dribbles', 'Touches in opposition box']
        
    if (radar_template == "Merkez Orta Saha"):
        stat_titles = ['Accurate passes', 'Pass accuracy', 'Accurate long balls', 'Long ball accuracy',
                    'Tackles won', 'Interceptions', 'Recoveries', 'Duels won', 'Aerials won', 'Possession won final 3rd',
                    'Touches', 'Dribbles']
        
    if (radar_template == "Kanat - Ofansif Orta Saha"):
        stat_titles = ['xG', 'Shots', 'Shots on target',
                    'xA', 'Chances created', 'Successful crosses',
                    'Duels won', 'Possession won final 3rd', 'Fouls won',
                    'Dribbles', 'Dribbles success rate']
        
    if (radar_template == "Santrafor"):
        stat_titles = ['xG', 'xGOT', 'Shots', 'Shots on target',
                    'xA', 'Chances created',
                    'Duels won', 'Duels won %', 'Aerials won', 'Aerials won %', 'Possession won final 3rd', 'Fouls won']

    player1_data = fetch_player_data(int(player1_id), player1_season_id)
    player2_data = fetch_player_data(int(player2_id), player2_season_id)

    player1_team_id = get_last_shot_team_id(player1_data)
    player2_team_id = get_last_shot_team_id(player2_data)

    if player1_team_id == 0 and player2_team_id != 0:
        player1_team = get_current_team_name(player1_id)
        player2_team = get_team_name(player2_team_id)

    elif player1_team_id != 0 and player2_team_id == 0:
        player1_team = get_team_name(player1_team_id)
        player2_team = get_current_team_name(player2_id)

    elif player1_team_id != 0 and player1_team_id != 0:
        player1_team = get_team_name(player1_team_id)
        player2_team = get_team_name(player2_team_id)

    elif player1_team_id == 0 and player1_team_id == 0:
        player1_team = get_current_team_name(player1_id)
        player2_team = get_current_team_name(player2_id)
    
    if (player1_data and player2_data is not None):

        player1_df = create_player_df(player1_data)
        player2_df = create_player_df(player2_data)
        
        if (len(player1_df) >= 15) and (len(player2_df) >= 15):

            player1_age = get_age(player1_id)
            player2_age = get_age(player2_id)

            player1_birthday = get_birthday(player1_id)
            player2_birthday = get_birthday(player2_id)

            player1_matches = get_matches_count(player1_data, 'Matches')
            player2_matches = get_matches_count(player2_data, 'Matches')

            player1_started_matches = get_started_matches_count(player1_data, 'Started')
            player2_started_matches = get_started_matches_count(player2_data, 'Started')
        
            # player1_df ve player2_df'in boş olup olmadığını kontrol et
            player1_bos_mu = player1_df.empty or isinstance(player1_df, pd.DataFrame) and player1_df.shape == (0, 0)
            player2_bos_mu = player2_df.empty or isinstance(player2_df, pd.DataFrame) and player2_df.shape == (0, 0)

            # Her iki DataFrame'in de dolu olup olmadığını kontrol et
            if not player1_bos_mu and not player2_bos_mu:
                df1_stat_values = extract_stat_values(player1_df, stat_titles)
                df2_stat_values = extract_stat_values(player2_df, stat_titles)
                df1_stat_values_percentage = extract_stat_values_percentage(player1_df, stat_titles)
                df2_stat_values_percentage = extract_stat_values_percentage(player2_df, stat_titles)
                
                player1_season_name, player1_league = fetch_player_season_and_league(player1_id, player1_season_id)
                player2_season_name, player2_league = fetch_player_season_and_league(player2_id, player2_season_id)

                def create_radar_chart(stat_titles, df1_values_percentage, df2_values_percentage,
                                    df1_stat_values, df2_stat_values,
                                    player1_name, player2_name, player1_id, player2_id, player1_team, player2_team):  
                    player1_color = "#3a879e"
                    player2_color = "#a32f2f"

                    player1_minute = get_minutes(player1_data, 'Minutes')
                    player2_minute = get_minutes(player2_data, 'Minutes')

                    player1_90s = 0.0
                    player2_90s = 0.0

                    if player1_primary_position == "Goalkeeper" or player1_primary_position == "Keeper" or player2_primary_position == "Goalkeeper" or player2_primary_position == "Keeper":
                        player1_minute = ""
                        player2_minute = ""
                        player1_90s = ""
                        player2_90s = ""

                        table_columns = ['Sezon', 'Lig', 'Takım', 'Pozisyon', 'Yaş', 'Doğum Tarihi', 'Toplam Maç', 'İlk 11']
                        table_player1_values = [player1_season_name, player1_league, player1_team, player1_primary_position_tr, player1_age, player1_birthday, player1_matches, player1_started_matches]
                        table_player2_values = [player2_season_name, player2_league, player2_team, player2_primary_position_tr, player2_age, player2_birthday, player2_matches, player2_started_matches]
                    
                    else:
                        player1_90s = round(float(player1_minute) / 90, 1)
                        player2_90s = round(float(player2_minute) / 90, 1)

                        table_columns = ['Sezon', 'Lig', 'Takım', 'Pozisyon', 'Yaş', 'Doğum Tarihi', 'Toplam Maç', 'İlk 11', 'Aldığı Dakika', '90s (Aldığı Dakika / 90)']
                        table_player1_values = [player1_season_name, player1_league, player1_team, player1_primary_position_tr, player1_age, player1_birthday, player1_matches, player1_started_matches, player1_minute, player1_90s]
                        table_player2_values = [player2_season_name, player2_league, player2_team, player2_primary_position_tr, player2_age, player2_birthday, player2_matches, player2_started_matches, player2_minute, player2_90s]
                    
                    ######### RADAR #########
                    
                    
                    num_vars = len(stat_titles)
                    stat_titles_tr = translate_stats(stat_titles, translation_dict)
                    
                    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
                    angles += angles[:1]
                    
                    df1_values_percentage += df1_values_percentage[:1]
                    df2_values_percentage += df2_values_percentage[:1]

                    # Grafiklerin oluşturulması
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), subplot_kw=dict(polar=True))

                    fig.patch.set_facecolor('#0e0e0e')
                    
                    # Eksen spines'i transparan yap
                    for spine in ax1.spines.values():
                        spine.set_visible(False)
                    
                    ax1.set_theta_offset(np.pi / 2)
                    ax1.set_theta_direction(-1)
                    
                    ax1.set_rscale('linear')
                    ax1.set_ylim(0, 100)
                    ax1.set_yticks([])
                    ax1.set_xticks([])
                    
                    for i, angle_rad in enumerate(angles[:-1]):
                        label_angle = -np.degrees(angle_rad)  # Etiketi döndürme açısı

                        # Eğer açı 90° ile 270° arasında ise, etiketi 180° döndür
                        if -270 < label_angle < -90:
                            label_angle -= 180

                        lines = stat_titles_tr[i].split()  # Kelimeleri böl
                        new_lines = []

                        for j in range(len(lines)):
                            new_lines.append(lines[j])
                            # Her iki kelimede bir satır atlat
                            if j % 2 == 1 and j != len(lines) - 1:
                                new_lines.append("\n")

                        label = " ".join(new_lines)  # Boşluklarla birleştir

                        ax1.text(angle_rad, 112, label, horizontalalignment='center', verticalalignment='center', 
                                size=9, fontproperties=prop, color='gray', rotation=label_angle, rotation_mode='anchor')

                        
                    # Dairesel grid çizgilerini ekle ve aralıklarla renk doldurma
                    grid_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                    fill_colors = ['#626262', '#0e0e0e']
                    for i, value in enumerate(grid_values[:-1]):
                        circle_angles = np.linspace(0, 2 * np.pi, 100)
                        circle_inner = np.array([value] * len(circle_angles))
                        circle_outer = np.array([grid_values[i+1]] * len(circle_angles))
                        ax1.fill_between(circle_angles, circle_inner, circle_outer, color=fill_colors[i % 2], alpha=0.15)
                        
                    # Grid çizgilerini ekle
                    for angle in angles[:-1]:
                        ax1.plot([angle, angle], [0, 100], color='gray', linestyle='-', linewidth=1, alpha=0.1)
                        
                    for i, (angle_rad, df1_value, df2_value) in enumerate(zip(angles[:-1], df1_stat_values, df2_stat_values)):
                        # Player 1 için metin kutusu
                        ax1.text(angle_rad, df1_values_percentage[i] + 5, f'{df1_value:.2f}', 
                                horizontalalignment='center', verticalalignment='center',
                                size=8, color=player1_color,
                                rotation=-angle_rad * 180 / np.pi)  # Saat yönünün tersi

                        # Player 2 için metin kutusu
                        ax1.text(angle_rad, df2_values_percentage[i] + 5, f'{df2_value:.2f}', 
                                horizontalalignment='center', verticalalignment='center',
                                size=8, color=player2_color,
                                rotation=-angle_rad * 180 / np.pi)  # Saat yönünün tersi

                    # Oyuncu 1
                    ax1.plot(angles, df1_values_percentage, color=player1_color, linewidth=0, linestyle='solid', label=player1_name)
                    ax1.fill(angles, df1_values_percentage, color=player1_color, alpha=0.6)
                    
                    # Oyuncu 2
                    ax1.plot(angles, df2_values_percentage, color=player2_color, linewidth=0, linestyle='solid', label=player2_name)
                    ax1.fill(angles, df2_values_percentage, color=player2_color, alpha=0.6)

                    # Radar grafiği arka plan rengini ayarlama
                    ax1.set_facecolor('#0e0e0e')
                    
                    def fetch_image(player_id):
                        url = f'https://images.fotmob.com/image_resources/playerimages/{player_id}.png'
                        try:
                            # Resmi indirin
                            response = urlopen(url)
                            # Resmi açın ve RGBA formatına dönüştürün
                            image = Image.open(response).convert('RGBA')
                            return image
                        except HTTPError as e:
                            # HTTPError (403 ve diğer hatalar) durumunda, hata mesajını yazdırın ve None döndürün
                            if e.code == 403:
                                print(f"403 hatası: {player_id} için fotoğraf bulunamadı.")
                            else:
                                print(f"HTTPError: {e}")
                            return None

                    # Player 1 ve Player 2 resimlerini indirin
                    player1_foto = fetch_image(player1_id)
                    player2_foto = fetch_image(player2_id)

                    # Resimlerin mevcut olup olmadığını kontrol edin
                    if player1_foto:
                        # player1_foto'yu kullan
                        imagebox1 = OffsetImage(player1_foto, zoom=0.35, interpolation='hanning')
                        ab1 = AnnotationBbox(imagebox1, (0.15, 1.32), frameon=False, xycoords='axes fraction')
                        ax1.add_artist(ab1)
                        pass
                    else:
                        # Player 1 için fotoğraf mevcut değil
                        pass

                    if player2_foto:
                        # player2_foto'yu kullan
                        imagebox2 = OffsetImage(player2_foto, zoom=0.35, interpolation='hanning')
                        ab2 = AnnotationBbox(imagebox2, (0.85, 1.32), frameon=False, xycoords='axes fraction')
                        ax1.add_artist(ab2)
                        pass
                    else:
                        # Player 2 için fotoğraf mevcut değil
                        pass
                    
                    # Oyuncu isimlerini ve ek bilgileri ax1'e ekleme
                    ax1.text(0.143, 1.15, player1_name, transform=ax1.transAxes, ha='center', va='bottom', fontsize=16, fontproperties=bold_prop, color=player1_color, fontweight='bold')
                    ax1.text(0.845, 1.15, player2_name, transform=ax1.transAxes, ha='center', va='bottom', fontsize=16, fontproperties=bold_prop, color=player2_color, fontweight='bold')
                    
                    
                    ######### TABLO #########


                    ax2.axis('off')  
                    player_names = np.array([player1_name, player2_name])
                    table_data = np.array([table_player1_values + df1_stat_values, table_player2_values + df2_stat_values]).T

                    # İsimler satırını tabloya ekleyelim
                    table_data = np.vstack((player_names, table_data))

                    rowLabels = ['@bariscanyeksin\nVeri: FotMob'] + table_columns + stat_titles_tr

                    table = ax2.table(cellText=table_data,
                                    rowLabels=rowLabels,
                                    cellLoc='center',
                                    loc='center')

                    # Sütun genişliklerini ayarlama
                    table.auto_set_column_width([0, 1])  # Otomatik genişliği ayarla
                    for key, cell in table.get_celld().items():
                        if key[1] == 0:  # İlk sütun (satır etiketleri)
                            cell.set_width(0.2)
                        else:  # Oyuncu sütunları
                            cell.set_width(0.15)

                    # Başlık hücrelerinin arka plan rengini gri yapma ve diğer stil ayarları
                    for key, cell in table.get_celld().items():
                        if key[0] == 0:  # İlk satır (başlıklar)
                            cell.set_edgecolor('#0e0e0e')
                            if key == (0, -1):
                                cell.set_facecolor('#0e0e0e')
                                cell.set_text_props(color=to_rgba('gray', alpha=0.5), fontproperties=prop)
                            if key == (0, 0):
                                cell.set_facecolor(to_rgba(player1_color, alpha=0.15))
                                cell.set_text_props(color='gray', fontproperties=bold_prop)
                                cell.set_edgecolor(to_rgba('gray', alpha=0.25))
                            if key == (0, 1):
                                cell.set_facecolor(to_rgba(player2_color, alpha=0.15))
                                cell.set_text_props(color='gray', fontproperties=bold_prop)
                                cell.set_edgecolor(to_rgba('gray', alpha=0.25))
                            cell.set_fontsize(8)
                            cell.set_height(cell.get_height() * 1.5)  # Yüksekliği 1.5 katına çıkar

                        else:
                            value1 = table_data[key[0]-1][0]
                            value2 = table_data[key[0]-1][1]
                            cell.set_fontsize(8)
                            cell.set_edgecolor(to_rgba('gray', alpha=0.25))
                            # Satırlar arası arka plan rengini değiştirme, çift satırlar
                            if (key[0] % 2 == 0) & (key[1] == -1):  # Çift satırlar
                                cell.set_facecolor(to_rgba('gray', alpha=0.1))
                                cell.set_text_props(color='gray', fontproperties=bold_prop, horizontalalignment='left')
                            elif (key[0] % 2 == 1) & (key[1] == -1):  # Çift satırlar
                                cell.set_facecolor('#0e0e0e')
                                cell.set_text_props(color='gray', fontproperties=bold_prop, horizontalalignment='left')
                            elif (key[0] % 2 == 0):  # Çift satırlar
                                cell.set_facecolor(to_rgba('gray', alpha=0.1))
                                cell.set_text_props(color='gray', fontproperties=prop, horizontalalignment='center')
                            elif (key[0] % 2 == 1):  # Çift satırlar
                                cell.set_facecolor('#0e0e0e')
                                cell.set_text_props(color='gray', fontproperties=prop, horizontalalignment='center')
                            else:
                                cell.set_facecolor('#0e0e0e')
                                cell.set_text_props(color='gray', fontproperties=prop)

                            row_key = 0
                            if player1_primary_position == "Goalkeeper" or player1_primary_position == "Keeper" or player2_primary_position == "Goalkeeper" or player2_primary_position == "Keeper":
                                row_key = 8
                            else:
                                row_key = 10

                            if key[0] > row_key:
                                try:
                                    value1 = float(table_data[key[0], 0])
                                    value2 = float(table_data[key[0], 1])

                                    if key[1] == 0 and value1 > value2:
                                        cell.set_facecolor(to_rgba(player1_color, alpha=0.15))
                                        cell.set_text_props(color='gray', fontproperties=prop)
                                    elif key[1] == 1 and value2 > value1:
                                        cell.set_facecolor(to_rgba(player2_color, alpha=0.15))
                                        cell.set_text_props(color='gray', fontproperties=prop)

                                except ValueError:
                                    pass

                    table.scale(1, 2)

                    ax2.axis('off')
                        
                    # Radar grafiği konumu ve boyutu (ax1)
                    ax1.set_position([0.15, 0.25, 0.3, 0.6])  # [left, bottom, width, height]

                    # Tablonun konumu ve genişliği (ax2)
                    ax2.set_position([0.5, 0.2, 0.45, 0.7])  # [left, bottom, width, height]

                    #fig = plt.gcf()
                    #fig.subplots_adjust(wspace=0.7)
                                            
                    plt.tight_layout()
                    #plt.savefig(player1_name + " - " + player2_name + ".png", dpi = 300, bbox_inches = "tight")
                    return plt

                plot = create_radar_chart(stat_titles, df1_stat_values_percentage, df2_stat_values_percentage, df1_stat_values, df2_stat_values,
                                player1_name, player2_name, player1_id, player2_id, player1_team, player2_team)
                
                st.pyplot(plot)
                
                st.markdown("""
                    <style>
                    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

                    html, body, [class*="cache"], [class*="st-"]  {
                        font-family: 'Poppins', sans-serif;
                    }
                    </style>
                    """, unsafe_allow_html=True
                )
                
                st.markdown(
                    """
                    <style>
                        /* Bilgisayarlar için */
                        @media (min-width: 1024px) {
                            .block-container {
                                width: 800px;
                                max-width: 800px;
                                padding-top: 50px;
                                padding-bottom: 0px;
                            }
                        }

                        /* Tabletler için (genellikle 768px - 1024px arası ekran genişliği) */
                        @media (min-width: 768px) and (max-width: 1023px) {
                            .block-container.st-emotion-cache-13ln4jf.ea3mdgi5 {
                                width: 700px;
                                max-width: 700px;
                            }
                        }

                        /* Telefonlar için (genellikle 768px ve altı ekran genişliği) */
                        @media (max-width: 767px) {
                            .block-container.st-emotion-cache-13ln4jf.ea3mdgi5 {
                                width: 100%;
                                max-width: 100%;
                                padding-left: 10px;
                                padding-right: 10px;
                            }
                        }
                        .row-widget.stDownloadButton {
                            display: flex;
                            justify-content: center;
                            text-align: center;
                        }
                        .row-widget.stDownloadButton button {
                            background-color: rgba(51, 51, 51, 0.17);
                            color: gray;  /* Text color */
                            border: 0.5px solid gray;  /* Thin gray border */
                            transition: background-color 0.5s ease;
                        }
                        .row-widget.stDownloadButton button:hover {
                            background-color: rgba(51, 51, 51, 0.65);
                            border: 1px solid gray;  /* Thin gray border */
                        }
                        .row-widget.stDownloadButton button:active {
                            background-color: rgba(51, 51, 51, 0.17);
                            color: gray;  /* Text color */
                            border: 0.5px solid gray;  /* Thin gray border */
                            transition: background-color 0.5s ease;
                        }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                
                buf = io.BytesIO()
                plot.savefig(buf, format="png", dpi = 300, bbox_inches = "tight")
                buf.seek(0)
                player1_name_clean = player1_name.replace(" ", "-")
                player1_league_clean = player1_league.replace(" ", "-")
                player2_name_clean = player2_name.replace(" ", "-")
                player2_league_clean = player2_league.replace(" ", "-")
                
                st.download_button(
                    label="Grafiği İndir",
                    data=buf,
                    file_name=f"{player1_name_clean}-{player1_season_name}-{player1_league_clean}-vs-{player2_name_clean}-{player2_season_name}-{player2_league_clean}.png",
                    mime="image/png"
                )
                
                # Daha fazla boşluk bırakmak için ek boşluk ekleyin
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Bilgilendirme metinlerini div içinde ortalanmış olarak ayarlama
                st.markdown(
                    """
                    <div style='text-align: center; max-width:550px; margin: 0 auto; cursor:default'>
                        <p style='font-size:12px; color:gray;'>
                            Bu radar grafiği, iki oyuncunun belirli istatistiklerini karşılaştırmak için kullanılır.
                            Her eksen bir istatistiği temsil eder ve oyuncuların bu istatistiklerdeki performansını gösterir.
                            Radarda oyuncuların kapladıkları alan, yüzdelik dilime göre her istatistikte oyuncunun sıralamasına göre çizilir.
                        </p>
                        <p style='font-size:12px; color:gray;'>
                            Oyuncular yalnızca mevcut seçili olan ligdeki/turnuvadaki aynı pozisyonda oynayan oyuncularla karşılaştırılır.
                            Bu sebeple farklı ligdeki/turnuvadaki veya farklı pozisyondaki oyuncuları karşılaştırırken bazı absürtlükler olabilir.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.write("Bir veya her iki oyuncunun verisi bulunamadı.")        
    else:
        st.write("Bir veya her iki oyuncunun verisi bulunamadı.")
#else:
        #st.write("Bir veya her iki oyuncunun verisi bulunamadı.")

# Function to convert image to base64
def img_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Signature section
st.sidebar.markdown("---")  # Add a horizontal line to separate your signature from the content

# Load and encode icons
twitter_icon_base64 = img_to_base64("icons/twitter.png")
github_icon_base64 = img_to_base64("icons/github.png")
twitter_icon_white_base64 = img_to_base64("icons/twitter_white.png")  # White version of Twitter icon
github_icon_white_base64 = img_to_base64("icons/github_white.png")  # White version of GitHub icon

# Display the icons with links at the bottom of the sidebar
st.sidebar.markdown(
    f"""
    <style>
    .sidebar {{
        width: auto;
    }}
    .sidebar-content {{
        display: flex;
        flex-direction: column;
        height: 100%;
        margin-top: 10px;
    }}
    .icon-container {{
        display: flex;
        justify-content: center;
        margin-top: auto;
        padding-bottom: 20px;
        gap: 30px;  /* Space between icons */
    }}
    .icon-container img {{
        transition: filter 0.5s cubic-bezier(0.4, 0, 0.2, 1);  /* Smooth and natural easing */
    }}
    .icon-container a:hover img {{
        filter: brightness(0) invert(1);  /* Inverts color to white */
    }}
    </style>
    <div class="sidebar-content">
        <!-- Other sidebar content like selectbox goes here -->
        <div class="icon-container">
            <a href="https://x.com/bariscanyeksin" target="_blank">
                <img src="data:image/png;base64,{twitter_icon_base64}" alt="Twitter" width="30">
            </a>
            <a href="https://github.com/bariscanyeksin" target="_blank">
                <img src="data:image/png;base64,{github_icon_base64}" alt="GitHub" width="30">
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
