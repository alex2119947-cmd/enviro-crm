import streamlit as st
import time
from datetime import datetime
import base64
import os
import json # <-- 1. Импортируем библиотеку для работы с JSON

# --- ИМЯ ФАЙЛА ДЛЯ ХРАНЕНИЯ ДАННЫХ ---
DATA_FILE = "projects.json"

# --- ПАРОЛЬ ---
CORRECT_PASSWORD = "zxenv2026"

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="CRM ENVIRO.KG", layout="wide", initial_sidebar_state="collapsed")

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛОМ ДАННЫХ ---

def load_projects():
    """Загружает проекты из файла projects.json. Если файл не найден или пуст, возвращает пустой список."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # Если файл поврежден или пуст, начинаем с чистого листа
                return []
    return []

def save_projects(data):
    """Сохраняет весь список проектов в файл projects.json."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def video_to_base64(path):
    if not os.path.exists(path): return None
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode()

def create_project(data):
    """Создает новый проект, добавляет его в session_state и сохраняет в файл."""
    # Улучшенная генерация ID: находим максимальный существующий ID и прибавляем 1
    if st.session_state.projects:
        max_id = max(p['id'] for p in st.session_state.projects)
    else:
        max_id = 0
    
    new_project_id = max_id + 1
    
    new_project = {
        "id": new_project_id,
        "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "На рассмотрении у инженера",
        "status_desc": "Ожидайте ответа...",
        "chat_history": [{"role": "assistant", "content": f"Здравствуйте, {data.get('client_name') or data.get('contact_person')}! Ваша заявка принята."}]
    }
    new_project.update(data)
    
    st.session_state.projects.append(new_project)
    save_projects(st.session_state.projects) # <-- 2. СОХРАНЯЕМ ДАННЫЕ В ФАЙЛ
    
    st.session_state.current_project_id = new_project["id"]
    st.session_state.page = "project_page"
    st.rerun()

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ---

# 3. При первом запуске сессии загружаем проекты из файла, а не создаем пустой список
if 'projects' not in st.session_state:
    st.session_state.projects = load_projects()

if 'page' not in st.session_state: st.session_state.page = "client_form"
if 'current_project_id' not in st.session_state: st.session_state.current_project_id = None
if 'is_authenticated' not in st.session_state: st.session_state.is_authenticated = False

# --- НАВИГАЦИЯ ---
def handle_role_change():
    st.session_state.current_project_id = None
    if st.session_state.role_selector == "Сотрудник ENVIRO":
        st.session_state.page = "login" if not st.session_state.is_authenticated else "employee_dashboard"
    else:
        st.session_state.page = "client_form"

st.sidebar.title("Навигация")
st.sidebar.radio(
    "Выберите вашу роль:",
    ("Новый клиент", "Сотрудник ENVIRO"),
    key="role_selector",
    on_change=handle_role_change
)
st.sidebar.info("Версия прототипа: 4.0 (с БД)")


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

    def shared_form_elements():
        st.subheader("5. Загрузка файлов")
        return st.file_uploader("Прикрепите фото, планы или другие документы (PDF, DOC, JPG, PNG)", type=['jpg', 'png', 'jpeg', 'pdf', 'doc', 'docx'], accept_multiple_files=True)

    if object_type == 'Частный дом':
        st.header("Анкета для Частного Дома")
        with st.form("private_house_form", clear_on_submit=True):
            st.subheader("1. Контактная информация"); name = st.text_input("Имя клиента \*"); phone = st.text_input("Номер телефона \*"); email = st.text_input("Email")
            st.subheader("2. Информация об объекте"); address = st.text_input("Точный адрес \*"); col1, col2 = st.columns(2)
            with col1: area = st.number_input("Площадь дома (м²)", min_value=10); plot_size = st.number_input("Размер участка (в сотках)", min_value=1)
            with col2: floors = st.selectbox("Этажность", ["1 этаж", "2 этажа", "3 этажа", "Более 3"]); insulation = st.text_input("Наличие и тип утепления \*"); boiler_location = st.text_input("Расположение котельной")
            st.subheader("3. Текущие системы"); col3, col4 = st.columns(2)
            with col3: heating_type = st.text_input("Используемый вид отопления зимой"); power_phases = st.text_input("Сколько фаз идёт на объект"); cooling_type = st.text_input("Используемый вид охлаждения летом")
            with col4: coal_usage = st.number_input("Кол-во сжигае
