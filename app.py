# ==============================================================================
# Библиотеки
# ==============================================================================
import base64
import json
import os
import time
from datetime import datetime

import requests
import streamlit as st

# ==============================================================================
# Конфигурация
# ==============================================================================
DATA_FILE = "projects.json"
UPLOAD_DIR = "file_uploads"
CORRECT_PASSWORD = "zxenv2026"
STATUS_OPTIONS = [
    "На рассмотрении у инженера",
    "В работе",
    "Требуются уточнения от клиента",
    "Расчет готов",
    "Проект завершен",
    "Отменен",
]
ENGINEER_OPTIONS = [
    "Не назначен",
    "Азамат К.",
    "Тимур М.",
    "Евгений П.",
    "Другой специалист",
]

# ==============================================================================
# Настройка Telegram
# ==============================================================================
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except (KeyError, FileNotFoundError):
    TELEGRAM_TOKEN = None
    TELEGRAM_CHAT_ID = None

# ==============================================================================
# Инициализация
# ==============================================================================
os.makedirs(UPLOAD_DIR, exist_ok=True)
st.set_page_config(
    page_title="CRM ENVIRO.KG", layout="wide", initial_sidebar_state="collapsed"
)

# ==============================================================================
# Функции
# ==============================================================================

def send_telegram_notification(message):
    """Отправляет уведомление в Telegram, если настроены секреты."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram-уведомления не настроены.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки Telegram: {e}")

def load_projects():
    """Загружает проекты из JSON-файла."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_projects(data):
    """Сохраняет проекты в JSON-файл."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def video_to_base64(path):
    """Кодирует видео в base64 для отображения."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def create_project(data):
    """Создает новый проект, сохраняет и отправляет уведомление."""
    all_projects = st.session_state.get("projects", [])
    max_id = max(p["id"] for p in all_projects) if all_projects else 0

    new_project = {
        "id": max_id + 1,
        "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "На рассмотрении у инженера",
        "status_desc": "Ожидайте ответа...",
        "chat_history": [
            {
                "role": "assistant",
                "content": (
                    f"Здравствуйте, {data.get('client_name') or data.get('contact_person')}! "
                    "Ваша заявка принята."
                ),
            }
        ],
        "assigned_engineer": "Не назначен",
        "internal_notes": [],
    }
    new_project.update(data)
    all_projects.append(new_project)
    save_projects(all_projects)

    client_name = data.get("client_name") or data.get("company_name", "N/A")
    address = data.get("address", "Адрес не указан")
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


# ==============================================================================
# Инициализация Session State
# ==============================================================================
if "projects" not in st.session_state:
    st.session_state.projects = load_projects()
if "page" not in st.session_state:
    st.session_state.page = "client_form"
if "current_project_id" not in st.session_state:
    st.session_state.current_project_id = None
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False


# ==============================================================================
# Боковая панель (Sidebar)
# ==============================================================================
def handle_role_change():
    """Обрабатывает смену роли пользователя."""
    if st.session_state.role_selector == "Сотрудник ENVIRO":
        st.session_state.page = (
            "employee_dashboard" if st.session_state.get("is_authenticated") else "login"
        )
    else:
        st.session_state.page = "client_form"
    st.session_state.current_project_id = None


st.sidebar.title("Навигация")
st.sidebar.radio(
    "Выберите вашу роль:",
    ("Новый клиент", "Сотрудник ENVIRO"),
    key="role_selector",
    on_change=handle_role_change,
)
st.sidebar.info("Версия: 5.0")


# ==============================================================================
# Основная логика отображения страниц
# ==============================================================================
current_page = st.session_state.get("page", "client_form")

# --- СТРАНИЦА ВХОДА ---
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

# --- СТРАНИЦА КЛИЕНТА (ФОРМЫ) ---
elif current_page == "client_form":
    st.title("📋 Заявка в инженерный отдел ENVIRO.KG")
    object_type = st.radio(
        "Тип объекта:",
        ("Частный дом", "Коммерческое помещение"),
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("---")

    def shared_form_elements():
        st.subheader("5. Загрузка файлов")
        st.caption("Вы можете прикрепить несколько файлов: планы, схемы, фото и т.д.")
        return st.file_uploader(
            label="**Нажмите, чтобы выбрать файлы, или перетащите их в эту область**",
            type=["jpg", "png", "jpeg", "pdf", "doc", "docx"],
            accept_multiple_files=True,
        )

    if object_type == "Частный дом":
        with st.form("private_house_form", clear_on_submit=True):
            # ... (Код формы для частного дома без изменений)
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
          
