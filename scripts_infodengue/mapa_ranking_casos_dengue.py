import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

## Fonte: InfoDengue
ARQUIVO = "dados/dengue_brasil_2023_2025.csv"
ARQUIVO_GEOJSON = "../scripts_infogripe/br.geojson"

ARQUIVO_SAIDA = "../figuras_infodengue/mapa_ranking_dengue_2023_2025.tiff"


df = pd.read_csv(ARQUIVO)

print(df.columns)
print(df.head())

df["data_iniSE"] = pd.to_datetime(df["data_iniSE"], errors="coerce")

df["SE"] = pd.to_numeric(df["SE"], errors="coerce")

df["municipio_geocodigo"] = pd.to_numeric(df["municipio_geocodigo"], errors="coerce")

df["casos"] = pd.to_numeric(df["casos"], errors="coerce")


df = df[df["data_iniSE"].dt.year.between(2023, 2025)].copy()

# Remove registros sem município ou casos
df = df.dropna(subset=["municipio_geocodigo", "casos"])

df["codigo_uf"] = (df["municipio_geocodigo"].astype(int).astype(str).str.zfill(7).str[:2])

mapa_uf = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}


df["uf"] = df["codigo_uf"].map(mapa_uf)


ufs_nao_reconhecidas = sorted(
    df.loc[df["uf"].isna(), "codigo_uf"]
    .dropna()
    .unique()
)

if ufs_nao_reconhecidas:
    print("ATENÇÃO: códigos de UF não reconhecidos:", ufs_nao_reconhecidas)


dados_estado = (
    df.dropna(subset=["uf"])
    .groupby("uf", as_index=False)["casos"]
    .sum()
)

dados_estado = dados_estado.rename(columns={"uf": "sigla", "casos": "casos_notificados"})


ranking = (
    dados_estado
    .sort_values(
        "casos_notificados",
        ascending=False
    )
    .reset_index(drop=True)
)

ranking["ranking"] = ranking.index + 1

print("\n" + "=" * 60)
print("RANKING DE CASOS NOTIFICADOS DE DENGUE — 2023–2025")
print("=" * 60)

print(ranking[["ranking", "sigla", "casos_notificados"]].to_string(index=False))


gdf = gpd.read_file(ARQUIVO_GEOJSON)

ranking["sigla"] = (
    ranking["sigla"]
    .astype(str)
    .str.upper()
    .str.strip()
)

gdf = gdf.merge(
    ranking,
    on="sigla",
    how="left"
)

cmap = LinearSegmentedColormap.from_list(
    "dengue",
    [
        "#BCD0FF",
        "#001F43"
    ]
)

fig, ax = plt.subplots(
    figsize=(10, 10)
)

gdf.plot(
    column="casos_notificados",
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

for _, row in gdf.iterrows():

    if row.geometry is None:
        continue

    ponto = row.geometry.representative_point()

    ax.text(
        ponto.x,
        ponto.y,
        row["sigla"],
        ha="center",
        va="center",
        fontsize=8,
        fontweight="bold",
        color="white"
    )


ax.set_axis_off()

plt.tight_layout()

plt.savefig(
    ARQUIVO_SAIDA,
    dpi=300,
    bbox_inches="tight"
)

print(f"\nMapa salvo em: {ARQUIVO_SAIDA}")