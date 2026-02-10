import streamlit as st
import time
from datetime import datetime
import base64
import os
import json
import requests

# --- КОНФИГУРАЦИЯ ---
DATA_FILE = "projects.json"
UPLOAD_DIR = "file_uploads"
CORRECT_PASSWORD = "zxenv2026"
STATUS_OPTIONS = [
    "На рассмотрении у инженера", "В работе", 
    "Требуются уточнения от клиента", "Расчет готов", 
    "Проект завершен", "Отменен"
]
ENGINEER_OPTIONS = [
    "Не назначен", "Азамат К.", "Тимур М.", 
    "Евгений П.", "Другой специалист"
]

# --- НАСТРОЙКИ TELEGRAM ---
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except (KeyError, FileNotFoundError):
    TELEGRAM_TOKEN = None
    TELEGRAM_CHAT_ID = None

# --- ИНИЦИАЛИЗАЦИЯ ---
os.makedirs(UPLOAD_DIR, exist_ok=True)
st.set_page_config(
    page_title="CRM ENVIRO.KG", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- ФУНКЦИИ ---

def send_telegram_notification(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram-уведомления не настроены.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, json=payload, timeout=5)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки Telegram: {e}")

def load_projects():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return []
    return []

def save_projects(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def video_to_base64(path):
    if not os.path.exists(path): return None
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode()

def create_project(data):
    all_projects = st.session_state.projects
    max_id = max(p['id'] for p in all_projects) if all_projects else 0
    new_project = {
        "id": max_id + 1,
        "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "На рассмотрении у инженера",
        "status_desc": "Ожидайте ответа...",
        "chat_history": [{
            "role": "assistant",
            "content": f"Здравствуйте, {data.get('client_name') or data.get('contact_person')}! Ваша заявка принята."
        }],
        "assigned_engineer": "Не назначен",
        "internal_notes": []
    }
    new_project.update(data)
    all_projects.append(new_project)
    save_projects(all_projects)
    
    client_name = data.get('client_name') or data.get('company_name', 'N/A')
    address = data.get('address', 'Адрес не указан')
    notification_message = (
        f"🔔 *Новая заявка №{new_project['id']}*\n\n"
        f"👤 *Клиент:* {client_name}\n"
        f"🏠 *Объект:* {data.get('object_type')}\n"
        f"📍 *Адрес:* {address}"
    )
    send_telegram_notification(notification_message)
    
    st.session_state.projects = all_projects
    st.session_state.current_project_id = new_project["id"]
    st.session_state.page = "project_page"
    st.rerun()

# --- ИНИЦИАЛИЗАЦИЯ SESSION STATE ---
if 'projects' not in st.session_state: 
    st.session_state.projects = load_projects()
if 'page' not in st.session_state: 
    st.session_state.page = "client_form"
if 'current_project_id' not in st.session_state: 
    st.session_state.current_project_id = None
if 'is_authenticated' not in st.session_state: 
    st.session_state.is_authenticated = False

# --- НАВИГАЦИЯ ---
def handle_role_change():
    st.session_state.page = "client_form"
    if st.session_state.role_selector == "Сотрудник ENVIRO":
        st.session_state.page = "login" if not st.session_state.get('is_authenticated') else "employee_dashboard"
    st.session_state.current_project_id = None

st.sidebar.title("Навигация")
st.sidebar.radio(
    "Выберите вашу роль:", 
    ("Новый клиент", "Сотрудник ENVIRO"), 
    key="role_selector", 
    on_change=handle_role_change
)
st.sidebar.info("Версия: 4.9 (Финальная)")

# ==============================================================================
#                     ОСНОВНАЯ ЛОГИКА ОТОБРАЖЕНИЯ СТРАНИЦ
# ==============================================================================
current_page = st.session_state.get('page', 'client_form')

if current_page == "login":
    st.title("🔐 Вход для сотрудников")
    password = st.text_input("Пароль:", type="password")
    if st.button("Войти"):
        if password == CORRECT_PASSWORD:
            st.session_state.is_authenticated = True
            st.session_state.page = "employee_dashboard"
            st.rerun()
        else:
            st.error("Неверный пароль.")

elif current_page == "client_form":
    st.title("📋 Заявка в инженерный отдел ENVIRO.KG")
    object_type = st.radio(
        "Тип объекта:", 
        ('Частный дом', 'Коммерческое помещение'), 
        horizontal=True, 
        label_visibility="collapsed"
    )
    st.markdown("---")

    def shared_form_elements():
        st.subheader("5. Загрузка файлов")
        st.caption("Вы можете прикрепить несколько файлов: планы, схемы, фотографии объекта и т.д.")
        return st.file_uploader(
            label="**Нажмите, чтобы выбрать файлы, или перетащите их в эту область**", 
            type=['jpg', 'png', 'jpeg', 'pdf', 'doc', 'docx'], 
            accept_multiple_files=True
        )

    if object_type == 'Частный дом':
        with st.form("private_house_form", clear_on_submit=True):
            st.subheader("1. Контактная информация")
            name = st.text_input("Имя клиента \*")
            phone = st.text_input("Номер телефона \*")
            email = st.text_input("Email")
            
            st.subheader("2. Информация об объекте")
            address = st.text_input("Точный адрес \*")
            col1, col2 = st.columns(2)
            with col1:
                area = st.number_input("Площадь дома (м²)", min_value=10)
                plot_size = st.number_input("Размер участка (в сотках)", min_value=1)
            with col2:
                floors = st.selectbox("Этажность", ["1 этаж", "2 этажа", "3 этажа", "Более 3"])
                insulation = st.text_input("Наличие и тип утепления \*")
                boiler_location = st.text_input("Расположение котельной")

            st.subheader("3. Текущие системы")
            col3, col4 = st.columns(2)
            with col3:
                heating_type = st.text_input("Используемый вид отопления зимой")
                power_phases = st.text_input("Сколько фаз идёт на объект")
                cooling_type = st.text_input("Используемый вид охлаждения летом")
            with col4:
                coal_usage = st.number_input("Кол-во сжигаемого угля в мес. (тонн)")
                energy_usage_kwh = st.number_input("Расход кВт\*ч в мес.")
                energy_usage_som = st.number_input("Расход на энергию/отопление в мес. (сом)")

            st.subheader("4. Дополнительно")
            wishes = st.text_area("Ваши пожелания")
            questions = st.text_area("Ваши вопросы")
            uploaded_files = shared_form_elements()
            st.markdown("---")
            
            if st.form_submit_button("Отправить заявку"):
                if not name or not phone or not address: 
                    st.error("Заполните обязательные поля (\*).")
                else: 
                    create_project({
                        "object_type": "Частный дом", "client_name": name, "phone": phone, "email": email, 
                        "address": address, "area": area, "plot_size": plot_size, "floors": floors, 
                        "insulation": insulation, "boiler_location": boiler_location, "heating_type": heating_type, 
                        "power_phases": power_phases, "cooling_type": cooling_type, "coal_usage": coal_usage, 
                        "energy_usage_kwh": energy_usage_kwh, "energy_usage_som": energy_usage_som, 
                        "wishes": wishes, "questions": questions, 
                        "uploaded_files_info": [{"name": f.name, "size": f.size} for f in uploaded_files]
                    })
    else: # 'Коммерческое помещение'
        with st.form("commercial_form", clear_on_submit=True):
            st.subheader("1. Контактная информация")
            company_name = st.text_input("Название компании \*")
            contact_person = st.text_input("Контактное лицо \*")
            phone = st.text_input("Номер телефона \*")
            email = st.text_input("Email")
            
            st.subheader("2. Информация об объекте")
            address = st.text_input("Адрес объекта \*")
            activity_type = st.text_input("Тип деятельности", placeholder="Например, кафе, офис, производство")
            area = st.number_input("Общая площадь (м²)", min_value=10)
            
            st.subheader("3. Дополнительно")
            wishes = st.text_area("Ваши пожелания и технические требования")
            uploaded_files = shared_form_elements()
            st.markdown("---")
            
            if st.form_submit_button("Отправить заявку"):
                if not company_name or not contact_person or not phone: 
                    st.error("Заполните обязательные поля (\*).")
                else: 
                    create_project({
                        "object_type": "Коммерческое помещение", "company_name": company_name, 
                        "contact_person": contact_person, "phone": phone, "email": email, 
                        "address": address, "activity_type": activity_type, "area": area, 
                        "wishes": wishes, 
                        "uploaded_files_info": [{"name": f.name, "size": f.size} for f in uploaded_files]
                    })

    video_base64 = video_to_base64("enviro1.mp4")
    if video_base64:
        st.markdown(
            f'<hr><div style="text-align: center;"><h2>ENVIRO — в действии</h2>'
            f'<video autoplay loop muted playsinline width="100%">'
            f'<source src="data:video/mp4;base64,{video_base64}" type="video/mp4">'
            f'</video></div>', 
            unsafe_allow_html=True
        )

elif current_page == "employee_dashboard" and st.session_state.get('is_authenticated'):
    st.title("Панель управления ENVIRO")
    st.subheader("Входящие заявки")
    if st.sidebar.button("Выйти"):
        st.session_state.is_authenticated = False
        st.session_state.page = "client_form"
        st.rerun()
    
    if not st.session_state.projects:
        st.info("Пока нет ни одной заявки от клиентов.")
    else:
        sorted_projects = sorted(st.session_state.projects, key=lambda p: p['id'], reverse=True)
        for project in sorted_projects:
            client_id = project.get('client_name') or project.get('company_name', 'N/A')
            engineer = project.get('assigned_engineer', 'Не назначен')
            expander_title = (
                f"Заявка №{project['id']} от {project['submission_date']} - "
                f"{client_id} (Ответственный: {engineer})"
            )
            with st.expander(expander_title):
                st.metric("Статус", project['status'])
                st.write(f"**Тип:** {project['object_type']}")
                if st.button("Просмотреть детали", key=f"details_btn_{project['id']}"):
                    st.session_state.current_project_id = project['id']
                    st.session_state.page = "project_page"
                    st.rerun()

elif current_page == "project_page":
    project_id = st.session_state.get('current_project_id')
    current_project = next((p for p in st.session_state.projects if p['id'] == project_id), None)
    
    if current_project is None:
        st.error("Проект не найден.")
        if st.button("Вернуться на главную"):
            st.session_state.page = "employee_dashboard" if st.session_state.get('is_authenticated') else "client_form"
            st.session_state.current_project_id = None
            st.rerun()
    else:
        is_auth = st.session_state.get('is_authenticated')
        client_id = current_project.get('client_name') or current_project.get('company_name', 'N/A')
        
        if is_auth:
            if st.button("← Назад к списку заявок"):
                st.session_state.page = "employee_dashboard"
                st.session_state.current_project_id = None
                st.rerun()

        st.title(f"Страница проекта: {client_id}")
        st.markdown(f"Заявка №{current_project['id']} от {current_project['submission_date']}")
        st.markdown("---")

        # --- БЛОК 1: СТАТУС (ИСПРАВЛЕНАЯ СТРОКА) ---
        st.subheader("1. Статус заявки")
        st.success(current_project.get('status', 'N/A'))
        st.info(current_project.get('status_desc', ''))
        st.markdown("---")

        with st.expander("2. Показать/скрыть детали заявки"):
            field_map = {
                "object_type": "Тип объекта", "client_name": "Имя клиента", "company_name": "Название компании",
                "contact_person": "Контактное лицо", "phone": "Номер телефона", "email": "Email", "address": "Адрес", 
                "area": "Площадь (м²)", "plot_size": "Размер участка (соток)", "floors": "Этажность", 
                "insulation": "Утепление", "boiler_location": "Расположение котельной", "activity_type": "Тип деятельности",
                "heating_type": "Вид отопления зимой", "cooling_type": "Вид охлаждения летом", "power_phases": "Количество фаз",
                "coal_usage": "Расход угля в мес. (тонн)", "energy_usage_kwh": "Расход кВт*ч в мес.",
                "energy_usage_som": "Расход на энергию в мес. (сом)", "wishes": "Пожелания", "questions": "Вопросы"
            }
            col1, col2 = st.columns(2)
            
            def display_field(project, key, label):
                value = project.get(key)
                display_value = value if value is not None and value != '' else "_не заполнено_"
                st.markdown(f"**{label}:**")
                st.write(display_value)
            
            with col1:
                st.markdown("##### **Общая информация**")
                for key in ["object_type", "client_name", "company_name", "contact_person", "phone", "email", "address", "activity_type"]:
                    if key in current_project: display_field(current_project, key, field_map[key])
            with col2:
                st.markdown("##### **Параметры и системы**")
                for key in ["area", "plot_size", "floors", "insulation", "boiler_location", "heating_type", "cooling_type", "power_phases", "coal_usage", "energy_usage_kwh", "energy_usage_som"]:
                    if key in current_project: display_field(current_project, key, field_map[key])
                st.markdown("##### **Дополнительно от клиента**")
                for key in ["wishes", "questions"]:
                    if key in current_project: display_field(current_project, key, field_map[key])

        if is_auth:
            st.markdown("---")
            st.subheader("3. Управление проектом (внутренняя информация)")
            
            try: current_status_index = STATUS_OPTIONS.index(current_project.get('status'))
            except ValueError: current_status_index = 0
            try: current_engineer_index = ENGINEER_O
