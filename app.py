import streamlit as st
import pandas as pd
from agent_logic import agent_onboarding, agent_executor, process_tool_call
from tools import load_dataframes_from_zip

# =============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# =============================================================================

st.set_page_config(
    layout="centered",
    page_title="Data Insights Pro",
    page_icon="🍏"
)

def load_css():
    """Carrega o CSS customizado para a aplicação."""
    st.markdown("""
    <style>
        html, body, [class*="st-"] { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
        h1 { font-weight: 600; letter-spacing: -0.03em; }
        .block-container { max-width: 720px; padding-top: 2rem; padding-bottom: 3rem; }
        [data-testid="stChatMessage"] { border-radius: 20px; padding: 1rem 1.25rem; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: none; }
        .stButton>button { border-radius: 10px; font-weight: 500; }
        [data-testid="stFileUploader"] { border: 1.5px dashed #d0d0d5; background-color: #f8f8fa; border-radius: 12px; padding: 2rem; }
        [data-testid="stAlert"] { border-radius: 12px; border: none; background-color: #f0f0f5; }
    </style>
    """, unsafe_allow_html=True)

load_css()

# =============================================================================
# 2. ESTADO DA SESSÃO
# =============================================================================

def initialize_session_state():
    """Inicializa as variáveis no estado da sessão do Streamlit."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "dataframes" not in st.session_state:
        st.session_state.dataframes = None
    if "active_scope" not in st.session_state:
        st.session_state.active_scope = "Nenhum"

initialize_session_state()

# =============================================================================
# 3. LÓGICA DA INTERFACE
# =============================================================================

def reset_analysis():
    """Reseta o estado da sessão para permitir uma nova análise de arquivo."""
    st.session_state.dataframes = None
    st.session_state.messages = []
    st.session_state.active_scope = "Nenhum"
    st.rerun()

# --- TELA DE UPLOAD (ESTADO INICIAL) ---
if st.session_state.dataframes is None:
    st.title("🍏 Data Insights Pro")
    st.markdown("##### Um universo de dados em um único lugar. Pergunte, explore, descubra.")
    st.markdown("---")
    
    st.info("Para começar, carregue um arquivo `.zip` contendo um ou mais arquivos `.csv`.")
    uploaded_file = st.file_uploader(
        "Arraste seu catálogo de dados aqui ou clique para procurar", 
        type="zip", 
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        with st.spinner("Catalogando e analisando seus arquivos..."):
            dfs = load_dataframes_from_zip(uploaded_file)
            if dfs:
                st.session_state.dataframes = dfs
                st.session_state.messages = []
                welcome_message = agent_onboarding(dfs)
                st.session_state.messages.append({"role": "assistant", "content": welcome_message})
                st.session_state.active_scope = "Analisar Todos em Conjunto"
                st.rerun()
            else:
                st.error("Nenhum arquivo .csv válido foi encontrado no arquivo .zip.")

# --- TELA DE CHAT (APÓS UPLOAD) ---
else:
    st.title("🍏 Conversando com seus Dados")

    col1, col2 = st.columns([3, 1])
    with col1:
        scope_options = ["Analisar Todos em Conjunto"] + list(st.session_state.dataframes.keys())
        st.session_state.active_scope = st.selectbox(
            "Escopo da Análise:",
            options=scope_options,
            index=scope_options.index(st.session_state.active_scope),
            label_visibility="collapsed"
        )
    with col2:
        if st.button("Analisar Outro", use_container_width=True, on_click=reset_analysis):
            pass
    
    st.markdown("---")

    # Exibição do histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            content = message["content"]
            if isinstance(content, str):
                st.markdown(content)
            elif isinstance(content, dict) and "thought" in content:
                with st.expander("Ver o Raciocínio do Agente", expanded=False):
                    st.info(content["thought"])
            elif "figure" in str(type(content)):
                st.pyplot(content)

    # Captura da pergunta do usuário
    if prompt := st.chat_input(f"Pergunte sobre '{st.session_state.active_scope}'..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Processamento com o agente
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    action_json, thought_process = agent_executor(
                        prompt, st.session_state.messages, st.session_state.active_scope
                    )
                    st.session_state.messages.append({"role": "assistant", "content": {"thought": thought_process}})
                    
                    final_response = process_tool_call(action_json, st.session_state.active_scope)

                    if final_response:
                        st.markdown(final_response)
                        st.session_state.messages.append({"role": "assistant", "content": final_response})
                    
                except Exception as e:
                    error_message = f"Ocorreu um erro crítico no ciclo do agente.\n\n**Detalhe técnico:** `{e}`"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})