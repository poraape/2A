# 🍏 Data Insights Pro

[![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-Streamlit-red.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Converse com seus dados.** Data Insights Pro é uma aplicação web que utiliza um agente de IA (Google Gemini) para permitir que usuários analisem conjuntos de dados complexos através de uma interface de chat intuitiva. Faça upload de múltiplos arquivos CSV, faça perguntas em linguagem natural e obtenha insights, cálculos e visualizações em tempo real.

![GIF da Aplicação em Ação](https://i.imgur.com/your-app-demo.gif)
*(Sugestão: Grave um GIF curto da sua aplicação funcionando e substitua o link acima para um impacto visual máximo.)*

---

## ✨ Principais Funcionalidades

*   **Análise Conversacional:** Interaja com seus dados como se estivesse conversando com um analista de dados.
*   **Upload de Múltiplos Arquivos:** Carregue um único arquivo `.zip` contendo múltiplos CSVs para uma análise integrada.
*   **Arquitetura de Agente Inteligente:** Utiliza o padrão ReAct (Reasoning and Acting) para que a IA possa pensar e escolher a ferramenta certa para cada tarefa.
*   **Ferramentas Poderosas:** O agente pode:
    *   **Executar Código Python:** Realizar manipulações e cálculos complexos com Pandas.
    *   **Gerar Gráficos:** Criar visualizações com Matplotlib e Seaborn.
    *   **Pesquisar na Web:** Buscar informações contextuais ou atuais que não estão nos seus dados.
    *   **Inspecionar Dados:** Listar arquivos e verificar o esquema (colunas e tipos de dados).
*   **Código Modular e Robusto:** A arquitetura é separada em UI, lógica do agente e ferramentas, facilitando a manutenção e a expansão.

---

## 🏛️ Arquitetura do Sistema

O projeto segue uma arquitetura modular inspirada no conceito de "Maestro e Orquestra" para garantir clareza e separação de responsabilidades.

*   `app.py` **(O Maestro 👨‍🏫):**
    > Responsável exclusivamente pela interface do usuário (UI) e pelo gerenciamento do estado da sessão. Ele orquestra o fluxo, decidindo quando chamar a lógica do agente, mas não se preocupa com os detalhes da execução.

*   `agent_logic.py` **(O Estrategista de IA 🧠):**
    > O cérebro da aplicação. Ele se comunica com o modelo de IA (Gemini), formata os prompts, interpreta o plano de ação retornado pela IA e delega a execução das tarefas para as ferramentas apropriadas.

*   `tools.py` **(A Caixa de Ferramentas 🧰):**
    > Contém as funções especialistas que o agente pode utilizar. Cada função é uma ferramenta discreta e testável (ex: `python_code_interpreter`, `web_search`).

---

## 🚀 Como Começar

Siga estes passos para executar a aplicação localmente.

### Pré-requisitos

*   Python 3.10 ou superior
*   Git

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/data-insights-pro.git
cd data-insights-pro
Use code with caution.
Markdown
2. Instale as Dependências
Crie um ambiente virtual (recomendado) e instale os pacotes necessários.

Generated bash
# Crie e ative um ambiente virtual (opcional, mas recomendado)
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instale os pacotes
pip install -r requirements.txt
Use code with caution.
Bash
3. Configure sua API Key do Google
Para que o agente de IA funcione, você precisa fornecer sua API Key do Google Gemini. O Streamlit carrega essa chave de forma segura através do arquivo secrets.toml.

Crie uma pasta chamada .streamlit no diretório raiz do seu projeto.

Dentro dela, crie um arquivo chamado secrets.toml.

Adicione o seguinte conteúdo ao arquivo, substituindo "sua_chave_aqui" pela sua chave real:

Generated toml
# .streamlit/secrets.toml

GOOGLE_API_KEY = "sua_chave_aqui"
Use code with caution.
Toml
4. Execute a Aplicação
Com tudo configurado, inicie o servidor do Streamlit:

Generated bash
streamlit run app.py

Abra seu navegador e acesse o endereço http://localhost:8501.

📁 Estrutura do Projeto
Generated code
📂 data-insights-pro/
├── .streamlit/
│   └── 📜 secrets.toml      # Armazena as chaves de API (não versionar no Git!)
├── 📜 app.py               # Ponto de entrada da UI (O Maestro)
├── 📜 agent_logic.py        # Lógica de comunicação com a IA (O Estrategista)
├── 📜 tools.py              # Funções que o agente pode executar (A Caixa de Ferramentas)
├── 📜 requirements.txt       # Lista de dependências Python
└── 📜 README.md             # Esta documentação
🛠️ Tecnologias Utilizadas
Frontend: Streamlit

IA & LLM: Google Gemini 1.5 Flash

Análise de Dados: Pandas

Visualização: Matplotlib, Seaborn

Busca na Web: DuckDuckGo Search

🗺️ Próximos Passos (Roadmap)
Containerização: Criar um Dockerfile para empacotar a aplicação e facilitar o deploy.

Deploy na Nuvem: Publicar a aplicação em plataformas como Streamlit Community Cloud ou Google Cloud Run.

Expandir Ferramentas: Adicionar novas ferramentas ao agente (ex: salvar arquivos, conectar a bancos de dados).

Cache Avançado: Implementar caching mais granular para os resultados das ferramentas, reduzindo custos de API e latência.

📄 Licença
Este projeto está sob a Licença MIT. Veja o arquivo LICENSE para mais detalhes.
