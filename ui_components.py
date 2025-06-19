import streamlit as st
import re

def handle_suggestion_click(question_text):
    """Callback para definir a pergunta no estado da sessão e adicioná-la ao chat."""
    st.session_state.run_prompt_from_suggestion = question_text

def display_onboarding_results(metadata, summary_df, strategic_questions):
    """Renderiza os resultados do onboarding usando um layout de abas para melhor UX."""
    st.success("Análise inicial concluída! Explore os resultados abaixo e faça sua primeira pergunta.")

    tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "🔢 Resumo Estatístico", "🧠 Perguntas Sugeridas"])

    with tab1:
        st.subheader("Catálogo de Dados Carregados")
        total_files = len(metadata)
        total_rows = sum(v['linhas'] for v in metadata.values())
        
        col1, col2 = st.columns(2)
        col1.metric("Arquivos CSV Processados", f"{total_files}")
        col2.metric("Total de Linhas Analisadas", f"{total_rows:,}".replace(",", "."))
        
        st.markdown("---")
        for filename, details in metadata.items():
            with st.expander(f"📄 **{filename}** ({details['linhas']} linhas)"):
                st.json({"colunas": details["nomes_colunas"]})

    with tab2:
        st.subheader("Análise Descritiva Combinada")
        st.markdown("Estatísticas para todas as colunas (numéricas e de texto) dos arquivos combinados.")
        st.dataframe(summary_df)

    with tab3:
        st.subheader("Sugestões para Iniciar a Análise")
        st.info("Clique em uma pergunta para que o agente a responda imediatamente.")
        
        # DevÆGENT-R (Robustness): Regex para extrair perguntas de forma mais confiável.
        # Lida com formatos como "1.", "1)", "1- " etc.
        questions = re.findall(r'^\s*\d+[.)-]\s*(.*)', strategic_questions, re.MULTILINE)

        if not questions:
            st.warning("O modelo não conseguiu gerar perguntas sugeridas no formato esperado.")
            st.code(strategic_questions)

        for question_text in questions:
            # DevÆGENT-R: Usa o callback `on_click`, o método moderno e robusto do Streamlit para lidar com ações de botão.
            # Isso evita o uso de `st.rerun()` e torna o fluxo de controle mais claro.
            st.button(
                question_text,
                key=f"btn_{question_text}",
                on_click=handle_suggestion_click,
                args=(question_text,),
                use_container_width=True
            )

def render_chat_message(message):
    """Renderiza uma única mensagem de chat com estilo apropriado."""
    role = message.get("role", "assistant")
    with st.chat_message(role):
        content = message["content"]
        if isinstance(content, str):
            st.markdown(content)
        elif isinstance(content, dict) and "thought" in content:
            with st.expander("🧠 Ver o Raciocínio do Agente", expanded=False):
                st.info(content["thought"])
        # DevÆGENT-R: Checagem mais segura para o tipo de figura.
        elif hasattr(content, 'savefig'): # Uma maneira mais pythônica de verificar se é um objeto de figura
            st.pyplot(content)
        elif content is not None:
             st.markdown(str(content))
