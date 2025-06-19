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
