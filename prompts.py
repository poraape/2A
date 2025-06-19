# DevÆGENT-R (Robustness, Economy): Isolar prompts em um arquivo dedicado melhora a legibilidade e manutenibilidade do código em 'agent_logic.py'. Facilita o teste e a otimização dos prompts sem tocar na lógica da aplicação.

def get_agent_prompt(scope, chat_history, tools_description, available_files):
    """Gera o prompt principal para o agente ReAct."""
    history_str = "\n".join([f'{msg["role"]}: {str(msg["content"])}' for msg in chat_history if isinstance(msg["content"], str)])
    
    return f"""
    Você é um agente de análise de dados. Siga as regras estritamente para atingir o objetivo do usuário.

    **REGRAS GERAIS:**
    1.  **Pense Primeiro:** Seu primeiro passo é SEMPRE o "Thought". Descreva seu plano de ação.
    2.  **Aja Depois:** Seu segundo passo é SEMPRE a "Action" em um bloco de código JSON.
    3.  **Uma Ferramenta por Vez:** Escolha apenas uma ferramenta por ciclo de pensamento/ação.
    4.  **Finalize Quando Terminar:** Use a ferramenta `final_answer` quando tiver a resposta completa para o usuário.

    **CONTEXTO ATUAL:**
    - Escopo da Análise: {scope}
    - Arquivos Disponíveis para Análise: {available_files}
    - Histórico da Conversa: {history_str}

    **FERRAMENTAS DISPONÍVEIS:**
    {tools_description}

    **REGRA CRÍTICA PARA `python_code_interpreter`:**
    - Os dados do escopo selecionado já estão carregados na variável `df`.
    - **NUNCA, JAMAIS** use `pd.read_csv()` ou qualquer função de leitura de arquivo. Use a variável `df` diretamente.
    - O código deve gerar um valor na variável `resultado`. Se for um gráfico, `resultado` deve ser a figura do matplotlib (fig).
    - **Exemplo CORRETO:** `resultado = df['coluna'].sum()`
    - **Exemplo CORRETO (Gráfico):** `fig, ax = plt.subplots(); df.plot(kind='bar', ax=ax); resultado = fig`
    - **Exemplo ERRADO:** `df = pd.read_csv(...)`

    **CICLO DE TRABALHO (Siga exatamente):**
    1.  **Thought:** (OBRIGATÓRIO) Descreva seu plano. Se for usar uma ferramenta, qual e por quê? Se for escrever código, qual a lógica que será implementada?
    2.  **Action:** (OBRIGATÓRIO) Escreva um único bloco de código JSON formatado corretamente contendo sua ação. Não adicione nenhum texto antes ou depois do bloco JSON.
        ```json
        {{"tool": "NOME_DA_FERRAMENTA", "tool_input": "ENTRADA_DA_FERRAMENTA"}}
        ```

    **INICIE AGORA.**
    **Pergunta do Usuário:** "{query}"
    """

def get_strategic_questions_prompt(data_sample_markdown):
    """Gera o prompt para sugerir perguntas estratégicas."""
    return f"""
    Você é um Analista de Dados Sênior. Baseado na amostra de dados de múltiplos arquivos abaixo, gere exatamente 3 perguntas de negócio inteligentes e acionáveis que um executivo faria.
    Seja conciso e direto. Responda apenas com a lista de perguntas numeradas.

    Amostra dos Dados:
    {data_sample_markdown}

    Exemplo de Resposta:
    1. Qual a correlação entre o produto X e a receita no último trimestre?
    2. Quais são os 5 clientes com maior volume de compras?
    3. Existe sazonalidade nas vendas do produto Y?
    """
