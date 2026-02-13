import pandas as pd
import os
import json
import plotly.graph_objects as go
import streamlit as st
import numpy as np
import ssl
import smtplib
from pathlib import Path
from email.message import EmailMessage
from smtplib import SMTPAuthenticationError

FICHEIRO_INDICES = os.path.join(os.getcwd(), "data", "ficheiro.csv")
FICHEIRO_GRUPOS = os.path.join(os.getcwd(), "data", "grupos_scouting.csv")
CONFIG_PATH = os.path.join(os.getcwd(), "data", "config_monitorizacao.json")

# Criar diretório se não existir
os.makedirs(os.path.dirname(FICHEIRO_INDICES), exist_ok=True)


def guardar_indices_csv(indices):
    linhas = []
    for indice in indices:
        for metrica, peso in indice["metricas"].items():
            linhas.append({"nome": indice["nome"], "metrica": metrica, "peso": peso})
    df = pd.DataFrame(linhas)

    # Criar diretório se necessário
    os.makedirs(os.path.dirname(FICHEIRO_INDICES), exist_ok=True)
    df.to_csv(FICHEIRO_INDICES, index=False)


def carregar_indices_csv():
    if not os.path.exists(FICHEIRO_INDICES) or os.path.getsize(FICHEIRO_INDICES) == 0:
        return []

    try:
        df = pd.read_csv(FICHEIRO_INDICES)
    except pd.errors.EmptyDataError:
        return []

    indices_dict = {}
    for _, row in df.iterrows():
        nome = row["nome"]
        if nome not in indices_dict:
            indices_dict[nome] = {}
        indices_dict[nome][row["metrica"]] = row["peso"]

    return [
        {"nome": nome, "metricas": metricas} 
        for nome, metricas in indices_dict.items()
    ]


def carregar_dfs_campeonatos(campeonatos, pasta="data/leagues"):
    dfs = []

    for liga in campeonatos:
        nome_ficheiro = os.path.join(pasta, f"{liga}.csv")
        if os.path.isfile(nome_ficheiro):
            df_liga = pd.read_csv(nome_ficheiro)
            df_liga["Liga"] = liga  # adiciona coluna identificadora
            dfs.append(df_liga)
        else:
            print(f"⚠️ Ficheiro não encontrado: {nome_ficheiro}")

    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()  # DataFrame vazio se nenhum ficheiro foi lido


def funcao_normalizacao(df, colunas, minutos_col="Min"):
    """
    Para cada coluna:
    - Se for métrica estática (percentagens, médias, razões), cria <col>_norm (min-max) e mantém a original.
    - Caso contrário, cria <col>_per90 e normaliza essa (substitui o _per90 pelo valor normalizado).
    """
    # garantir minutos a numérico
    if minutos_col in df.columns:
        df[minutos_col] = pd.to_numeric(df[minutos_col], errors='coerce')

    df_norm = df.copy()

    colunas_estaticas = {
        "Goals_per_shot",
        "PSxG/SoT",
        "PSxG+/-",
        "Launched_Cmp%",
        "Passes_Launch%",
        "Passes_AvgLen",
        "Goal_Kicks_Launch%",
        "Goal_Kicks_AvgLen",
        "Crosses_Stp%",
        "Sweeper_AvgDist",
    }

    for col in colunas:
        if col not in df.columns:
            continue

        if col in colunas_estaticas:
            # NÃO tocar na coluna original; criar <col>_norm
            x = pd.to_numeric(df[col], errors='coerce')
            max_val, min_val = x.max(), x.min()
            if pd.notna(max_val) and max_val != min_val:
                df_norm[f"{col}_norm"] = (x - min_val) / (max_val - min_val)
            else:
                df_norm[f"{col}_norm"] = 0.0

        elif minutos_col in df.columns:
            # Criar _per90 e normalizar essa
            vals = pd.to_numeric(df[col], errors='coerce')
            per90_col = f"{col}_per90"

            per90 = (vals / df[minutos_col].replace(0, pd.NA)) * 90
            df_norm[per90_col] = per90.fillna(0)

            max_val, min_val = df_norm[per90_col].max(), df_norm[per90_col].min()
            if pd.notna(max_val) and max_val != min_val:
                df_norm[per90_col] = (df_norm[per90_col] - min_val) / (max_val - min_val)
            else:
                df_norm[per90_col] = 0.0

    return df_norm

def guardar_grupos_csv(lista_grupos, path=FICHEIRO_GRUPOS):
    df = pd.DataFrame(lista_grupos)
    df.to_csv(path, index=False)


def carregar_grupos_csv(path=FICHEIRO_GRUPOS):
    # Verifica se o ficheiro não existe ou está completamente vazio
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return []

    try:
        df = pd.read_csv(path)

        # Verifica se o ficheiro tem colunas
        if df.empty or df.columns.size == 0:
            return []

        # Converter listas de volta (campeonatos, posicoes), se necessário
        for col in ["campeonatos", "posicoes"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: eval(x) if pd.notnull(x) else [])

        return df.to_dict(orient="records")

    except pd.errors.EmptyDataError:
        return []
    except Exception as e:
        print(f"❌ Erro ao carregar grupos CSV: {e}")
        return []


def calcular_score(
    idade_min,
    idade_max,
    altura_min,
    valor_max,
    minutos_min,
    pe,
    campeonatos,
    posicoes,
    indice,
):

    df_filtrado = carregar_dfs_campeonatos(campeonatos)

    colunas_normalizar = [
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
            "Sweeper_AvgDist",
        ]

    df_filtrado = funcao_normalizacao(df_filtrado, colunas_normalizar)

    df_filtrado["Age"] = pd.to_numeric(df_filtrado["Age"], errors="coerce")

    df_filtrado = df_filtrado[
        (df_filtrado["Age"] >= idade_min) & (df_filtrado["Age"] <= idade_max)
    ]

    df_filtrado["altura"] = pd.to_numeric(df_filtrado["altura"], errors="coerce")
    df_filtrado = df_filtrado[df_filtrado["altura"] >= altura_min]

    df_filtrado["valor_mercado"] = pd.to_numeric(df_filtrado["valor_mercado"], errors="coerce")
    df_filtrado = df_filtrado[df_filtrado["valor_mercado"] <= valor_max * 1000000]

    df_filtrado["Min"] = pd.to_numeric(df_filtrado["Min"], errors="coerce")

    df_filtrado = df_filtrado[df_filtrado["Min"] >= minutos_min]

    df_filtrado = df_filtrado[df_filtrado["Pos_x"].isin(posicoes)]

    if pe != "Indiferente":
        # meter em minusculas
        pe = pe.lower()

        # verififcar se e esquerdo ou direito ou ambos
        df_filtrado = df_filtrado[(df_filtrado["pe"] == pe) | (df_filtrado["pe"] == "ambos")]

    indices_df = pd.read_csv(FICHEIRO_INDICES)

    indice_performance = indices_df[indices_df["nome"] == indice]

    metricas = indice_performance.set_index("metrica")["peso"].to_dict()

    # Lista das métricas que devem ser incluídas
    metricas_utilizadas = list(metricas.keys())

    lista_estaticas = {
        "Goals_per_shot",
        "PSxG/SoT",
        "PSxG+/-",
        "Launched_Cmp%",
        "Passes_Launch%",
        "Passes_AvgLen",
        "Goal_Kicks_Launch%",
        "Goal_Kicks_AvgLen",
        "Crosses_Stp%",
        "Sweeper_AvgDist",
    }

    # Garantir que df_filtrado inclui essas colunas
    lista_estaticas = [m for m in metricas_utilizadas if m in lista_estaticas]
    colunas_estaticas = [f"{m}_norm" for m in lista_estaticas]


    outras_metricas = [m for m in metricas_utilizadas if m not in lista_estaticas]
    colunas_outros = [f"{m}_per90" for m in outras_metricas]

    lista_metricas = colunas_estaticas + colunas_outros

    # Juntar colunas informativas + métricas usadas
    colunas_final = ["Player", "Team", "Pos_x", "MP", "Min", "Age", "pe", "altura", "valor_mercado"] + lista_estaticas + outras_metricas + colunas_estaticas + colunas_outros

    # renomear colunas para manter consistência

    # Subset final
    df_filtrado = df_filtrado[colunas_final].copy()

    # Calcular score baseado no índice
    # Criar um mapeamento de coluna_final -> peso
    pesos_final = {}
    for m in lista_metricas:
        if m.endswith('_per90'):
            m_original = m.replace('_per90', '')  # volta ao nome original para ir buscar o peso
        elif m.endswith('_norm'):
            m_original = m.replace('_norm', '')
        else:
            m_original = m
        pesos_final[m] = metricas[m_original]

    # Calcular o Score usando as colunas certas e os pesos correspondentes
    df_filtrado["Score"] = sum(
        df_filtrado[col] * peso for col, peso in pesos_final.items()
    )

    # Ordenar por Score decrescente
    df_resultado = df_filtrado.sort_values(by="Score", ascending=False).reset_index(
        drop=True
    )

    renomear_colunas = {
        "Player": "Jogador",
        "Team": "Equipa",
        "Pos_x": "Posição",
        "MP": "Jogos Disputados",
        "Min": "Minutos",
        "Age": "Idade",
        "pe": "Pé",
        "altura": "Altura (cm)",
        "valor_mercado": "Valor de Mercado (€)",
    }
    df_resultado.rename(columns=renomear_colunas, inplace=True)

    df_resultado["Valor de Mercado (€)"] = df_resultado["Valor de Mercado (€)"].astype(int)
    df_resultado["Altura (cm)"] = df_resultado["Altura (cm)"].astype(int)

    # Manter apenas as colunas relevantes
    colunas_relevantes = ["Jogador", "Equipa", "Posição", "Jogos Disputados", "Minutos", "Idade", "Pé", "Altura (cm)", "Valor de Mercado (€)"] + lista_estaticas + outras_metricas + ["Score"]
    df_resultado = df_resultado[colunas_relevantes]

    print(df_resultado)

    # Filtrar apenas os 10 melhores jogadores
    top_10 = df_resultado.head(10).copy()

    # Garantir que a coluna Score está presente e visível
    top_10["Score"] = top_10["Score"].round(3)  # arredonda para facilitar leitura
    return top_10


def carregar_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return None


def guardar_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)


# --- Função auxiliar para atualizar config_monitorizacao.json ---
def remover_grupo_da_config(nome_grupo):

    if os.path.exists(CONFIG_PATH):

        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        if "grupos" in config and nome_grupo in config["grupos"]:
            config["grupos"].remove(nome_grupo)
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)
            print(f"✅ Grupo '{nome_grupo}' removido da config_monitorizacao.json.")

def _normalize_columns(df, cols, method="minmax", q_low=0.05, q_high=0.95, invert=None):
    """
    Normaliza cada coluna de 'cols' para [0,1].
    method: 'minmax' (min-max) ou 'quantile' (robusto aos outliers).
    invert: lista/SET de métricas onde menor é melhor (ex.: 'GA', 'Faltas', etc.).
    """
    invert = set(invert or [])
    norm = pd.DataFrame(index=df.index)

    for c in cols:
        s = pd.to_numeric(df[c], errors="coerce")
        if method == "quantile":
            lo, hi = s.quantile(q_low), s.quantile(q_high)
            # evita hi==lo
            if pd.isna(lo) or pd.isna(hi) or hi == lo:
                lo, hi = s.min(), s.max()
        else:  # minmax
            lo, hi = s.min(), s.max()

        if pd.isna(lo) or pd.isna(hi) or hi == lo:
            # coluna constante → tudo 0.5 para não “matar” o radar
            z = pd.Series(0.5, index=s.index)
        else:
            z = (s - lo) / (hi - lo)
            z = z.clip(0, 1)

        if c in invert:
            z = 1 - z

        norm[c] = z

    return norm


def grafico_radar(df, jogador1, jogador2, jogador3,
                  titulo="Comparação de Jogadores",
                  method="quantile",           # 'minmax' ou 'quantile'
                  invert_metricas=None):       # ex.: {'GA','Faltas'}
    # 1) escolher métricas úteis
    metricas = [m for m in df.columns
                if m not in ["Jogador", "Equipa", "Posição", "Jogos Disputados", "Minutos", "Idade", "Score", "Pé", "Valor de Mercado (€)", "Altura (cm)"]]

    # 2) normalizar por métrica (cada coluna na sua própria escala)
    df_norm = _normalize_columns(df, metricas, method=method, invert=invert_metricas)

    # 3) preparar dados (mantemos originais para hover)
    def _vals(jog):
        r = df_norm.loc[df["Jogador"] == jog, metricas].values.flatten().tolist()
        orig = df.loc[df["Jogador"] == jog, metricas].values.flatten().tolist()
        return r, orig

    r1, o1 = _vals(jogador1)
    r2, o2 = _vals(jogador2)
    r3, o3 = _vals(jogador3)

    fig = go.Figure()

    # helper p/ hover template com valor normalizado e original
    hover_tmpl = (
        "<b>%{text}</b><br>"
        "<i>%{customdata}</i><br>"
    )

    fig.add_trace(go.Scatterpolar(
        r=r1, theta=metricas, fill='toself', name=jogador1,
        line=dict(color='royalblue', width=3), opacity=1,
        customdata=[f"{v:.3g}" if isinstance(v, (int, float, np.number)) else str(v) for v in o1],
        text=[jogador1]*len(metricas), hovertemplate=hover_tmpl
    ))

    fig.add_trace(go.Scatterpolar(
        r=r2, theta=metricas, fill='toself', name=jogador2,
        line=dict(color='darkorange', width=3), opacity=0.7,
        customdata=[f"{v:.3g}" if isinstance(v, (int, float, np.number)) else str(v) for v in o2],
        text=[jogador2]*len(metricas), hovertemplate=hover_tmpl
    ))

    fig.add_trace(go.Scatterpolar(
        r=r3, theta=metricas, fill='toself', name=jogador3,
        line=dict(color='green', width=3), opacity=0.7,
        customdata=[f"{v:.3g}" if isinstance(v, (int, float, np.number)) else str(v) for v in o3],
        text=[jogador3]*len(metricas), hovertemplate=hover_tmpl
    ))

    fig.update_layout(
        title=dict(text=titulo, x=0.5, xanchor="center", font=dict(size=20, family="Arial", color="black")),
        polar=dict(
            bgcolor="white",
            radialaxis=dict(visible=True, range=[0, 1], showline=False, gridcolor="#E8E8E8",
                            tickfont=dict(size=11, color="black")),
            angularaxis=dict(showline=False, linewidth=1, gridcolor="#E8E8E8",
                             tickfont=dict(size=12, color="black"))
        ),
        showlegend=True,
        legend=dict(font=dict(size=12, color="black"), orientation="h", x=0.5, xanchor="center", y=-0.1),
        margin=dict(t=80, b=60, l=60, r=60),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True)

EMAIL_USER = "" 
EMAIL_PASS = "" 



def enviar_email(destinatario, grupos):
    """
    Envia um e-mail por cada grupo:
      - Top 3 (Jogador + Score)
      - Jogador mais novo no Top 10
      - Anexa o CSV já existente (score/top10_{nome}.csv)
    'grupos' pode ser lista de strings (nomes) OU de dicts {'nome': str, 'csv_path': str}
    """
    if not EMAIL_USER or not EMAIL_PASS:
        raise ValueError("Define EMAIL_USER e EMAIL_PASS (usa App Password do Gmail).")

    for g in grupos:
        # aceita 'Extremos U23' ou {'nome': 'Extremos U23', 'csv_path': '...'}
        if isinstance(g, dict):
            nome = g.get("nome")
            csv_path = Path(g.get("csv_path", f"score/top10_{nome}.csv"))
        else:
            nome = str(g)
            csv_path = Path(f"score/top10_{nome}.csv")

        corpo_html = ["<h2>Relatório de Scouting</h2>"]

        if not csv_path.exists():
            corpo_html.append(f"<h3>{nome}</h3><p><em>CSV não encontrado: {csv_path}</em></p>")
            anexar_csv = False
        else:
            df = pd.read_csv(csv_path)

            # Normalizar nomes mínimos
            if "Jogador" not in df.columns and "Player" in df.columns:
                df = df.rename(columns={"Player": "Jogador"})
            if "Idade" not in df.columns and "Age" in df.columns:
                df = df.rename(columns={"Age": "Idade"})

            if "Jogador" not in df.columns or "Score" not in df.columns:
                corpo_html.append(f"<h3>{nome}</h3><p><em>Faltam colunas 'Jogador' ou 'Score' no CSV.</em></p>")
                anexar_csv = True  # ainda assim anexa para referência
            else:
                # Garantir ordenação e formatação
                df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
                df = df.sort_values("Score", ascending=False).reset_index(drop=True)

                top3 = df.head(3).copy()
                linhas_top3 = (
                    "".join(f"<tr><td>{r['Jogador']}</td><td>{r['Score']:.2f}</td></tr>"
                            for _, r in top3.iterrows())
                    if not top3.empty else "<tr><td colspan='2'>(sem dados)</td></tr>"
                )

                desc_mais_novo = "<em>(Sem coluna de idade)</em>"
                if "Idade" in df.columns:
                    top10 = df.head(10).copy()
                    top10["Idade"] = pd.to_numeric(top10["Idade"], errors="coerce")
                    top10 = top10.dropna(subset=["Idade"])
                    if not top10.empty:
                        rn = top10.sort_values("Idade").iloc[0]
                        desc_mais_novo = f"{rn['Jogador']} ({int(rn['Idade'])} anos)"

                corpo_html.append(f"""
                    <h3>Grupo: {nome}</h3>
                    <p><strong>Top 3</strong></p>
                    <table border="1" cellpadding="6" cellspacing="0">
                      <tr><th>Jogador</th><th>Score</th></tr>
                      {linhas_top3}
                    </table>
                    <p><strong>Jogador mais novo no Top 10:</strong> {desc_mais_novo}</p>
                """)
                anexar_csv = True

        # Enviar 1 e-mail por grupo
        msg = EmailMessage()
        msg["From"] = EMAIL_USER
        msg["To"] = destinatario
        msg["Subject"] = f"Relatório de Scouting - {nome}"
        msg.set_content("O seu cliente de e-mail não suporta HTML.")
        msg.add_alternative("\n".join(corpo_html), subtype="html")

        if anexar_csv and csv_path.exists():
            with open(csv_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="text", subtype="csv", filename=csv_path.name)

        context = ssl.create_default_context()
        try:
            # SSL (465)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(EMAIL_USER, EMAIL_PASS)
                server.send_message(msg)
        except SMTPAuthenticationError:
            # Fallback STARTTLS (587)
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.send_message(msg)
