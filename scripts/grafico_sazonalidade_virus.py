import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

INFOGRIPE_URL = (
    "https://raw.githubusercontent.com/"
    "infogripe/Boletim_InfoGripe/main/"
    "Dados/InfoGripe/"
    "casos_semanais_fx_etaria_virus_sem_filtro_febre.csv"
)

CORES_ANOS = {
    2019: "#F36900",
    2023: "#0583F4",
    2024: "#70A130",
    2025: "#BF42F2",
}

COR_SRAG = "#025FB4"

COR_GRID = "#D9D9D9"
COR_TEXTO = "#4A4A4A"

dados = pd.read_csv(
    INFOGRIPE_URL,
    sep=";",
)

flu = dados[
    (dados["epiyear"].isin([2019, 2023, 2024]))
    & (dados["DS_UF_SIGLA"] == "BR")
    & (dados["fx_etaria"] == "Total")
].copy()


flu = flu[
    [
        "epiyear",
        "epiweek",
        "FLU_A",
        "VSR",
    ]
]

flu = flu.melt(
    id_vars=[
        "epiyear",
        "epiweek",
    ],
    value_vars=[
        "FLU_A",
        "VSR",
    ],
    var_name="virus",
    value_name="cases",
)

covi = dados[
    (dados["epiyear"].isin([2023, 2024, 2025]))
    & (dados["DS_UF_SIGLA"] == "BR")
    & (dados["fx_etaria"] == "Total")
].copy()

covi = covi[
    [
        "epiyear",
        "epiweek",
        "SARS2",
    ]
]

covi = covi.melt(
    id_vars=[
        "epiyear",
        "epiweek",
    ],
    value_vars=[
        "SARS2",
    ],
    var_name="virus",
    value_name="cases",
)

virus = pd.concat(
    [
        flu,
        covi,
    ],
    ignore_index=True,
)

nomes_virus = {
    "FLU_A": "Influenza A",
    "VSR": "VSR",
    "SARS2": "SARS-CoV-2",
}

virus["virus2"] = (
    virus["virus"]
    .map(nomes_virus)
)

ORDEM_VIRUS = [
    "Influenza A",
    "VSR",
    "SARS-CoV-2",
]

fig, axes = plt.subplots(
    1,
    3,
    figsize=(
        30 / 2.54,
        10 / 2.54,
    ),
)

for ax, nome_virus in zip(
    axes,
    ORDEM_VIRUS,
):

    dados_virus = virus[
        virus["virus2"] == nome_virus
    ].copy()

    anos_virus = sorted(
        dados_virus["epiyear"]
        .unique()
    )

    for ano in anos_virus:

        dados_ano = (
            dados_virus[
                dados_virus["epiyear"] == ano
            ]
            .sort_values("epiweek")
        )

        ax.plot(
            dados_ano["epiweek"],
            dados_ano["cases"],
            linewidth=1.5,
            color=CORES_ANOS.get(
                ano,
                "#333333",
            ),
            label=str(ano),
        )

    ax.set_title(
        nome_virus,
        fontsize=12,
        fontweight="bold",
        pad=10,
    )

    ax.set_xlabel(
        "Semana epidemiológica",
        fontsize=10,
        fontweight="bold"
    )

    ax.set_facecolor("white")

    ax.grid(
        axis="y",
        color=COR_GRID,
        linewidth=0.8,
    )

    ax.grid(
        axis="x",
        visible=False,
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.tick_params(
        labelsize=9,
        colors=COR_TEXTO,
    )

    ax.autoscale(
        axis="y",
    )

axes[0].set_ylabel(
    "Casos de SRAG",
    fontsize=10,
    fontweight="bold"
)

handles = [
    Line2D([0], [0], color=cor, linewidth=1.5, label=str(ano))
    for ano, cor in CORES_ANOS.items()
]

fig.legend(
    handles=handles,
    labels=[str(ano) for ano in CORES_ANOS.keys()],
    title=None,
    loc="upper center",
    ncol=len(CORES_ANOS),
    frameon=False,
    bbox_to_anchor=(0.5, 1.05),
)

plt.tight_layout()

plt.savefig(
    "../figuras/plot_BR_SAZO.tiff",
    dpi=300,
    format="tiff",
    bbox_inches="tight",
)

plt.close()

srag = dados[
    (dados["epiyear"] >= 2016)
    & (dados["epiyear"] <= 2025)
    & (~dados["epiyear"].isin([2020, 2021, 2022]))
    & (dados["DS_UF_SIGLA"] == "BR")
    & (dados["fx_etaria"] == "Total")
].copy()

srag = srag[
    [
        "epiyear",
        "epiweek",
        "SRAG",
    ]
]

srag = srag.sort_values(
    [
        "epiyear",
        "epiweek",
    ]
)

anos = sorted(
    srag["epiyear"]
    .unique()
)

mapa_posicao_ano = {
    ano: i
    for i, ano in enumerate(anos)
}

srag["week_cont"] = (
    srag["epiweek"]
    + srag["epiyear"].map(
        mapa_posicao_ano
    ) * 53
)

breaks = (
    srag.groupby(
        "epiyear",
        as_index=False,
    )["week_cont"]
    .min()
)

divisao = (
    breaks.loc[breaks["epiyear"] == 2023, "week_cont",].iloc[0] - 0.5
)

ymax = srag["SRAG"].max()

fig, ax = plt.subplots(
    figsize=(
        40 / 2.54,
        15 / 2.54,
    ),
)

ax.plot(
    srag["week_cont"],
    srag["SRAG"],
    linewidth=0.8,
    color=COR_SRAG,
)

x_min = srag["week_cont"].min()

x_max = srag["week_cont"].max()

ax.hlines(
    y=ymax * 1.08,
    xmin=x_min,
    xmax=divisao,
    linewidth=0.8,
    color="black",
)

ax.hlines(
    y=ymax * 1.08,
    xmin=divisao,
    xmax=x_max,
    linewidth=0.8,
    color="black",
)

ax.vlines(
    x=divisao,
    ymin=ymax * 1.05,
    ymax=ymax * 1.11,
    linewidth=0.8,
    color="black",
)

ax.text(
    (x_min + divisao) / 2,
    ymax * 1.13,
    "Pré-pandemia da COVID-19",
    ha="center",
    va="bottom",
    fontsize=12,
    fontweight="bold",
)

ax.text(
    (divisao + x_max) / 2,
    ymax * 1.13,
    "Pós-pandemia",
    ha="center",
    va="bottom",
    fontsize=12,
    fontweight="bold",
)

ax.set_xticks(
    breaks["week_cont"]
)

ax.set_xticklabels(
    breaks["epiyear"]
)

ax.set_xlim(
    x_min - 1,
    x_max + 1,
)

ax.set_ylim(
    0,
    ymax * 1.18,
)

ax.set_xlabel(
    "Ano epidemiológico",
    fontsize=14,
    fontweight="bold"
)

ax.set_ylabel(
    "Casos de SRAG",
    fontsize=14,
    fontweight="bold"
)

ax.set_facecolor("white")

ax.grid(
    which="major",
    color=COR_GRID,
    linewidth=0.8,
)

ax.minorticks_off()

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.tick_params(
    labelsize=12,
    colors=COR_TEXTO,
)

plt.subplots_adjust(
    top=0.80,
)

plt.savefig(
    "../figuras/plot_BR_SRAG_serie.tiff",
    dpi=300,
    format="tiff",
    bbox_inches="tight",
)

plt.close()