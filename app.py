import streamlit as st
import json
from agent_logic import agent_executor, process_tool_call, suggest_strategic_questions
from tools import process_uploaded_file, catalog_files_metadata, generate_global_analysis_summary

# =============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# =============================================================================
st.set_page_config(page_title="Data Insights Pro v3.0", page_icon="🍏", layout="centered")

def load_css():
    st.markdown("""
    <style>
        html, body, [class*="st-"] { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
        .block-container { max-width: 720px; padding: 2rem 1rem; }
        [data-testid="stFileUploader"] { border: 1.5px dashed #d0d0d5; background: #f8f8fa; border-radius: 12px; padding: 2rem; }
        [data-testid="stAlert"] { background: #f0f0f5; border-radius: 12px; border: none; }
        .stButton>button { border-radius: 10px; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

load_css()

# =============================================================================
# 2. ESTADO DA SESSÃO
# =============================================================================
def initialize_session_state():
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

# --- TELA DE UPLOAD (ESTADO INICIAL) ---
if st.session_state.dataframes is None:
    st.title("🍏 Data Insights Pro v3.0")
    st.markdown("##### Análise de dados com um pipeline de agentes inteligentes.")
    st.markdown("---")
    
    # DevÆGENT-V3.0: Aceita .zip e .csv, melhorando a flexibilidade.
    uploaded_file = st.file_uploader(
        "Carregue um arquivo `.zip` ou `.csv` para começar",
        type=["zip", "csv"],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        with st.spinner("Processando e analisando seus dados..."):
            # DevÆGENT-V3.0: A lógica de processamento de arquivo foi movida para `tools.py` e está em cache.
            dfs = process_uploaded_file(uploaded_file)
            
            if dfs:
                st.session_state.dataframes = dfs
                
                # --- INÍCIO DO PIPELINE DE ONBOARDING ---
                # 1. Catalogação determinística com Python
                metadata = catalog_files_metadata(dfs)
                summary_markdown = generate_global_analysis_summary(dfs).to_markdown()
                
                # 2. Geração de perguntas estratégicas com IA
                strategic_questions = suggest_strategic_questions(dfs)
                
                # 3. Montagem da mensagem de boas-vindas
                onboarding_message = (
                    f"### 🚀 Análise Iniciada com Sucesso!\n\n"
                    f"Seu catálogo de dados foi processado. Aqui está um resumo completo:\n\n"
                    f"#### 1. Metadados do Catálogo\n"
                    f"```json\n{json.dumps(metadata, indent=2)}\n```\n\n"
                    f"#### 2. Resumo Estatístico Global\n"
                    f"{summary_markdown}\n\n"
                    f"#### 3. Perguntas Estratégicas Sugeridas pela IA\n"
                    f"{strategic_questions}"
                )
                # --- FIM DO PIPELINE DE ONBOARDING ---

                st.session_state.messages = [{"role": "assistant", "content": onboarding_message}]
                st.session_state.active_scope = "Analisar Todos em Conjunto"
                st.rerun()
            else:
                st.error("Falha ao processar os dados. Verifique o formato do arquivo.")

# --- TELA DE CHAT (APÓS UPLOAD) ---
else:
    st.title("🍏 Conversando com seus Dados")
    col1, col2 = st.columns([3, 1])
    with col1:
        options = ["Analisar Todos em Conjunto"] + list(st.session_state.dataframes.keys())
        st.session_state.active_scope = st.selectbox("Escopo da Análise:", options, index=options.index(st.session_state.active_scope), label_visibility="collapsed")
    with col2:
        # DevÆGENT-V3.0: st.session_state.clear() é a forma mais robusta de resetar.
        if st.button("Analisar Outro", use_container_width=True, on_click=st.session_state.clear):
            st.rerun()

    st.markdown("---")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            content = msg["content"]
            if isinstance(content, str):
                st.markdown(content)
            elif isinstance(content, dict) and "thought" in content:
                with st.expander("Ver o Raciocínio do Agente", expanded=False):
                    st.info(content["thought"])
            elif "figure" in str(type(content)):
                st.pyplot(content)

    if prompt := st.chat_input(f"Pergunte sobre '{st.session_state.active_scope}'..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    action_json, thought_process = agent_executor(prompt, st.session_state.messages, st.session_state.active_scope)
                    st.session_state.messages.append({"role": "assistant", "content": {"thought": thought_process}})
                    
                    final_response = process_tool_call(action_json, st.session_state.active_scope)

                    if final_response:
                        st.markdown(final_response)
                        st.session_state.messages.append({"role": "assistant", "content": final_response})
                    
                except Exception as e:
                    error_message = f"Ocorreu um erro crítico no ciclo do agente: {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
