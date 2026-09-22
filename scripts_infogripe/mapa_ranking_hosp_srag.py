import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


# https://github.com/infogripe/Boletim_InfoGripe/blob/main/Dados/InfoGripe/casos_semanais_fx_etaria_virus_sem_filtro_febre.csv
ARQUIVO = "casos_semanais_fx_etaria_virus_sem_filtro_febre.csv"

ARQUIVO_GEOJSON = "br.geojson"


df = pd.read_csv(ARQUIVO, sep=";")

df = df[df["Ano epidemiológico"].between(2023, 2025)].copy()

df = df[df["DS_UF_SIGLA"] != "BR"].copy()

df["SRAG"] = pd.to_numeric(df["SRAG"], errors="coerce")

dados_estado = (df.groupby("DS_UF_SIGLA", as_index=False)["SRAG"].sum())


dados_estado = dados_estado.rename(
    columns={
        "DS_UF_SIGLA": "sigla",
        "SRAG": "hospitalizacoes"
    }
)

ranking = (
    dados_estado
    .sort_values(
        "hospitalizacoes",
        ascending=False
    )
    .reset_index(drop=True)
)


ranking["ranking"] = (ranking.index + 1)


# EXIBINDO RANKING NO TERMINAL

print()
print("=" * 60)
print("RANKING DE HOSPITALIZAÇÕES POR SRAG")
print("BRASIL — 2023 A 2025")
print("=" * 60)

print(
    ranking[
        [
            "ranking",
            "sigla",
            "hospitalizacoes"
        ]
    ].to_string(index=False)
)

brasil = gpd.read_file(ARQUIVO_GEOJSON)

possiveis_colunas = [
    "sigla",
    "SIGLA",
    "UF",
    "uf",
    "SG_UF",
    "SG_UF_NOT"
]

COLUNA_SIGLA = None

for coluna in possiveis_colunas:

    if coluna in brasil.columns:

        COLUNA_SIGLA = coluna
        break


if COLUNA_SIGLA is None:

    raise ValueError(
        "Não foi encontrada a coluna de sigla no "
        "br.geojson.\n\n"
        "Colunas encontradas:\n"
        + "\n".join(brasil.columns.astype(str))
    )

brasil[COLUNA_SIGLA] = (
    brasil[COLUNA_SIGLA]
    .astype(str)
    .str.upper()
    .str.strip()
)

brasil = brasil.merge(
    dados_estado,
    left_on=COLUNA_SIGLA,
    right_on="sigla",
    how="left"
)

cmap = LinearSegmentedColormap.from_list(
    "srag",
    [
        "#BCD0FF",
        "#001F43"
    ]
)

fig, ax = plt.subplots(figsize=(10, 10))

brasil.plot(
    column="hospitalizacoes",
    cmap=cmap,
    linewidth=0.7,
    edgecolor="white",
    ax=ax,
    legend=False,
    missing_kwds={
        "color": "#E6E6E6",
        "edgecolor": "white"
    }
)

for _, estado in brasil.iterrows():

    if pd.isna(estado["hospitalizacoes"]):
        continue

    sigla = estado["sigla"]

    ponto = estado.geometry.representative_point()

    ax.text(
        ponto.x,
        ponto.y,
        sigla,
        fontsize=7,
        fontweight="bold",
        color="white",
        ha="center",
        va="center"
    )

vmin = dados_estado["hospitalizacoes"].min()
vmax = dados_estado["hospitalizacoes"].max()

norm = plt.Normalize(
    vmin=vmin,
    vmax=vmax
)

sm = plt.cm.ScalarMappable(
    cmap=cmap,
    norm=norm
)

sm.set_array([])


cbar = fig.colorbar(
    sm,
    ax=ax,
    fraction=0.035,
    pad=0.02
)


cbar.set_label(
    "Hospitalizações por SRAG (2023-2025)",
    fontsize=10
)

cbar.ax.tick_params(
    labelsize=9
)

ax.set_axis_off()

plt.tight_layout()

plt.savefig(
    "../figuras_infogripe/mapa_ranking_srag_2023_2025.tiff",
    dpi=300,
    bbox_inches="tight"
)