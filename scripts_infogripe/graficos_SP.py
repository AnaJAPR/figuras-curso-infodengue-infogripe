import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ANOS_ANALISE = [
    2018,
    2019,
    2023,
]

INFOGRIPE_URL = (
    "https://raw.githubusercontent.com/"
    "infogripe/Boletim_InfoGripe/main/"
    "Dados/InfoGripe/"
    "casos_semanais_fx_etaria_virus_sem_filtro_febre.csv"
)

POP_URL = (
    "https://ftp.ibge.gov.br/"
    "Projecao_da_Populacao/"
    "Projecao_da_Populacao_2024/"
    "projecoes_2024_tab1_idade_simples.xlsx"
)

COR_LINHA = "#F36900"
COR_BARRAS = "#D087F7"

COR_GRID = "#D9D9D9"
COR_TEXTO = "#5F6368"

MESES = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}


def epiweek_para_mes(epiyear, epiweek):
    try:
        data = pd.to_datetime(
            f"{int(epiyear)}-W{int(epiweek):02d}-1",
            format="%G-W%V-%u",
        )
        return data.month
    except ValueError:
        return None


def extrair_inicio_faixa(faixa):

    faixa = str(faixa).strip()

    if faixa.startswith("<"):
        return 0

    numeros = re.findall(r"\d+", faixa)

    if numeros:
        return int(numeros[0])

    return 999


def teto_simples(valores, folga=1.1):

    maximo = valores.max() * folga

    if maximo <= 10:
        return 10
    elif maximo <= 50:
        return int(np.ceil(maximo / 10) * 10)
    elif maximo <= 100:
        return int(np.ceil(maximo / 20) * 20)
    elif maximo <= 500:
        return int(np.ceil(maximo / 50) * 50)
    elif maximo <= 1000:
        return int(np.ceil(maximo / 100) * 100)
    elif maximo <= 5000:
        return int(np.ceil(maximo / 500) * 500)
    else:
        return int(np.ceil(maximo / 1000) * 1000)


def estilizar_grafico_linha(ax):
    ax.set_facecolor("white")

    ax.grid(axis="y", color=COR_GRID, linewidth=0.8)
    ax.grid(axis="x", visible=False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.spines["bottom"].set_color(COR_GRID)
    ax.spines["bottom"].set_linewidth(0.8)

    ax.tick_params(
        axis="both",
        colors=COR_TEXTO,
        labelsize=9,
        length=0,
    )


def estilizar_grafico_barras(ax):
    ax.set_facecolor("white")

    ax.grid(axis="y", color=COR_GRID, linewidth=0.8, zorder=0)
    ax.grid(axis="x", visible=False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.spines["bottom"].set_color(COR_GRID)

    ax.tick_params(
        axis="both",
        colors=COR_TEXTO,
        length=0,
    )


dados = pd.read_csv(
    INFOGRIPE_URL,
    sep=";",
    low_memory=False,
)

pop = pd.read_excel(
    POP_URL,
    skiprows=5,
)

pop_sp = (
    pop[
        (pop["SIGLA"] == "SP")
        & (pop["SEXO"] == "Ambos")
    ]
    .groupby("SIGLA", as_index=False)[ANOS_ANALISE]
    .sum()
)

pop_sp = pop_sp.melt(
    id_vars="SIGLA",
    var_name="epiyear",
    value_name="populacao",
)

pop_sp["epiyear"] = pop_sp["epiyear"].astype(int)


df_linha = dados[
    (dados["DS_UF_SIGLA"] == "SP")
    & (dados["epiyear"].isin(ANOS_ANALISE))
    & (dados["fx_etaria"] == "Total")
].copy()

df_linha["mes_numero"] = df_linha.apply(
    lambda linha: epiweek_para_mes(
        linha["epiyear"],
        linha["epiweek"],
    ),
    axis=1,
)

df_linha = df_linha.dropna(subset=["mes_numero"]).copy()
df_linha["mes_numero"] = df_linha["mes_numero"].astype(int)

casos_mensais = (
    df_linha.groupby(
        ["epiyear", "mes_numero"],
        as_index=False,
    )["SRAG"]
    .sum()
)

casos_mensais = casos_mensais.merge(
    pop_sp[["epiyear", "populacao"]],
    on="epiyear",
    how="left",
)

casos_mensais["incidencia"] = (
    casos_mensais["SRAG"]
    * 100000
    / casos_mensais["populacao"]
)

fig, axes = plt.subplots(
    1,
    len(ANOS_ANALISE),
    figsize=(30 / 2.54, 10 / 2.54),
)

if len(ANOS_ANALISE) == 1:
    axes = [axes]

for ax, ano in zip(axes, ANOS_ANALISE):

    dados_ano = (
        casos_mensais[casos_mensais["epiyear"] == ano]
        .sort_values("mes_numero")
    )

    ax.plot(
        dados_ano["mes_numero"],
        dados_ano["incidencia"],
        color=COR_LINHA,
        linewidth=1.0,
        alpha=0.75,
        zorder=2,
    )

    ax.scatter(
        dados_ano["mes_numero"],
        dados_ano["incidencia"],
        color=COR_LINHA,
        s=14,
        zorder=3,
    )

    letra = chr(65 + list(ANOS_ANALISE).index(ano))

    ax.set_title(
        f"{letra}.",
        fontsize=12,
        fontweight="bold",
        color="#4A4A4A",
        loc="left",
        pad=12,
    )

    ax.set_xlabel(
        "Mês",
        fontsize=10,
        fontweight="bold",
        color=COR_TEXTO,
        labelpad=15,
    )

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(
        [MESES[i] for i in range(1, 13)],
        rotation=45,
        ha="right",
    )

    ax.set_xlim(0.5, 12.5)

    maximo = dados_ano["incidencia"].max()
    teto_ano = maximo * 1.10
    ax.set_ylim(0, teto_ano)

    estilizar_grafico_linha(ax)

axes[0].set_ylabel(
    "Incidência de SRAG\n(por 100 mil habitantes)",
    fontsize=10,
    fontweight="bold",
    color=COR_TEXTO,
    labelpad=12,
)

plt.subplots_adjust(wspace=0.35)

plt.savefig(
    "../figuras_infogripe/plot_mes_SP.tiff",
    dpi=300,
    format="tiff",
    bbox_inches="tight",
)

plt.close()


sub_fx = dados[
    (dados["DS_UF_SIGLA"] == "SP")
    & (dados["fx_etaria"] != "Total")
    & (dados["epiyear"].isin(ANOS_ANALISE))
].copy()

sub_fx = (
    sub_fx.groupby(
        ["epiyear", "fx_etaria"],
        as_index=False,
    )["SRAG"]
    .sum()
)

faixas_existentes = sub_fx["fx_etaria"].unique()

ordem_final = sorted(
    faixas_existentes,
    key=extrair_inicio_faixa,
)

sub_fx["fx_etaria"] = pd.Categorical(
    sub_fx["fx_etaria"],
    categories=ordem_final,
    ordered=True,
)

fig, axes = plt.subplots(
    1,
    len(ANOS_ANALISE),
    figsize=(40 / 2.54, 15 / 2.54),
)

if len(ANOS_ANALISE) == 1:
    axes = [axes]

TETO_BARRAS = teto_simples(sub_fx["SRAG"])

for ax, ano in zip(axes, ANOS_ANALISE):

    dados_ano = (
        sub_fx[sub_fx["epiyear"] == ano]
        .sort_values("fx_etaria")
    )

    ax.bar(
        dados_ano["fx_etaria"],
        dados_ano["SRAG"],
        color=COR_BARRAS,
        edgecolor="none",
        zorder=3,
    )

    letra = chr(65 + list(ANOS_ANALISE).index(ano))

    ax.set_title(
        f"{letra}.",
        fontsize=12,
        fontweight="bold",
        color="#4A4A4A",
        loc="left",
        pad=12,
    )

    ax.set_xlabel(
        "Faixa etária",
        fontsize=14,
        fontweight="bold",
        color=COR_TEXTO,
        labelpad=12,
    )

    ax.tick_params(
        axis="x",
        labelrotation=45,
        labelsize=10,
    )

    ax.tick_params(
        axis="y",
        labelsize=10,
    )

    estilizar_grafico_barras(ax)

    teto_ano = teto_simples(dados_ano["SRAG"])
    ax.set_ylim(0, teto_ano)

axes[0].set_ylabel(
    "Casos",
    fontsize=14,
    fontweight="bold",
    color=COR_TEXTO,
    labelpad=12,
)

plt.subplots_adjust(wspace=0.25)

plt.savefig(
    "../figuras_infogripe/plot_SP_fx_etaria.tiff",
    dpi=300,
    format="tiff",
    bbox_inches="tight",
)

plt.close()