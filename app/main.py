import streamlit as st
import ui_components

st.set_page_config(layout="wide")
st.title("Odoo分析アプリ")

ui_components.backend_communication_section()