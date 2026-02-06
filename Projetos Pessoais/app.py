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
    spreadsheet = client.open("Controle Financeiro Mensal with Gráficos")
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
        df = df.dropna(subset=['Data'])
        df['Mes_Ano'] = df['Data'].dt.strftime('%Y-%m')

    return df


# --- INTERFACE DO DASHBOARD ---
try:
    df = load_data()

    if df.empty:
        st.warning("Nenhum dado encontrado.")
    else:
        st.title("📊 Meu Dashboard Financeiro")

        # --- SIDEBAR ---
        st.sidebar.header("Configurações de Filtro")
        lista_meses = sorted(df['Mes_Ano'].unique().tolist(), reverse=True)
        mes_selecionado = st.sidebar.selectbox("Mês de análise detalhada", lista_meses)

        lista_cat = sorted([c for c in df["Categoria"].unique().tolist() if c])
        cat_escolhidas = st.sidebar.multiselect("Filtrar Categorias", lista_cat, default=lista_cat)

        df_mes = df[df['Mes_Ano'] == mes_selecionado]
        df_filtrado = df_mes[df_mes["Categoria"].isin(cat_escolhidas)]

        # --- MÉTRICAS ---
        col_tipo = "Tipo (Entrada/Saída)"
        entradas = df_mes[df_mes[col_tipo] == "ENTRADA"]["Valor"].sum()
        saidas = df_mes[df_mes[col_tipo] == "SAÍDA"]["Valor"].sum()
        saldo = entradas - saidas

        m1, m2, m3 = st.columns(3)
        m1.metric(f"Entradas ({mes_selecionado})", f"R$ {entradas:,.2f}")
        m2.metric(f"Saídas ({mes_selecionado})", f"R$ {saidas:,.2f}")
        m3.metric("Saldo Mensal", f"R$ {saldo:,.2f}", delta=f"{saldo:,.2f}")

        st.divider()

        # --- GRÁFICO 1: EVOLUÇÃO (VERSÃO FINAL SEM SUMIÇO DE LINHAS) ---
        st.subheader("📈 Evolução Financeira Detalhada")

        # Estratégia: Agrupamos para a linha não quebrar, mas mantemos o detalhe no hover
        df_evol = df_mes.copy()

        # Criamos uma coluna de texto formatada para o hover que não interfere na estrutura da linha
        df_evol['hover_text'] = df_evol.apply(lambda x: f"Valor: R$ {x['Valor']:,.2f}<br>Categoria: {x['Categoria']}",
                                              axis=1)

        fig_evolucao = px.line(
            df_evol,
            x='Data',
            y='Valor',
            color=col_tipo,
            markers=True,
            # Voltamos ao padrão para a linha conectar, mas o hover fará o trabalho duro
            color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"},
            template="plotly_dark",
            custom_data=['hover_text']
        )

        fig_evolucao.update_traces(
            hovertemplate="<b>%{customdata[0]}</b><extra></extra>"
        )

        fig_evolucao.update_layout(
            hovermode="x unified",
            legend_title_text='',
            xaxis_title="",
            yaxis_title="Valor (R$)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        fig_evolucao.update_xaxes(tickformat="%d/%m/%y", dtick="D1")
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # --- GRÁFICOS INFERIORES ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"Gastos por Categoria ({mes_selecionado})")
            fig_pizza = px.pie(
                df_filtrado[df_filtrado[col_tipo] == "SAÍDA"],
                values="Valor", names="Categoria", hole=0.4,
                color_discrete_sequence=px.colors.qualitative.T10
            )
            st.plotly_chart(fig_pizza, use_container_width=True)
        with c2:
            st.subheader(f"Entradas vs Saídas ({mes_selecionado})")
            fig_bar = px.bar(
                df_mes.groupby(col_tipo)["Valor"].sum().reset_index(),
                x=col_tipo, y="Valor", color=col_tipo,
                color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"}
            )
            fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="Total (R$)")
            st.plotly_chart(fig_bar, use_container_width=True)

        with st.expander("🔍 Ver lançamentos deste mês"):
            st.dataframe(df_filtrado.sort_values("Data", ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")