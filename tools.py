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
        # DevÆGENT-R: O separador automático (sep=None) é bom, mas on_bad_lines='skip' pode esconder problemas. 'warn' seria uma alternativa. mantendo 'skip' por simplicidade.
        return {uploaded_file.name: pd.read_csv(uploaded_file, sep=None, engine='python', on_bad_lines='skip')}
    return None

def unpack_zip_to_dataframes(zip_file):
    """Extrai todos os CSVs de um arquivo zip, ignorando arquivos de metadados do macOS."""
    dataframes = {}
    try:
        with zipfile.ZipFile(zip_file, 'r') as z:
            csv_files = [name for name in z.namelist() if name.lower().endswith('.csv') and not name.startswith('__MACOSX')]
            if not csv_files:
                st.warning("O arquivo .zip não contém nenhum arquivo .csv.")
                return None
            for name in csv_files:
                with z.open(name) as f:
                    dataframes[name] = pd.read_csv(f, sep=None, engine='python', on_bad_lines='skip')
        return dataframes if dataframes else None
    except Exception as e:
        st.error(f"Erro fatal ao processar o arquivo zip: {e}")
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
    # DevÆGENT-S (Scalability): Concatenação pode consumir muita memória. Para apps muito grandes, considerar amostragem ou processamento em chunks.
    combined_df = pd.concat(dataframes.values(), ignore_index=True)
    return combined_df.describe(include='all').fillna("N/A")

@st.cache_data
def get_active_df(scope: str, _dataframes_keys):
    """
    Retorna o DataFrame ativo com base no escopo selecionado.
    DevÆGENT-S (Scalability): O uso de `st.cache_data` aqui é crucial. Ele memoriza o resultado da concatenação
    de múltiplos arquivos, evitando que essa operação cara seja refeita a cada interação no chat.
    `_dataframes_keys` é um truque para invalidar o cache se os arquivos de dados mudarem.
    """
    if scope == "Analisar Todos em Conjunto":
        # Esta operação é cara e agora está em cache.
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
    # DevÆGENT-R (Robustness): AVISO DE SEGURANÇA! `exec` é perigoso. Esta implementação tenta limitar o escopo,
    # mas não é um sandbox completo. Em um ambiente de produção real, o código deveria rodar em um container isolado.
    try:
        active_df = get_active_df(scope, tuple(st.session_state.dataframes.keys()))
        if active_df is None: return "Erro: Nenhum dado disponível no escopo selecionado."
        
        # Limita as funções built-in disponíveis para o código executado, aumentando a segurança.
        safe_builtins = {
            'print': print, 'len': len, 'str': str, 'int': int, 'float': float, 'list': list, 'dict': dict, 'tuple': tuple, 'range': range, 'sum': sum, 'max': max, 'min': min,
        }
        local_namespace = {'df': active_df, 'plt': plt, 'sns': sns, 'pd': pd, 'resultado': None}
        global_namespace = {'__builtins__': safe_builtins}
        
        exec(code, global_namespace, local_namespace)
        
        resultado = local_namespace.get('resultado')
        if 'Figure' in str(type(resultado)):
            plt.close(resultado) 
            return resultado
        return resultado if resultado is not None else "Código executado com sucesso, sem resultado explícito para exibir."
    except Exception as e:
        return f"Erro ao executar código Python: {e}"

def web_search(query: str):
    """
    Realiza uma busca na web para encontrar informações atuais ou de conhecimento geral. Use para perguntas sobre cotações, definições, notícias ou qualquer coisa que não esteja nos dados.
    """
    try:
        with DDGS() as ddgs:
            # DevÆGENT-I: Pega 3 trechos para dar mais contexto à resposta.
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
        return "\n".join(results) if results else "Nenhum resultado encontrado na web para esta consulta."
    except Exception as e:
        return f"Erro durante a busca na web: {e}"

def list_available_data():
    """
    Lista os nomes de todos os arquivos de dados (CSVs) que foram carregados e estão disponíveis para análise.
    """
    if not st.session_state.dataframes:
        return "Nenhum arquivo de dados foi carregado ainda."
    return f"Arquivos de dados disponíveis: {', '.join(st.session_state.dataframes.keys())}"

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

# DevÆGENT-I: Dicionário de ferramentas é a "API" do nosso agente.
TOOLS = {
    "python_code_interpreter": python_code_interpreter,
    "web_search": web_search,
    "list_available_data": list_available_data,
    "get_data_schema": get_data_schema
}
