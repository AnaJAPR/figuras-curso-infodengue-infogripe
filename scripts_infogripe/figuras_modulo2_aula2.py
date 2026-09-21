import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
    "../figuras_infogripe/grafico1_inc_mg_2026.png",
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
    "../figuras_infogripe/Limiares_SRAG_desafio_TELA1.png",
    dpi=300,
    bbox_inches="tight"
)