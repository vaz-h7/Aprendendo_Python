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
        # Colunas fundamentais para os filtros
        df['Ano'] = df['Data'].dt.year.astype(str)
        df['Mes_Ano'] = df['Data'].dt.strftime('%Y-%m')
        df['Mes_Ano_Exibicao'] = df['Data'].dt.strftime('%m/%Y')

    return df


# --- INTERFACE DO DASHBOARD ---
try:
    df = load_data()

    if df.empty:
        st.warning("Aguardando dados válidos na planilha.")
    else:
        st.title("📊 Meu Dashboard Financeiro")

        # --- SIDEBAR (FILTROS CORRIGIDOS) ---
        st.sidebar.header("Configurações de Filtro")

        # 1. Filtro de Ano (Único e Limpo)
        lista_anos = sorted(df['Ano'].unique().tolist(), reverse=True)
        ano_selecionado = st.sidebar.selectbox("1. Selecione o Ano", lista_anos)

        # 2. Filtro de Mês (Dependente do Ano selecionado)
        df_ano = df[df['Ano'] == ano_selecionado]
        df_meses = df_ano[['Mes_Ano_Exibicao', 'Mes_Ano']].drop_duplicates().sort_values('Mes_Ano', ascending=False)

        lista_exibicao = df_meses['Mes_Ano_Exibicao'].tolist()
        mes_visual = st.sidebar.selectbox("2. Mês de análise detalhada", lista_exibicao)

        # Pegamos o valor interno (YYYY-MM) para os cálculos
        mes_selecionado = df_meses.loc[df_meses['Mes_Ano_Exibicao'] == mes_visual, 'Mes_Ano'].values[0]

        ver_tudo = st.sidebar.checkbox("Visualizar todo o histórico no gráfico", value=False)

        # Categorias
        lista_cat = sorted([c for c in df["Categoria"].unique().tolist() if c])
        if "selecao_categorias" not in st.session_state:
            st.session_state.selecao_categorias = lista_cat

        if st.sidebar.button("Selecionar todas categorias"):
            st.session_state.selecao_categorias = lista_cat

        cat_escolhidas = st.sidebar.multiselect("Filtrar Categorias", lista_cat, key="selecao_categorias")

        # --- PREPARAÇÃO DOS DADOS ---
        df_mes_base = df[df['Mes_Ano'] == mes_selecionado]
        df_mes = df_mes_base[df_mes_base["Categoria"].isin(cat_escolhidas)]

        is_invest = df_mes['Categoria'].str.contains("Investimento", case=False, na=False)
        df_mes_Receitas = df_mes[((df_mes['Valor'] > 0) & (~is_invest)) | ((df_mes['Valor'] < 0) & (is_invest))]
        df_mes_saidas = df_mes[((df_mes['Valor'] < 0) & (~is_invest)) | ((df_mes['Valor'] > 0) & (is_invest))]

        data_referencia = df['Data'].min().replace(day=1)

        if ver_tudo:
            df_para_evolucao = df[df["Categoria"].isin(cat_escolhidas)]
            df_para_investimentos = df
            texto_periodo = "Histórico Total"
            intervalo_ms = 10 * 24 * 60 * 60 * 1000
        else:
            df_para_evolucao = df_mes
            df_para_investimentos = df_mes
            texto_periodo = mes_visual
            intervalo_ms = 5 * 24 * 60 * 60 * 1000

        # --- MÉTRICAS ---
        Receitas_total = df_mes_Receitas['Valor'].abs().sum()
        saidas_total_abs = df_mes_saidas['Valor'].abs().sum()
        saldo_mensal = Receitas_total - saidas_total_abs

        data_limite = df_mes_base['Data'].max()
        df_acum_temp = df[df['Data'] <= data_limite].copy()
        is_invest_acum = df_acum_temp['Categoria'].str.contains("Investimento", case=False, na=False)
        df_acum_temp.loc[is_invest_acum, 'Valor'] = -df_acum_temp.loc[is_invest_acum, 'Valor']
        saldo_acumulado = df_acum_temp['Valor'].sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receitas", f"R$ {Receitas_total:,.2f}")
        m2.metric("Despesas", f"R$ {saidas_total_abs:,.2f}")
        m3.metric("Saldo Mensal", f"R$ {saldo_mensal:,.2f}", delta=f"{saldo_mensal:,.2f}")
        m4.metric("Saldo Acumulado", f"R$ {saldo_acumulado:,.2f}", delta=f"{saldo_acumulado:,.2f}")

        st.divider()

        # --- GRÁFICO 1: EVOLUÇÃO ---
        st.subheader("📈 Evolução Financeira Detalhada")
        df_para_evolucao = df_para_evolucao.copy()


        def definir_status(row):
            if "Investimento" in str(row['Categoria']):
                return 'Receitas' if row['Valor'] < 0 else 'Despesas'
            return 'Receitas' if row['Valor'] > 0 else 'Despesas'


        df_para_evolucao['Status'] = df_para_evolucao.apply(definir_status, axis=1)
        df_plot = df_para_evolucao.groupby(['Data', 'Status', 'Categoria'])['Valor'].sum().reset_index()
        df_plot['Valor_Grafico'] = df_plot['Valor'].abs()

        fig_evolucao = px.line(df_plot, x='Data', y='Valor_Grafico', color='Status', markers=True,
                               color_discrete_map={"Receitas": "#2ecc71", "Despesas": "#e74c3c"},
                               template="plotly_dark", custom_data=['Categoria', 'Valor'])
        fig_evolucao.update_xaxes(tickformat="%d/%m/%Y", dtick=intervalo_ms, tickmode="linear")
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # --- CARTÃO DE CRÉDITO ---
        st.divider()
        st.subheader("💳 Área do Cartão de Crédito")


        def calcular_fatura(row):
            dt = row['Data']
            fatura_dt = dt - pd.DateOffset(months=1) if dt.day <= 2 else dt
            return fatura_dt.strftime('%m/%Y')


        df_cartao_base = df[df['Forma de Pagamento'].str.contains("Cartão de Crédito", case=False, na=False)].copy()
        if not df_cartao_base.empty:
            df_cartao_base['Mes_Fatura'] = df_cartao_base.apply(calcular_fatura, axis=1)
            df_faturas = df_cartao_base.groupby('Mes_Fatura')['Valor'].sum().abs().reset_index()

            valor_fatura_atual = df_faturas.loc[df_faturas['Mes_Fatura'] == mes_visual, 'Valor'].sum()
            st.metric(f"Total da Fatura ({mes_visual})", f"R$ {valor_fatura_atual:,.2f}")

            fig_cartao = px.bar(df_faturas, x='Mes_Fatura', y='Valor', color_discrete_sequence=["#9b59b6"],
                                template="plotly_dark")
            st.plotly_chart(fig_cartao, use_container_width=True)

            df_fatura_atual = df_cartao_base[df_cartao_base['Mes_Fatura'] == mes_visual].copy()
            if not df_fatura_atual.empty:
                st.markdown(f"**Lançamentos da Fatura de {mes_visual}:**")
                df_fatura_lista = df_fatura_atual[
                    ['Data', 'Categoria', 'Valor', 'Parcelas', 'Descrição (Opcional)']].copy()
                df_fatura_lista['Data'] = df_fatura_lista['Data'].dt.strftime('%d/%m/%Y')
                st.dataframe(df_fatura_lista.style.map(
                    lambda x: f'color: {"#2ecc71" if x > 0 else "#e74c3c"}; font-weight: bold',
                    subset=['Valor']).format({"Valor": "R$ {:,.2f}"}), use_container_width=True, hide_index=True)

        # --- ANÁLISES MENSAIS ---
        st.divider()
        st.header("🎯 Análises Mensais")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribuição de Gastos")
            df_pizza = df_mes_saidas.copy()
            df_pizza['Valor'] = df_pizza['Valor'].abs()
            if not df_pizza.empty:
                fig_pizza = px.pie(df_pizza, values="Valor", names="Categoria", hole=0.4)
                st.plotly_chart(fig_pizza, use_container_width=True)
        with c2:
            st.subheader("Balanço Mensal")
            df_balanco = pd.DataFrame({'Status': ['Receitas', 'Despesas'], 'Total': [Receitas_total, saidas_total_abs]})
            fig_bar = px.bar(df_balanco, x='Status', y='Total', color='Status',
                             color_discrete_map={"Receitas": "#2ecc71", "Despesas": "#e74c3c"})
            st.plotly_chart(fig_bar, use_container_width=True)

