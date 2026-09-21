import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import tempfile
import requests
import pyreadr
from pathlib import Path

URL_DADOS_VIRUS = (
    "https://raw.githubusercontent.com/infogripe/Boletim_InfoGripe/"
    "main/Dados/InfoGripe/"
    "casos_semanais_fx_etaria_virus_sem_filtro_febre.csv"
)

URL_DADOS = (
    "https://raw.githubusercontent.com/infogripe/Boletim_InfoGripe/"
    "main/Dados/InfoGripe/"
    "estados_e_pais_serie_estimativas_tendencia_sem_filtro_febre.csv"
)

URL_LIMIAR = (
    "https://raw.githubusercontent.com/infogripe/Boletim_InfoGripe/"
    "main/Dados/InfoGripe/"
    "limiares_UF_capitais.csv"
)

URL_POP = (
    "https://ftp.ibge.gov.br/Projecao_da_Populacao/"
    "Projecao_da_Populacao_2024/"
    "projecoes_2024_tab1_idade_simples.xlsx"
)

URL_BANDAS_VSR = (
    "https://raw.githubusercontent.com/infogripe/"
    "Figuras_curso_TGHN/main/dados/bands_vsr_uf.RData"
)

print("Lendo dados do InfoGripe...")

dados_virus = pd.read_csv(
    URL_DADOS_VIRUS,
    sep=";",
    decimal=","
)

dados = pd.read_csv(
    URL_DADOS,
    sep=";",
    decimal=","
)

limiar = pd.read_csv(URL_LIMIAR)

limiar = limiar[
    (limiar["escala_reg"] == "UF") &
    (limiar["escala"] == "incidencia")
].copy()

print("Lendo projeções populacionais do IBGE...")

pop = pd.read_excel(
    URL_POP,
    skiprows=5
)

pop_br = pop[
    ~pop["SIGLA"].isin([
        "N", "NE", "SE", "S", "CO", "BR"
    ])
].copy()

pop_br = pop_br[
    pop_br["SEXO"].astype(str).str.strip().str.lower() == "ambos"
].copy()

anos_pop = [2023, 2024, 2025, 2026]

colunas_anos = [
    col for col in anos_pop
    if col in pop_br.columns
]

if not colunas_anos:
    raise ValueError(
        "Nenhuma das colunas de população 2023-2026 "
        "foi encontrada no arquivo do IBGE."
    )


pop_br = pop_br[
    ["SIGLA", "IDADE"] + colunas_anos
].copy()

pop_br = (
    pop_br
    .groupby("SIGLA", as_index=False)[colunas_anos]
    .sum()
)

pop_br = pop_br.melt(
    id_vars="SIGLA",
    value_vars=colunas_anos,
    var_name="Ano epidemiológico",
    value_name="pop"
)

pop_br["Ano epidemiológico"] = (
    pd.to_numeric(
        pop_br["Ano epidemiológico"],
        errors="coerce"
    )
)

pop_br["pop"] = pd.to_numeric(
    pop_br["pop"],
    errors="coerce"
)

pop_br = pop_br.rename(
    columns={
        "SIGLA": "DS_UF_SIGLA"
    }
)

dados_1 = dados_virus[
    dados_virus["Ano epidemiológico"] >= 2024
].copy()


dados_1 = dados_1[
    dados_1["fx_etaria"] == "Total"
].copy()


dados_1 = dados_1[
    dados_1["DS_UF_SIGLA"] != "BR"
].copy()

dados_1 = (
    dados_1
    .groupby(
        [
            "SG_UF_NOT",
            "Semana epidemiológica",
            "Ano epidemiológico"
        ],
        as_index=False
    )["SRAG"]
    .sum()
)

dados_1 = dados_1.rename(
    columns={
        "SG_UF_NOT": "CO_UF"
    }
)

dados_1 = dados_1[
    [
        "CO_UF",
        "Semana epidemiológica",
        "Ano epidemiológico",
        "SRAG"
    ]
].copy()

dados_1 = dados_1.rename(
    columns={
        "SRAG":
        "Casos.semanais.reportados.até.a.última.atualização"
    }
)

dados_1 = dados_1.sort_values(
    [
        "Ano epidemiológico",
        "Semana epidemiológica"
    ]
)

dados_1["sequencia"] = (
    dados_1
    .groupby("CO_UF")
    .cumcount() + 1
)

coluna_casos = (
    "Casos.semanais.reportados.até.a.última.atualização"
)

dados_base = dados.copy()

if coluna_casos in dados_base.columns:
    dados_base = dados_base.drop(
        columns=[coluna_casos]
    )

dado_now = dados_base.merge(
    dados_1,
    on=[
        "CO_UF",
        "Ano epidemiológico",
        "Semana epidemiológica"
    ],
    how="left"
)

dado_now = dado_now[
    dado_now["escala"] == "casos"
].copy()


dado_now = dado_now[
    dado_now["Ano epidemiológico"] >= 2023
].copy()


dado_now = dado_now[
    dado_now["DS_UF_SIGLA"] != "BR"
].copy()

dado_now["regiao"] = dado_now["DS_UF_SIGLA"]

dado_now = dado_now.merge(
    pop_br,
    on=[
        "DS_UF_SIGLA",
        "Ano epidemiológico"
    ],
    how="left"
)

dado_now["noti"] = (
    dado_now[
        "Casos.semanais.reportados.até.a.última.atualização"
    ]
    * 100000
    / dado_now["pop"]
)

dado_now["media_m"] = (
    dado_now["média móvel"]
    * 100000
    / dado_now["pop"]
)

dado_now["IC95I"] = (
    dado_now["IC95I"]
    * 100000
    / dado_now["pop"]
)

dado_now["IC95S"] = (
    dado_now["IC95S"]
    * 100000
    / dado_now["pop"]
)


dado_now["incidencia.estimada"] = (
    dado_now["casos estimados"]
    * 100000
    / dado_now["pop"]
)


dado_now = dado_now.sort_values(
    [
        "Ano epidemiológico",
        "Semana epidemiológica"
    ]
)


dado_now["sequencia"] = (
    dado_now
    .groupby("DS_UF_SIGLA")
    .cumcount() + 1
)


dado_now = dado_now.merge(
    limiar,
    on="regiao",
    how="left"
)

df = dado_now[
    (dado_now["Ano epidemiológico"] == 2026) &
    (dado_now["DS_UF_SIGLA"] == "MG")
].copy()

df = df.sort_values(
    "Semana epidemiológica"
)

print("\n============================================================")
print("DADOS UTILIZADOS NO GRÁFICO")
print("============================================================")

print(f"Ano: {df['Ano epidemiológico'].unique()}")
print(f"UF: {df['DS_UF_SIGLA'].unique()}")

print(f"Semanas disponíveis: ", f"{df['Semana epidemiológica'].min()} ", f"a ", f"{df['Semana epidemiológica'].max()}")

print(f"População utilizada em 2026: ", f"{df['pop'].dropna().unique()}")

COR_MUITO_ALTO = "#4F1D00"
COR_ALTO = "#823500"
COR_MODERADO = "#B94E00"
COR_BAIXO = "#025FB4"

def adicionar_limiar(ax, valor, texto, cor):

    if pd.isna(valor):
        return

    ax.axhline(
        y=valor,
        color=cor,
        linestyle="--",
        linewidth=1
    )

    ax.text(
        0.99,
        valor,
        texto,
        color=cor,
        fontsize=9,
        va="bottom",
        ha="right",
        transform=ax.get_yaxis_transform()
    )

fig, ax = plt.subplots(
    figsize=(9, 6)
)

ax.fill_between(
    df["Semana epidemiológica"],
    df["IC95I"],
    df["IC95S"],
    color="#FFA186",
    alpha=0.5,
    label="Intervalo de Credibilidade"
)

ax.plot(
    df["Semana epidemiológica"],
    df["noti"],
    color="#013E79",
    linewidth=1.5,
    label="Incidência notificada"
)

ax.plot(
    df["Semana epidemiológica"],
    df["incidencia.estimada"],
    color="#F36900",
    linewidth=1.5,
    label="Incidência estimada"
)

if "muito_alto" in df.columns:
    adicionar_limiar(
        ax,
        df["muito_alto"].iloc[0],
        "Muito alto",
        COR_MUITO_ALTO
    )

if "alto" in df.columns:
    adicionar_limiar(
        ax,
        df["alto"].iloc[0],
        "Alto",
        COR_ALTO
    )

if "moderado" in df.columns:
    adicionar_limiar(
        ax,
        df["moderado"].iloc[0],
        "Moderado",
        COR_MODERADO
    )

if "baixo" in df.columns:
    adicionar_limiar(
        ax,
        df["baixo"].iloc[0],
        "Baixo",
        COR_BAIXO
    )

ax.set_xlabel(
    "Semana epidemiológica"
)

ax.set_ylabel(
    "Incidência de SRAG (por 100 mil hab)"
)

ax.set_xticks(
    np.arange(1, 54, 9)
)

ax.grid(
    True,
    axis="both",
    linestyle="-",
    linewidth=0.5,
    alpha=0.3
)

ax.set_axisbelow(True)

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.10),
    ncol=4,
    frameon=False
)

plt.tight_layout()

plt.savefig(
    "../figuras_infogripe/grafico1_inc_mg_2026.tiff",
    dpi=300,
    bbox_inches="tight"
)

fig, ax = plt.subplots(
    figsize=(9, 6)
)

ax.bar(
    df["Semana epidemiológica"],
    df["noti"],
    color="#79A9FF",
    edgecolor="#79A9FF",
    alpha=0.75,
    label="Incidência notificada"
)

ax.plot(
    df["Semana epidemiológica"],
    df["media_m"],
    color="#013E79",
    linewidth=1.5,
    label="Média Móvel"
)

ax.fill_between(
    df["Semana epidemiológica"],
    df["IC95I"],
    df["IC95S"],
    color="#001F43",
    alpha=0.2,
    label="Incidência estimada"
)

if "muito_alto" in df.columns:
    adicionar_limiar(
        ax,
        df["muito_alto"].iloc[0],
        "Muito alto",
        COR_MUITO_ALTO
    )

if "alto" in df.columns:
    adicionar_limiar(
        ax,
        df["alto"].iloc[0],
        "Alto",
        COR_ALTO
    )

if "moderado" in df.columns:
    adicionar_limiar(
        ax,
        df["moderado"].iloc[0],
        "Moderado",
        COR_MODERADO
    )

if "baixo" in df.columns:
    adicionar_limiar(
        ax,
        df["baixo"].iloc[0],
        "Baixo",
        COR_BAIXO
    )

ax.set_xlabel(
    "Semana epidemiológica"
)

ax.set_ylabel(
    "Incidência de SRAG (por 100 mil hab)"
)

ax.set_xticks(
    np.arange(1, 54, 9)
)

ax.grid(
    True,
    axis="both",
    linestyle="-",
    linewidth=0.5,
    alpha=0.3
)

ax.set_axisbelow(True)

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.10),
    ncol=4,
    frameon=False
)

plt.tight_layout()

plt.savefig(
    "../figuras_infogripe/limiares_SRAG_desafio_tela1.tiff",
    dpi=300,
    bbox_inches="tight"
)

with tempfile.TemporaryDirectory() as tmp:

    arquivo_bandas = Path(tmp) / "bands_vsr_uf.RData"

    resposta = requests.get(
        URL_BANDAS_VSR,
        timeout=120
    )

    resposta.raise_for_status()

    arquivo_bandas.write_bytes(
        resposta.content
    )

    objetos_r = pyreadr.read_r(
        str(arquivo_bandas)
    )


print("Objetos encontrados no RData:")

for nome, objeto in objetos_r.items():

    if isinstance(objeto, pd.DataFrame):

        print(
            f"  {nome}: {objeto.shape}"
        )


dataframes_r = {
    nome: objeto
    for nome, objeto in objetos_r.items()
    if isinstance(objeto, pd.DataFrame)
}


if not dataframes_r:

    raise ValueError(
        "Nenhum DataFrame foi encontrado em bands_vsr_uf.RData."
    )

bandas = None

for nome, objeto in dataframes_r.items():

    nome_lower = nome.lower()

    if "band" in nome_lower or "vsr" in nome_lower:

        bandas = objeto.copy()

        print(
            f"Objeto utilizado: {nome}"
        )

        break

if bandas is None:

    nome, objeto = next(
        iter(dataframes_r.items())
    )

    bandas = objeto.copy()

    print(
        f"Objeto utilizado: {nome}"
    )

col_uf_banda = "SG_UF_NOT"

col_semana_banda = "Semana.epidemiológica"

col_q25 = "0.25quant"
col_q50 = "0.5quant"
col_q75 = "0.75quant"
col_q90 = "0.9quant"

bandas["SG_UF_NOT"] = pd.to_numeric(
    bandas["SG_UF_NOT"],
    errors="coerce"
)

bandas = bandas[
    bandas["SG_UF_NOT"] == 31
].copy()

bandas["Semana epidemiológica"] = pd.to_numeric(
    bandas[col_semana_banda],
    errors="coerce"
)

bandas["q25"] = pd.to_numeric(
    bandas[col_q25],
    errors="coerce"
)

bandas["q50"] = pd.to_numeric(
    bandas[col_q50],
    errors="coerce"
)

bandas["q75"] = pd.to_numeric(
    bandas[col_q75],
    errors="coerce"
)

bandas["q90"] = pd.to_numeric(
    bandas[col_q90],
    errors="coerce"
)


bandas = bandas[
    [
        "Semana epidemiológica",
        "q25",
        "q50",
        "q75",
        "q90"
    ]
].copy()


bandas = bandas.dropna(
    subset=["Semana epidemiológica"]
)


bandas = (
    bandas
    .sort_values("Semana epidemiológica")
    .drop_duplicates(
        subset=["Semana epidemiológica"]
    )
)

# As bandas do arquivo original foram construídas usando a população de 2025, mas os anos observados sejam 2025 e 2026.

pop_mg_2025 = pop_br[
    (pop_br["DS_UF_SIGLA"] == "MG") &
    (pop_br["Ano epidemiológico"] == 2025)
]["pop"]


if pop_mg_2025.empty:

    raise ValueError(
        "População de MG em 2025 não encontrada."
    )


pop_mg_2025 = float(
    pop_mg_2025.iloc[0]
)

bandas["q25"] = (
    bandas["q25"]
    * 100000
    / pop_mg_2025
)

bandas["q50"] = (
    bandas["q50"]
    * 100000
    / pop_mg_2025
)

bandas["q75"] = (
    bandas["q75"]
    * 100000
    / pop_mg_2025
)

bandas["q90"] = (
    bandas["q90"]
    * 100000
    / pop_mg_2025
)

dados_bandas = dados_virus[
    (dados_virus["DS_UF_SIGLA"] == "MG") &
    (dados_virus["fx_etaria"] == "Total") &
    (dados_virus["Ano epidemiológico"].isin([2025, 2026]))
].copy()

dados_bandas = (
    dados_bandas
    .groupby(
        [
            "Ano epidemiológico",
            "Semana epidemiológica"
        ],
        as_index=False
    )["VSR"]
    .sum()
)

pop_mg = pop_br[
    pop_br["DS_UF_SIGLA"] == "MG"
].copy()


dados_bandas = dados_bandas.merge(
    pop_mg[
        [
            "Ano epidemiológico",
            "pop"
        ]
    ],
    on="Ano epidemiológico",
    how="left"
)

dados_bandas["incidencia"] = (
    dados_bandas["VSR"]
    * 100000
    / dados_bandas["pop"]
)

grafico_bandas = bandas.merge(
    dados_bandas[
        [
            "Ano epidemiológico",
            "Semana epidemiológica",
            "incidencia"
        ]
    ],
    on="Semana epidemiológica",
    how="left"
)

fig, ax = plt.subplots(
    figsize=(9, 6)
)

ax.fill_between(
    bandas["Semana epidemiológica"],
    0,
    bandas["q50"],
    color="#79A9FF",
    alpha=0.55,
    linewidth=0
)

ax.fill_between(
    bandas["Semana epidemiológica"],
    bandas["q50"],
    bandas["q75"],
    color="#025FB4",
    alpha=0.45,
    linewidth=0
)

ax.fill_between(
    bandas["Semana epidemiológica"],
    bandas["q75"],
    bandas["q90"],
    color="#F36900",
    alpha=0.55,
    linewidth=0
)

max_y = max(
    bandas["q90"].max(),
    dados_bandas["incidencia"].max()
)


ax.fill_between(
    bandas["Semana epidemiológica"],
    bandas["q90"],
    max_y * 1.10,
    color="#FFA186",
    alpha=0.45,
    linewidth=0
)

dados_2025 = dados_bandas[
    dados_bandas["Ano epidemiológico"] == 2025
].copy()


ax.plot(
    dados_2025["Semana epidemiológica"],
    dados_2025["incidencia"],
    color="#4F1D00",
    linewidth=1,
    linestyle="--",
    alpha=0.65
)

dados_2026 = dados_bandas[
    dados_bandas["Ano epidemiológico"] == 2026
].copy()


ax.plot(
    dados_2026["Semana epidemiológica"],
    dados_2026["incidencia"],
    color="#4F1D00",
    linewidth=1.5
)

ax.set_xlim(
    1,
    52
)


ax.set_xlabel(
    "Semana epidemiológica"
)


ax.set_ylabel(
    "Incidência de VSR (por 100 mil hab)"
)


ax.set_xticks(
    np.arange(1, 53, 9)
)

ax.grid(
    True,
    axis="both",
    linestyle="-",
    linewidth=0.5,
    alpha=0.3
)


ax.set_axisbelow(True)

handles = [

    plt.Rectangle(
        (0, 0),
        1,
        1,
        facecolor="#79A9FF",
        edgecolor="none",
        alpha=0.55
    ),

    plt.Rectangle(
        (0, 0),
        1,
        1,
        facecolor="#025FB4",
        edgecolor="none",
        alpha=0.45
    ),

    plt.Rectangle(
        (0, 0),
        1,
        1,
        facecolor="#F36900",
        edgecolor="none",
        alpha=0.55
    ),

    plt.Rectangle(
        (0, 0),
        1,
        1,
        facecolor="#FFA186",
        alpha=0.45,
        edgecolor="none"
    ),

    Line2D(
        [0],
        [0],
        color="#4F1D00",
        linewidth=1,
        linestyle="--",
        alpha=0.65
    ),

    Line2D(
        [0],
        [0],
        color="#4F1D00",
        linewidth=1.5,
        linestyle="-"
    )
]


labels = [
    "Faixa típica",
    "Faixa moderadamente elevada",
    "Faixa elevada",
    "Faixa excepcionalmente elevada",
    "2025",
    "2026"
]


leg = ax.legend(
    handles,
    labels,
    loc="upper left",
    bbox_to_anchor=(1.02, 1),
    frameon=False,
    title="Bandas epidêmicas probabilísticas"
)

leg.get_title().set_fontweight("bold")

plt.tight_layout()


plt.savefig(
    "../figuras_infogripe/bandas_prob_desafio_tela2.tiff",
    dpi=300,
    bbox_inches="tight"
)