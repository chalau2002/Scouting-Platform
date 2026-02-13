import streamlit as st
import json
import os
from utils.functions import carregar_config, guardar_config, carregar_grupos_csv

st.title("🔔 Configurar Notificações")

# Garantir que temos a variável no session_state
if "grupos_scouting" not in st.session_state:
    st.session_state.grupos_scouting = carregar_grupos_csv()


# Carregar sempre a versão mais recente do ficheiro
config_carregada = carregar_config()

if config_carregada:
    st.session_state.config_monitorizacao = config_carregada
else:
    st.session_state.config_monitorizacao = {
        "frequencia": 1,
        "email": "",
        "grupos": [],
    }


config = st.session_state.config_monitorizacao

st.subheader("⏱ Frequência de verificação dos dados")
freq_valor = st.number_input(
    f"De quantos em quantos meses pretende atualizar os dados?",
    min_value=1,
    step=1,
    max_value=12,
    value=int(config["frequencia"]),
)

st.subheader("📧 Notificações por email")
email = st.text_input(
    "Para que email deseja receber as notificações?",
    value=config["email"],
    placeholder="email@dominio.com",
)
nomes_grupos = [g["nome"] for g in st.session_state.grupos_scouting]

st.subheader("📝 Grupos de scouting para notificação")
grupos_escolhidos = st.multiselect(
    "Escolha os grupos de scouting que quer monitorizar:",
    nomes_grupos,
    default=config["grupos"],
)

## Atualizar no session_state e guardar em ficheiro
nova_config = {
    "frequencia": freq_valor,
    "email": email,
    "grupos": grupos_escolhidos,
}
st.session_state.config_monitorizacao = nova_config
guardar_config(nova_config)
