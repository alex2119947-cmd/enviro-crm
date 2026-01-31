import streamlit as st
import time
from datetime import datetime
import base64
import os

# --- НАСТРОЙКА ПАРОЛЯ ---
CORRECT_PASSWORD = "enviro2026"

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="Прототип CRM ENVIRO", layout="wide")

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
    st.experimental_rerun()

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ---
if 'projects' not in st.session_state: st.session_state.projects = []
if 'page' not in st.session_state: st.session_state.page = "client_form"
if 'current_project_id' not in st.session_state: st.session_state.current_project_id = None
if 'is_authenticated' not in st.session_state: st.session_state.is_authenticated = False

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.title("Навигация")
role = st.sidebar.radio("Выберите вашу роль:", ("Новый клиент", "Сотрудник ENVIRO"), key="role_selector")

if role == "Новый клиент":
    st.session_state.is_authenticated = False # Сбрасываем аутентификацию при смене на клиента
    if st.session_state.page != "project_page":
        st.session_state.page = "client_form"
else: # Сотрудник ENVIRO
    if not st.session_state.is_authenticated:
        st.session_state.page = "login"
    else:
        st.session_state.page = "employee_dashboard"

st.sidebar.info("Версия прототипа: 2.7")

# ==============================================================================
#                     СТРАНИЦА ВХОДА ДЛЯ СОТРУДНИКА
# ==============================================================================
if st.session_state.page == "login":
    st.title("🔐 Вход для сотрудников")
    password = st.text_input("Пожалуйста, введите пароль:", type="password")
    if st.button("Войти"):
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
    # ... (Весь код этой страницы остается без изменений) ...
    st.title("📋 Новая заявка")
    st.write("Для начала, пожалуйста, укажите тип вашего объекта.")
    object_type = st.radio("Тип объекта:", ('Частный дом', 'Коммерческое помещение'), horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    if object_type == 'Частный дом':
        st.header("Анкета для Частного Дома")
        with st.form("private_house_form"):
            st.subheader("1. Контактная информация")
            name = st.text_input("Имя клиента *", placeholder="Алексей")
            phone = st.text_input("Номер телефона *", placeholder="+996 (XXX) XX-XX-XX")
            st.subheader("2. Информация об объекте")
            address = st.text_input("Точный адрес *")
            #... и остальные поля
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                if not name or not phone or not address: st.error("Заполните обязательные поля (*).")
                else: create_project({"object_type": "Частный дом", "client_name": name, "phone": phone, "address": address})

    elif object_type == 'Коммерческое помещение':
        st.header("Анкета для Коммерческого Объекта")
        with st.form("commercial_form"):
            st.subheader("1. Контактная информация")
            company_name = st.text_input("Название компании *")
            contact_person = st.text_input("Контактное лицо *")
            phone = st.text_input("Номер телефона *")
            st.subheader("2. Информация об объекте")
            address = st.text_input("Адрес объекта *")
            #... и остальные поля
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                if not company_name or not contact_person or not phone: st.error("Заполните обязательные поля (*).")
                else: create_project({"object_type": "Коммерческое помещение", "company_name": company_name, "contact_person": contact_person, "phone": phone, "address": address})
    
    st.markdown("---")
    st.header("ENVIRO — в действии")
    video_path = "enviro1.mp4"
    video_base64 = video_to_base64(video_path)
    if video_base64:
        st.markdown(f"""<video autoplay loop muted playsinline width="100%"><source src="data:video/mp4;base64,{video_base64}" type="video/mp4"></video>""", unsafe_allow_html=True)

# ==============================================================================
#                ВИД СОТРУДНИКА: ПАНЕЛЬ УПРАВЛЕНИЯ
# ==============================================================================
elif st.session_state.page == "employee_dashboard" and st.session_state.is_authenticated:
    st.title("Панель управления ENVIRO")
    st.subheader("Входящие заявки")
    if st.sidebar.button("Выйти"):
        st.session_state.is_authenticated = False
        st.session_state.page = "login"
        st.experimental_rerun()
        
    if not st.session_state.projects:
        st.info("Пока нет ни одной заявки от клиентов.")
    else:
        # ... (Код отображения заявок остается без изменений) ...
        for project in reversed(st.session_state.projects):
            client_identifier = project.get('client_name') or project.get('company_name')
            with st.expander(f"Заявка №{project['id']} от {project['submission_date']} - {client_identifier} ({project['address']})"):
                st.metric("Статус", project['status'])
                st.write(f"**Тип:** {project['object_type']}")
                st.write(f"**Площадь:** {project.get('area', 'N/A')} м²")
                if st.button("Просмотреть детали", key=f"details_btn_{project['id']}"):
                    st.session_state.current_project_id = project['id']
                    st.session_state.page = "project_page"
                    st.experimental_rerun()

# ==============================================================================
#                ОБЩИЙ ВИД: СТРАНИЦА КОНКРЕТНОГО ПРОЕКТА
# ==============================================================================
elif st.session_state.page == "project_page":
    # ... (Этот блок почти без изменений, только добавил кнопку "Назад" для сотрудника) ...
    current_project = next((p for p in st.session_state.projects if p['id'] == st.session_state.current_project_id), None)
    if current_project is None:
        st.error("Проект не найден.")
        st.session_state.page = "employee_dashboard" if st.session_state.is_authenticated else "client_form"
        if st.button("Вернуться"): st.experimental_rerun()
    else:
        if st.session_state.is_authenticated:
            if st.button("← Назад к списку заявок"):
                st.session_state.page = "employee_dashboard"
                st.session_state.current_project_id = None
                st.experimental_rerun()
        # ... (остальной код страницы проекта)
        client_identifier = current_project.get('client_name') or current_project.get('company_name')
        st.title(f"Страница проекта: {client_identifier}")
        st.markdown(f"Заявка №{current_project['id']} от {current_project['submission_date']}")
        # ...
