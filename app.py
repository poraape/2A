import streamlit as st
from agent_logic import agent_executor, process_tool_call, suggest_strategic_questions
from tools import process_uploaded_file, catalog_files_metadata, generate_global_analysis_summary, TOOLS
from ui_components import display_onboarding_results, render_chat_message

# =============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO (UI Revertida)
# =============================================================================
st.set_page_config(page_title="Data Insights Pro", page_icon="🍏", layout="centered")

def load_css():
    st.markdown("""
    <style>
        :root { --primary-color: #007AFF; } /* Apple Blue */
        html, body, [class*="st-"] { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
        .block-container { max-width: 760px; padding: 2rem 1rem; }
        .stButton>button {
            border-radius: 10px; font-weight: 500; border: 1px solid var(--primary-color);
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
    if "messages" not in st.session_state: st.session_state.messages = []
    if "dataframes" not in st.session_state: st.session_state.dataframes = None
    if "active_scope" not in st.session_state: st.session_state.active_scope = "Nenhum"
    if "run_prompt_from_suggestion" not in st.session_state: st.session_state.run_prompt_from_suggestion = None
    if "onboarding_data" not in st.session_state: st.session_state.onboarding_data = None

initialize_session_state()

# =============================================================================
# 3. LÓGICA DO CHAT (AGORA COM LOOP ReAct)
# =============================================================================
def run_chat_logic(prompt: str):
    """
    Encapsula a lógica de execução do agente em um loop ReAct multi-passo.
    """
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # DevÆGENT-R (Robustness): MAX_STEPS previne loops infinitos, uma salvaguarda crucial para agentes autônomos.
    MAX_STEPS = 7
    observations = []
    
    with st.chat_message("assistant"):
        for step in range(MAX_STEPS):
            with st.spinner(f"Passo {step + 1}: Pensando..."):
                action_json, thought_process = agent_executor(prompt, st.session_state.messages, st.session_state.active_scope, observations)
            
            # Exibe o pensamento do agente
            st.session_state.messages.append({"role": "assistant", "content": {"thought": thought_process}})
            st.rerun() # Atualiza a UI para mostrar o pensamento imediatamente

            tool_name = action_json.get("tool")
            if tool_name == "final_answer":
                final_response = action_json.get("tool_input", "Análise concluída.")
                st.session_state.messages.append({"role": "assistant", "content": final_response})
                st.rerun()
                return # Encerra o loop

            # Executa a ferramenta e coleta a observação
            with st.spinner(f"Passo {step + 1}: Executando ferramenta `{tool_name}`..."):
                tool_output = process_tool_call(action_json, st.session_state.active_scope)

            if "figure" in str(type(tool_output)):
                # Se a ferramenta retorna um gráfico, exibe-o e encerra.
                st.session_state.messages.append({"role": "assistant", "content": tool_output})
                st.rerun()
                return

            observation_text = f"**Resultado da Ferramenta `{tool_name}`:**\n\n```\n{str(tool_output)}\n```"
            observations.append(observation_text)
            st.session_state.messages.append({"role": "assistant", "content": {"observation": str(tool_output), "tool": tool_name}})
            st.rerun() # Atualiza a UI para mostrar a observação
        
        # Se o loop terminar por atingir MAX_STEPS
        st.warning(f"O agente atingiu o limite de {MAX_STEPS} passos sem chegar a uma resposta final. Por favor, tente reformular a pergunta.")
        st.session_state.messages.append({"role": "assistant", "content": "Não consegui concluir a análise. Tente ser mais específico."})
        st.rerun()

# =============================================================================
# 4. RENDERIZAÇÃO DA INTERFACE
# =============================================================================

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
                st.session_state.onboarding_data = {
                    "metadata": catalog_files_metadata(dfs),
                    "summary_df": generate_global_analysis_summary(dfs),
                    "strategic_questions": suggest_strategic_questions(dfs)
                }
                st.session_state.active_scope = "Analisar Todos em Conjunto"
                st.rerun()
else:
    if not st.session_state.messages:
        display_onboarding_results(**st.session_state.onboarding_data)
        st.session_state.messages.append({"role": "assistant", "content": "Estou pronto para ajudar. Faça uma pergunta ou escolha uma das sugestões."})

    st.title("🍏 Conversando com seus Dados")
    
    options = ["Analisar Todos em Conjunto"] + list(st.session_state.dataframes.keys())
    st.selectbox("Escopo da Análise:", options, key="active_scope", label_visibility="collapsed")
    st.markdown("---")

    for msg in st.session_state.messages:
        render_chat_message(msg)

    if prompt_from_suggestion := st.session_state.run_prompt_from_suggestion:
        st.session_state.run_prompt_from_suggestion = None
        run_chat_logic(prompt_from_suggestion)

    elif prompt_from_input := st.chat_input(f"Pergunte sobre '{st.session_state.active_scope}'..."):
        run_chat_logic(prompt_from_input)
