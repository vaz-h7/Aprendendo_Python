import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Controle Financeiro Real-Time")


# --- FUNÇÃO PARA CARREGAR DADOS ---
@st.cache_data(ttl=60)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]

    # Lógica Híbrida: Nuvem (Secrets) ou Local (Arquivo)
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception:
        try:
            creds = Credentials.from_service_account_file("Projetos Pessoais/credentials.json", scopes=scope)
        except:
            creds = Credentials.from_service_account_file("credentials.json", scopes=scope)

    client = gspread.authorize(creds)
    spreadsheet = client.open("Controle Financeiro Mensal com Gráficos")
    sheet = spreadsheet.worksheet("Controle de Gastos")

    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # 1. Limpeza da coluna Valor (Converte R$ para número)
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

    # 2. Tratamento rigoroso de DATAS
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data'])  # Remove o que não for data válida (limpa o 'nan')
        df['Mes_Ano'] = df['Data'].dt.strftime('%Y-%m')

    return df


# --- INTERFACE DO DASHBOARD ---
try:
    df = load_data()

    if df.empty:
        st.warning("Aguardando dados válidos na planilha (verifique a coluna Data).")
    else:
        st.title("📊 Meu Dashboard Financeiro")

        # --- SIDEBAR (FILTROS) ---
        st.sidebar.header("Configurações de Filtro")

        # Filtro de Mês/Ano para as Métricas e Pizza
        lista_meses = sorted(df['Mes_Ano'].unique().tolist(), reverse=True)
        mes_selecionado = st.sidebar.selectbox("Mês de análise detalhada", lista_meses)

        # Filtro de Categoria
        lista_cat = sorted([c for c in df["Categoria"].unique().tolist() if c])
        cat_escolhidas = st.sidebar.multiselect("Filtrar Categorias", lista_cat, default=lista_cat)

        # --- PREPARAÇÃO DOS DADOS FILTRADOS ---
        df_mes = df[df['Mes_Ano'] == mes_selecionado]
        df_filtrado = df_mes[df_mes["Categoria"].isin(cat_escolhidas)]

        # --- MÉTRICAS DO MÊS ---
        col_tipo = "Tipo (Entrada/Saída)"
        entradas = df_mes[df_mes[col_tipo] == "ENTRADA"]["Valor"].sum()
        saidas = df_mes[df_mes[col_tipo] == "SAÍDA"]["Valor"].sum()
        saldo = entradas - saidas

        m1, m2, m3 = st.columns(3)
        m1.metric(f"Entradas ({mes_selecionado})", f"R$ {entradas:,.2f}")
        m2.metric(f"Saídas ({mes_selecionado})", f"R$ {saidas:,.2f}")
        m3.metric("Saldo Mensal", f"R$ {saldo:,.2f}", delta=f"{saldo:,.2f}")

        st.divider()

        # --- GRÁFICO 1: EVOLUÇÃO DIA A DIA (Histórico Real) ---
        st.subheader("📈 Evolução Financeira (Datas Reais da Planilha)")

        # Aqui agrupamos pela DATA exata para o gráfico não ficar travado no dia 1º
        df_evolucao_real = df.groupby(['Data', col_tipo])['Valor'].sum().reset_index()

        fig_evolucao = px.line(
            df_evolucao_real,
            x='Data',
            y='Valor',
            color=col_tipo,
            markers=True,
            color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"},
            labels={"Data": "Dia da Transação", "Valor": "Valor (R$)"},
            template="plotly_dark"
        )
        # Melhora a exibição das datas no eixo X
        fig_evolucao.update_xaxes(tickformat="%d/%m/%y", dtick="D1")
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # --- GRÁFICOS DO MÊS SELECIONADO ---
        c1, c2 = st.columns(2)

        with c1:
            st.subheader(f"Gastos por Categoria ({mes_selecionado})")
            fig_pizza = px.pie(
                df_filtrado[df_filtrado[col_tipo] == "SAÍDA"],
                values="Valor",
                names="Categoria",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.T10
            )
            st.plotly_chart(fig_pizza, use_container_width=True)

        with c2:
            st.subheader(f"Entradas vs Saídas ({mes_selecionado})")
            fig_bar = px.bar(
                df_mes.groupby(col_tipo)["Valor"].sum().reset_index(),
                x=col_tipo,
                y="Valor",
                color=col_tipo,
                color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- TABELA DE CONFERÊNCIA ---
        with st.expander("🔍 Visualizar lista de lançamentos deste mês"):
            st.dataframe(df_filtrado.sort_values("Data", ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")