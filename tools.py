import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import seaborn as sns
import zipfile
from duckduckgo_search import DDGS

# =============================================================================
# FUNÇÕES DO PIPELINE DE ONBOARDING E DADOS
# =============================================================================

@st.cache_data
def process_uploaded_file(uploaded_file):
    """Processa um arquivo .zip ou .csv e retorna um dicionário de DataFrames."""
    if uploaded_file.name.lower().endswith(".zip"):
        return unpack_zip_to_dataframes(uploaded_file)
    elif uploaded_file.name.lower().endswith(".csv"):
        return {uploaded_file.name: pd.read_csv(uploaded_file, sep=None, engine='python', on_bad_lines='skip')}
    return None

def unpack_zip_to_dataframes(zip_file):
    """Extrai todos os CSVs de um arquivo zip."""
    dataframes = {}
    try:
        with zipfile.ZipFile(zip_file, 'r') as z:
            for name in z.namelist():
                if name.lower().endswith('.csv') and not name.startswith('__MACOSX'):
                    with z.open(name) as f:
                        dataframes[name] = pd.read_csv(f, sep=None, engine='python', on_bad_lines='skip')
        return dataframes if dataframes else None
    except Exception as e:
        st.error(f"Erro ao processar o arquivo zip: {e}")
        return None

def catalog_files_metadata(dataframes):
    """Cria um dicionário com os metadados de cada DataFrame."""
    catalog = {}
    for name, df in dataframes.items():
        catalog[name] = {"linhas": len(df), "colunas": len(df.columns), "nomes_colunas": list(df.columns)}
    return catalog

def generate_global_analysis_summary(dataframes):
    """Combina todos os DataFrames e gera um resumo estatístico."""
    if not dataframes: return pd.DataFrame()
    combined_df = pd.concat(dataframes.values(), ignore_index=True)
    return combined_df.describe(include='all').fillna("N/A")

def get_active_df(scope: str):
    """Retorna o DataFrame ativo com base no escopo selecionado."""
    if scope == "Analisar Todos em Conjunto":
        return pd.concat(st.session_state.dataframes.values(), ignore_index=True)
    return st.session_state.dataframes.get(scope)

# =============================================================================
# FERRAMENTAS DO AGENTE
# =============================================================================

def python_code_interpreter(code: str, scope: str):
    """
    Executa código Python para análise ou visualização de dados. Essencial para cálculos, manipulações e gráficos.
    O código DEVE usar um DataFrame chamado `df`.
    Para retornar um valor (texto, número, tabela), salve-o em uma variável chamada `resultado`.
    Para gerar um gráfico, crie um objeto de figura Matplotlib (ex: `fig, ax = plt.subplots()`) e salve a figura `fig` na variável `resultado`.
    """
    try:
        active_df = get_active_df(scope)
        if active_df is None: return "Erro: Nenhum dado no escopo."
        
        local_namespace = {'df': active_df, 'plt': plt, 'sns': sns, 'pd': pd, 'resultado': None}
        exec(code, local_namespace)
        
        if 'Figure' in str(type(local_namespace.get('resultado'))):
            fig = local_namespace['resultado']
            plt.close(fig) 
            return fig
        return local_namespace.get('resultado', "Código executado com sucesso, sem resultado explícito.")
    except Exception as e:
        return f"Erro ao executar código: {e}"

def web_search(query: str):
    """
    Realiza uma busca na web para encontrar informações atuais ou de conhecimento geral. Use para perguntas sobre cotações, definições, notícias ou qualquer coisa que não esteja nos dados.
    """
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
        return "\n".join(results) if results else "Nenhum resultado encontrado."
    except Exception as e:
        return f"Erro na busca web: {e}"

def list_available_data():
    """
    Lista os nomes de todos os arquivos de dados (CSVs) que foram carregados e estão disponíveis para análise.
    """
    return f"Arquivos disponíveis: {', '.join(st.session_state.dataframes.keys())}"

def get_data_schema(filename: str):
    """
    Fornece o esquema detalhado (nomes das colunas, tipos de dados, contagem de valores não nulos) de um arquivo de dados específico.
    """
    if filename not in st.session_state.dataframes:
        return f"Erro: Arquivo '{filename}' não encontrado. Use a ferramenta 'list_available_data' para ver os nomes corretos."
    df = st.session_state.dataframes[filename]
    buffer = io.StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()

TOOLS = {
    "python_code_interpreter": python_code_interpreter,
    "web_search": web_search,
    "list_available_data": list_available_data,
    "get_data_schema": get_data_schema
}
