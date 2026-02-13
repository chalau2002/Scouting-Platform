import streamlit as st
from datetime import date
import os
import pandas as pd
from utils.functions import (
    carregar_grupos_csv,
    guardar_grupos_csv,
    carregar_indices_csv,
)


st.title("🔍 Criar Novo Grupo de Scouting")
st.markdown(
    "Defina os critérios e selecione um índice para gerar o seu grupo personalizado de jogadores."
)

# Inicializar estado para guardar grupos
if "grupos_scouting" not in st.session_state:
    st.session_state.grupos_scouting = carregar_grupos_csv()

if "indices_performance" not in st.session_state:
    st.session_state.indices_performance = carregar_indices_csv()

# --- Filtros ---
st.subheader("🎯 Filtros de Pesquisa")

col1, col2 = st.columns(2)

with col1:
    idade_min = st.number_input("Idade mínima", 15, 40, 18)
    idade_max = st.number_input("Idade máxima", 15, 40, 30)
    altura_min = st.number_input("Altura mínima (cm)", 150, 220, 170)

with col2:

    pasta_leagues = "data/leagues"

    # Obter os nomes dos ficheiros .csv e remover a extensão
    opcoes_campeonatos = [
        os.path.splitext(f)[0] for f in os.listdir(pasta_leagues) if f.endswith(".csv")
    ]

    campeonato = st.multiselect(
        "Campeonato",
        opcoes_campeonatos,
        default=[],
    )

    # Carregar o ficheiro da Liga Portugal
    df = pd.read_csv("data/leagues/liga_portugal.csv")

    # Filtrar posições únicas que não têm vírgulas
    opcoes_posicoes = sorted(df["Pos_x"].dropna().unique())
    opcoes_posicoes = [pos for pos in opcoes_posicoes if "," not in pos]

    # Multiselect baseado nessas posições
    posicoes = st.multiselect("Posição", opcoes_posicoes, default=[])
    pe_preferido = st.selectbox(
        "Pé preferencial", ["Indiferente", "Esquerdo", "Direito"]
    )

# --- Filtros Avançados ---
with st.expander("⚙️ Filtros Avançados"):
    col3, col4 = st.columns(2)

    with col3:
        valor_max = st.number_input(
            "Valor de mercado máximo (€M)", min_value=0, max_value=200, value=20
        )

    with col4:
        minutos_min = st.slider("Minutos jogados mínimos", 0, 4000, 900)

# --- Seleção de índice ---
st.subheader("📊 Índice de Performance")

# Garantir que os índices foram carregados
if (
    "indices_performance" not in st.session_state
    or not st.session_state.indices_performance
):
    st.warning(
        "❗ Ainda não existem índices de performance definidos. Cria um primeiro em 'Índices de Performance'."
    )
    indice_escolhido = None
else:
    nomes_indices = [indice["nome"] for indice in st.session_state.indices_performance]
    indice_escolhido = st.selectbox(
        "Escolha o índice de performance a utilizar",
        nomes_indices,
    )

# --- Nome do grupo ---
st.subheader("📝 Nome do Grupo")
nome_grupo = st.text_input("Insira o nome do grupo de scouting")

# --- Criar grupo ---
criar = st.button("✅ Criar Grupo")

if criar:
    if not nome_grupo.strip():
        st.error("❌ Por favor, insere um nome para o grupo de scouting.")
    elif any(
        grupo["nome"].lower() == nome_grupo.strip().lower()
        for grupo in st.session_state.grupos_scouting
    ):
        st.error(
            f"❌ Já existe um grupo chamado '{nome_grupo.strip()}'. Escolhe um nome diferente."
        )
    elif not indice_escolhido:
        st.error("❌ Tens de escolher um índice de performance válido.")
    elif not campeonato:
        st.error("❌ Tens de selecionar pelo menos um campeonato.")
    else:
        # Criar dicionário de filtros
        filtros = {
            "idade_min": idade_min,
            "idade_max": idade_max,
            "altura_min": altura_min,
            "pe": pe_preferido,
            "campeonatos": campeonato,
            "posicoes": posicoes,
            "valor_max": valor_max,
            "minutos_min": minutos_min,
        }

        # Buscar o índice completo
        indice = next(
            (
                i
                for i in st.session_state.indices_performance
                if i["nome"] == indice_escolhido
            ),
            None,
        )

        if indice:

            # Guardar grupo
            grupo = filtros.copy()
            grupo["nome"] = nome_grupo.strip()
            grupo["indice"] = indice_escolhido
            st.session_state.grupos_scouting.append(grupo)
            guardar_grupos_csv(st.session_state.grupos_scouting)

            st.success(f"Grupo '{grupo['nome']}' criado com sucesso!")
        else:
            st.error("❌ Índice selecionado não encontrado.")
