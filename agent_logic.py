import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re
from tools import TOOLS

# =============================================================================
# 1. CONFIGURAÇÃO E INICIALIZAÇÃO DO MODELO
# =============================================================================

@st.cache_resource
def load_gemini_model():
    """Carrega e configura o modelo Gemini. O cache evita recargas desnecessárias."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-pro-latest')
    except Exception as e:
        st.error(f"Erro ao configurar a API do Google. Verifique sua GOOGLE_API_KEY nos secrets. Detalhe: {e}")
        st.stop()

model = load_gemini_model()

# =============================================================================
# 2. FUNÇÕES DO AGENTE
# =============================================================================

def agent_onboarding(dataframes_dict):
    """Gera um resumo de boas-vindas e perguntas estratégicas sobre os dados carregados."""
    summary = "### 🗂️ Catálogo de Dados Carregado\n\n"
    summary += f"Detectei e carreguei com sucesso **{len(dataframes_dict)}** arquivo(s):\n"
    for name, df in dataframes_dict.items():
        summary += f"- **{name}**: `{len(df)}` linhas, `{len(df.columns)}` colunas.\n"
    
    sample_summary = "\n".join([f"Amostra de '{name}':\n{df.head(2).to_markdown()}" for name, df in dataframes_dict.items()])
    
    prompt = f"""
    Você é um Analista de Dados Estratégico. Sua missão é fazer o onboarding de um novo conjunto de dados.
    
    RESUMO DO CATÁLOGO:
    {summary}
    
    AMOSTRAS DOS DADOS:
    {sample_summary}
    
    Com base nisso, realize as seguintes tarefas:
    1.  **Resumo Executivo:** Escreva um parágrafo conciso sobre o potencial analítico combinado desses dados.
    2.  **Perguntas Estratégicas:** Formule uma lista de 3 a 4 perguntas inteligentes que um usuário poderia fazer, cobrindo análises individuais, combinadas e de visualização.
    """
    response = model.generate_content(prompt)
    return summary + "\n" + response.text

def agent_executor(query, chat_history, scope):
    """Gera o pensamento e a ação da ferramenta para o LLM (ciclo ReAct)."""
    history_str = "\n".join([f'{msg["role"]}: {str(msg["content"])}' for msg in chat_history if isinstance(msg["content"], str)])
    
    prompt = f"""
    Você é um Analista de Dados Autônomo (ReAct Agent). Sua missão é responder à pergunta do usuário usando o ciclo Pensamento-Ação.

    **Contexto da Análise:**
    - Escopo Atual: {scope}
    - Arquivos Disponíveis: {list(st.session_state.dataframes.keys())}
    - Ferramentas Disponíveis com suas descrições:
        - `python_code_interpreter(code: str, scope: str)`: {TOOLS['python_code_interpreter'].__doc__}
        - `web_search(query: str)`: {TOOLS['web_search'].__doc__}
        - `list_available_data(query: str = None)`: {TOOLS['list_available_data'].__doc__}
        - `get_data_schema(filename: str)`: {TOOLS['get_data_schema'].__doc__}
    - Histórico da Conversa:
    {history_str}

    **Ciclo de Trabalho:**
    1.  **Thought:** Descreva seu plano de ação passo a passo. Pense em qual ferramenta é a melhor para a tarefa.
    2.  **Action:** Responda APENAS com um bloco de código JSON contendo a ferramenta e sua entrada.
        Exemplo: ```json\n{{"tool": "web_search", "tool_input": "cotação BRL USD"}}\n```
        Se você já tem a resposta, use a ferramenta 'final_answer'.
        Exemplo: ```json\n{{"tool": "final_answer", "tool_input": "A resposta final é..."}}\n```

    **Inicie o processo para a pergunta do usuário.**
    **Pergunta:** "{query}"
    """
    
    response = model.generate_content(prompt)
    thought_process = response.text

    try:
        # Extrai o JSON de dentro do bloco de código Markdown
        json_block = re.search(r"```json\n(.*?)\n```", thought_process, re.DOTALL)
        if json_block:
            json_str = json_block.group(1)
        else: # Fallback para JSON sem formatação
            json_str = thought_process[thought_process.find('{'):thought_process.rfind('}')+1]
        
        action_json = json.loads(json_str)
        return action_json, thought_process
    except (IndexError, json.JSONDecodeError):
        return {"tool": "final_answer", "tool_input": f"Não consegui usar uma ferramenta, mas aqui está minha resposta direta:\n\n{response.text}"}, thought_process

def process_tool_call(action_json, scope):
    """Executa a ferramenta escolhida pelo agente e retorna o resultado formatado."""
    tool_name = action_json.get("tool")
    tool_input = action_json.get("tool_input")

    if tool_name == "final_answer":
        return tool_input
    
    if tool_name in TOOLS:
        try:
            tool_function = TOOLS[tool_name]
            # Passa os argumentos corretos para cada função
            if tool_name == "python_code_interpreter":
                tool_output = tool_function(code=tool_input, scope=scope)
            elif tool_name == "get_data_schema":
                 tool_output = tool_function(filename=tool_input)
            elif tool_name == "list_available_data":
                 tool_output = tool_function()
            else:
                tool_output = tool_function(query=tool_input)

            # Lida com a saída da ferramenta
            if "figure" in str(type(tool_output)):
                st.pyplot(tool_output)
                st.session_state.messages.append({"role": "assistant", "content": tool_output})
                return "Gerei um gráfico com base na sua solicitação. Veja acima."
            else:
                return f"**Resultado da Ferramenta `{tool_name}`:**\n\n```\n{str(tool_output)}\n```"

        except Exception as e:
            return f"Erro ao executar a ferramenta `{tool_name}`: {e}"
    else:
        return f"Erro: O agente tentou usar uma ferramenta desconhecida: `{tool_name}`."