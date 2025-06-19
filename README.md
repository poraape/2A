# 🍏 Data Insights Pro

**Transforme seus dados em diálogos. Um agente de IA para análise de dados interativa.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Framework: Streamlit](https://img.shields.io/badge/Framework-Streamlit-red.svg)](https://streamlit.io)

Data Insights Pro é uma aplicação web construída com Streamlit que permite a usuários fazer upload de múltiplos arquivos CSV (dentro de um `.zip`) e interagir com eles através de um agente de IA conversacional. Faça perguntas em linguagem natural, peça cálculos, gere visualizações e obtenha insights sem escrever uma única linha de código.

---

### ✨ Demonstração

*(Recomendação: Grave um GIF curto da aplicação em funcionamento e substitua o link abaixo. Ferramentas como [LICEcap](https://www.cockos.com/licecap/) ou [ScreenToGif](https://www.screentogif.com/) são ótimas para isso.)*

![Demonstração do Data Insights Pro](https://user-images.githubusercontent.com/12345/example_gif.gif)

---

### 🚀 Principais Funcionalidades

*   **Upload Simplificado:** Carregue um ou mais arquivos `.csv` de uma só vez, compactados em um único arquivo `.zip`.
*   **Agente de IA Inteligente:** Equipado com o modelo Gemini 1.5 Pro da Google, o agente utiliza um ciclo ReAct (Reasoning and Acting) para entender suas perguntas e planejar a execução.
*   **Interpretador de Python Dinâmico:** O agente pode escrever e executar código Python (Pandas, Matplotlib, Seaborn) para realizar manipulações, cálculos e gerar gráficos sob demanda.
*   **Busca na Web Integrada:** Faça perguntas que exigem conhecimento externo (ex: "Qual a cotação atual do dólar?") e o agente buscará a informação na web para complementar a análise.
*   **Escopo de Análise Flexível:** Analise um arquivo CSV individualmente ou combine todos os arquivos carregados para uma visão agregada.
*   **Interface Limpa e Intuitiva:** Design inspirado na estética Apple para uma experiência de usuário agradável e focada.

---

### 🏗️ Arquitetura do Projeto

O projeto segue uma arquitetura modular para facilitar a manutenção e a extensibilidade:

*   **`app.py` (O Maestro 👨‍🏫):** Ponto de entrada da aplicação. Controla a interface do usuário (UI) com o Streamlit, gerencia o estado da sessão e orquestra as chamadas para a lógica do agente.
*   **`agent_logic.py` (O Estrategista de IA 🧠):** Contém toda a lógica de comunicação com o modelo Gemini. Formata os prompts, executa o ciclo ReAct e processa as respostas do modelo.
*   **`tools.py` (A Caixa de Ferramentas 🧰):** Define as ferramentas que o agente pode usar, como o interpretador de Python, a busca na web e funções para inspecionar os dados carregados.
*   **`requirements.txt` (A Lista de Compras 📦):** Lista todas as dependências Python necessárias para o projeto.

```
📂 data-insights-pro/
├── 📜 app.py
├── 📜 agent_logic.py
├── 📜 tools.py
└── 📜 requirements.txt
```

---

### 🛠️ Começando: Instalação e Configuração

Siga estes passos para executar o Data Insights Pro em sua máquina local.

#### 1. Pré-requisitos

*   **Python 3.9 ou superior**
*   **Git**

#### 2. Clone o Repositório
```bash
git clone https://github.com/seu-usuario/data-insights-pro.git
cd data-insights-pro
```

#### 3. Crie um Ambiente Virtual (Recomendado)
*   **No macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
*   **No Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

#### 4. Instale as Dependências
```bash
pip install -r requirements.txt
```

#### 5. Configure sua API Key do Google
O Streamlit utiliza um sistema de gerenciamento de segredos para manter suas chaves de API seguras.

1.  Crie uma pasta chamada `.streamlit` na raiz do seu projeto.
2.  Dentro da pasta `.streamlit`, crie um arquivo chamado `secrets.toml`.
3.  Adicione sua chave da API do Google Gemini ao arquivo da seguinte forma:

    ```toml
    # .streamlit/secrets.toml
    GOOGLE_API_KEY = "sua-chave-secreta-do-google-aqui"
    ```
    **Importante:** O arquivo `.gitignore` deste projeto já está configurado para ignorar o `secrets.toml`, garantindo que sua chave não seja enviada para o GitHub.

---

### ▶️ Como Usar

1.  Certifique-se de que seu ambiente virtual está ativado.
2.  Execute o seguinte comando no terminal, a partir da raiz do projeto:
    ```bash
    streamlit run app.py
    ```
3.  Abra seu navegador no endereço local fornecido (geralmente `http://localhost:8501`).
4.  Arraste e solte um arquivo `.zip` contendo seus CSVs na área de upload.
5.  Comece a conversar com seus dados!

---

### 📄 Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
```
