import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re
from tools import TOOLS

# =============================================================================
# 1. CONFIGURAÇÃO E INICIALIZAÇÃO DO MODELO (COM CACHING)
# =============================================================================
# DevÆGENT-V3.0: Caching do modelo é crucial para performance e economia.
@st.cache_resource
def load_gemini_model():
    """Carrega e configura o modelo Gemini. O cache evita recargas e custos de API."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-pro-latest')
    except Exception as e:
        st.error(f"Erro ao configurar a API do Google. Verifique sua GOOGLE_API_KEY. Detalhe: {e}")
        st.stop()

model = load_gemini_model()

# =============================================================================
# 2. FUNÇÕES DO AGENTE
# =============================================================================

# DevÆGENT-V3.0: Nova função de IA, focada apenas em gerar perguntas.
def suggest_strategic_questions(dataframes):
    """Usa a IA para gerar perguntas inteligentes com base em uma amostra dos dados."""
    try:
        combined_head = pd.concat([df.head(2) for df in dataframes.values()]).to_markdown()
        prompt = f"""
        Você é um Analista de Dados Sênior. Sua tarefa é inspirar um usuário, sugerindo análises inteligentes.
        Baseado na seguinte amostra de dados combinados, gere uma lista de 3 a 4 perguntas estratégicas e acionáveis.
        As perguntas devem explorar diferentes ângulos: uma sobre um insight geral, uma sobre uma correlação, e uma que sugira uma visualização.
        
        Amostra de Dados:
        {combined_head}
        
        Responda apenas com a lista de perguntas.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Não foi possível gerar perguntas: {e}"

def agent_executor(query, chat_history, scope):
    """O cérebro principal do agente ReAct."""
    history_str = "\n".join([f'{msg["role"]}: {str(msg["content"])}' for msg in chat_history if isinstance(msg["content"], str)])
    
    prompt = f"""
    Você é um Analista de Dados Autônomo (ReAct Agent). Use o ciclo Pensamento-Ação para responder ao usuário.

    **Contexto:**
    - Escopo: {scope}
    - Arquivos: {list(st.session_state.dataframes.keys())}
    - Ferramentas: {list(TOOLS.keys())}
    - Histórico: {history_str}

    **Ciclo de Trabalho:**
    1.  **Thought:** Descreva seu plano de ação.
    2.  **Action:** Responda APENAS com um bloco de código JSON. Ex: ```json\n{{"tool": "...", "tool_input": "..."}}\n```
    3.  Se tiver a resposta, use a ferramenta 'final_answer'.

    **Pergunta do Usuário:** "{query}"
    """
    
    response = model.generate_content(prompt)
    thought_process = response.text

    # DevÆGENT-V3.0: Lógica de parsing de JSON robusta.
    try:
        json_block = re.search(r"```json\n(.*?)\n```", thought_process, re.DOTALL)
        json_str = json_block.group(1) if json_block else thought_process[thought_process.find('{'):thought_process.rfind('}')+1]
        action_json = json.loads(json_str)
        return action_json, thought_process
    except (IndexError, json.JSONDecodeError):
        return {"tool": "final_answer", "tool_input": response.text}, thought_process

def process_tool_call(action_json, scope):
    """Executa a ferramenta escolhida pelo agente e retorna o resultado."""
    tool_name = action_json.get("tool")
    tool_input = action_json.get("tool_input")

    if tool_name == "final_answer":
        return tool_input
    
    if tool_name in TOOLS:
        try:
            tool_function = TOOLS[tool_name]
            # Lógica de chamada de ferramenta adaptativa
            if tool_name == "python_code_interpreter":
                output = tool_function(code=tool_input, scope=scope)
            elif tool_name in ["get_data_schema", "web_search"]:
                output = tool_function(query=tool_input)
            else: # Para list_available_data
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
