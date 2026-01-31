import streamlit as st
import time
from datetime import datetime
import base64
import os

# --- ПАРОЛЬ ---
CORRECT_PASSWORD = "zxenv2026"

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="CRM ENVIRO.KG", 
    layout="wide",
    # --- ИЗМЕНЕНИЕ 2: ПАНЕЛЬ ИЗНАЧАЛЬНО СКРЫТА ---
    initial_sidebar_state="collapsed" 
)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (без изменений) ---
def video_to_base64(path):
    if not os.path.exists(path): return None
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode()

def create_project(data):
    new_project = {
        "id": len(st.session_state.projects) + 1,
        "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "На рассмотрении у инженера",
        "status_desc": "Ожидайте ответа. Наш специалист изучает предоставленные вами данные.",
        "chat_history": [{"role": "assistant", "content": f"Здравствуйте, {data.get('client_name') or data.get('contact_person')}! Я ваш виртуальный помощник. Ваша заявка принята и уже передана инженеру."}]
    }
    new_project.update(data)
    st.session_state.projects.append(new_project)
    st.session_state.current_project_id = new_project["id"]
    st.session_state.page = "project_page"
    st.experimental_rerun()

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ (без изменений) ---
if 'projects' not in st.session_state: st.session_state.projects = []
if 'page' not in st.session_state: st.session_state.page = "client_form"
if 'current_project_id' not in st.session_state: st.session_state.current_project_id = None
if 'is_authenticated' not in st.session_state: st.session_state.is_authenticated = False

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.title("Навигация")
role = st.sidebar.radio("Выберите вашу роль:", ("Новый клиент", "Сотрудник ENVIRO"), key="role_selector")

if role == "Новый клиент":
    st.session_state.is_authenticated = False 
    if st.session_state.page != "project_page":
        st.session_state.page = "client_form"
else: 
    if not st.session_state.is_authenticated:
        st.session_state.page = "login"
    else:
        st.session_state.page = "employee_dashboard"

st.sidebar.info("Версия прототипа: 2.9")

# ==============================================================================
#                     СТРАНИЦА ВХОДА ДЛЯ СОТРУДНИКА (без изменений)
# ==============================================================================
if st.session_state.page == "login":
    st.title("🔐 Вход для сотрудников")
    password = st.text_input("Пожалуйста, введите пароль:", type="password", key="password_input")
    if st.button("Войти", key="login_button"):
        if password == CORRECT_PASSWORD:
            st.session_state.is_authenticated = True
            st.session_state.page = "employee_dashboard"
            st.experimental_rerun()
        else:
            st.error("Неверный пароль.")

# ==============================================================================
#                     ГЛАВНАЯ СТРАНИЦА (АНКЕТА)
# ==============================================================================
elif st.session_state.page == "client_form":
    # --- ИЗМЕНЕНИЕ 1: НОВЫЙ ЗАГОЛОВОК ---
    st.title("📋 Заявка в инженерный отдел ENVIRO.KG")
    st.write("Для начала, пожалуйста, укажите тип вашего объекта.")
    
    # ... (остальной код анкет и видео без изменений) ...
    object_type = st.radio("Тип объекта:", ('Частный дом', 'Коммерческое помещение'), horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    if object_type == 'Частный дом':
        st.header("Анкета для Частного Дома")
        with st.form("private_house_form", clear_on_submit=True):
            st.subheader("1. Контактная информация")
            # ... поля ...
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                pass # Логика отправки
    elif object_type == 'Коммерческое помещение':
        st.header("Анкета для Коммерческого Объекта")
        with st.form("commercial_form", clear_on_submit=True):
            st.subheader("1. Контактная информация")
            # ... поля ...
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                pass # Логика отправки
    
    st.markdown("---")
    st.header("ENVIRO — в действии")
    video_path = "enviro1.mp4"
    video_base64 = video_to_base64(video_path)
    if video_base64:
        st.markdown(f"""<video autoplay loop muted playsinline width="100%"><source src="data:video/mp4;base64,{video_base64}" type="video/mp4"></video>""", unsafe_allow_html=True)
    else: st.warning("Видео-заставка не найдена.")

# ==============================================================================
#                Остальные страницы (без изменений)
# ==============================================================================
elif st.session_state.page == "employee_dashboard" and st.session_state.is_authenticated:
    # ...
    pass
elif st.session_state.page == "project_page":
    # ...
    pass
