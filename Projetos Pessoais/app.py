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

    return df


# --- INTERFACE DO DASHBOARD ---
try:
    df = load_data()
    col_tipo = "Tipo (Entrada/Saída)"

    if not df.empty:
        st.title("📊 Meu Dashboard Financeiro")

        # Filtros
        lista_meses = sorted(df['Mes_Ano'].unique().tolist(), reverse=True)
        mes_selecionado = st.sidebar.selectbox("Mês de análise", lista_meses)
        df_mes = df[df['Mes_Ano'] == mes_selecionado]

        # --- GRÁFICO 1: EVOLUÇÃO (VOLTANDO AO MODO ORIGINAL DE PONTOS) ---
        st.subheader("📈 Evolução Financeira Detalhada")

        # Criamos o gráfico sem agrupar por dia, para que cada ponto exista sozinho
        fig_evolucao = px.line(
            df_mes,
            x='Data',
            y='Valor',
            color=col_tipo,
            markers=True,
            color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"},
            template="plotly_dark",
            # Adicionamos a categoria aqui para o hover ler
            custom_data=['Categoria']
        )

        # AJUSTE DA CAIXINHA (HOVER) - Estilo da Imagem 1, mas limpo
        fig_evolucao.update_traces(
            hovertemplate="<b>Data:</b> %{x|%d/%m/%y}<br>" +
                          "<b>Valor:</b> R$ %{y:,.2f}<br>" +
                          "<b>Categoria:</b> %{customdata[0]}<extra></extra>"
        )

        fig_evolucao.update_layout(
            hovermode="closest",  # <--- O SEGREDO: Volta a ser uma caixinha por ponto
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
            st.subheader("Gastos por Categoria")
            st.plotly_chart(px.pie(df_mes[df_mes[col_tipo] == "SAÍDA"], values="Valor", names="Categoria", hole=0.4),
                            use_container_width=True)
        with c2:
            st.subheader("Entradas vs Saídas")
            # Aqui agrupamos só para a barra mostrar o total do mês
            df_barras = df_mes.groupby(col_tipo)['Valor'].sum().reset_index()
            st.plotly_chart(px.bar(df_barras, x=col_tipo, y="Valor", color=col_tipo,
                                   color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"}),
                            use_container_width=True)

except Exception as e:
    st.error(f"Erro: {e}")