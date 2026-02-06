import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Controle Financeiro Real-Time")


@st.cache_data(ttl=60)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)

    client = gspread.authorize(creds)
    spreadsheet = client.open("Controle Financeiro Mensal com Gráficos")
    sheet = spreadsheet.worksheet("Controle de Gastos")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if 'Valor' in df.columns:
        df['Valor'] = (
            df['Valor']
            .astype(str)
            .str.replace('R$', '', regex=False)
            .str.replace(' ', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)

    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data']).sort_values('Data')
        df['Mes_Ano'] = df['Data'].dt.strftime('%Y-%m')
        df['Mes_Ano_Exibicao'] = df['Data'].dt.strftime('%m/%Y')

    return df


try:
    df = load_data()

    if df.empty:
        st.warning("Aguardando dados válidos na planilha.")
    else:
        st.title("📊 Meu Dashboard Financeiro")

        # --- SIDEBAR ---
        st.sidebar.header("Configurações de Filtro")
        df_meses = df[['Mes_Ano_Exibicao', 'Mes_Ano']].drop_duplicates().sort_values('Mes_Ano', ascending=False)
        lista_exibicao = df_meses['Mes_Ano_Exibicao'].tolist()
        mes_visual = st.sidebar.selectbox("Mês de análise detalhada", lista_exibicao)
        mes_selecionado = df_meses.loc[df_meses['Mes_Ano_Exibicao'] == mes_visual, 'Mes_Ano'].values[0]

        ver_tudo = st.sidebar.checkbox("Visualizar todo o histórico", value=True)
        lista_cat = sorted([c for c in df["Categoria"].unique().tolist() if c])
        cat_escolhidas = st.sidebar.multiselect("Filtrar Categorias", lista_cat, default=lista_cat)

        # --- PROCESSAMENTO ---
        df_mes = df[df['Mes_Ano'] == mes_selecionado]

        # Métricas limpas (sem sinais de + ou -)
        entradas_total = df_mes[df_mes['Valor'] > 0]['Valor'].sum()
        saidas_total = df_mes[df_mes['Valor'] < 0]['Valor'].sum()
        saldo_mensal = entradas_total + saidas_total

        m1, m2, m3 = st.columns(3)
        m1.metric("Entradas", f"R$ {entradas_total:,.2f}")
        m2.metric("Saídas", f"R$ {abs(saidas_total):,.2f}")
        m3.metric("Saldo Líquido", f"R$ {saldo_mensal:,.2f}", delta=f"{saldo_mensal:,.2f}")

        st.divider()

        # --- GRÁFICO 1: EVOLUÇÃO FINANCEIRA (LIMPO) ---
        st.subheader("📈 Evolução Financeira")
        df_para_evolucao = df[df["Categoria"].isin(cat_escolhidas)] if ver_tudo else df_mes[
            df_mes["Categoria"].isin(cat_escolhidas)]
        df_para_evolucao = df_para_evolucao.copy()
        df_para_evolucao['Status'] = df_para_evolucao['Valor'].apply(lambda x: 'RECEITA' if x > 0 else 'DESPESA')

        fig_evolucao = px.line(df_para_evolucao, x='Data', y=df_para_evolucao['Valor'].abs(), color='Status',
                               markers=True,
                               color_discrete_map={"RECEITA": "#2ecc71", "DESPESA": "#e74c3c"},
                               template="plotly_dark", custom_data=['Categoria', 'Valor'])

        fig_evolucao.update_traces(
            hovertemplate="<b>Data:</b> %{x|%d/%m/%y}<br><b>Valor:</b> R$ %{customdata[1]:,.2f}<br><b>Categoria:</b> %{customdata[0]}<extra></extra>")
        fig_evolucao.update_layout(hovermode="x unified",
                                   legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # --- NOVO GRÁFICO: SALDO ACUMULADO (PATRIMÔNIO) ---
        st.divider()
        st.subheader("💰 Saldo Acumulado (Histórico Total)")
        df_acumulado = df.groupby('Data')['Valor'].sum().reset_index()
        df_acumulado['Saldo_Acumulado'] = df_acumulado['Valor'].cumsum()

        fig_patrimonio = px.area(df_acumulado, x='Data', y='Saldo_Acumulado',
                                 template="plotly_dark", color_discrete_sequence=['#00d4ff'])
        fig_patrimonio.update_traces(fillcolor="rgba(0, 212, 255, 0.2)",
                                     hovertemplate="<b>Data:</b> %{x|%d/%m/%y}<br><b>Saldo Total:</b> R$ %{y:,.2f}<extra></extra>")
        st.plotly_chart(fig_patrimonio, use_container_width=True)

        # --- DISTRIBUIÇÃO ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Onde você mais gastou")
            df_pizza = df_mes[df_mes['Valor'] < 0].copy()
            df_pizza['Valor'] = df_pizza['Valor'].abs()
            if not df_pizza.empty:
                fig_pizza = px.pie(df_pizza, values="Valor", names="Categoria", hole=0.4)
                st.plotly_chart(fig_pizza, use_container_width=True)
        with c2:
            st.subheader("Balanço do Mês")
            df_balanco = pd.DataFrame({'Tipo': ['Receitas', 'Despesas'], 'Total': [entradas_total, abs(saidas_total)]})
            fig_bar = px.bar(df_balanco, x='Tipo', y='Total', color='Tipo',
                             color_discrete_map={"Receitas": "#2ecc71", "Despesas": "#e74c3c"})
            st.plotly_chart(fig_bar, use_container_width=True)

except Exception as e:
    st.error(f"Erro: {e}")