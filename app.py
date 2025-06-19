import streamlit as st
from agent_logic import agent_executor, process_tool_call, suggest_strategic_questions
from tools import process_uploaded_file, catalog_files_metadata, generate_global_analysis_summary
from ui_components import display_onboarding_results, render_chat_message

# =============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# =============================================================================
st.set_page_config(page_title="DevÆGENT BI", page_icon="⚜️", layout="centered")

def load_css():
    st.markdown("""
    <style>
        :root { --primary-color: #1E90FF; } /* Dodger Blue */
        html, body, [class*="st-"] { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
        .block-container { max-width: 820px; padding: 2rem 1rem; }
        .stButton>button {
            border-radius: 8px; font-weight: 500; border: 1px solid var(--primary-color);
            background-color: white; color: var(--primary-color); transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            border-color: var(--primary-color); background-color: var(--primary-color); color: white;
        }
        .stButton>button:focus { box-shadow: 0 0 0 2px white, 0 0 0 4px var(--primary-color) !important; }
        [data-baseweb="tab-list"] { justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

load_css()

# =============================================================================
# 2. ESTADO DA SESSÃO
# =============================================================================
def initialize_session_state():
    """Inicializa as variáveis no estado da sessão para manter a consistência entre os reruns."""
    if "messages" not in st.session_state: st.session_state.messages = []
    if "dataframes" not in st.session_state: st.session_state.dataframes = None
    if "active_scope" not in st.session_state: st.session_state.active_scope = "Nenhum"
    if "run_prompt_from_suggestion" not in st.session_state: st.session_state.run_prompt_from_suggestion = None
    if "onboarding_data" not in st.session_state: st.session_state.onboarding_data = None

initialize_session_state()

# =============================================================================
# 3. LÓGICA DO CHAT (FUNÇÃO PRINCIPAL)
# =============================================================================
def run_chat_logic(prompt: str):
    """Encapsula a lógica de execução do agente e processamento de resposta."""
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Analisando e executando..."):
            # O agente pensa e decide qual ferramenta usar.
            action_json, thought_process = agent_executor(prompt, st.session_state.messages, st.session_state.active_scope)
            
            # O pensamento do agente é guardado para fins de depuração e transparência.
            st.session_state.messages.append({"role": "assistant", "content": {"thought": thought_process}})
            
            # A ferramenta é executada e a resposta final é obtida.
            final_response = process_tool_call(action_json, st.session_state.active_scope)

            if final_response:
                st.session_state.messages.append({"role": "assistant", "content": final_response})
    
    st.rerun()

# =============================================================================
# 4. RENDERIZAÇÃO DA INTERFACE
# =============================================================================

# --- TELA DE UPLOAD (ESTADO INICIAL) ---
if st.session_state.dataframes is None:
    st.title("⚜️ DevÆGENT BI")
    st.markdown("##### Um agente de IA para análise de dados interativa. Comece fazendo o upload.")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Carregue um arquivo `.zip` (com múltiplos CSVs) ou um único `.csv`",
        type=["zip", "csv"],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        with st.spinner("Processando e catalogando seus dados... Por favor, aguarde."):
            dfs = process_uploaded_file(uploaded_file)
            if dfs:
                st.session_state.dataframes = dfs
                # Análise inicial é feita apenas uma vez.
                st.session_state.onboarding_data = {
                    "metadata": catalog_files_metadata(dfs),
                    "summary_df": generate_global_analysis_summary(dfs),
                    "strategic_questions": suggest_strategic_questions(dfs)
                }
                st.session_state.active_scope = "Analisar Todos em Conjunto"
                st.rerun()

# --- TELA DE CHAT E ANÁLISE (ESTADO PRINCIPAL) ---
else:
    # Mostra o painel de onboarding apenas na primeira vez (quando o chat está vazio).
    if not st.session_state.messages:
        display_onboarding_results(**st.session_state.onboarding_data)
        st.session_state.messages.append({"role": "assistant", "content": "Estou pronto para ajudar. Faça uma pergunta ou escolha uma das sugestões acima."})

    st.title("⚜️ Conversando com seus Dados")
    
    options = ["Analisar Todos em Conjunto"] + list(st.session_state.dataframes.keys())
    st.selectbox("**Escopo da Análise:**", options, key="active_scope", label_visibility="visible")
    
    st.markdown("---")

    # Exibe o histórico de chat
    for msg in st.session_state.messages:
        render_chat_message(msg)

    # DevÆGENT-R (Robustness): A lógica de usar um prompt de um botão de sugestão foi
    # refatorada para ser mais robusta, usando um callback e uma variável de estado dedicada.
    # Isso elimina a necessidade de um `st.rerun()` manual no componente de UI.
    if prompt_from_suggestion := st.session_state.run_prompt_from_suggestion:
        st.session_state.run_prompt_from_suggestion = None  # Reseta imediatamente
        run_chat_logic(prompt_from_suggestion)

    elif prompt_from_input := st.chat_input(f"Pergunte sobre '{st.session_state.active_scope}'..."):
        run_chat_logic(prompt_from_input)
