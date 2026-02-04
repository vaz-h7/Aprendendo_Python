import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Dashboard Financeiro")


# --- FUNÇÃO PARA CARREGAR DADOS ---
@st.cache_data(ttl=60)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]

    # Tenta carregar as credenciais (Híbrido: Nuvem ou Local)
    try:
        # 1. Tenta usar os Secrets do Streamlit Cloud
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception:
        # 2. Se falhar, tenta usar o arquivo local no seu PC
        try:
            creds = Credentials.from_service_account_file("Projetos Pessoais/credentials.json", scopes=scope)
        except:
            creds = Credentials.from_service_account_file("credentials.json", scopes=scope)

    client = gspread.authorize(creds)

    # Abre a planilha e a aba exata
    spreadsheet = client.open("Controle Financeiro Mensal com Gráficos")
    sheet = spreadsheet.worksheet("Controle de Gastos")

    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Limpeza da coluna Valor (converte R$ para número)
    if 'Valor' in df.columns:
        df['Valor'] = (
            df['Valor']
            .astype(str)
            .str.replace('R$', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)

    return df


# --- INTERFACE DO DASHBOARD ---
try:
    df = load_data()

    if df.empty:
        st.warning("A aba 'Controle de Gastos' foi encontrada, mas está sem dados.")
    else:
        st.title("📊 Meu Dashboard Financeiro")
        st.markdown(f"Status: **Conectado com sucesso!**")

        # --- FILTROS ---
        st.sidebar.header("Filtros")
        lista_cat = [c for c in df["Categoria"].unique().tolist() if c]
        escolha = st.sidebar.multiselect("Selecione as Categorias", lista_cat, default=lista_cat)

        df_filtrado = df[df["Categoria"].isin(escolha)]

        # --- MÉTRICAS ---
        col_tipo = "Tipo (Entrada/Saída)"
        entradas = df_filtrado[df_filtrado[col_tipo] == "ENTRADA"]["Valor"].sum()
        saidas = df_filtrado[df_filtrado[col_tipo] == "SAÍDA"]["Valor"].sum()
        saldo = entradas - saidas

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", f"R$ {entradas:,.2f}")
        c2.metric("Total Saídas", f"R$ {saidas:,.2f}")
        c3.metric("Saldo Real", f"R$ {saldo:,.2f}")

        st.divider()

        # --- LOGICA DE DATAS (Adicione após carregar o df) ---
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df['Mes_Ano'] = df['Data'].dt.strftime('%Y-%m')  # Cria uma coluna "2026-02"

        # --- FILTRO DE MÊS NA SIDEBAR ---
        meses_disponiveis = sorted(df['Mes_Ano'].unique().tolist())
        mes_selecionado = st.sidebar.selectbox("Selecione o Mês para análise detalhada", meses_disponiveis)

        # Filtra os dados para o dashboard principal
        df_mes = df[df['Mes_Ano'] == mes_selecionado]

        # --- NOVO GRÁFICO: EVOLUÇÃO MENSAL (Comparações) ---
        st.subheader("Comparação Mensal: Entradas vs Saídas")
        df_evolucao = df.groupby(['Mes_Ano', 'Tipo (Entrada/Saída)'])['Valor'].sum().reset_index()
        fig_evolucao = px.line(df_evolucao, x='Mes_Ano', y='Valor', color='Tipo (Entrada/Saída)', markers=True)
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # --- GRÁFICOS ---
        col_esq, col_dir = st.columns(2)

        with col_esq:
            st.subheader("Gastos por Categoria")
            fig_pizza = px.pie(
                df_filtrado[df_filtrado[col_tipo] == "SAÍDA"],
                values="Valor",
                names="Categoria",
                hole=0.4
            )
            st.plotly_chart(fig_pizza, use_container_width=True)

        with col_dir:
            st.subheader("Entradas vs Saídas")
            fig_bar = px.bar(
                df_filtrado.groupby(col_tipo)["Valor"].sum().reset_index(),
                x=col_tipo,
                y="Valor",
                color=col_tipo,
                color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- TABELA ---
        with st.expander("Ver dados brutos"):
            st.dataframe(df_filtrado, use_container_width=True)

except Exception as e:
    st.error("Erro ao carregar o dashboard.")
    st.info(f"Detalhe técnico: {e}")