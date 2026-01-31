import streamlit as st
import time
from datetime import datetime
import base64
import os

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="Прототип CRM ENVIRO", layout="wide")

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ КОДИРОВАНИЯ ВИДЕО ---
def video_to_base64(path):
    if not os.path.exists(path): return None
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode()

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ---
if 'projects' not in st.session_state: st.session_state.projects = []
if 'page' not in st.session_state: st.session_state.page = "client_form"
if 'current_project_id' not in st.session_state: st.session_state.current_project_id = None

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.title("Навигация")
role = st.sidebar.radio("Выберите вашу роль:", ("Новый клиент", "Сотрудник ENVIRO"), key="role_selector")

if role == "Сотрудник ENVIRO":
    if st.sidebar.button("Посмотреть все заявки"):
        st.session_state.page = "employee_dashboard"
        st.experimental_rerun()
else:
    if st.session_state.page != "client_form":
         if st.sidebar.button("Заполнить новую анкету"):
            st.session_state.page = "client_form"
            st.session_state.current_project_id = None
            st.experimental_rerun()

st.sidebar.info("Версия прототипа: 2.5")

# ==============================================================================
#                     ГЛАВНАЯ СТРАНИЦА (АНКЕТА)
# ==============================================================================
if st.session_state.page == "client_form":
    
    st.title("📋 Новая заявка")
    st.write("Для начала, пожалуйста, укажите тип вашего объекта.")

    # --- ИЗМЕНЕНИЕ 3: ВЫБОР ТИПА ОБЪЕКТА ---
    object_type = st.radio(
        "Тип объекта:",
        ('Частный дом', 'Коммерческое помещение'),
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("---")

    # --- АНКЕТА ДЛЯ ЧАСТНОГО ДОМА ---
    if object_type == 'Частный дом':
        st.header("Анкета для Частного Дома")
        with st.form("private_house_form"):
            st.subheader("1. Контактная информация")
            name = st.text_input("Имя клиента *", placeholder="Алексей")
            phone = st.text_input("Номер телефона *", placeholder="+996 (XXX) XX-XX-XX")
            email = st.text_input("Email")

            st.subheader("2. Информация об объекте")
            col1, col2 = st.columns(2)
            with col1:
                address = st.text_input("Точный адрес *")
                area = st.number_input("Площадь дома (м²) *", min_value=10)
                plot_size = st.number_input("Размер участка (в сотках)", min_value=1)
            with col2:
                floors = st.selectbox("Этажность", ["1 этаж", "2 этажа", "3 этажа", "Более 3"])
                insulation = st.text_input("Наличие и тип утепления *", placeholder="Базальтовая вата 10 см")
                boiler_location = st.text_input("Расположение котельной")

            st.subheader("3. Текущие системы")
            col3, col4 = st.columns(2)
            with col3:
                heating_type = st.text_input("Используемый вид отопления зимой")
                # --- ИЗМЕНЕНИЕ 2: ПЕРЕИМЕНОВАНИЕ ПОЛЯ ---
                power_phases = st.text_input("Сколько фаз идёт на объект", placeholder="1 фаза / 3 фазы")
                cooling_type = st.text_input("Используемый вид охлаждения летом")
            with col4:
                # --- ИЗМЕНЕНИЕ 1: НОВЫЕ ПОЛЯ ---
                coal_usage = st.number_input("Количество сжигаемого угля в мес. (тонн)")
                energy_usage_kwh = st.number_input("Расход кВт*ч в мес.")
                energy_usage_som = st.number_input("Расход на энергию/отопление в мес. (сом)")

            st.subheader("4. Дополнительно")
            wishes = st.text_area("Ваши пожелания")
            questions = st.text_area("Ваши вопросы")
            st.markdown("---")
            submitted = st.form_submit_button("Отправить заявку")

            if submitted:
                # ... (логика отправки, адаптированная для частного дома)
                if not name or not phone or not address: st.error("Заполните обязательные поля (*).")
                else:
                    new_project_data = {
                        "object_type": "Частный дом", "client_name": name, "phone": phone, "email": email, "address": address, "area": area, "plot_size": plot_size, "floors": floors, "insulation": insulation, "boiler_location": boiler_location, "heating_type": heating_type, "power_phases": power_phases, "cooling_type": cooling_type, "coal_usage": coal_usage, "energy_usage_kwh": energy_usage_kwh, "energy_usage_som": energy_usage_som, "wishes": wishes, "questions": questions,
                    }
                    # ... (остальная логика создания проекта)
                    st.session_state.page = "project_page"
                    # ...

    # --- АНКЕТА ДЛЯ КОММЕРЧЕСКОГО ПОМЕЩЕНИЯ ---
    elif object_type == 'Коммерческое помещение':
        st.header("Анкета для Коммерческого Объекта")
        with st.form("commercial_form"):
            st.subheader("1. Контактная информация")
            company_name = st.text_input("Название компании *")
            contact_person = st.text_input("Контактное лицо *")
            phone = st.text_input("Номер телефона *")
            email = st.text_input("Email")
            
            st.subheader("2. Информация об объекте")
            address = st.text_input("Адрес объекта *")
            activity_type = st.text_input("Тип деятельности", placeholder="Например, кафе, офис, производство")
            area = st.number_input("Общая площадь (м²) *", min_value=10)

            st.subheader("3. Дополнительно")
            wishes = st.text_area("Ваши пожелания и технические требования")
            
            st.markdown("---")
            submitted = st.form_submit_button("Отправить заявку")
            
            if submitted:
                if not company_name or not contact_person or not phone: st.error("Заполните обязательные поля (*).")
                else:
                    new_project_data = {
                        "object_type": "Коммерческое помещение", "company_name": company_name, "contact_person": contact_person, "phone": phone, "email": email, "address": address, "activity_type": activity_type, "area": area, "wishes": wishes,
                    }
                    # ... (логика создания проекта)
                    st.session_state.page = "project_page"
                    # ...
    
    # Общая часть для обеих форм - Видео
    st.markdown("---")
    st.header("ENVIRO — в действии")
    video_path = "enviro1.mp4"
    # ... (код видео без изменений) ...


# ==============================================================================
#                Остальные страницы (Панель управления и Страница проекта)
#                Остались без изменений.
# ==============================================================================

# ... (Код для employee_dashboard и project_page остается прежним) ...

