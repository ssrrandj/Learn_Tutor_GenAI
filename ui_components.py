import   streamlit as st

def page_config():

    st.set_page_config(
        page_title="AI Book Tutor",
        page_icon="",
        layout="centered"
    )

def shou_header(title):

    st.title("AI Book Tutor")
    st.caption("upload a book and ask questions instantly")
    st.divider()

def show_Answer(answer):
    st.markdown("### Answer")
    st.info(answer)

def show_source(chunks):
    if chunks:

        st.markdown("### source from book")

        for chunk in chunks:
            st.markdown(f"- {chunk}")
