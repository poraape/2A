import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re
from tools import TOOLS
from prompts import get_agent_prompt, get_strategic_questions_prompt # DevÆGENT-R: Importa prompts do arquivo dedicado.

# =============================================================================
# 1. CONFIGURAÇÃO E INICIALIZAÇÃO DO MODELO (COM CACHING)
# =============================================================================
@st.cache_resource
def load_gemini_model():
    """Carrega e configura o modelo Gemini. O cache evita recargas e custos de API."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"Erro ao configurar a API do Google. Verifique sua GOOGLE_API_KEY. Detalhe: {e}")
        st.stop()

model = load_gemini_model()

# =============================================================================
# 2. FUNÇÕES DO AGENTE
# =============================================================================
def suggest_strategic_questions(dataframes):
    """Gera perguntas estratégicas com base em uma amostra dos dados."""
    try:
        # DevÆGENT-I: Garante que a amostra não seja excessivamente grande.
        combined_head = pd.concat([df.head(3) for df in dataframes.values()]).to_markdown(index=False)
        # DevÆGENT-R: Utiliza a função de prompt para manter a lógica limpa.
        prompt = get_strategic_questions_prompt(combined_head)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Não foi possível gerar perguntas estratégicas: {e}"

def extract_json_from_response(text):
    """Extrai um bloco de código JSON de uma string, mesmo com texto adicional ao redor."""
    # DevÆGENT-R (Robustness): Este Regex é mais resiliente. Procura por um bloco ```json ... ``` ou, como fallback, pelo JSON mais abrangente possível.
    # Isso evita falhas se o modelo adicionar saudações ou comentários fora do bloco de código.
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    
    # Fallback para encontrar o primeiro '{' e o último '}'
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != 0:
            return text[start:end]
    except:
        return None
    return None

def agent_executor(query, chat_history, scope):
    """Executa um ciclo de pensamento-ação (ReAct) para responder à consulta do usuário."""
    history_str = "\n".join([f'{msg["role"]}: {str(msg["content"])}' for msg in chat_history if isinstance(msg["content"], str)])
    
    tools_description = "\n".join([f"- `{name}`: {func.__doc__.strip()}" for name, func in TOOLS.items()])
    available_files = list(st.session_state.dataframes.keys())

    # DevÆGENT-R: Utiliza a função de prompt para construir o prompt do agente.
    prompt = get_agent_prompt(scope, history_str, tools_description, available_files)
    prompt = prompt.format(query=query) # Formata a query no final
    
    response = model.generate_content(prompt)
    thought_process = response.text

    # DevÆGENT-R (Robustness): Utiliza a função de extração de JSON dedicada e mais robusta.
    json_str = extract_json_from_response(thought_process)
    
    if not json_str:
        # Se nenhum JSON for encontrado, assume que a resposta inteira é a resposta final.
        return {"tool": "final_answer", "tool_input": thought_process}, thought_process

    try:
        action_json = json.loads(json_str)
        return action_json, thought_process
    except json.JSONDecodeError:
        # Se o JSON extraído for inválido, retorna um erro claro.
        error_message = f"O agente gerou uma resposta com JSON malformado. Resposta recebida:\n{thought_process}"
        return {"tool": "final_answer", "tool_input": error_message}, thought_process


def process_tool_call(action_json, scope):
    """Processa a chamada da ferramenta decidida pelo agente."""
    tool_name = action_json.get("tool")
    tool_input = action_json.get("tool_input")

    if tool_name == "final_answer":
        return tool_input
    
    if tool_name in TOOLS:
        try:
            tool_function = TOOLS[tool_name]
            # DevÆGENT-I: A chamada das ferramentas é mais explícita e segura.
            if tool_name == "python_code_interpreter":
                output = tool_function(code=tool_input, scope=scope)
            elif tool_name == "get_data_schema":
                output = tool_function(filename=tool_input)
            elif tool_name == "web_search":
                output = tool_function(query=tool_input)
            else: # Para ferramentas sem argumentos como list_available_data
                output = tool_function()

            # Lógica de exibição de gráficos e resultados
            if "figure" in str(type(output)):
                st.pyplot(output)
                return "Gerei um gráfico com base na sua solicitação. Veja acima."
            else:
                return f"**Resultado da Ferramenta `{tool_name}`:**\n\n```\n{str(output)}\n```"
        except Exception as e:
            return f"Erro ao executar a ferramenta `{tool_name}`: {e}"
    else:
        return f"Erro: O agente tentou usar uma ferramenta desconhecida: `{tool_name}`."
