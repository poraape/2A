# ui_components.py

import streamlit as st
import json

def display_onboarding_results(metadata, summary_df, strategic_questions):
    """
    Renderiza os resultados do onboarding usando um layout de abas para melhor UX.
    """
    st.success("Análise inicial concluída! Explore os resultados abaixo.")

    tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "🔢 Resumo Estatístico", "🧠 Perguntas Sugeridas"])

    with tab1:
        st.subheader("Resumo do Catálogo de Dados")
        total_files = len(metadata)
        total_rows = sum(v['linhas'] for v in metadata.values())
        total_cols = sum(v['colunas'] for v in metadata.values())

        col1, col2, col3 = st.columns(3)
        col1.metric("Arquivos Carregados", f"{total_files}")
        col2.metric("Total de Linhas", f"{total_rows:,}".replace(",", "."))
        col3.metric("Total de Colunas", f"{total_cols}")
        
        st.markdown("---")
        st.subheader("Detalhes por Arquivo")
        for filename, details in metadata.items():
            with st.expander(f"📄 {filename}"):
                st.json(details)

    with tab2:
        st.subheader("Análise Descritiva Combinada")
        st.markdown("Esta tabela mostra estatísticas para todas as colunas numéricas e as mais frequentes para colunas de texto.")
        st.dataframe(summary_df)

    with tab3:
        st.subheader("Explore Seus Dados")
        st.info("Clique em uma pergunta para que o agente a responda imediatamente.")
        
        # Transforma a string de perguntas em uma lista
        questions = [q.strip() for q in strategic_questions.split('\n') if q.strip() and q.strip().startswith(tuple('123456789.'))]

        for question in questions:
            # Remove o número inicial (ex: "1. ") para limpar o texto do botão
            question_text = ". ".join(question.split(". ")[1:])
            if st.button(question_text, use_container_width=True):
                # Usando st.session_state para passar a pergunta para o input de chat
                st.session_state.run_prompt = question_text
                st.rerun()

def render_chat_message(message):
    """Renderiza uma única mensagem de chat com estilo apropriado."""
    with st.chat_message(message["role"]):
        content = message["content"]
        if isinstance(content, str):
            st.markdown(content)
        elif isinstance(content, dict) and "thought" in content:
            with st.expander("🧠 Ver o Raciocínio do Agente", expanded=False):
                st.info(content["thought"])
        elif "figure" in str(type(content)):
            st.pyplot(content)
