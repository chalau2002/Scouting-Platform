import streamlit as st
import json
import os
from utils.functions import (
    carregar_grupos_csv,
    guardar_grupos_csv,
    remover_grupo_da_config,
    calcular_score,
    grafico_radar
)

# --- Título e Secção ---
st.subheader("📂 Grupos de Scouting Criados")

# --- Inicializar Estado ---
if "grupos_scouting" not in st.session_state:
    st.session_state.grupos_scouting = carregar_grupos_csv()

grupos = st.session_state.grupos_scouting

# --- Mostrar Grupos ---
if grupos:
    for i, grupo in enumerate(grupos):
        with st.expander(f"🔹 {grupo['nome']} — {grupo['indice']}"):

            # --- Mostrar dados em duas colunas ---
            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.markdown(f"• **Idade:** {grupo['idade_min']} - {grupo['idade_max']}")
                st.markdown(f"• **Altura mínima:** {grupo['altura_min']} cm")
                st.markdown(f"• **Pé preferido:** {grupo['pe']}")

            with col_dir:
                st.markdown(f"• **Valor máximo:** {grupo['valor_max']} M€")
                st.markdown(f"• **Minutos mínimos:** {grupo['minutos_min']}")

            # --- Botões de Ação ---
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Ver Resultados", key=f"ver_{i}"):
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
                
                    st.session_state[f"res_{i}"] = top10


            with col2:
                if st.button(f"Apagar Grupo", key=f"apagar_{i}"):
                    nome_a_apagar = grupo["nome"]
                    grupos.pop(i)
                    guardar_grupos_csv(grupos)
                    remover_grupo_da_config(nome_a_apagar)
                    st.rerun()
                    

            top10 = st.session_state.get(f"res_{i}")
            if top10 is not None:

                st.subheader("Resultados")
                styler = top10.style.apply(
                    lambda s: ["background-color:#0b5d1e;color:white;font-weight:700" if v == s.max() else "" for v in s],
                    subset=["Score"]
                )

                styler = styler.apply(
                    lambda s: ["background-color:#0b5d1e;color:white;font-weight:700" if v == s.min() else "" for v in s],
                    subset=["Valor de Mercado (€)"]
                )

                styler = styler.apply(
                    lambda s: ["background-color:#0b5d1e;color:white;font-weight:700" if v == s.min() else "" for v in s],
                    subset=["Idade"]
                )

                st.dataframe(styler, use_container_width=True, hide_index=True)  
                
                opts = top10["Jogador"].tolist()
                prefix = f"{grupo['nome']}_{i}".replace(" ", "_")  # chave estável por grupo

                idx1 = 0 if len(opts) > 0 else None
                idx2 = 1 if len(opts) > 1 else 0
                idx3 = 2 if len(opts) > 2 else (1 if len(opts) > 1 else 0)

                jogador1 = st.selectbox(
                    "Escolher Jogador 1", options=opts, index=idx1, key=f"{prefix}_jogador1"
                )
                jogador2 = st.selectbox(
                    "Escolher Jogador 2", options=opts, index=idx2, key=f"{prefix}_jogador2"
                )
                jogador3 = st.selectbox(
                    "Escolher Jogador 3", options=opts, index=idx3, key=f"{prefix}_jogador3"
                )
                
                grafico_radar(
                    df=top10,
                    jogador1=jogador1,
                    jogador2=jogador2,
                    jogador3=jogador3
                )

else:
    st.info("Ainda não foi criado nenhum grupo de scouting.")
