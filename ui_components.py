import streamlit as st
import re

def handle_suggestion_click(question_text):
    """Callback para definir a pergunta no estado da sessão."""
    st.session_state.run_prompt_from_suggestion = question_text

def display_onboarding_results(metadata, summary_df, strategic_questions):
    """Renderiza os resultados do onboarding."""
    st.success("Análise inicial concluída! Explore os resultados abaixo e faça sua primeira pergunta.")
    tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "🔢 Resumo Estatístico", "🧠 Perguntas Sugeridas"])
    with tab1:
        st.subheader("Resumo do Catálogo de Dados")
        col1, col2 = st.columns(2)
        col1.metric("Arquivos Carregados", len(metadata))
        col2.metric("Total de Linhas", f"{sum(v['linhas'] for v in metadata.values()):,}")
        st.markdown("---")
        for filename, details in metadata.items():
            with st.expander(f"📄 {filename}"):
                st.json(details)
    with tab2:
        st.subheader("Análise Descritiva Combinada")
        st.dataframe(summary_df)
    with tab3:
        st.subheader("Explore Seus Dados")
        st.info("Clique em uma pergunta para que o agente a responda imediatamente.")
        questions = re.findall(r'^\s*\d+[.)-]\s*(.*)', strategic_questions, re.MULTILINE)
        for question_text in questions:
            st.button(
                question_text,
                key=f"btn_{question_text}",
                on_click=handle_suggestion_click,
                args=(question_text,),
                use_container_width=True
            )

def render_chat_message(message):
    """
    Renderiza uma única mensagem de chat, agora com suporte para exibir
    pensamentos, observações de ferramentas e respostas finais.
    """
    role = message.get("role", "assistant")
    with st.chat_message(role):
        content = message["content"]
        
        if isinstance(content, str):
            st.markdown(content)
        elif isinstance(content, dict):
            # DevÆGENT-I: Adiciona novos tipos de conteúdo para melhor visualização do processo do agente.
            if "thought" in content:
                with st.expander("🧠 Raciocínio do Agente", expanded=False):
                    st.info(content["thought"])
            elif "observation" in content:
                 with st.expander(f"⚙️ Observação da Ferramenta: `{content['tool']}`", expanded=True):
                    st.code(str(content['observation']), language='text')
            elif hasattr(content, 'savefig'): # Checagem para figuras Matplotlib
                st.pyplot(content)
        elif content is not None:
            st.markdown(str(content))
