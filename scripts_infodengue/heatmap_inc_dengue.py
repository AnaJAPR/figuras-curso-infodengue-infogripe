import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# dados do infodengue
ARQUIVO = "dados_heatmap.csv"

ANO_INICIAL = 2010
ANO_FINAL = 2025

COLUNA_CAPITAL = "municipio_nome"
COLUNA_SE = "SE"
COLUNA_INCIDENCIA = "p_inc100k"

try:
    df = pd.read_csv(
        ARQUIVO,
        encoding="utf-8"
    )

except UnicodeDecodeError:
    df = pd.read_csv(
        ARQUIVO,
        encoding="latin1"
    )

print(df.columns)

df[COLUNA_SE] = pd.to_numeric(
    df[COLUNA_SE],
    errors="coerce"
)

df[COLUNA_INCIDENCIA] = pd.to_numeric(
    df[COLUNA_INCIDENCIA],
    errors="coerce"
)

df["ano"] = (
    df[COLUNA_SE]
    .floordiv(100)
    .astype("Int64")
)

df["semana"] = (
    df[COLUNA_SE]
    .mod(100)
    .astype("Int64")
)

df = df[
    df["ano"].between(
        ANO_INICIAL,
        ANO_FINAL
    )
].copy()

df = df[
    df["semana"].between(
        1,
        53
    )
].copy()


df = df.dropna(
    subset=[
        COLUNA_CAPITAL,
        "semana",
        COLUNA_INCIDENCIA
    ]
)

ordem_capitais = (
    df[COLUNA_CAPITAL]
    .drop_duplicates()
    .tolist()
)

heatmap = (
    df
    .groupby(
        [
            COLUNA_CAPITAL,
            "semana"
        ],
        as_index=False
    )[COLUNA_INCIDENCIA]
    .mean()
)

matriz = heatmap.pivot(
    index=COLUNA_CAPITAL,
    columns="semana",
    values=COLUNA_INCIDENCIA
)

matriz = matriz.reindex(
    columns=range(1, 54)
)

matriz = matriz.reindex(
    ordem_capitais
)

cmap = LinearSegmentedColormap.from_list(
    "dengue",
    [
        "#BCD0FF",
        "#001F43"
    ]
)

fig, ax = plt.subplots(
    figsize=(18, 9)
)


im = ax.imshow(
    matriz.values,
    aspect="auto",
    cmap=cmap,
    interpolation="nearest"
)

meses = [
    "Jan",
    "Mar",
    "Jun",
    "Set",
    "Dez"
]

semanas_meses = [
    1,
    9,
    22,
    35,
    48
]

ax.set_xticks(
    np.array(semanas_meses) - 1
)

ax.set_xticklabels(
    meses,
    fontsize=10
)

for semana in semanas_meses[1:]:
    ax.axvline(
        semana - 0.5,
        color="black",
        linestyle="--",
        linewidth=1,
        alpha=0.8
    )

ax.set_yticks(
    np.arange(len(matriz.index))
)

ax.set_yticklabels(
    matriz.index,
    fontsize=9
)

ax.set_ylabel(
    "Capital",
    fontsize=11
)

ax.set_title(
    "Sazonalidade da dengue",
    fontsize=12,
    fontweight="bold",
    color="#4A4A4A",
    loc="left",
    x=0.0,
    pad=8
)

cbar = fig.colorbar(
    im,
    ax=ax,
    pad=0.02
)

cbar.set_label(
    "Incidência semanal média (por 100 mil habitantes)",
    fontsize=10
)

cbar.ax.tick_params(
    labelsize=9
)

ax.tick_params(
    axis="both",
    length=0
)

plt.tight_layout()

plt.savefig(
    "../figuras_infodengue/heatmap_incidencia_dengue_2010_2025.tiff",
    dpi=300,
    bbox_inches="tight"
)

plt.close()