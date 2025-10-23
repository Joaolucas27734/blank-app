import streamlit as st

# Usuários e senhas (exemplo)
usuarios = {
    "joao": "senha123",
    "maria": "123456"
}

st.title("🔒 Login")

username = st.text_input("Usuário")
password = st.text_input("Senha", type="password")

if st.button("Entrar"):
    if username in usuarios and usuarios[username] == password:
        st.success(f"Bem-vindo, {username}!")
        # Aqui você coloca o restante do dashboard
    else:
        st.error("Usuário ou senha incorretos")
