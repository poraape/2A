
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
        return genai.GenerativeModel('gemini-1.5-pro-latest')
    except Exception as e:
        st.error(f"Erro ao configurar a API do Google. Verifique sua GOOGLE_API_KEY. Detalhe: {e}")
        st.stop()

model = load_gemini_model()

# =============================================================================
# 2. FUNÇÕES DO AGENTE
# =============================================================================
def suggest_strategic_questions(dataframes):
    # ... (sem alterações nesta função)
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
    """O cérebro principal do agente ReAct, agora com conhecimento completo e regras estritas."""
    history_str = "\n".join([f'{msg["role"]}: {str(msg["content"])}' for msg in chat_history if isinstance(msg["content"], str)])
    
    tools_description = "\n".join([f"- `{name}`: {func.__doc__.strip()}" for name, func in TOOLS.items()])
    
    # DevÆGENT-V3.3: A otimização CRÍTICA está na nova diretiva do prompt.
    prompt = f"""
    Você é um Analista de Dados Autônomo de elite (ReAct Agent). Sua missão é entender a pergunta do usuário e usar as ferramentas disponíveis para construir a resposta passo a passo.

    **Contexto da Análise:**
    - Escopo Atual: {scope}
    - Arquivos Disponíveis: {list(st.session_state.dataframes.keys())}
    - Histórico da Conversa: {history_str}

    **Ferramentas Disponíveis:**
    {tools_description}

    ---
    **DIRETIVA CRÍTICA PARA `python_code_interpreter`:**
    A ferramenta `python_code_interpreter` AUTOMATICAMENTE carrega os dados do escopo atual em uma variável chamada `df`.
    Você **NUNCA** deve gerar código que tente ler arquivos do disco (ex: `pd.read_csv()`). SEMPRE opere diretamente na variável `df`.

    -   **ERRADO:** `meu_df = pd.read_csv('{scope}'); resultado = len(meu_df)`
    -   **CERTO:** `resultado = len(df)`
    -   **ERRADO:** `df_itens = pd.read_csv('202401_NFs_Itens.csv'); resultado = df_itens['Valor'].sum()`
    -   **CERTO:** `resultado = df['Valor'].sum()` (quando o escopo está definido para '202401_NFs_Itens.csv')
    ---

    **Ciclo de Trabalho Obrigatório:**
    1.  **Thought:** Descreva seu plano de ação em português. Se precisar de código, planeje o código correto usando a variável `df`.
    2.  **Action:** Responda APENAS com um bloco de código JSON contendo a ferramenta e sua entrada.
    3.  Se você já tem a resposta final, use a ferramenta 'final_answer'.

    **Inicie o processo para a pergunta do usuário.**
    **Pergunta:** "{query}"
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
