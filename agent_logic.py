import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re
from tools import TOOLS, validate_python_code # <-- NOVO IMPORT

# =============================================================================
# 1. CONFIGURAÇÃO E INICIALIZAÇÃO DO MODELO
# =============================================================================
@st.cache_resource
def load_gemini_model():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"Erro ao configurar a API do Google: {e}"); st.stop()

model = load_gemini_model()

# =============================================================================
# 2. FUNÇÕES DO AGENTE
# =============================================================================
def suggest_strategic_questions(dataframes):
    # ... (sem alterações)
    try:
        combined_head = pd.concat([df.head(2) for df in dataframes.values()]).to_markdown()
        prompt = f"""Você é um Analista de Dados. Baseado na amostra de dados abaixo, gere 3 perguntas inteligentes para análise. Amostra:\n{combined_head}\nResponda apenas com a lista de perguntas."""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"Não foi possível gerar perguntas: {e}"

def agent_executor(query, chat_history, scope):
    history_str = "\n".join([f'{msg["role"]}: {str(msg["content"])}' for msg in chat_history if isinstance(msg["content"], str)])
    tools_description = "\n".join([f"- `{name}`: {func.__doc__.strip()}" for name, func in TOOLS.items()])
    
    # DevÆGENT-V3.5: Prompt atualizado para informar o agente sobre a camada de validação.
    prompt = f"""
    Você é um agente de análise de dados. Siga as regras estritamente.

    **REGRAS GERAIS:**
    1.  **Pense, Depois Aja:** Seu fluxo é sempre "Thought", depois "Action" em JSON.
    2.  **Uma Ferramenta por Vez:** Escolha apenas uma ferramenta por ciclo.

    **CONTEXTO:**
    - Escopo da Análise: {scope}
    - Arquivos Disponíveis: {list(st.session_state.dataframes.keys())}
    - Histórico: {history_str}

    **FERRAMENTAS:**
    {tools_description}

    **REGRAS CRÍTICAS PARA `python_code_interpreter`:**
    1.  **SEGURANÇA:** Seu código será validado. Se você usar comandos proibidos (`pd.read_csv`, `open`, `os`, `shutil`), sua ação será bloqueada e você terá que corrigi-la.
    2.  **CONTEXTO:** Os dados já estão na variável `df`. **NUNCA** tente ler arquivos. Opere diretamente em `df`.

    **CICLO DE TRABALHO:**
    1.  **Thought:** (OBRIGATÓRIO) Descreva seu plano.
    2.  **Action:** (OBRIGATÓRIO) Escreva um bloco de código JSON com sua ação.
    3.  Se tiver a resposta final, use a ferramenta `final_answer`.

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
    """Executa a ferramenta escolhida pelo agente, agora com uma camada de validação."""
    tool_name = action_json.get("tool")
    tool_input = action_json.get("tool_input")

    if tool_name == "final_answer":
        return tool_input
    
    if tool_name == "python_code_interpreter":
        # DevÆGENT-V3.5: Intercepta a chamada e valida o código ANTES da execução.
        is_valid, message = validate_python_code(tool_input)
        if not is_valid:
            # Cria a mensagem de feedback para o loop de auto-correção.
            feedback = f"**🛡️ Código Bloqueado pelo Validador:**\n\n`{message}`\n\n**Ação para o Agente:** Por favor, corrija o código e tente novamente, seguindo as regras."
            return feedback
    
    if tool_name in TOOLS:
        try:
            tool_function = TOOLS[tool_name]
            # ... (Lógica de chamada de ferramenta permanece a mesma)
            if tool_name == "python_code_interpreter": output = tool_function(code=tool_input, scope=scope)
            elif tool_name == "get_data_schema": output = tool_function(filename=tool_input)
            elif tool_name == "web_search": output = tool_function(query=tool_input)
            else: output = tool_function()

            if "figure" in str(type(output)):
                st.pyplot(output); st.session_state.messages.append({"role": "assistant", "content": output})
                return "Gerei um gráfico com base na sua solicitação. Veja acima."
            else:
                return f"**Resultado da Ferramenta `{tool_name}`:**\n\n```\n{str(output)}\n```"
        except Exception as e: return f"Erro ao executar a ferramenta `{tool_name}`: {e}"
    else:
        return f"Erro: O agente tentou usar uma ferramenta desconhecida: `{tool_name}`."
