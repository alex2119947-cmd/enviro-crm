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
    initial_sidebar_state="collapsed" 
)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
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
    st.rerun() # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ---
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

st.sidebar.info("Версия прототипа: 3.0")

# ==============================================================================
#                     СТРАНИЦА ВХОДА ДЛЯ СОТРУДНИКА
# ==============================================================================
if st.session_state.page == "login":
    st.title("🔐 Вход для сотрудников")
    password = st.text_input("Пожалуйста, введите пароль:", type="password", key="password_input")
    if st.button("Войти", key="login_button"):
        if password == CORRECT_PASSWORD:
            st.session_state.is_authenticated = True
            st.session_state.page = "employee_dashboard"
            st.rerun() # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
        else:
            st.error("Неверный пароль.")

# ==============================================================================
#                     ГЛАВНАЯ СТРАНИЦА (АНКЕТА)
# ==============================================================================
elif st.session_state.page == "client_form":
    st.title("📋 Заявка в инженерный отдел ENVIRO.KG")
    st.write("Для начала, пожалуйста, укажите тип вашего объекта.")
    object_type = st.radio("Тип объекта:", ('Частный дом', 'Коммерческое помещение'), horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    if object_type == 'Частный дом':
        st.header("Анкета для Частного Дома")
        with st.form("private_house_form", clear_on_submit=True):
            st.subheader("1. Контактная информация")
            name = st.text_input("Имя клиента *", placeholder="Алексей")
            # ... и т.д.
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                if not name: st.error("Заполните обязательные поля (*).")
                else: create_project({"object_type": "Частный дом", "client_name": name})

    elif object_type == 'Коммерческое помещение':
        st.header("Анкета для Коммерческого Объекта")
        with st.form("commercial_form", clear_on_submit=True):
            st.subheader("1. Контактная информация")
            company_name = st.text_input("Название компании *")
            # ... и т.д.
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                if not company_name: st.error("Заполните обязательные поля (*).")
                else: create_project({"object_type": "Коммерческое помещение", "company_name": company_name})
    
    st.markdown("---")
    st.header("ENVIRO — в действии")
    video_path = "enviro1.mp4"
    video_base64 = video_to_base64(video_path)
    if video_base64:
        st.markdown(f"""<video autoplay loop muted playsinline width="100%"><source src="data:video/mp4;base64,{video_base64}" type="video/mp4"></video>""", unsafe_allow_html=True)
    else: st.warning("Видео-заставка не найдена.")

# ==============================================================================
#                ВИД СОТРУДНИКА: ПАНЕЛЬ УПРАВЛЕНИЯ
# ==============================================================================
elif st.session_state.page == "employee_dashboard" and st.session_state.is_authenticated:
    st.title("Панель управления ENVIRO")
    st.subheader("Входящие заявки")
    if st.sidebar.button("Выйти", key="logout_button"):
        st.session_state.is_authenticated = False
        st.session_state.page = "login"
        st.rerun() # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
        
    if not st.session_state.projects:
        st.info("Пока нет ни одной заявки от клиентов.")
    else:
        for project in reversed(st.session_state.projects):
            client_identifier = project.get('client_name') or project.get('company_name', 'N/A')
            with st.expander(f"Заявка №{project['id']} от {project['submission_date']} - {client_identifier}"):
                st.metric("Статус", project['status'])
                st.write(f"**Тип:** {project['object_type']}")
                if st.button("Просмотреть детали", key=f"details_btn_{project['id']}"):
                    st.session_state.current_project_id = project['id']
                    st.session_state.page = "project_page"
                    st.rerun() # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ

# ==============================================================================
#                ОБЩИЙ ВИД: СТРАНИЦА КОНКРЕТНОГО ПРОЕКТА
# ==============================================================================
elif st.session_state.page == "project_page":
    current_project = next((p for p in st.session_state.projects if p['id'] == st.session_state.current_project_id), None)
    if current_project is None:
        st.error("Проект не найден.")
        st.session_state.page = "employee_dashboard" if st.session_state.is_authenticated else "client_form"
        if st.button("Вернуться"): st.rerun() # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
    else:
        if st.session_state.is_authenticated:
            if st.button("← Назад к списку заявок"):
                st.session_state.page = "employee_dashboard"
                st.session_state.current_project_id = None
                st.rerun() # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
        
        client_identifier = current_project.get('client_name') or current_project.get('company_name', 'N/A')
        st.title(f"Страница проекта: {client_identifier}")
        # ... остальная часть страницы
