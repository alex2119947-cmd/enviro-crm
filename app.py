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
        "status_desc": "Ожидайте ответа. Наш специалист изучает предоставленные вами данные.",
        "chat_history": [{"role": "assistant", "content": f"Здравствуйте, {data.get('client_name') or data.get('contact_person')}! Я ваш виртуальный помощник. Ваша заявка принята."}]
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

st.sidebar.info("Версия прототипа: 3.4")

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
        st.subheader("5. Загрузка файлов")
        return st.file_uploader(
            "Прикрепите фото, планы или другие документы (PDF, DOC, JPG, PNG)",
            type=['jpg', 'png', 'jpeg', 'pdf', 'doc', 'docx'],
            accept_multiple_files=True
        )

    if object_type == 'Частный дом':
        st.header("Анкета для Частного Дома")
        with st.form("private_house_form", clear_on_submit=True):
            st.subheader("1. Контактная информация")
            name = st.text_input("Имя клиента *")
            phone = st.text_input("Номер телефона *")
            email = st.text_input("Email")
            st.subheader("2. Информация об объекте")
            address = st.text_input("Точный адрес *")
            col1, col2 = st.columns(2)
            with col1:
                area = st.number_input("Площадь дома (м²)", min_value=10)
                plot_size = st.number_input("Размер участка (в сотках)", min_value=1)
            with col2:
                floors = st.selectbox("Этажность", ["1 этаж", "2 этажа", "3 этажа", "Более 3"])
                insulation = st.text_input("Наличие и тип утепления *")
                boiler_location = st.text_input("Расположение котельной")
            st.subheader("3. Текущие системы")
            col3, col4 = st.columns(2)
            with col3:
                heating_type = st.text_input("Используемый вид отопления зимой")
                power_phases = st.text_input("Сколько фаз идёт на объект")
                cooling_type = st.text_input("Используемый вид охлаждения летом")
            with col4:
                coal_usage = st.number_input("Кол-во сжигаемого угля в мес. (тонн)")
                energy_usage_kwh = st.number_input("Расход кВт*ч в мес.")
                energy_usage_som = st.number_input("Расход на энергию/отопление в мес. (сом)")
            st.subheader("4. Дополнительно")
            wishes = st.text_area("Ваши пожелания")
            questions = st.text_area("Ваши вопросы")
            uploaded_files = shared_form_elements()
            st.markdown("---")
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                if not name or not phone or not address: st.error("Заполните обязательные поля (*).")
                else:
                    files_info = [{"name": f.name, "size": f.size} for f in uploaded_files]
                    create_project({"object_type": "Частный дом", "client_name": name, "phone": phone, "email": email, "address": address, "area": area, "plot_size": plot_size, "floors": floors, "insulation": insulation, "boiler_location": boiler_location, "heating_type": heating_type, "power_phases": power_phases, "cooling_type": cooling_type, "coal_usage": coal_usage, "energy_usage_kwh": energy_usage_kwh, "energy_usage_som": energy_usage_som, "wishes": wishes, "questions": questions, "uploaded_files_info": files_info})

    elif object_type == 'Коммерческое помещение':
        st.header("Анкета для Коммерческого Объекта")
        with st.form("commercial_form", clear_on_submit=True):
            st.subheader("1. Контактная информация")
            company_name = st.text_input("Название компании *")
            contact_person = st.text_input("Контактное лицо *")
            phone = st.text_input("Номер телефона *")
            email = st.text_input("Email")
            st.subheader("2. Информация об объекте")
            address = st.text_input("Адрес объекта *")
            activity_type = st.text_input("Тип деятельности", placeholder="Например, кафе, офис, производство")
            area = st.number_input("Общая площадь (м²)", min_value=10)
            st.subheader("3. Дополнительно")
            wishes = st.text_area("Ваши пожелания и технические требования")
            uploaded_files = shared_form_elements()
            st.markdown("---")
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                if not company_name or not contact_person or not phone: st.error("Заполните обязательные поля (*).")
                else:
                    files_info = [{"name": f.name, "size": f.size} for f in uploaded_files]
                    create_project({"object_type": "Коммерческое помещение", "company_name": company_name, "contact_person": contact_person, "phone": phone, "email": email, "address": address, "activity_type": activity_type, "area": area, "wishes": wishes, "uploaded_files_info": files_info})
    
    st.markdown("---")
    st.header("ENVIRO — в действии")
    video_path = "enviro1.mp4"
    video_base64 = video_to_base64(video_path)
    if video_base64: st.markdown(f'<video autoplay loop muted playsinline width="100%"><source src="data:video/mp4;base64,{video_base64}" type="video/mp4"></video>', unsafe_allow_html=True)

# ==============================================================================
#                ПАНЕЛЬ УПРАВЛЕНИЯ
# ==============================================================================
elif st.session_state.page == "employee_dashboard" and st.session_state.is_authenticated:
    st.title("Панель управления ENVIRO")
    st.subheader("Входящие заявки")
    if st.sidebar.button("Выйти", key="logout_button"):
        st.session_state.is_authenticated = False
        st.session_state.page = "login"
        st.rerun()
    if not st.session_state.projects: st.info("Пока нет ни одной заявки от клиентов.")
    else:
        for project in reversed(st.session_state.projects):
            client_identifier = project.get('client_name') or project.get('company_name', 'N/A')
            with st.expander(f"Заявка №{project['id']} от {project['submission_date']} - {client_identifier} ({project.get('address', 'Адрес не указан')})"):
                st.metric("Статус", project['status'])
                st.write(f"**Тип:** {project['object_type']}")
                st.write(f"**Площадь:** {project.get('area', 'N/A')} м²")
                if st.button("Просмотреть детали", key=f"details_btn_{project['id']}"):
                    st.session_state.current_project_id = project['id']
                    st.session_state.page = "project_page"
                    st.rerun()

# ==============================================================================
#                СТРАНИЦА ПРОЕКТА
# ==============================================================================
elif st.session_state.page == "project_page":
    current_project = next((p for p in st.session_state.projects if p['id'] == st.session_state.current_project_id), None)
    if current_project is None:
        st.error("Проект не найден.")
        st.session_state.page = "employee_dashboard" if st.session_state.is_authenticated else "client_form"
        if st.button("Вернуться"): st.rerun()
    else:
        if st.session_state.is_authenticated:
            if st.button("← Назад к списку заявок"):
                st.session_state.page = "employee_dashboard"
                st.session_state.current_project_id = None
                st.rerun()
        client_identifier = current_project.get('client_name') or current_project.get('company_name', 'N/A')
        st.title(f"Страница проекта: {client_identifier}")
        st.markdown(f"Заявка №{current_project['id']} от {current_project['submission_date']}")
        st.markdown("---")
        st.subheader("1. Статус заявки")
        st.success(current_project['status'])
        st.info(current_project['status_desc'])
        st.markdown("---")
        with st.expander("Показать/скрыть полные детали заявки"):
             display_data = current_project.copy()
             display_data.pop('chat_history', None)
             st.json(display_data)
        st.subheader("3. Загруженные файлы")
        if "uploaded_files_info" in current_project and current_project["uploaded_files_info"]:
            for file_info in current_project["uploaded_files_info"]:
                size_mb = file_info['size'] / (1024 * 1024)
                st.info(f"📄 {file_info['name']} ({size_mb:.2f} MB)")
            st.warning("Примечание: в режиме прототипа отображается только информация о файлах, но не сами файлы.")
        else:
            st.write("Клиент не прикрепил файлы к этой заявке.")
        st.subheader("4. Чат по проекту")
        for message in current_project["chat_history"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        if prompt := st.chat_input("Напишите ваш вопрос..."):
            current_project["chat_history"].append({"role": "user", "content": prompt})
            st.rerun()
