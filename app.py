import streamlit as st
import time
from datetime import datetime
import base64
import os

# --- ПАРОЛЬ ---
CORRECT_PASSWORD = "zxenv2026"

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="CRM ENVIRO.KG", layout="wide", initial_sidebar_state="collapsed")

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def video_to_base64(path):
    if not os.path.exists(path): return None
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode()

def create_project(data):
    new_project = {
        "id": len(st.session_state.projects) + 1,
        "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "На рассмотрении у инженера",
        "status_desc": "Ожидайте ответа...",
        "chat_history": [{"role": "assistant", "content": f"Здравствуйте, {data.get('client_name') or data.get('contact_person')}! Ваша заявка принята."}]
    }
    new_project.update(data)
    st.session_state.projects.append(new_project)
    st.session_state.current_project_id = new_project["id"]
    st.session_state.page = "project_page"
    st.rerun()

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
    if st.session_state.page != "project_page": st.session_state.page = "client_form"
else: 
    if not st.session_state.is_authenticated: st.session_state.page = "login"
    else: st.session_state.page = "employee_dashboard"

st.sidebar.info("Версия прототипа: 3.3")

# ==============================================================================
#                     СТРАНИЦА ВХОДА
# ==============================================================================
if st.session_state.page == "login":
    st.title("🔐 Вход для сотрудников")
    password = st.text_input("Пароль:", type="password", key="password_input")
    if st.button("Войти", key="login_button"):
        if password == CORRECT_PASSWORD:
            st.session_state.is_authenticated = True
            st.session_state.page = "employee_dashboard"
            st.rerun()
        else: st.error("Неверный пароль.")

# ==============================================================================
#                     ГЛАВНАЯ СТРАНИЦА (АНКЕТА)
# ==============================================================================
elif st.session_state.page == "client_form":
    st.title("📋 Заявка в инженерный отдел ENVIRO.KG")
    st.write("Для начала, пожалуйста, укажите тип вашего объекта.")
    object_type = st.radio("Тип объекта:", ('Частный дом', 'Коммерческое помещение'), horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    def shared_form_elements():
        # --- ИЗМЕНЕНИЕ: ДОБАВЛЯЕМ ПОЛЕ ДЛЯ ЗАГРУЗКИ ФАЙЛОВ ---
        st.subheader("5. Загрузка файлов")
        uploaded_files = st.file_uploader(
            "Прикрепите фото, планы или другие документы",
            type=['jpg', 'png', 'jpeg', 'pdf', 'doc', 'docx'],
            accept_multiple_files=True,
            help="Вы можете загрузить несколько файлов. Например: фото фасада, план котельной, технические условия."
        )
        return uploaded_files

    if object_type == 'Частный дом':
        st.header("Анкета для Частного Дома")
        with st.form("private_house_form", clear_on_submit=True):
            # ... (все поля анкеты для дома)
            st.subheader("1. Контактная информация")
            name = st.text_input("Имя клиента *")
            phone = st.text_input("Номер телефона *")
            # ...
            uploaded_files = shared_form_elements() # Вызываем общую функцию
            st.markdown("---")
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                if not name or not phone: st.error("Заполните обязательные поля (*).")
                else:
                    files_info = [{"name": f.name, "size": f.size} for f in uploaded_files] if uploaded_files else []
                    create_project({"object_type": "Частный дом", "client_name": name, "phone": phone, "uploaded_files_info": files_info})

    elif object_type == 'Коммерческое помещение':
        st.header("Анкета для Коммерческого Объекта")
        with st.form("commercial_form", clear_on_submit=True):
            # ... (все поля анкеты для комм. объекта)
            st.subheader("1. Контактная информация")
            company_name = st.text_input("Название компании *")
            contact_person = st.text_input("Контактное лицо *")
            # ...
            uploaded_files = shared_form_elements() # Вызываем общую функцию
            st.markdown("---")
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                if not company_name or not contact_person: st.error("Заполните обязательные поля (*).")
                else:

                    files_info = [{"name": f.name, "size": f.size} for f in uploaded_files] if uploaded_files else []
                    create_project({"object_type": "Коммерческое помещение", "company_name": company_name, "contact_person": contact_person, "uploaded_files_info": files_info})
    
    st.markdown("---") # Видео внизу
    st.header("ENVIRO — в действии")
    video_path = "enviro1.mp4"
    video_base64 = video_to_base64(video_path)
    if video_base64: st.markdown(f'<video autoplay loop muted playsinline width="100%"><source src="data:video/mp4;base64,{video_base64}" type="video/mp4"></video>', unsafe_allow_html=True)

# ==============================================================================
#                ПАНЕЛЬ УПРАВЛЕНИЯ
# ==============================================================================
elif st.session_state.page == "employee_dashboard" and st.session_state.is_authenticated:
    st.title("Панель управления ENVIRO")
    # ... (код панели)

# ==============================================================================
#                СТРАНИЦА ПРОЕКТА
# ==============================================================================
elif st.session_state.page == "project_page":
    current_project = next((p for p in st.session_state.projects if p['id'] == st.session_state.current_project_id), None)
    if current_project:
        # ... (код страницы проекта)
        
        # --- ИЗМЕНЕНИЕ: ОТОБРАЖАЕМ ИНФОРМАЦИЮ О ЗАГРУЖЕННЫХ ФАЙЛАХ ---
        st.subheader("3. Загруженные файлы")
        if "uploaded_files_info" in current_project and current_project["uploaded_files_info"]:
            for file_info in current_project["uploaded_files_info"]:
                # Форматируем размер файла для читаемости
                size_mb = file_info['size'] / (1024 * 1024)
                st.info(f"📄 {file_info['name']} ({size_mb:.2f} MB)")
            st.warning("Примечание: в режиме прототипа отображается только информация о файлах, но не сами файлы.")
        else:
            st.write("Клиент не прикрепил файлы к этой заявке.")
            
        st.subheader("4. Чат по проекту")
        # ... (остальной код чата)
