import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re
from tools import TOOLS

# =============================================================================
# 1. CONFIGURAÇÃO E INICIALIZAÇÃO DO MODELO (COM CACHING)
# =============================================================================
@st.cache_resource
def load_gemini_model():
    """Carrega e configura o modelo Gemini. O cache evita recargas e custos de API."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        # DevÆGENT-Flash: Modelo alterado para a versão Flash.
        return genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"Erro ao configurar a API do Google. Verifique sua GOOGLE_API_KEY. Detalhe: {e}")
        st.stop()

model = load_gemini_model()

# =============================================================================
# 2. FUNÇÕES DO AGENTE
# =============================================================================
def suggest_strategic_questions(dataframes):
    # ... (sem alterações nesta função, já é simples o suficiente para o Flash)
    try:
        combined_head = pd.concat([df.head(2) for df in dataframes.values()]).to_markdown()
        prompt = f"""
        Você é um Analista de Dados. Baseado na amostra de dados abaixo, gere 3 perguntas inteligentes para análise.
        Amostra:
        {combined_head}
        Responda apenas com a lista de perguntas.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Não foi possível gerar perguntas: {e}"

def agent_executor(query, chat_history, scope):
    """O cérebro principal do agente ReAct, com prompt reforçado para o Gemini Flash."""
    history_str = "\n".join([f'{msg["role"]}: {str(msg["content"])}' for msg in chat_history if isinstance(msg["content"], str)])
    
    tools_description = "\n".join([f"- `{name}`: {func.__doc__.strip()}" for name, func in TOOLS.items()])
    
    # DevÆGENT-Flash: Prompt reforçado com regras mais estritas e explícitas para o Flash.
    prompt = f"""
    Você é um agente de análise de dados. Siga as regras estritamente.

    **REGRAS GERAIS:**
    1.  **Pense Primeiro:** Seu primeiro passo é SEMPRE o "Thought".
    2.  **Aja Depois:** Seu segundo passo é SEMPRE a "Action" em formato JSON.
    3.  **Uma Ferramenta por Vez:** Escolha apenas uma ferramenta por ciclo.

    **CONTEXTO:**
    - Escopo da Análise: {scope}
    - Arquivos Disponíveis: {list(st.session_state.dataframes.keys())}
    - Histórico: {history_str}

    **FERRAMENTAS (Use as descrições para decidir):**
    {tools_description}

    **REGRA CRÍTICA PARA `python_code_interpreter`:**
    - Os dados do escopo já estão na variável `df`.
    - **NUNCA, JAMAIS** use `pd.read_csv()`. Use a variável `df` diretamente.
    - **Exemplo CORRETO:** `resultado = df['coluna'].sum()`
    - **Exemplo ERRADO:** `df = pd.read_csv(...)`

    **CICLO DE TRABALHO (Siga exatamente):**
    1.  **Thought:** (OBRIGATÓRIO) Descreva seu plano. Se for usar uma ferramenta, qual e por quê? Se for escrever código, qual código?
    2.  **Action:** (OBRIGATÓRIO) Escreva um bloco de código JSON contendo sua ação.
        ```json
        {{"tool": "NOME_DA_FERRAMENTA", "tool_input": "ENTRADA_DA_FERRAMENTA"}}
        ```
    3.  Se a resposta já foi encontrada, use a ferramenta `final_answer`.

    **INICIE AGORA.**
    **Pergunta do Usuário:** "{query}"
    """
    
    response = model.generate_content(prompt)
    thought_process = response.text

    try:
        json_block = re.search(r"```json\n(.*?)\n```", thought_process, re.DOTALL)
        json_str = json_block.group(1) if json_block else thought_process[thought_process.find('{'):thought_process.rfind('}')+1]
        action_json = json.loads(json_str)
        return action_json, thought_process
    except (IndexError, json.JSONDecodeError):
        return {"tool": "final_answer", "tool_input": response.text}, thought_process

def process_tool_call(action_json, scope):
    # ... (sem alterações nesta função)
    tool_name = action_json.get("tool")
    tool_input = action_json.get("tool_input")

    if tool_name == "final_answer":
        return tool_input
    
    if tool_name in TOOLS:
        try:
            tool_function = TOOLS[tool_name]
            if tool_name == "python_code_interpreter":
                output = tool_function(code=tool_input, scope=scope)
            elif tool_name == "get_data_schema":
                output = tool_function(filename=tool_input)
            elif tool_name == "web_search":
                output = tool_function(query=tool_input)
            else:
                output = tool_function()

            if "figure" in str(type(output)):
                st.pyplot(output)
                st.session_state.messages.append({"role": "assistant", "content": output})
                return "Gerei um gráfico com base na sua solicitação. Veja acima."
            else:
                return f"**Resultado da Ferramenta `{tool_name}`:**\n\n```\n{str(output)}\n```"
        except Exception as e:
            return f"Erro ao executar a ferramenta `{tool_name}`: {e}"
    else:
        return f"Erro: O agente tentou usar uma ferramenta desconhecida: `{tool_name}`."
