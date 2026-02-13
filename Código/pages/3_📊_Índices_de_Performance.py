import streamlit as st
import pandas as pd
from utils.functions import carregar_indices_csv, guardar_indices_csv, carregar_grupos_csv

metricas_disponiveis = [
    "xG_total",
    "xAG_total",
    "Shots_total",
    "Shots_on_target",
    "Goals_per_shot",
    "Passes_completed",
    "Progressive_passes",
    "Key_passes",
    "Tackles_total",
    "Interceptions",
    "Blocks",
    "GA",
    "PKA",
    "FK",
    "CK",
    "OG",
    "PSxG",
    "PSxG/SoT",
    "PSxG+/-",
    "Launched_Cmp",
    "Launched_Att",
    "Launched_Cmp%",
    "Passes_Att (GK)",
    "Passes_Thr",
    "Passes_Launch%",
    "Passes_AvgLen",
    "Goal_Kicks_Att",
    "Goal_Kicks_Launch%",
    "Goal_Kicks_AvgLen",
    "Crosses_Opp",
    "Crosses_Stp",
    "Crosses_Stp%",
    "Sweeper_#OPA",
    "Sweeper_#OPA/90",
    "Sweeper_AvgDist",
]

# Inicializar estado
if "indices_performance" not in st.session_state:
    st.session_state.indices_performance = carregar_indices_csv()

if "grupos_scouting" not in st.session_state:
    st.session_state.grupos_scouting = carregar_grupos_csv()

if "modo_edicao" not in st.session_state:
    st.session_state.modo_edicao = None  # índice a editar

if "edit_temp" not in st.session_state:
    st.session_state.edit_temp = {}

st.title("📊 Índices de Performance Personalizados")

# --- Carregar dados se estiver em modo edição ---
nome_editar = ""
metricas_editar = []
pesos_editar = {}

if st.session_state.modo_edicao is not None:
    indice = st.session_state.indices_performance[st.session_state.modo_edicao]
    nome_editar = indice["nome"]
    metricas_editar = list(indice["metricas"].keys())
    pesos_editar = indice["metricas"]

nome_indice = st.text_input(
    "Nome do Índice",
    value=nome_editar if st.session_state.modo_edicao is not None else "",
    key="nome_input",
)

metricas_selecionadas = st.multiselect(
    "Seleciona as métricas para o índice",
    options=metricas_disponiveis,
    default=metricas_editar if st.session_state.modo_edicao is not None else [],
    key="metricas_select",
)

pesos = {}
soma_pesos = 0.0

if metricas_selecionadas:
    st.markdown("### Atribui um peso (entre 0 e 1) a cada métrica")
    for metrica in metricas_selecionadas:
        valor_inicial = pesos_editar[metrica] if metrica in pesos_editar else round(float(pesos_editar.get(metrica, 0.10)), 2)
        peso = st.number_input(
            f"Peso para {metrica}",
            min_value=0.00,
            max_value=1.00,
            step=0.01,
            format="%.2f",
            value=valor_inicial,
            key=f"peso_{metrica}",
        )
        pesos[metrica] = round(float(peso), 2)
        soma_pesos += pesos[metrica]

# --- Verificação e ação ---
if metricas_selecionadas:
    st.markdown(f"**Soma dos pesos:** `{round(soma_pesos, 3)}`")

    nomes_existentes = [
        idx["nome"].strip().lower() for idx in st.session_state.indices_performance
    ]

    nome_duplicado = nome_indice.strip().lower() in nomes_existentes and (
        st.session_state.modo_edicao is None
        or st.session_state.indices_performance[st.session_state.modo_edicao]["nome"]
        .strip()
        .lower()
        != nome_indice.strip().lower()
    )

    if len(metricas_selecionadas) < 3:
        st.warning("Deve selecionar pelo menos 3 métricas para criar o índice.")
    elif nome_duplicado:
        st.error("❌ Já existe um índice com esse nome. Escolhe um nome diferente.")
    elif soma_pesos != 1.0:
        st.warning("A soma dos pesos deve ser exatamente 1.0.")
    else:
        if st.session_state.modo_edicao is not None:
            if st.button("💾 Guardar Alterações"):
                st.session_state.indices_performance[st.session_state.modo_edicao] = {
                    "nome": nome_indice,
                    "metricas": pesos,
                }
                guardar_indices_csv(st.session_state.indices_performance)
                st.success(f"Índice '{nome_indice}' atualizado com sucesso.")

                st.session_state.modo_edicao = None
                st.rerun()
        else:
            if st.button("➕ Criar Índice"):
                st.session_state.indices_performance.append(
                    {"nome": nome_indice, "metricas": pesos}
                )
                guardar_indices_csv(st.session_state.indices_performance)
                st.success(f"Índice '{nome_indice}' criado com sucesso.")
                st.rerun()


# --- Lista de índices existentes ---
st.subheader("📄 Índices Criados")

if st.session_state.indices_performance:
    for i, indice in enumerate(st.session_state.indices_performance):
        with st.expander(f"🔹 {indice['nome']}"):
            for metrica, peso in indice["metricas"].items():
                st.markdown(f"- **{metrica}**: `{peso:.2f}`")

            # ⭐ verificar se está a ser usado por algum grupo
            grupos_que_usam = [
                g for g in st.session_state.grupos_scouting
                if str(g.get("indice", "")).strip().lower() == indice["nome"].strip().lower()
            ]
            indice_em_uso = len(grupos_que_usam) > 0

            if indice_em_uso:
                st.warning(
                    "Este índice está a ser usado pelos seguintes grupos, pelo que **não pode ser apagado**:\n\n" +
                    "\n".join([f"• {g.get('nome','(sem nome)')}" for g in grupos_que_usam])
                )

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✏️ Editar índice '{indice['nome']}'", key=f"edit_{i}"):
                    st.session_state.modo_edicao = i
                    st.rerun()
            with col2:
                # ⭐ botão desativado se o índice estiver em uso
                if st.button(
                    f"🗑️ Apagar índice '{indice['nome']}'",
                    key=f"delete_{i}",
                    disabled=indice_em_uso
                ):
                    del st.session_state.indices_performance[i]
                    guardar_indices_csv(st.session_state.indices_performance)
                    st.success(f"Índice '{indice['nome']}' removido com sucesso.")
                    st.rerun()
else:
    st.info("Nenhum índice de performance foi criado ainda.")
