import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="Monitor de Clima",
    page_icon="🌤️",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Fundo geral com gradiente suave */
    .stApp {
        background: linear-gradient(180deg, #eef5ff 0%, #f7fbff 35%, #ffffff 100%);
    }

        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    
    /* Título principal */
    h1 {
        font-weight: 800 !important;
        background: linear-gradient(90deg, #2c5282, #00a8e8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Subtítulos com pequena borda esquerda colorida */
    h2, h3 {
        font-size: 50px !important;
        text-align: center;
        color: #1e3a5f !important;
        border-left: 5px solid #4facfe;
        border-right: 5px solid #4facfe;
        padding-left: 12px;
        margin-top: 1.2rem !important;
    }

    /* Cartões de métricas */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border-radius: 14px;
        padding: 16px 12px;
        box-shadow: 0 2px 10px rgba(30, 58, 95, 0.08);
        border: 1px solid #e3edf7;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(30, 58, 95, 0.15);
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #4a5568 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #1e3a5f !important;
        font-weight: 700;
    }

    /* Linha divisória mais sutil */
    hr {
        border-color: #d9e6f5 !important;
    }

    /* Tabela de previsão */
    [data-testid="stTable"] table {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(30, 58, 95, 0.08);
    }
    [data-testid="stTable"] th,
    [data-testid="stTable"] td {
        color: #1a1a1a !important;
    }
    [data-testid="stTable"] tbody tr:hover td {
        background-color: #e3edf7 !important;
    }

    /* Caption (última atualização, localização) */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #6b7a8f !important;
    }

    /* Mensagens de erro/aviso com cantos arredondados */
    div[data-testid="stAlert"] {
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: ("Céu limpo", "☀️"),
    1: ("Principalmente limpo", "🌤️"),
    2: ("Parcialmente nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Neblina", "🌫️"),
    48: ("Neblina com geada", "🌫️"),
    51: ("Chuvisco leve", "🌦️"),
    53: ("Chuvisco moderado", "🌦️"),
    55: ("Chuvisco intenso", "🌧️"),
    61: ("Chuva leve", "🌧️"),
    63: ("Chuva moderada", "🌧️"),
    65: ("Chuva forte", "🌧️"),
    71: ("Neve leve", "🌨️"),
    73: ("Neve moderada", "🌨️"),
    75: ("Neve forte", "❄️"),
    80: ("Aguaceiros leves", "🌦️"),
    81: ("Aguaceiros moderados", "🌧️"),
    82: ("Aguaceiros violentos", "⛈️"),
    95: ("Trovoada", "⛈️"),
    96: ("Trovoada com granizo leve", "⛈️"),
    99: ("Trovoada com granizo forte", "⛈️"),
}


def descrever_clima(codigo: int):
    return WEATHER_CODES.get(codigo, ("Condição desconhecida", "❔"))


@st.cache_data(show_spinner=False, ttl=3600)
def buscar_cidades(nome: str):
    params = {"name": nome, "count": 5, "language": "pt", "format": "json"}
    resp = requests.get(GEOCODING_URL, params=params, timeout=10)
    resp.raise_for_status()
    dados = resp.json()
    return dados.get("results", [])


@st.cache_data(show_spinner=False, ttl=600)
def buscar_previsao(lat: float, lon: float, dias: int, unidade_temp: str):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,apparent_temperature",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        "forecast_days": dias,
        "timezone": "auto",
        "temperature_unit": "celsius" if unidade_temp == "Celsius (°C)" else "fahrenheit",
    }
    resp = requests.get(FORECAST_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def card_metrica(col, titulo, valor, ajuda=""):
    col.metric(titulo, valor, help=ajuda)


st.header("Previsão do tempo com OpenWeatherMap")

col1, col2 = st.columns(2)
flex_box1 = st.container(vertical_alignment="center",horizontal_alignment="distribute")
unidade_temp = "Celsius (°C)"

with col1:
    st.title("🌤️ Monitor de Clima")
    st.write("Consulte o clima atual e a previsão para qualquer cidade do mundo, em tempo real.")

with col2:
    cidade_input = st.text_input("Informe a cidade voce deseja saber a previsão", value="Londrina")
    dias_previsao = st.slider("Dias de previsão futura", min_value=1, max_value=14, value=7)

buscar = st.button("🔍 Buscar clima", type="primary", use_container_width=True)


if "cidade_selecionada" not in st.session_state:
    st.session_state.cidade_selecionada = None

if buscar or cidade_input:
    if not cidade_input.strip():
        st.warning("Digite o nome de uma cidade na barra lateral.")
        st.stop()

    with st.spinner("Buscando cidade..."):
        try:
            resultados = buscar_cidades(cidade_input.strip())
        except requests.RequestException as e:
            st.error(f"Erro ao consultar a API de geocoding: {e}")
            st.stop()

    if not resultados:
        st.error("Nenhuma cidade encontrada com esse nome. Tente outro termo de busca.")
        st.stop()

    opcoes = [
        f"{r['name']}, {r.get('admin1', '')}, {r['country']}".replace(", ,", ",")
        for r in resultados
    ]
    if len(resultados) > 1:
        escolha = st.selectbox("Foram encontradas várias cidades. Selecione a correta:", opcoes)
        cidade_escolhida = resultados[opcoes.index(escolha)]
    else:
        cidade_escolhida = resultados[0]
        st.caption(f"📍 {opcoes[0]}")

    lat = cidade_escolhida["latitude"]
    lon = cidade_escolhida["longitude"]

    with st.spinner("Buscando dados meteorológicos..."):
        try:
            dados = buscar_previsao(lat, lon, dias_previsao, unidade_temp)
        except requests.RequestException as e:
            st.error(f"Erro ao consultar a API de previsão: {e}")
            st.stop()

    simbolo_temp = "°C" if unidade_temp == "Celsius (°C)" else "°F"

    atual = dados.get("current", {})
    codigo_atual = atual.get("weather_code", 0)
    descricao, emoji = descrever_clima(codigo_atual)

    st.subheader(f"{emoji} Agora em {cidade_escolhida['name']}, {cidade_escolhida['country']}")
    st.caption(descricao)

    col1, col2, col3, col4 = st.columns(4)
    temp_atual = atual.get("temperature_2m")
    sensacao_atual = atual.get("apparent_temperature")
    temp_atual_fmt = f"{temp_atual:.1f}" if isinstance(temp_atual, (int, float)) else "--"
    sensacao_atual_fmt = f"{sensacao_atual:.1f}" if isinstance(sensacao_atual, (int, float)) else "--"
    card_metrica(col1, "Temperatura", f"{temp_atual_fmt}{simbolo_temp}")
    card_metrica(col2, "Sensação térmica", f"{sensacao_atual_fmt}{simbolo_temp}")
    card_metrica(col3, "Umidade", f"{atual.get('relative_humidity_2m', '--')}%")
    card_metrica(col4, "Vento", f"{atual.get('wind_speed_10m', '--')} km/h")

    st.markdown("---")

    st.subheader(f"📅 Previsão para os próximos {dias_previsao} dia(s)")

    diario = dados.get("daily", {})
    datas_iso = diario.get("time", [])
    minimas = diario.get("temperature_2m_min", [])
    maximas = diario.get("temperature_2m_max", [])
    chances_chuva = diario.get("precipitation_probability_max", [])
    codigos_clima = diario.get("weather_code", [])

    previsao = []
    for i in range(len(datas_iso)):
        data_formatada = datetime.fromisoformat(datas_iso[i]).strftime("%d/%m")
        descricao_dia, emoji_dia = descrever_clima(codigos_clima[i])
        minima_fmt = f"{minimas[i]:.1f}" if isinstance(minimas[i], (int, float)) else minimas[i]
        maxima_fmt = f"{maximas[i]:.1f}" if isinstance(maximas[i], (int, float)) else maximas[i]
        previsao.append({
            "data": data_formatada,
            "minima": minima_fmt,
            "maxima": maxima_fmt,
            "chuva": chances_chuva[i],
            "condicao": f"{emoji_dia} {descricao_dia}",
        })

    tabela = [
        {
            "Data": dia["data"],
            "Condição": dia["condicao"],
            "Mínima": dia["minima"],
            "Máxima": dia["maxima"],
            "Chance de chuva (%)": dia["chuva"],
        }
        for dia in previsao
    ]
    st.table(tabela)

    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
