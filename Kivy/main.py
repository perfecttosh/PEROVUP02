import calendar
from datetime import datetime
from functools import partial

import mysql.connector
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.app import App

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'calendar'
}





def save_meeting_changes(meeting, name, date_str, desc, loc, event_type):
    if event_type == 'meeting':
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE meetings
            SET meeting_name = %s,
                meeting_date = %s,
                description = %s,
                location = %s
            WHERE idmeetings = %s
        """, (name.text.strip(), date_str, desc.text.strip(), loc.text.strip(), meeting['idmeetings']))

        conn.commit()
        conn.close()
    elif event_type == 'event':
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE events
            SET event_name = %s,
                event_date = %s,
                description = %s,
                location = %s
            WHERE idevents = %s
        """, (name.text.strip(), date_str, desc.text.strip(), loc.text.strip(), meeting['idevents']))

        conn.commit()
        conn.close()

def update_event(user_id, event_id, name, date, description, location, event_type=None):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE events
        SET event_name = %s, event_date = %s, description = %s, location = %s
        WHERE idevents = %s AND idusers = %s
    """, (name, date, description, location, event_id, user_id))
    conn.commit()
    conn.close()

def update_meeting(user_id, meeting_id, name, date, description, location, event_type=None):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE meetings
        SET meeting_name = %s, meeting_date = %s, description = %s, location = %s
        WHERE idmeetings = %s AND idusers = %s
    """, (name, date, description, location, meeting_id, user_id))
    conn.commit()
    conn.close()



def get_events_for_date(user_id, date):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events WHERE idusers = %s AND event_date = %s", (user_id, date))
    events = cursor.fetchall()
    conn.close()
    return events

def get_meetings_for_date(user_id, date):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM meetings WHERE idusers = %s AND meeting_date = %s", (user_id, date))
    meetings = cursor.fetchall()
    conn.close()
    return meetings

def delete_event(event_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE idevents = %s", (event_id,))
    conn.commit()
    conn.close()


def add_event(user_id, name, date, description, location, event_type):
    # Создание подключения к базе данных
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Добавляем событие
    if event_type == 'event':
        cursor.execute("""
            INSERT INTO events (idusers, event_name, event_date, description, location)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, name, date, description, location))
    # Добавляем мероприятие
    elif event_type == 'meeting':
        cursor.execute("""
            INSERT INTO meetings (idusers, meeting_name, meeting_date, description, location)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, name, date, description, location))

    # Подтверждаем транзакцию
    conn.commit()

    # Закрываем соединение
    cursor.close()
    conn.close()


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.username_input = TextInput(hint_text='Логин')
        self.password_input = TextInput(hint_text='Пароль', password=True)
        login_btn = Button(text='Войти')
        login_btn.bind(on_release=self.login)
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(login_btn)
        self.add_widget(layout)

    def login(self, _):
        username = self.username_input.text
        password = self.password_input.text
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE login = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            self.manager.current = 'calendar'
            self.manager.get_screen('calendar').set_user(user['idusers'])
        else:
            self.show_popup("Неверный логин или пароль")

    def show_popup(self, msg):
        popup = Popup(title='Ошибка', content=Label(text=msg), size_hint=(0.8, 0.3))
        popup.open()





class CalendarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_id = None
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)
        self.build_ui()

    def send_email(self, to_address, subject, body):
        import smtplib
        from email.mime.text import MIMEText

        from_address = "emailformycalendar@mail.ru"  # ← сюда свою почту
        password = "4eKhbUr7Lh2Zg1ujz6B9"  # ← сюда app password

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_address
        msg['To'] = to_address

        with smtplib.SMTP_SSL('smtp.mail.ru', 465) as server:
            server.login(from_address, password)
            server.sendmail(from_address, [to_address], msg.as_string())

    def send_email_popup(self):
        box = BoxLayout(orientation='vertical', spacing=10, padding=10)

        to_input = TextInput(hint_text="Кому (email)", multiline=False)
        subject_input = TextInput(hint_text="Тема письма", multiline=False)
        body_input = TextInput(hint_text="Текст письма", multiline=True)

        send_btn = Button(text="Отправить", background_color=(0.3, 0.6, 1, 1), size_hint_y=None, height=40)

        popup = Popup(title="Отправить письмо",
                      content=box,
                      size_hint=(0.9, 0.9))

        def send_email(_):
            to_address = to_input.text.strip()
            subject = subject_input.text.strip()
            body = body_input.text.strip()

            if not to_address or not subject or not body:

                return

            try:
                self.send_email(to_address, subject, body)
                print("Письмо успешно отправлено!")
                popup.dismiss()
            except Exception as e:
                print("Ошибка при отправке:", e)

        send_btn.bind(on_release=send_email)

        box.add_widget(Label(text="Отправка письма", size_hint_y=None, height=30))
        box.add_widget(to_input)
        box.add_widget(subject_input)
        box.add_widget(body_input)
        box.add_widget(send_btn)

        popup.open()



    def delete_event_or_meeting(self, item_id, item_type):
        """
        Универсальная функция для удаления события или мероприятия.
        :param item_id: ID события или мероприятия
        :param item_type: Тип объекта ('event' или 'meeting')
        """
        # Определяем таблицу в зависимости от типа
        table = 'events' if item_type == 'event' else 'meetings'

        # Удаляем запись из базы данных
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table} WHERE id{table[:-1]}s = %s", (item_id,))
        conn.commit()
        conn.close()

    def save_meeting_changes(self, meeting, name, desc, loc, type_spinner, date_str):

        meeting_name = name.text.strip()
        meeting_desc = desc.text.strip()
        meeting_location = loc.text.strip()
        event_type = 'meeting'
        update_meeting(self.user_id, meeting['idmeetings'], meeting_name, date_str, meeting_desc, meeting_location,
                        event_type)
        self.update_calendar()
        self.update_calendar()

    def set_user(self, user_id):
        self.user_id = user_id
        self.update_calendar()

    def build_ui(self):
        nav_bar = BoxLayout(size_hint_y=0.1)
        prev_btn = Button(text='<')
        next_btn = Button(text='>')
        self.month_label = Label()
        prev_btn.bind(on_release=self.prev_month)
        next_btn.bind(on_release=self.next_month)
        nav_bar.add_widget(prev_btn)
        nav_bar.add_widget(self.month_label)
        nav_bar.add_widget(next_btn)
        self.layout.add_widget(nav_bar)


        email_btn = Button(
            text="Отправить письмо",
            size_hint_y=None,
            height=40,
            background_color=(0.2, 0.5, 0.8, 1)
        )
        email_btn.bind(on_release=lambda x: self.send_email_popup())
        self.layout.add_widget(email_btn)

        self.grid = GridLayout(cols=7)
        self.layout.add_widget(self.grid)

    def update_calendar(self):
        self.grid.clear_widgets()  # Очищаем сетку
        russian_months = [
            '', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        self.month_label.text = f"{russian_months[self.current_month]} {self.current_year}"

        # Заголовки дней недели
        for day in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']:
            self.grid.add_widget(Label(text=day))

        # Получаем первый день месяца и количество дней
        first_day, total_days = calendar.monthrange(self.current_year, self.current_month)
        first_day = (first_day + 1) % 7  # Преобразуем первый день недели к понедельнику

        # Добавляем пустые метки для дней до первого дня месяца
        for _ in range(first_day):
            self.grid.add_widget(Label())

        # Проходим по всем дням месяца
        for day in range(1, total_days + 1):
            date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"

            # Получаем все события и мероприятия для этой даты из разных таблиц
            events = get_events_for_date(self.user_id, date_str)  # Получаем события
            meetings = get_meetings_for_date(self.user_id, date_str)  # Получаем мероприятия

            # Проверяем наличие события в таблице events
            has_event = len(events) > 0  # Если есть хотя бы одно событие
            has_meeting = len(meetings) > 0  # Если есть хотя бы одно мероприятие

            # Маркер для отображения на кнопке (если есть событие или мероприятие)
            marker = ''
            if has_event:  # Если есть событие, ставим маркер '*'
                marker = '*'
            if has_meeting:  # Если есть мероприятие, ставим маркер 'M'
                marker += 'M'

            # Текст для кнопки (номер дня и маркер)
            text = f"{day}{marker}"

            # Создаём кнопку с текстом
            btn = Button(text=text)

            # При нажатии на кнопку, открываем попап с событиями на эту дату
            btn.bind(on_release=lambda inst, d=date_str: self.open_event_popup(d))

            # Добавляем кнопку в сетку
            self.grid.add_widget(btn)

    def prev_month(self, _):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.update_calendar()

    def next_month(self, _):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.update_calendar()


    def open_event_popup(self, date_str):
        # Создаем базовую структуру для попапа
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Получаем события и мероприятия для данной даты
        events = get_events_for_date(self.user_id, date_str)  # Получаем события
        meetings = get_meetings_for_date(self.user_id, date_str)  # Получаем мероприятия

        # Если есть события или мероприятия, отображаем их
        event_list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        event_list_layout.bind(minimum_height=event_list_layout.setter('height'))  # Чтобы можно было прокручивать

        # Добавляем все события
        if events:
            for event in events:
                event_label = BoxLayout(size_hint_y=None, height=40, orientation='horizontal', spacing=5)
                event_label.add_widget(Label(
                    text=f"Событие: {event.get('event_name', 'Без названия')} - {event.get('location', 'Без места')}"
                ))

                # Кнопка редактировать событие
                edit_btn = Button(text="Редактировать", size_hint_x=None, width=120)
                edit_btn.bind(on_release=lambda btn, e=event: self.edit_event_popup(e, date_str))
                event_label.add_widget(edit_btn)

                event_list_layout.add_widget(event_label)

        # Добавляем все мероприятия
        if meetings:
            for meeting in meetings:
                meeting_label = BoxLayout(size_hint_y=None, height=40, orientation='horizontal', spacing=5)
                meeting_label.add_widget(Label(
                    text=f"Мероприятие: {meeting.get('meeting_name', 'Без названия мероприятия')} - {meeting.get('location', 'Без места')}"
                ))

                # Кнопка редактировать мероприятие
                edit_btn = Button(text="Редактировать", size_hint_x=None, width=120)
                # Добавляем date_str в лямбда-функцию
                edit_btn.bind(on_release=lambda btn, m=meeting, d=date_str: self.edit_meeting_popup(m, d))
                meeting_label.add_widget(edit_btn)

                # Вложенная функция для захвата текущих значений
                def bind_edit_button(btn, m):
                    name_input = TextInput(text=m.get('meeting_name', ''))
                    desc_input = TextInput(text=m.get('description', ''))
                    loc_input = TextInput(text=m.get('location', ''))

                    def on_edit(_):
                        save_meeting_changes(
                            meeting=m,
                            name=name_input,
                            date_str=date_str,
                            desc=desc_input,
                            loc=loc_input,
                            event_type='meeting'
                        )

                    btn.bind(on_release=on_edit)

                bind_edit_button(edit_btn, meeting)

                # Добавляем meeting_label в основной layout
                event_list_layout.add_widget(meeting_label)

        # Если scroll уже добавлен в box, нужно его удалить и создать заново
        for child in box.children:
            if isinstance(child, ScrollView):
                box.remove_widget(child)

        # Добавляем скролл для списка событий и мероприятий
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(event_list_layout)

        # Кнопка для добавления нового события/мероприятия
        add_btn = Button(text="Добавить событие/мероприятие", size_hint_y=None, height=40,
                         background_color=(.3, .6, .4, 1))
        add_btn.bind(on_release=lambda btn: self.open_add_event_popup(date_str))

        # Добавляем все элементы в попап
        box.add_widget(Label(text=f"События и мероприятия на {date_str}", size_hint_y=None, height=30))
        box.add_widget(scroll)
        box.add_widget(add_btn)

        # Открываем попап
        popup = Popup(title=f"События и мероприятия для {date_str}",
                      content=box,
                      size_hint=(0.9, 0.9))
        popup.open()

    def open_add_event_popup(self, date_str):
        # Создаем базовую структуру для добавления нового события/мероприятия
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Поля для добавления нового события/мероприятия
        name = TextInput(hint_text='Название')
        desc = TextInput(hint_text='Описание')
        loc = TextInput(hint_text='Место')
        type_spinner = Spinner(text='Тип: событие', values=('Тип: событие', 'Тип: мероприятие'))
        save_btn = Button(text='Сохранить', size_hint_y=None, height=40, background_color=(.3, .6, .4, 1))

        # Сохраняем новое событие/мероприятие
        def save_event(_):
            text = name.text.strip()
            if text:
                event_type = 'event' if type_spinner.text == 'Тип: событие' else 'meeting'
                # Добавляем событие/мероприятие в базу данных
                add_event(self.user_id, text, date_str, desc.text, loc.text, event_type)
                self.update_calendar()  # Обновляем календарь
                popup.dismiss()  # Закрываем попап

        save_btn.bind(on_release=save_event)

        # Добавляем все элементы в попап
        box.add_widget(Label(text=f"Добавить событие/мероприятие на {date_str}", size_hint_y=None, height=30))
        box.add_widget(name)
        box.add_widget(desc)
        box.add_widget(loc)
        box.add_widget(type_spinner)
        box.add_widget(save_btn)

        # Открываем попап для добавления
        popup = Popup(title=f"Добавить событие/мероприятие для {date_str}",
                      content=box,
                      size_hint=(0.9, 0.9))
        popup.open()

    def edit_event_popup(self, event, date_str):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)

        name = TextInput(text=event.get('event_name', ''), hint_text='Название')
        desc = TextInput(text=event.get('description', ''), hint_text='Описание')
        loc = TextInput(text=event.get('location', ''), hint_text='Место')
        type_spinner = Spinner(text='Тип: событие', values=('Тип: событие', 'Тип: мероприятие'))
        save_btn = Button(text='Сохранить изменения', size_hint_y=None, height=40, background_color=(.3, .6, .4, 1))
        delete_btn = Button(text='Удалить событие', size_hint_y=None, height=40, background_color=(.8, .2, .2, 1))

        def save_changes(_):
            event_type = 'event' if type_spinner.text == 'Тип: событие' else 'meeting'
            update_event(self.user_id, event['idevents'], name.text, date_str, desc.text, loc.text, event_type)
            self.update_calendar()
            popup.dismiss()

        # Используем универсальную функцию для удаления
        delete_btn.bind(on_release=lambda btn: self.delete_event_or_meeting(event['idevents'], 'event'))

        save_btn.bind(on_release=save_changes)

        box.add_widget(Label(text=f"Редактировать событие для {date_str}", size_hint_y=None, height=30))
        box.add_widget(name)
        box.add_widget(desc)
        box.add_widget(loc)
        box.add_widget(type_spinner)
        box.add_widget(save_btn)
        box.add_widget(delete_btn)

        popup = Popup(title=f"Редактировать событие для {date_str}",
                      content=box,
                      size_hint=(0.9, 0.9))
        popup.open()

    def edit_meeting_popup(self, meeting, date_str):
        # Создаем базовую структуру для редактирования мероприятия
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        # Поля для редактирования мероприятия
        name = TextInput(text=meeting.get('meeting_name', ''), hint_text='Название мероприятия')
        desc = TextInput(text=meeting.get('description', ''), hint_text='Описание')
        loc = TextInput(text=meeting.get('location', ''), hint_text='Место')
        type_spinner = Spinner(text='Тип: мероприятие', values=('Тип: событие', 'Тип: мероприятие'))

        # Кнопка сохранения изменений
        save_btn = Button(text='Сохранить изменения', size_hint_y=None, height=40, background_color=(.3, .6, .4, 1))

        # Кнопка удаления мероприятия
        delete_btn = Button(text='Удалить мероприятие', size_hint_y=None, height=40, background_color=(.8, .2, .2, 1))

        # Сохранение изменений
        save_btn.bind(
            on_release=lambda btn: self.save_meeting_changes(meeting, name, desc, loc, type_spinner, date_str))

        # Используем универсальную функцию для удаления
        delete_btn.bind(on_release=lambda btn: self.delete_event_or_meeting(meeting['idmeetings'], 'meeting'))

        # Добавляем все элементы в попап
        box.add_widget(name)
        box.add_widget(desc)
        box.add_widget(loc)
        box.add_widget(type_spinner)
        box.add_widget(save_btn)
        box.add_widget(delete_btn)

        # Открытие попапа
        popup = Popup(title='Редактировать мероприятие', content=box, size_hint=(None, None), size=(400, 500))
        popup.open()

        def save_meeting_changes(instance):
            meeting_name = name.text.strip()
            meeting_desc = desc.text.strip()
            meeting_location = loc.text.strip()
            event_type = 'meeting'
            update_meeting(self.user_id, meeting['idmeetings'], meeting_name, date_str, meeting_desc, meeting_location,
                           event_type)
            self.update_calendar()
            popup.dismiss()


class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(CalendarScreen(name='calendar'))
        return sm

if __name__ == '__main__':
    MyApp().run()
