"""
Streamlit — Reportana-like Dashboard with GitHub OAuth Login
File: streamlit_reportana_clone_with_github_login.py

INSTRUÇÕES RÁPIDAS (LEIA):
1) Crie um OAuth App no GitHub: https://github.com/settings/developers -> New OAuth App
   - Homepage URL: https://your-domain-or-ngrok-url/   (ex: http://localhost:8501 for dev with Streamlit)
   - Authorization callback URL: https://your-domain-or-ngrok-url/  (same)
   - Copie CLIENT_ID e CLIENT_SECRET

2) Configure variáveis de ambiente no seu ambiente de execução (ou .env):
   - GITHUB_CLIENT_ID
   - GITHUB_CLIENT_SECRET
   - APP_URL (ex: http://localhost:8501)

3) Requisitos (pip):
   pip install streamlit requests plotly python-dotenv

4) Execute:
   streamlit run streamlit_reportana_clone_with_github_login.py

O que o app faz:
- Autentica o usuário via GitHub OAuth (fluxo de autorização padrão)
- Mostra um dashboard simplificado (métricas, gráficos) parecido com um "overview"
- Permite logout (limpa sessão)

Observação técnica:
- Este é um exemplo didático. Em produção, utilize HTTPS, valide estados de CSRF, e armazene segredos com segurança.

"""

import os
import time
import json
import urllib.parse
from typing import Optional

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
APP_URL = os.getenv("APP_URL", "http://localhost:8501")  # must match GitHub app

# OAuth endpoints
AUTH_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_API = "https://api.github.com/user"

# ---------- Helper functions ----------

def _get_state():
    # keep a simple nonce to mitigate CSRF; in production use a better store
    if "oauth_state" not in st.session_state:
        st.session_state.oauth_state = str(int(time.time()))
    return st.session_state.oauth_state


def build_github_auth_url():
    state = _get_state()
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": APP_URL,
        "scope": "read:user",
        "state": state,
        # "allow_signup": "false"
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code: str) -> Optional[str]:
    headers = {"Accept": "application/json"}
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": APP_URL,
        "state": _get_state(),
    }
    resp = requests.post(TOKEN_URL, data=data, headers=headers, timeout=10)
    if resp.status_code != 200:
        st.error("Erro ao trocar código por token: " + str(resp.status_code))
        return None
    token_json = resp.json()
    return token_json.get("access_token")


def fetch_github_user(access_token: str) -> Optional[dict]:
    headers = {"Authorization": f"token {access_token}", "Accept": "application/json"}
    resp = requests.get(USER_API, headers=headers, timeout=10)
    if resp.status_code != 200:
        return None
    return resp.json()


# ---------- OAuth flow handling ----------

st.set_page_config(page_title="Reportana Clone — Login GitHub", layout="wide")

# Logout
if st.experimental_get_query_params().get("logout"):
    # Clear session and redirect to base url without params
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.experimental_set_query_params()
    st.experimental_rerun()

# On first load, check for GitHub callback (code + state)
qp = st.experimental_get_query_params()
if "code" in qp and "state" in qp and "user" not in st.session_state:
    code = qp.get("code")[0]
    state = qp.get("state")[0]
    # validate state
    if state != _get_state():
        st.error("State mismatch. Possível ataque CSRF.")
    else:
        token = exchange_code_for_token(code)
        if token:
            user = fetch_github_user(token)
            if user:
                st.session_state.user = user
                st.session_state.access_token = token
            else:
                st.error("Não foi possível obter dados do usuário GitHub.")
        else:
            st.error("Falha ao obter token do GitHub.")
    # Clean query params after processing
    st.experimental_set_query_params()
    st.experimental_rerun()

# ---------- Login UI ----------

if "user" not in st.session_state:
    st.markdown("# Bem-vindo — Faça login com GitHub")
    st.markdown("Para acessar o dashboard é necessário autenticar via GitHub.")
    cols = st.columns([1,1,1])
    with cols[1]:
        if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
            st.warning("Variáveis de ambiente GITHUB_CLIENT_ID e GITHUB_CLIENT_SECRET não configuradas. Veja o topo do arquivo para instruções.")
        else:
            auth_url = build_github_auth_url()
            st.markdown(f"[Entrar com GitHub]({auth_url})")
    st.stop()

# ---------- Authenticated UI (Dashboard) ----------
user = st.session_state.user
st.sidebar.image(user.get("avatar_url"), width=64)
st.sidebar.markdown(f"**{user.get('name') or user.get('login')}**")
st.sidebar.markdown(f"[Logout]({APP_URL}?logout=1)")

st.title("📊 Dashboard — Overview")
st.markdown("Visão geral das métricas (demo). Este layout é inspirado na página Overview do Reportana.")

# --- Mock / demo data ---
# In a real app você traria dados de APIs ou banco

@st.cache_data(ttl=60)
def load_demo_data():
    dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
    df = pd.DataFrame({
        "date": dates,
        "visitors": (pd.Series(range(30)) * 10 + pd.np.random.randint(0, 50, 30)).tolist(),
        "conversions": (pd.Series(range(30)) + pd.np.random.randint(0, 5, 30)).tolist(),
        "revenue": (pd.Series(range(30)) * 3 + pd.np.random.randint(0, 200, 30)).tolist(),
    })
    return df

try:
    df = load_demo_data()
except Exception:
    # fallback in case pd.np deprecated
    import numpy as np
    dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
    df = pd.DataFrame({
        "date": dates,
        "visitors": (np.arange(30) * 10 + np.random.randint(0, 50, 30)).tolist(),
        "conversions": (np.arange(30) + np.random.randint(0, 5, 30)).tolist(),
        "revenue": (np.arange(30) * 3 + np.random.randint(0, 200, 30)).tolist(),
    })

# Top KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Visitantes (últimos 30d)", int(df['visitors'].sum()))
with kpi2:
    st.metric("Conversões", int(df['conversions'].sum()))
with kpi3:
    st.metric("Receita (R$)", int(df['revenue'].sum()))
with kpi4:
    st.metric("Taxa de Conversão", f"{(df['conversions'].sum()/max(1,df['visitors'].sum())*100):.2f}%")

# Charts
st.subheader("Visão temporal")
fig = px.line(df, x='date', y=['visitors','conversions','revenue'], labels={'value':'Quantidade','variable':'Métrica'})
st.plotly_chart(fig, use_container_width=True)

# Campaigns / Channels mock
st.subheader("Canais e desempenho")
channels = pd.DataFrame({
    'channel': ['WhatsApp','E-mail','SMS','Voz','Orgânico'],
    'sent': [1200, 2000, 300, 50, 800],
    'opens': [900, 800, 180, 40, 600],
    'conversions': [120, 150, 20, 2, 60]
})
st.dataframe(channels)

c1, c2 = st.columns(2)
with c1:
    fig2 = px.bar(channels, x='channel', y='sent', title='Mensagens enviadas por canal')
    st.plotly_chart(fig2, use_container_width=True)
with c2:
    fig3 = px.pie(channels, names='channel', values='conversions', title='Conversões por canal')
    st.plotly_chart(fig3, use_container_width=True)

# Recent activity / table
st.subheader("Atividades recentes")
recent = pd.DataFrame({
    'time': pd.date_range(end=pd.Timestamp.now(), periods=6, freq='H').strftime('%Y-%m-%d %H:%M'),
    'event': ['Campanha enviada','Lead convertido','Mensagem falhou','Nova assinatura','Envio reprogramado','Teste A/B completado'],
    'by': [user.get('login')] * 6
})
st.table(recent)

st.markdown("---")
st.markdown("_Este é um protótipo. Para funcionalidades completas (integração multicanal, envio de campanhas, análises profundas), é necessário conectar APIs externas e um banco de dados._")

# Footer / debug (show GitHub profile summary)
with st.expander("Perfil GitHub (raw)"):
    st.json(user)


# End of file
