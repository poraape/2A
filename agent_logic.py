import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re
from tools import TOOLS
from prompts import get_agent_prompt, get_strategic_questions_prompt

@st.cache_resource
def load_gemini_model():
    """Carrega e configura o modelo Gemini."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"Erro ao configurar a API do Google: {e}")
        st.stop()

model = load_gemini_model()

def suggest_strategic_questions(dataframes):
    """Gera perguntas estratégicas com base em uma amostra dos dados."""
    try:
        combined_head = pd.concat([df.head(3) for df in dataframes.values()]).to_markdown(index=False)
        prompt = get_strategic_questions_prompt(combined_head)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Não foi possível gerar perguntas estratégicas: {e}"

def extract_json_from_response(text):
    """Extrai um bloco de código JSON de uma string de forma robusta."""
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != 0:
            return text[start:end]
    except:
        return None
    return None

def agent_executor(query, chat_history, scope, observations):
    """
    Executa um único passo do ciclo ReAct.
    """
    tools_description = "\n".join([f"- `{name}`: {func.__doc__.strip()}" for name, func in TOOLS.items()])
    available_files = list(st.session_state.dataframes.keys())

    # DevÆGENT-R (Correção): A variável `query` agora é passada diretamente para a função de criação do prompt.
    # A linha problemática `.format(query=query)` foi removida.
    prompt = get_agent_prompt(scope, chat_history, tools_description, available_files, observations, query)
    
    response = model.generate_content(prompt)
    thought_process = response.text
    json_str = extract_json_from_response(thought_process)
    
    if not json_str:
        return {"tool": "final_answer", "tool_input": thought_process}, thought_process

    try:
        action_json = json.loads(json_str)
        return action_json, thought_process
    except json.JSONDecodeError:
        error_message = f"Ocorreu um erro. O agente gerou uma resposta com JSON malformado. Resposta recebida:\n{thought_process}"
        return {"tool": "final_answer", "tool_input": error_message}, thought_process
def process_tool_call(action_json, scope):
    """Processa a chamada da ferramenta decidida pelo agente."""
    tool_name = action_json.get("tool")
    tool_input = action_json.get("tool_input")

    # A ferramenta `final_answer` não é processada aqui, mas sim no loop de controle.
    if tool_name not in TOOLS:
        return f"Erro: O agente tentou usar uma ferramenta desconhecida: `{tool_name}`."

    try:
        tool_function = TOOLS[tool_name]
        
        # Adapta a chamada com base nos argumentos da ferramenta
        if tool_name == "python_code_interpreter":
            output = tool_function(code=tool_input, scope=scope)
        elif tool_name == "get_data_schema":
            output = tool_function(filename=tool_input)
        elif tool_name == "web_search":
            output = tool_function(query=tool_input)
        else: # Para ferramentas sem argumentos
            output = tool_function()

        return output
    except Exception as e:
        return f"Erro ao executar a ferramenta `{tool_name}`: {e}"
