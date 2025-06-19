import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import seaborn as sns
import zipfile
from duckduckgo_search import DDGS

# =============================================================================
# FUNÇÕES AUXILIARES DE DADOS
# =============================================================================

@st.cache_data
def load_dataframes_from_zip(zip_file):
    """Carrega todos os CSVs de um arquivo zip em um dicionário de DataFrames."""
    dataframes = {}
    try:
        with zipfile.ZipFile(zip_file, 'r') as z:
            for filename in z.namelist():
                if filename.lower().endswith('.csv') and not filename.startswith('__MACOSX'):
                    with z.open(filename) as f:
                        # Tenta detectar o separador e lida com erros de encoding
                        try:
                            dataframes[filename] = pd.read_csv(f, sep=None, engine='python', on_bad_lines='skip', encoding='utf-8')
                        except UnicodeDecodeError:
                            f.seek(0)
                            dataframes[filename] = pd.read_csv(f, sep=None, engine='python', on_bad_lines='skip', encoding='latin-1')
        return dataframes if dataframes else None
    except Exception as e:
        st.error(f"Erro crítico ao ler o arquivo zip: {e}")
        return None

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
    Executa código Python (Pandas, Matplotlib) em um escopo de dados específico.
    Use esta ferramenta para qualquer tipo de cálculo, manipulação ou visualização de dados.
    O código deve usar um DataFrame chamado `df`.
    Para visualizações, gere uma figura e a armazene em uma variável `resultado`.
    Para outros resultados (números, textos, tabelas), armazene-os em uma variável `resultado`.
    Retorna o conteúdo da variável `resultado` ou uma mensagem de erro.
    """
    try:
        active_df = get_active_df(scope)
        if active_df is None:
            return "Erro: Nenhum dado encontrado para o escopo selecionado."
            
        local_namespace = {'df': active_df, 'plt': plt, 'sns': sns, 'pd': pd, 'io': io, 'resultado': None}
        exec(code, local_namespace)
        
        if 'Figure' in str(type(local_namespace.get('resultado'))):
            fig = local_namespace['resultado']
            plt.close(fig) 
            return fig
        
        return local_namespace.get('resultado', "Código executado, mas sem resultado explícito na variável 'resultado'.")
    except Exception as e:
        return f"Erro ao executar o código Python: {e}"

def web_search(query: str):
    """
    Realiza uma busca na web para encontrar informações atuais ou de conhecimento geral.
    Use para perguntas sobre cotações, definições, notícias ou qualquer coisa que não esteja nos dados.
    """
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
        return "\n".join(results) if results else "Nenhum resultado encontrado na web."
    except Exception as e:
        return f"Erro ao realizar a busca na web: {e}"

def list_available_data():
    """
    Lista todos os arquivos de dados (CSVs) que foram carregados e estão disponíveis para análise.
    """
    if not st.session_state.dataframes:
        return "Nenhum arquivo de dados foi carregado ainda."
    return f"Os seguintes arquivos estão disponíveis para análise: {', '.join(st.session_state.dataframes.keys())}"

def get_data_schema(filename: str):
    """
    Fornece o esquema (nomes das colunas, tipos de dados, valores não nulos) de um arquivo de dados específico.
    """
    if filename not in st.session_state.dataframes:
        return f"Erro: O arquivo '{filename}' não foi encontrado. Use a ferramenta 'list_available_data' para ver os arquivos disponíveis."
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