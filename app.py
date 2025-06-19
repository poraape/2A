# 🍏 Data Insights Pro — Versão Avançada com Pipeline Multi-Agente

import streamlit as st
import pandas as pd
import zipfile
import io
import matplotlib.pyplot as plt
import seaborn as sns
import json
from duckduckgo_search import DDGS
import google.generativeai as genai

# =============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# =============================================================================

st.set_page_config(page_title="Data Insights Pro", page_icon="🍏", layout="centered")

st.markdown("""
<style>
    html, body, [class*="st-"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    .block-container { max-width: 720px; padding: 3rem 1rem; }
    [data-testid="stFileUploader"] { border: 1.5px dashed #d0d0d5; background: #f8f8fa; border-radius: 12px; padding: 2rem; }
    [data-testid="stAlert"] { background: #f0f0f5; border-radius: 12px; }
    .stButton>button { border-radius: 10px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. CONFIGURAÇÃO GEMINI
# =============================================================================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
except Exception:
    st.error("Chave da API do Google não configurada.")
    st.stop()

# =============================================================================
# 3. FUNÇÕES PRINCIPAIS DO PIPELINE
# =============================================================================

def receive_and_validate_file(uploaded_file):
    if uploaded_file.name.endswith(".zip"):
        return unpack_zip_to_dataframes(uploaded_file)
    elif uploaded_file.name.endswith(".csv"):
        return {uploaded_file.name: pd.read_csv(uploaded_file, on_bad_lines='skip')}
    else:
        st.error("Formato não suportado. Envie .zip ou .csv.")
        return None

def unpack_zip_to_dataframes(zip_file):
    dataframes = {}
    try:
        with zipfile.ZipFile(zip_file, 'r') as z:
            for name in z.namelist():
                if name.endswith('.csv'):
                    with z.open(name) as f:
                        dataframes[name] = pd.read_csv(f, on_bad_lines='skip')
        return dataframes if dataframes else None
    except Exception as e:
        st.error(f"Erro ao processar zip: {e}")
        return None

def catalog_files_metadata(dataframes):
    catalog = {}
    for name, df in dataframes.items():
        catalog[name] = {
            "linhas": len(df),
            "colunas": list(df.columns),
            "tipos": df.dtypes.astype(str).to_dict()
        }
    return catalog

def generate_global_analysis_summary(dataframes):
    combined = pd.concat(dataframes.values(), ignore_index=True)
    return combined.describe(include='all')

def suggest_strategic_questions(dataframes):
    combined = pd.concat(dataframes.values(), ignore_index=True)
    prompt = f"""
    Você é um analista de dados. A seguir, um sample dos dados:
    {combined.head().to_markdown()}
    Gere um resumo executivo + 4 perguntas estratégicas para análise dos dados.
    """
    response = model.generate_content(prompt)
    return response.text

# =============================================================================
# 4. FERRAMENTAS DO AGENTE
# =============================================================================

def python_code_interpreter(code: str, scope: str):
    try:
        df = pd.concat(st.session_state.dataframes.values(), ignore_index=True) if scope == "Analisar Todos em Conjunto" else st.session_state.dataframes[scope]
        namespace = {'df': df, 'plt': plt, 'sns': sns, 'pd': pd, 'io': io}
        exec(code, namespace)
        return namespace.get('resultado', "Código executado com sucesso.")
    except Exception as e:
        return f"Erro: {e}"

def web_search(query: str):
    with DDGS() as ddgs:
        results = [r['body'] for r in ddgs.text(query, max_results=3)]
    return "\n".join(results) or "Nenhum resultado encontrado."

def list_available_data():
    return "Arquivos: " + ", ".join(st.session_state.dataframes.keys())

def get_data_schema(filename: str):
    df = st.session_state.dataframes.get(filename)
    if df is None:
        return f"Arquivo '{filename}' não encontrado."
    buf = io.StringIO()
    df.info(buf=buf)
    return buf.getvalue()

TOOLS = {
    "python_code_interpreter": python_code_interpreter,
    "web_search": web_search,
    "list_available_data": list_available_data,
    "get_data_schema": get_data_schema
}

# =============================================================================
# 5. AGENTE EXECUTOR
# =============================================================================

def agent_executor(query, chat_history, scope):
    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history])
    context = f"Escopo: {scope}\nArquivos: {list(st.session_state.dataframes.keys())}\nHistórico:\n{history_str}"
    prompt = f"""
    Você é um agente autônomo. Use o ciclo: Thought → Action (tool + input) → Observation → Repeat → Final Answer.
    Query: {query}\n{context}
    """
    response = model.generate_content(prompt)
    try:
        action_block = response.text.split('```json')[1].split('```')[0]
        return json.loads(action_block), response.text
    except:
        return {"tool": "final_answer", "tool_input": response.text}, response.text

# =============================================================================
# 6. INTERFACE STREAMLIT
# =============================================================================

if "messages" not in st.session_state: st.session_state.messages = []
if "dataframes" not in st.session_state: st.session_state.dataframes = None
if "active_scope" not in st.session_state: st.session_state.active_scope = "Nenhum"

if st.session_state.dataframes is None:
    st.title("🍏 Data Insights Pro")
    uploaded_file = st.file_uploader("Upload .zip ou .csv", type=["zip", "csv"])
    if uploaded_file:
        dfs = receive_and_validate_file(uploaded_file)
        if dfs:
            st.session_state.dataframes = dfs
            metadata = catalog_files_metadata(dfs)
            strategic = suggest_strategic_questions(dfs)
            summary = generate_global_analysis_summary(dfs).to_markdown()
            onboarding = f"### 📦 Arquivos Carregados\n{json.dumps(metadata, indent=2)}\n\n### 📊 Resumo Global\n{summary}\n\n### 🧠 Perguntas Sugeridas\n{strategic}"
            st.session_state.messages = [{"role": "assistant", "content": onboarding}]
            st.session_state.active_scope = "Analisar Todos em Conjunto"
            st.rerun()
        else:
            st.error("Falha ao processar os dados.")
else:
    st.title("🍏 Conversando com seus Dados")
    col1, col2 = st.columns([3, 1])
    with col1:
        options = ["Analisar Todos em Conjunto"] + list(st.session_state.dataframes.keys())
        st.session_state.active_scope = st.selectbox("Escopo da Análise:", options, index=options.index(st.session_state.active_scope))
    with col2:
        if st.button("Novo Catálogo"):
            st.session_state.clear()
            st.rerun()

    st.markdown("---")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if isinstance(msg["content"], str):
                st.markdown(msg["content"])
            elif "thought" in msg["content"]:
                with st.expander("Ver raciocínio do agente"):
                    st.markdown(msg["content"]["thought"])

    if prompt := st.chat_input(f"Pergunte sobre '{st.session_state.active_scope}'..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    action_json, thought = agent_executor(prompt, st.session_state.messages, st.session_state.active_scope)
                    st.session_state.messages.append({"role": "assistant", "content": {"thought": thought}})
                    with st.expander("Ver raciocínio do agente"):
                        st.markdown(thought)

                    tool, tool_input = action_json.get("tool"), action_json.get("tool_input")
                    if tool == "final_answer":
                        st.markdown(tool_input)
                        st.session_state.messages.append({"role": "assistant", "content": tool_input})
                    elif tool in TOOLS:
                        output = (TOOLS[tool](tool_input, st.session_state.active_scope)
                                  if tool == "python_code_interpreter"
                                  else TOOLS[tool](tool_input))
                        if isinstance(output, plt.Figure):
                            st.pyplot(output)
                            st.session_state.messages.append({"role": "assistant", "content": output})
                        else:
                            st.markdown(f"**{tool}:**\n{output}")
                            st.session_state.messages.append({"role": "assistant", "content": output})
                    else:
                        st.markdown("Ferramenta desconhecida.")
                except Exception as e:
                    st.error(f"Erro interno: {e}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Erro: {e}"})
