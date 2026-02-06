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


# --- INTERFACE DO DASHBOARD ---
try:
    df = load_data()
    col_tipo = "Tipo (Entrada/Saída)"

    if df.empty:
        st.warning("Aguardando dados válidos na planilha.")
    else:
        st.title("📊 Meu Dashboard Financeiro")

        # --- SIDEBAR (FILTROS) ---
        st.sidebar.header("Configurações de Filtro")
        df_meses = df[['Mes_Ano_Exibicao', 'Mes_Ano']].drop_duplicates().sort_values('Mes_Ano', ascending=False)
        lista_exibicao = df_meses['Mes_Ano_Exibicao'].tolist()
        mes_visual = st.sidebar.selectbox("Mês de análise detalhada", lista_exibicao)
        mes_selecionado = df_meses.loc[df_meses['Mes_Ano_Exibicao'] == mes_visual, 'Mes_Ano'].values[0]

        ver_tudo = st.sidebar.checkbox("Visualizar todo o histórico no gráfico", value=False)

        lista_cat = sorted([c for c in df["Categoria"].unique().tolist() if c])
        cat_escolhidas = st.sidebar.multiselect("Filtrar Categorias", lista_cat, default=lista_cat)

        # --- PREPARAÇÃO DOS DADOS ---
        df_mes = df[df['Mes_Ano'] == mes_selecionado]
        df_filtrado_mes = df_mes[df_mes["Categoria"].isin(cat_escolhidas)]

        if ver_tudo:
            df_para_evolucao = df[df["Categoria"].isin(cat_escolhidas)]
            df_para_investimentos = df  # Histórico total para investimentos
            texto_periodo = "Histórico Total"
        else:
            df_para_evolucao = df_filtrado_mes
            df_para_investimentos = df_mes  # Apenas mês atual para investimentos
            texto_periodo = mes_visual

        # --- MÉTRICAS DO MÊS ---
        entradas = df_mes[df_mes[col_tipo] == "ENTRADA"]["Valor"].sum()
        saidas = df_mes[df_mes[col_tipo] == "SAÍDA"]["Valor"].sum()
        saldo = entradas - saidas

        m1, m2, m3 = st.columns(3)
        m1.metric(f"Entradas ({mes_visual})", f"R$ {entradas:,.2f}")
        m2.metric(f"Saídas ({mes_visual})", f"R$ {saidas:,.2f}")
        m3.metric("Saldo Mensal", f"R$ {saldo:,.2f}", delta=f"{saldo:,.2f}")

        st.divider()

        # --- GRÁFICO 1: EVOLUÇÃO GERAL ---
        st.subheader("📈 Evolução Financeira Detalhada")
        df_plot = df_para_evolucao.groupby(['Data', col_tipo, 'Categoria'])['Valor'].sum().reset_index()
        fig_evolucao = px.line(df_plot, x='Data', y='Valor', color=col_tipo, markers=True,
                               color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"},
                               template="plotly_dark", custom_data=['Categoria'])

        fig_evolucao.update_traces(
            hovertemplate="<b>Data:</b> %{x|%d/%m/%y}<br><b>Valor:</b> R$ %{y:,.2f}<br><b>Categoria:</b> %{customdata[0]}<extra></extra>")
        fig_evolucao.update_layout(hovermode="closest",
                                   legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig_evolucao.update_xaxes(tickformat="%d/%m/%y", tickangle=45, nticks=10)
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # --- GRÁFICOS INFERIORES ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"Gastos por Categoria ({mes_visual})")
            df_pizza = df_filtrado_mes[df_filtrado_mes[col_tipo] == "SAÍDA"]
            if not df_pizza.empty:
                fig_pizza = px.pie(df_pizza, values="Valor", names="Categoria", hole=0.4)
                st.plotly_chart(fig_pizza, use_container_width=True)
        with c2:
            st.subheader(f"Entradas vs Saídas ({mes_visual})")
            df_bar_resumo = df_mes.groupby(col_tipo)["Valor"].sum().reset_index()
            fig_bar = px.bar(df_bar_resumo, x=col_tipo, y="Valor", color=col_tipo,
                             color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"})
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- NOVA SEÇÃO: EVOLUÇÃO DE INVESTIMENTOS ---
        st.divider()
        st.subheader(f"🚀 Evolução de Investimentos ({texto_periodo})")

        # Filtramos apenas o que contém "Investimento"
        df_invest = df_para_investimentos[
            df_para_investimentos["Categoria"].str.contains("Investimento", case=False, na=False)]

        if not df_invest.empty:
            # Agrupamos por Data e Categoria para o gráfico de linha
            df_invest_plot = df_invest.groupby(['Data', 'Categoria'])['Valor'].sum().reset_index()

            fig_invest = px.line(
                df_invest_plot,
                x='Data',
                y='Valor',
                color='Categoria',
                markers=True,
                title="Acompanhamento de Aportes",
                template="plotly_dark"
            )

            fig_invest.update_layout(hovermode="x unified")
            fig_invest.update_xaxes(tickformat="%d/%m/%y", tickangle=45, nticks=10)
            st.plotly_chart(fig_invest, use_container_width=True)

            # Métrica rápida de total investido no período
            total_inv_periodo = df_invest["Valor"].sum()
            st.info(f"O valor total investido em {texto_periodo} foi de **R$ {total_inv_periodo:,.2f}**")
        else:
            st.info(f"Nenhum registro de 'Investimento' encontrado para {texto_periodo}.")

        with st.expander(f"🔍 Lista de lançamentos - {mes_visual}"):
            st.dataframe(df_filtrado_mes.sort_values("Data", ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")