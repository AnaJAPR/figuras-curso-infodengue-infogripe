import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable

ANOS = [2023, 2024, 2025]

INFOGRIPE_URL = (
    "https://raw.githubusercontent.com/"
    "infogripe/Boletim_InfoGripe/main/"
    "Dados/InfoGripe/"
    "casos_semanais_fx_etaria_virus_sem_filtro_febre.csv"
)

POPULACAO_URL = (
    "https://ftp.ibge.gov.br/"
    "Projecao_da_Populacao/"
    "Projecao_da_Populacao_2024/"
    "projecoes_2024_tab1_idade_simples.xlsx"
)

GEOJSON_PATH = "br.geojson"
OUTPUT_PATH = "../figuras_infogripe/mapa_srag.tiff"

COR_CASOS_INICIAL = "#E3BEFA"
COR_CASOS_FINAL = "#BF42F2"

COR_INCIDENCIA_INICIAL = "#BCD0FF"
COR_INCIDENCIA_FINAL = "#0583F4"

cmap_casos = LinearSegmentedColormap.from_list(
    "casos", [COR_CASOS_INICIAL, COR_CASOS_FINAL]
)

cmap_incidencia = LinearSegmentedColormap.from_list(
    "incidencia", [COR_INCIDENCIA_INICIAL, COR_INCIDENCIA_FINAL]
)

pop = pd.read_excel(POPULACAO_URL, skiprows=5)

pop = pop[
    ~pop["LOCAL"].isin(
        ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", "Brasil"]
    )
]
pop = pop[pop["SEXO"] == "Ambos"]
pop = pop[["SIGLA", "IDADE", 2023, 2024, 2025]]

pop_br = (
    pop.groupby("SIGLA")[[2023, 2024, 2025]]
    .sum()
    .reset_index()
    .melt(
        id_vars="SIGLA",
        value_vars=[2023, 2024, 2025],
        var_name="epiyear",
        value_name="pop",
    )
)
pop_br["epiyear"] = pop_br["epiyear"].astype(int)
pop_br = pop_br.rename(columns={"SIGLA": "DS_UF_SIGLA"})

dados = pd.read_csv(INFOGRIPE_URL, sep=";")

df = dados[
    (dados["epiyear"].isin(ANOS))
    & (dados["DS_UF_SIGLA"] != "BR")
    & (dados["fx_etaria"] == "Total")
].copy()

df = (
    df.groupby(["DS_UF_SIGLA", "epiyear"], as_index=False)["SRAG"]
    .sum()
)

df = df.merge(pop_br, on=["DS_UF_SIGLA", "epiyear"], how="left")
df["i_srag"] = (df["SRAG"] / df["pop"]) * 100000

df = (
    df.groupby("DS_UF_SIGLA", as_index=False)
    .agg(SRAG=("SRAG", "sum"), inci=("i_srag", "mean"))
)

mapa = gpd.read_file(GEOJSON_PATH)

COLUNA_SIGLA_GEOJSON = "sigla"

mapa["DS_UF_SIGLA"] = mapa[COLUNA_SIGLA_GEOJSON]

summa_sf = mapa.merge(df, on="DS_UF_SIGLA", how="left")

centroides = summa_sf.copy()
centroides["centroide"] = centroides.geometry.representative_point()
centroides["x"] = centroides["centroide"].x
centroides["y"] = centroides["centroide"].y

fig, axes = plt.subplots(
    1, 2, figsize=(180 / 25.4, 100 / 25.4)
)

summa_sf.plot(
    column="SRAG",
    scheme="FisherJenks",
    k=5,
    cmap=cmap_casos,
    legend=False,
    ax=axes[0],
    edgecolor="white",
    linewidth=0.4,
    missing_kwds={"color": "lightgrey"},
)

for _, row in centroides.iterrows():
    if pd.notna(row["DS_UF_SIGLA"]):
        axes[0].annotate(
            row["DS_UF_SIGLA"],
            xy=(row["x"], row["y"]),
            ha="center",
            va="center",
            fontsize=4,
            color="black",
        )

axes[0].axis("off")

summa_sf.plot(
    column="inci",
    scheme="FisherJenks",
    k=5,
    cmap=cmap_incidencia,
    legend=False,
    ax=axes[1],
    edgecolor="white",
    linewidth=0.4,
    missing_kwds={"color": "lightgrey"},
)

for _, row in centroides.iterrows():
    if pd.notna(row["DS_UF_SIGLA"]):
        axes[1].annotate(
            row["DS_UF_SIGLA"],
            xy=(row["x"], row["y"]),
            ha="center",
            va="center",
            fontsize=4,
            color="black",
        )

axes[1].axis("off")

def add_cbar(ax, gdf, column, cmap, titulo):

    valores = gdf[column].dropna().values
    vmin, vmax = valores.min(), valores.max()

    norm = Normalize(vmin=vmin, vmax=vmax)
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    cax = ax.inset_axes([0.76, 0.06, 0.20, 0.02])

    cbar = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(labelsize=4, length=1.5)
    cbar.set_label(titulo, fontsize=4, fontweight="bold", labelpad=1)

    return cbar


add_cbar(axes[0], summa_sf, "SRAG", cmap_casos, "Número de casos")
add_cbar(axes[1], summa_sf, "inci", cmap_incidencia,
         "Incidência média\npor 100 mil hab")

plt.tight_layout()

plt.savefig(
    OUTPUT_PATH,
    dpi=300,
    format="tiff",
    bbox_inches="tight",
)

plt.close()