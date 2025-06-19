# app.py (Versão 3.2 - Design)

import streamlit as st
from agent_logic import agent_executor, process_tool_call, suggest_strategic_questions
from tools import process_uploaded_file, catalog_files_metadata, generate_global_analysis_summary
from ui_components import display_onboarding_results, render_chat_message # <-- NOVO IMPORT

# =============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# =============================================================================
st.set_page_config(page_title="Data Insights Pro v3.2", page_icon="🍏", layout="centered")

def load_css():
    st.markdown("""
    <style>
        /* Cor de destaque para uma identidade visual profissional */
        :root {
            --primary-color: #007AFF; /* Apple Blue */
        }
        html, body, [class*="st-"] { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
        .block-container { max-width: 760px; padding: 2rem 1rem; }
        
        /* Botões com a cor de destaque */
        .stButton>button {
            border-radius: 10px;
            font-weight: 500;
            border: 1px solid var(--primary-color);
            background-color: white;
            color: var(--primary-color);
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            border-color: var(--primary-color);
            background-color: var(--primary-color);
            color: white;
        }
        .stButton>button:focus {
            box-shadow: 0 0 0 2px white, 0 0 0 4px var(--primary-color) !important;
        }

        /* Estilo das abas */
        [data-baseweb="tab-list"] {
            justify-content: center;
        }
    </style>
    """, unsafe_allow_html=True)

load_css()

# =============================================================================
# 2. ESTADO DA SESSÃO
# =============================================================================
def initialize_session_state():
    # ... (sem alterações aqui)
    if "messages" not in st.session_state: st.session_state.messages = []
    if "dataframes" not in st.session_state: st.session_state.dataframes = None
    if "active_scope" not in st.session_state: st.session_state.active_scope = "Nenhum"
    if "run_prompt" not in st.session_state: st.session_state.run_prompt = None

initialize_session_state()

# =============================================================================
# 3. LÓGICA DA INTERFACE
# =============================================================================

# --- TELA DE UPLOAD ---
if st.session_state.dataframes is None:
    st.title("🍏 Data Insights Pro")
    st.markdown("##### Transforme dados brutos em insights claros. Comece fazendo o upload.")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Carregue um arquivo `.zip` ou `.csv`", type=["zip", "csv"], label_visibility="collapsed")
    
    if uploaded_file:
        with st.spinner("Processando e analisando seus dados..."):
            dfs = process_uploaded_file(uploaded_file)
            if dfs:
                st.session_state.dataframes = dfs
                metadata = catalog_files_metadata(dfs)
                summary_df = generate_global_analysis_summary(dfs)
                strategic_questions = suggest_strategic_questions(dfs)
                
                # Armazena os resultados do onboarding no estado da sessão
                st.session_state.onboarding_data = {
                    "metadata": metadata,
                    "summary_df": summary_df,
                    "strategic_questions": strategic_questions
                }
                st.session_state.active_scope = "Analisar Todos em Conjunto"
                st.rerun()

# --- TELA DE CHAT E ONBOARDING ---
else:
    # Mostra o painel de onboarding apenas na primeira vez
    if st.session_state.messages == []:
        onboarding_data = st.session_state.onboarding_data
        display_onboarding_results(
            onboarding_data["metadata"],
            onboarding_data["summary_df"],
            onboarding_data["strategic_questions"]
        )
        # Adiciona uma mensagem inicial para que o onboarding não apareça novamente
        st.session_state.messages.append({"role": "assistant", "content": "Estou pronto para ajudar. Faça uma pergunta ou escolha uma das sugestões acima."})

    st.title("🍏 Conversando com seus Dados")
    
    # Seletor de escopo
    options = ["Analisar Todos em Conjunto"] + list(st.session_state.dataframes.keys())
    st.selectbox("Escopo da Análise:", options, key="active_scope", label_visibility="collapsed")
    
    st.markdown("---")

    # Exibe o histórico de chat
    for msg in st.session_state.messages:
        render_chat_message(msg)

    # Lógica para executar prompt a partir de um botão
    if st.session_state.run_prompt:
        prompt = st.session_state.run_prompt
        st.session_state.run_prompt = None # Reseta para não rodar em loop
    else:
        prompt = st.chat_input(f"Pergunte sobre '{st.session_state.active_scope}'...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                action_json, thought_process = agent_executor(prompt, st.session_state.messages, st.session_state.active_scope)
                st.session_state.messages.append({"role": "assistant", "content": {"thought": thought_process}})
                
                final_response = process_tool_call(action_json, st.session_state.active_scope)

                if final_response:
                    st.session_state.messages.append({"role": "assistant", "content": final_response})
        
        st.rerun()
