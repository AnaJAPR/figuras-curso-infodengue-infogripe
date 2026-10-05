import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


arquivos = [
    "dados/RJ_dengue.parquet",
    "dados/MG_dengue.parquet",
    "dados/SP_dengue.parquet",
    "dados/BA_dengue.parquet"
]

ANO_INICIAL = 2010
ANO_FINAL = 2025

estados = ["RJ", "MG", "SP", "BA"]

CORES = {
    "RJ": "#9122BA",
    "MG": "#F36900",
    "SP": "#537A22",
    "BA": "#0583F4",
}


dfs = []

for arquivo in arquivos:
    print(f"Lendo: {arquivo}")

    df = pd.read_parquet(arquivo)

    df = df.reset_index()

    estado = Path(arquivo).stem.split("_")[0]

    df["estado"] = estado

    dfs.append(df)


dados = pd.concat(dfs, ignore_index=True)


dados["data_iniSE"] = pd.to_datetime(
    dados["data_iniSE"],
    errors="coerce"
)

dados = dados.dropna(subset=["data_iniSE"])

dados["ano"] = dados["data_iniSE"].dt.year


dados = dados[
    (dados["ano"] >= ANO_INICIAL)
    & (dados["ano"] <= ANO_FINAL)
].copy()


serie = (
    dados
    .groupby(
        ["ano", "estado"],
        as_index=False
    )["casos"]
    .sum()
)


anos = range(ANO_INICIAL, ANO_FINAL + 1)

indice_completo = pd.MultiIndex.from_product(
    [anos, estados],
    names=["ano", "estado"]
)

serie = (
    serie
    .set_index(["ano", "estado"])
    .reindex(
        indice_completo,
        fill_value=0
    )
    .reset_index()
)

serie = serie.sort_values(["ano", "estado"])


print("\nSérie temporal:")

print(serie.to_string(index=False))


plt.figure(figsize=(12, 6))

for estado in estados:

    dados_estado = serie[
        serie["estado"] == estado
    ]

    plt.plot(
        dados_estado["ano"],
        dados_estado["casos"],
        color=CORES[estado],
        linewidth=2,
        markersize=5,
        label=estado
    )


plt.xlabel("Ano")

plt.ylabel("Casos notificados")

plt.title("Casos notificados de dengue — RJ, MG, SP e BA (2010–2025)")

plt.xticks(list(anos), rotation=45)

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.4
)

plt.legend(title="Estado")

plt.tight_layout()


saida_figura = Path("../figuras_infodengue/serie_temporal_dengue_RJ_MG_SP_BA_2010_2025.png")

plt.savefig(
    saida_figura,
    dpi=300,
    bbox_inches="tight"
)

print(f"\nImagem salva em: {saida_figura}")


saida_csv = Path("dados/serie_temporal_dengue_RJ_MG_SP_BA_2010_2025.csv")

serie.to_csv(saida_csv, index=False)

print(f"Dados salvos em: {saida_csv}")