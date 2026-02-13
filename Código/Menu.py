import streamlit as st
import os
import json
from utils.functions import carregar_indices_csv, carregar_grupos_csv,enviar_email, calcular_score
from data.scrapping import process_league, tm_main, soccerdonna_main
import datetime

FICHEIRO_INDICES = os.path.join(os.getcwd(), "data", "indices", "indices_performance.csv")

# Criar diretório se não existir
os.makedirs(os.path.dirname(FICHEIRO_INDICES), exist_ok=True)

st.set_page_config(page_title="Plataforma de Scouting", page_icon="⚽", layout="wide")

# Liga Portuguesa
sections_portugal = {
    "standard": {
        "url": "https://fbref.com/en/comps/32/2024-2025/stats/2024-2025-Primeira-Liga-Stats",
        "id": "stats_standard",
    },
    "shooting": {
        "url": "https://fbref.com/en/comps/32/2024-2025/shooting/2024-2025-Primeira-Liga-Stats",
        "id": "stats_shooting",
    },
    "passing": {
        "url": "https://fbref.com/en/comps/32/2024-2025/passing/2024-2025-Primeira-Liga-Stats",
        "id": "stats_passing",
    },
    "defense": {
        "url": "https://fbref.com/en/comps/32/2024-2025/defense/2024-2025-Primeira-Liga-Stats",
        "id": "stats_defense",
    },
    "goalkeeping": {
        "url": "https://fbref.com/en/comps/32/2024-2025/keepersadv/2024-2025-Primeira-Liga-Stats",
        "id": "stats_keeper_adv",
    },
}

# Liga Espanhola
sections_espanhola = {
    "standard": {
        "url": "https://fbref.com/en/comps/12/2024-2025/stats/2024-2025-La-Liga-Stats",
        "id": "stats_standard",
    },
    "shooting": {
        "url": "https://fbref.com/en/comps/12/2024-2025/shooting/2024-2025-La-Liga-Stats",
        "id": "stats_shooting",
    },
    "passing": {
        "url": "https://fbref.com/en/comps/12/2024-2025/passing/2024-2025-La-Liga-Stats",
        "id": "stats_passing",
    },
    "defense": {
        "url": "https://fbref.com/en/comps/12/2024-2025/defense/2024-2025-La-Liga-Stats",
        "id": "stats_defense",
    },
    "goalkeeping": {
        "url": "https://fbref.com/en/comps/12/2024-2025/keepersadv/2024-2025-La-Liga-Stats",
        "id": "stats_keeper_adv",
    },
}

# Liga Espanhola Feminina
sections_espanhola_fem = {
    "standard": {
        "url": "https://fbref.com/en/comps/230/2024-2025/stats/2024-2025-Liga-F-Stats",
        "id": "stats_standard",
    },
    "shooting": {
        "url": "https://fbref.com/en/comps/230/2024-2025/shooting/2024-2025-Liga-F-Stats",
        "id": "stats_shooting",
    },
    "passing": {
        "url": "https://fbref.com/en/comps/230/2024-2025/passing/2024-2025-Liga-F-Stats",
        "id": "stats_passing",
    },
    "defense": {
        "url": "https://fbref.com/en/comps/230/2024-2025/defense/2024-2025-Liga-F-Stats",
        "id": "stats_defense",
    },
    "goalkeeping": {
        "url": "https://fbref.com/en/comps/230/2024-2025/keepersadv/2024-2025-Liga-F-Stats",
        "id": "stats_keeper_adv",
    },
}

# Premier League Feminina
sections_premier_fem = {
    "standard": {
        "url": "https://fbref.com/en/comps/189/2024-2025/stats/2024-2025-Womens-Super-League-Stats",
        "id": "stats_standard",
    },
    "shooting": {
        "url": "https://fbref.com/en/comps/189/2024-2025/shooting/2024-2025-Womens-Super-League-Stats",
        "id": "stats_shooting",
    },
    "passing": {
        "url": "https://fbref.com/en/comps/189/2024-2025/passing/2024-2025-Womens-Super-League-Stats",
        "id": "stats_passing",
    },
    "defense": {
        "url": "https://fbref.com/en/comps/189/2024-2025/defense/2024-2025-Womens-Super-League-Stats",
        "id": "stats_defense",
    },
    "goalkeeping": {
        "url": "https://fbref.com/en/comps/189/2024-2025/keepersadv/2024-2025-Womens-Super-League-Stats",
        "id": "stats_keeper_adv",
    },
}

ligas = [
    ("Liga Portugal", sections_portugal, "data/leagues/liga_portugal.csv"),
    ("Liga Espanhola", sections_espanhola, "data/leagues/liga_espanhola.csv"),
    (
        "Liga Espanhola Feminina",
        sections_espanhola_fem,
        "data/leagues/liga_espanhola_feminina.csv",
    ),
    (
        "Premier League Feminina",
        sections_premier_fem,
        "data/leagues/premier_feminina.csv",
    ),
]

# Inicializar estado para guardar grupos
if "grupos_scouting" not in st.session_state:
    st.session_state.grupos_scouting = carregar_grupos_csv()

if "indices_performance" not in st.session_state:
    st.session_state.indices_performance = carregar_indices_csv()

CONFIG_PATH = "data/config_monitorizacao.json"
status_path = "data/email_status.json"
hoje = datetime.date.today()

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

notifications_months = config["frequencia"]

for i, (nome, sections, path) in enumerate(ligas):

    process_league(nome, sections, path, notifications_months)

tm_main(notifications_months)

soccerdonna_main(notifications_months)

if st.session_state.get("grupos_scouting") is not None:

    for grupo in st.session_state.grupos_scouting:

        top10 = calcular_score(
                    grupo["idade_min"],
                    grupo["idade_max"],
                    grupo["altura_min"],
                    grupo["valor_max"],
                    grupo["minutos_min"],
                    grupo["pe"],
                    grupo["campeonatos"],
                    grupo["posicoes"],
                    grupo["indice"],
                )
        
        top10['Idade'] = top10['Idade'].astype(int)

        # guardar resultados csv
        output_path = f"score/top10_{grupo['nome']}.csv"
        top10.to_csv(output_path, index=False)

# ------------------------
# NOVA LÓGICA DO EMAIL
# ------------------------
config_path = "data/config_monitorizacao.json"
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    destinatario = config.get("email")
    grupos = config.get("grupos", [])
    frequencia = config.get("frequencia", 1)

    # Ler status do último envio
    ultima_execucao = None
    if os.path.exists(status_path):
        with open(status_path, "r") as f:
            status = json.load(f)
            ultima_execucao_str = status.get("ultima_execucao")
            if ultima_execucao_str:
                ultima_execucao = datetime.datetime.strptime(ultima_execucao_str, "%Y-%m-%d").date()

    # Verificar se deve enviar
    enviar = False
    if not ultima_execucao:
        enviar = True
    else:
        diferenca_meses = (hoje.year - ultima_execucao.year) * 12 + (hoje.month - ultima_execucao.month)
        if diferenca_meses >= frequencia:
            enviar = True

    if enviar and destinatario:
        enviar_email(
            destinatario=destinatario,
            grupos=grupos,
        )
        # Atualizar status
        status = {"ultima_execucao": hoje.strftime("%Y-%m-%d")}
        with open(status_path, "w") as f:
            json.dump(status, f, indent=4)

        #st.success("📧 Email enviado com sucesso com base nas suas preferências.")
    else:
        print("Ainda não passou o período definido para novo envio de email.")
        #st.info("⏳ Ainda não passou o período definido para novo envio de email.")

if "indices_performance" not in st.session_state:
    st.session_state.indices_performance = carregar_indices_csv()


st.title("⚽ Plataforma de Scouting")
st.markdown(
    """
Bem-vindo à **Plataforma de Scouting**.

Esta aplicação foi desenvolvida para ajudar clubes e analistas a:

- 🔍 Criar **índices personalizados de performance** com base em métricas como xG, xA, passes-chave, entre outros.
- 🎯 Identificar jogadores com **perfil ajustado ao clube** através de filtros como idade, liga, altura, posição ou pé preferencial.
- 📂 Organizar esses jogadores em **grupos de scouting personalizados**, com rankings definidos pelo utilizador.
- 📊 Aceder à área de **índices de performance**, onde é possível configurar e guardar diferentes modelos de avaliação.
- 📈 Visualizar gráficos interativos para facilitar a análise comparativa de jogadores.
- 💎 Detetar as **melhores oportunidades de mercado**, destacando os jogadores que melhor se enquadram nas necessidades do clube.
- 🔔 **Configurar notificações** periódicas para cada grupo de scout.


Use o menu lateral para começar 👈
"""
)
