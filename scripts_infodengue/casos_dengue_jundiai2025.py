import pandas as pd
import matplotlib.pyplot as plt

ARQUIVO = "dados_3525904.parquet"

ANO = 2025

CODIGO_JUNDIAI = 3525904

CID_DENGUE = "A90"

COR = "#5F137B"

MESES = [
    "Jan", "Fev", "Mar", "Abr",
    "Mai", "Jun", "Jul", "Ago",
    "Set", "Out", "Nov", "Dez"
]

df = pd.read_parquet(ARQUIVO)

df = df[
    df["cid10_codigo"] == CID_DENGUE
].copy()

df = df[
    df["municipio_geocodigo"] == CODIGO_JUNDIAI
].copy()

### Gráfico de casos de dengue em Jundiaí por mês (2025)
# Data utilizada: dt_sin_pri = data dos primeiros sintomas

df["dt_sin_pri"] = pd.to_datetime(
    df["dt_sin_pri"],
    errors="coerce"
)

df = df[
    df["dt_sin_pri"].dt.year == ANO
].copy()

def configurar_grafico(ax):

    ax.grid(
        axis="y",
        linestyle="--",
        alpha=0.3
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

#

df["mes"] = df["dt_sin_pri"].dt.month

casos_mes = (
    df["mes"]
    .value_counts()
    .reindex(range(1, 13), fill_value=0)
)

fig, ax = plt.subplots(
    figsize=(10, 6)
)

ax.plot(
    MESES,
    casos_mes.values,
    marker="o",
    linewidth=2,
    color=COR,
    solid_capstyle="round",
    solid_joinstyle="round"
)

ax.set_title(
    "Gráfico 3: Casos de dengue em Jundiaí por mês (2025). Fonte: InfoDengue.",
    fontsize=12,
    fontweight="bold",
    loc="left",
    pad=12
)

ax.set_xlabel("Mês")
ax.set_ylabel("Número de casos")

configurar_grafico(ax)

plt.tight_layout()

plt.savefig(
    "../figuras_infodengue/dengue_jundiai_mes_2025.tiff",
    dpi=300,
    bbox_inches="tight"
)

### Gráfico de casos de dengue em Jundiaí por faixa etária (2025)

df["nu_idade_n"] = pd.to_numeric(
    df["nu_idade_n"],
    errors="coerce"
)

df_idade = df[
    df["nu_idade_n"].notna()
].copy()

df_idade["unidade_idade"] = (
    df_idade["nu_idade_n"]
    .astype(int)
    .astype(str)
    .str[0]
)

df_idade = df_idade[
    df_idade["unidade_idade"] == "4"
].copy()

df_idade["idade_anos"] = (
    df_idade["nu_idade_n"]
    .astype(int)
    % 1000
)

df_idade = df_idade[
    (df_idade["idade_anos"] >= 0)
    & (df_idade["idade_anos"] <= 120)
].copy()

bins = [
    -1,
    4,
    9,
    14,
    19,
    29,
    39,
    49,
    59,
    69,
    79,
    float("inf")
]

labels = [
    "0–4",
    "5–9",
    "10–14",
    "15–19",
    "20–29",
    "30–39",
    "40–49",
    "50–59",
    "60–69",
    "70–79",
    "80+"
]


df_idade["faixa_etaria"] = pd.cut(
    df_idade["idade_anos"],
    bins=bins,
    labels=labels
)

casos_idade = (
    df_idade["faixa_etaria"]
    .value_counts()
    .reindex(
        labels,
        fill_value=0
    )
)

fig, ax = plt.subplots(
    figsize=(10, 6)
)

ax.bar(
    casos_idade.index,
    casos_idade.values,
    color=COR,
    width=0.7
)

ax.set_title(
    "Gráfico 5: Casos de dengue em Jundiaí por faixa etária (2025). Fonte: InfoDengue",
    fontsize=12,
    fontweight="bold",
    loc="left",
    pad=12
)

ax.set_xlabel("Faixa etária (anos)")
ax.set_ylabel("Número de casos")

configurar_grafico(ax)

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    "../figuras_infodengue/dengue_jundiai_idade_2025.tiff",
    dpi=300,
    bbox_inches="tight"
)


### Gráfico de casos de dengue em Jundiaí por sexo (2025)

df["sexo"] = (
    df["cs_sexo"]
    .astype("string")
    .str.strip()
    .str.upper()
)

df_sexo = df[
    df["sexo"].isin(["F", "M"])
].copy()

dados_sexo = (
    df_sexo["sexo"]
    .value_counts()
    .reindex(["F", "M"], fill_value=0)
)

cores_sexo = {
    "F": "#D087F7",
    "M": "#5F137B"
}

valores = dados_sexo.values

fig, ax = plt.subplots(
    figsize=(7, 7)
)

cores = [
    cores_sexo[sexo]
    for sexo in dados_sexo.index
]


wedges, textos, autotextos = ax.pie(
    valores,
    colors=cores,
    startangle=110,
    counterclock=False,
    autopct="%1.1f%%",
    wedgeprops={
        "edgecolor": "white",
        "linewidth": 1
    }
)

for i, texto in enumerate(autotextos):

    if dados_sexo.index[i] == "M":
        texto.set_color("white")
    else:
        texto.set_color("black")

ax.set_title(
    "Gráfico 4: Casos de dengue em Jundiaí por sexo (2025). Fonte: InfoDengue.",
    fontsize=12,
    fontweight="bold",
    loc="left",
    pad=6
)

handles = [
    plt.Rectangle(
        (0, 0),
        1,
        1,
        facecolor=cores_sexo["F"]
    ),
    plt.Rectangle(
        (0, 0),
        1,
        1,
        facecolor=cores_sexo["M"]
    )
]


ax.legend(
    handles,
    ["Feminino", "Masculino"],
    loc="upper center",
    bbox_to_anchor=(0.5, 0.05),
    ncol=2,
    frameon=False,
    handlelength=0.8,
    handleheight=0.8,
    columnspacing=1.5,
    fontsize=14
)


plt.tight_layout()

plt.savefig(
    "../figuras_infodengue/dengue_jundiai_sexo_2025.tiff",
    dpi=300,
    bbox_inches="tight"
)