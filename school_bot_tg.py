import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
API_TOKEN = "7119373986:AAGg8OiAV2jhIPyqNjt9CHHtusMRKSAZtlE"  # Замените на ваш токен
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

# Инициализация базы данных (MySQL)
MYSQL_USER = "root"  # Замените на вашего пользователя MySQL
MYSQL_PASSWORD = "LOLkek1488"  # Замените на ваш пароль
MYSQL_HOST = "127.0.0.1"  # Хост MySQL
MYSQL_DATABASE = "school_bot"  # Имя базы данных

# Формируем строку подключения
engine = sa.create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"
)
Session = sessionmaker(bind=engine)
Base = declarative_base()


# Модели базы данных
class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.BigInteger, unique=True)
    phone_number = sa.Column(sa.String(20))
    role = sa.Column(sa.String(20))
    name = sa.Column(sa.String(100))
    grades = relationship("Grade", back_populates="student")
    homeworks = relationship("Homework", back_populates="student")


class Subject(Base):
    __tablename__ = "subjects"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100))
    teacher_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    teacher = relationship("User")


class Grade(Base):
    __tablename__ = "grades"
    id = sa.Column(sa.Integer, primary_key=True)
    student_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    subject_id = sa.Column(sa.Integer, sa.ForeignKey("subjects.id"))
    grade = sa.Column(sa.Integer)
    semester = sa.Column(sa.Integer)
    date = sa.Column(sa.Date)
    student = relationship("User", back_populates="grades")
    subject = relationship("Subject")


class Schedule(Base):
    __tablename__ = "schedule"
    id = sa.Column(sa.Integer, primary_key=True)
    subject_id = sa.Column(sa.Integer, sa.ForeignKey("subjects.id"))
    day_of_week = sa.Column(sa.String(20))
    time = sa.Column(sa.String(10))
    location = sa.Column(sa.String(100))
    subject = relationship("Subject")


class Homework(Base):
    __tablename__ = "homework"
    id = sa.Column(sa.Integer, primary_key=True)
    subject_id = sa.Column(sa.Integer, sa.ForeignKey("subjects.id"))
    student_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    description = sa.Column(sa.Text)
    due_date = sa.Column(sa.Date)
    subject = relationship("Subject")
    student = relationship("User", back_populates="homeworks")


class Feedback(Base):
    __tablename__ = "feedback"
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    message = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime)
    user = relationship("User")


# Состояния для FSM
class AuthStates(StatesGroup):
    waiting_for_phone = State()


class FeedbackStates(StatesGroup):
    waiting_for_message = State()


# Клавиатуры
def get_main_menu(role):
    buttons = []
    if role == "student":
        buttons = [
            [KeyboardButton(text="Мои оценки"), KeyboardButton(text="Расписание")],
            [KeyboardButton(text="Домашнее задание"), KeyboardButton(text="Обратная связь")]
        ]
    elif role == "teacher":
        buttons = [
            [KeyboardButton(text="Моё расписание"), KeyboardButton(text="Оценки учеников")],
            [KeyboardButton(text="Домашнее задание"), KeyboardButton(text="Обратная связь")]
        ]
    elif role == "admin":
        buttons = [
            [KeyboardButton(text="Список пользователей"), KeyboardButton(text="Предложения")]
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# Inline-кнопки для выбора дня или недели
def get_schedule_inline_keyboard():
    days = [
        ("Пн", "monday"), ("Вт", "tuesday"), ("Ср", "wednesday"),
        ("Чт", "thursday"), ("Пт", "friday"), ("Сб", "saturday"),
        ("Вс", "sunday")
    ]

    inline_keyboard = [
        [InlineKeyboardButton(text=day_label, callback_data=f"schedule_day_{day_value}") for day_label, day_value in days[i:i + 4]]
        for i in range(0, len(days), 4)
    ]

    inline_keyboard.append([InlineKeyboardButton(text="Неделя", callback_data="schedule_week")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return keyboard


# Inline-кнопки для выбора семестра
def get_semester_inline_keyboard(semesters):
    inline_keyboard = [
        [InlineKeyboardButton(text=f"Семестр {semester}", callback_data=f"grades_semester_{semester}")]
        for semester in sorted(semesters)
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# Команда /start
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    session = Session()
    print(f"Telegram ID при /start: {message.from_user.id}")
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    if user:
        print(f"Найден пользователь: {user.name}, роль: {user.role}, телефон: {user.phone_number}")
        await message.answer(f"Добро пожаловать, {user.name}!", reply_markup=get_main_menu(user.role))
        await state.update_data(phone_number=user.phone_number)
    else:
        phone_button = KeyboardButton(text="Отправить номер", request_contact=True)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[phone_button]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer("Пожалуйста, отправьте свой номер телефона для авторизации.", reply_markup=keyboard)
        await state.set_state(AuthStates.waiting_for_phone)
    session.close()


# Обработка номера телефона
@dp.message(AuthStates.waiting_for_phone)
async def process_phone_number(message: types.Message, state: FSMContext):
    if message.contact:
        session = Session()
        phone = message.contact.phone_number
        user = session.query(User).filter_by(phone_number=phone).first()
        if user:
            user.telegram_id = message.from_user.id
            session.commit()
            print(f"Обновлен telegram_id для пользователя {user.name}: {user.telegram_id}")
            await message.answer(f"Авторизация успешна, {user.name}!", reply_markup=get_main_menu(user.role))
            await state.update_data(phone_number=phone)
        else:
            user = User(
                telegram_id=message.from_user.id,
                phone_number=phone,
                role="student",
                name=message.from_user.full_name
            )
            session.add(user)
            session.commit()
            print(f"Создан новый пользователь: {user.name}, telegram_id: {user.telegram_id}")
            await message.answer("Вы зарегистрированы как студент!", reply_markup=get_main_menu("student"))
            await state.update_data(phone_number=phone)
        session.close()
        await state.clear()
    else:
        await message.answer("Пожалуйста, используйте кнопку для отправки номера.")


# Общий обработчик расписания (для учеников и преподавателей)
@dp.message(lambda message: message.text in ["Расписание", "Моё расписание"])
async def show_schedule_options(message: types.Message, state: FSMContext):
    session = Session()
    user_data = await state.get_data()
    phone_number = user_data.get("phone_number")
    user = session.query(User).filter_by(phone_number=phone_number).first()
    if user and user.role in ["student", "teacher"]:
        today = datetime.now().strftime("%A").lower()
        if user.role == "student":
            schedules = session.query(Schedule).join(Subject).filter(Schedule.day_of_week == today).all()
        else:  # teacher
            schedules = session.query(Schedule).join(Subject).filter(Subject.teacher_id == user.id,
                                                                     Schedule.day_of_week == today).all()

        # Сортируем уроки по времени
        schedules = sorted(schedules, key=lambda x: x.time)

        if schedules:
            response = f"📅 Расписание на {today.capitalize()}:\n\n"
            for schedule in schedules:
                subject = session.get(Subject, schedule.subject_id)
                teacher = session.get(User, subject.teacher_id)
                response += f"🕒 {schedule.time} — {subject.name}\n"
                response += f"   📍 {schedule.location}, 👩‍🏫 {teacher.name}\n\n"
        else:
            response = f"📅 Расписание на {today.capitalize()}:\n\nНа этот день занятий нет."

        await message.answer(response, reply_markup=get_schedule_inline_keyboard())
    else:
        await message.answer("Эта команда недоступна для вашей роли.")
    session.close()


# Обработка inline-кнопок для расписания
@dp.callback_query(lambda c: c.data.startswith("schedule_"))
async def process_schedule_callback(callback_query: types.CallbackQuery, state: FSMContext):
    session = Session()
    user_data = await state.get_data()
    phone_number = user_data.get("phone_number")
    user = session.query(User).filter_by(phone_number=phone_number).first()

    if not user or user.role not in ["student", "teacher"]:
        await callback_query.message.edit_text("Эта команда недоступна для вашей роли.")
        session.close()
        return

    callback_data = callback_query.data
    if callback_data == "schedule_week":
        # Показать расписание на неделю
        if user.role == "student":
            schedules = session.query(Schedule).join(Subject).all()
        else:  # teacher
            schedules = session.query(Schedule).join(Subject).filter(Subject.teacher_id == user.id).all()

        response = "📅 Расписание на неделю:\n\n"
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        for day, day_name in zip(days, day_names):
            day_schedules = [s for s in schedules if s.day_of_week == day]
            if day_schedules:
                # Сортируем уроки по времени
                day_schedules = sorted(day_schedules, key=lambda x: x.time)
                response += f"📌 {day_name}:\n"
                for schedule in day_schedules:
                    subject = session.get(Subject, schedule.subject_id)
                    teacher = session.get(User, subject.teacher_id)
                    response += f"🕒 {schedule.time} — {subject.name}\n"
                    response += f"   📍 {schedule.location}, 👩‍🏫 {teacher.name}\n\n"

        if response == "📅 Расписание на неделю:\n\n":
            response = "На эту неделю расписания нет."
        await callback_query.message.edit_text(response, reply_markup=get_schedule_inline_keyboard())

    else:
        # Показать расписание на конкретный день
        day = callback_data.split("_")[-1]
        day_names = {
            "monday": "Понедельник", "tuesday": "Вторник", "wednesday": "Среда",
            "thursday": "Четверг", "friday": "Пятница", "saturday": "Суббота", "sunday": "Воскресенье"
        }
        if user.role == "student":
            schedules = session.query(Schedule).join(Subject).filter(Schedule.day_of_week == day).all()
        else:  # teacher
            schedules = session.query(Schedule).join(Subject).filter(Subject.teacher_id == user.id, Schedule.day_of_week == day).all()

        # Сортируем уроки по времени
        schedules = sorted(schedules, key=lambda x: x.time)

        if schedules:
            response = f"📅 Расписание на {day_names[day]}:\n\n"
            for schedule in schedules:
                subject = session.get(Subject, schedule.subject_id)
                teacher = session.get(User, subject.teacher_id)
                response += f"🕒 {schedule.time} — {subject.name}\n"
                response += f"   📍 {schedule.location}, 👩‍🏫 {teacher.name}\n\n"
        else:
            response = f"📅 Расписание на {day_names[day]}:\n\nНа этот день занятий нет."

        await callback_query.message.edit_text(response, reply_markup=get_schedule_inline_keyboard())

    session.close()
    await callback_query.answer()


# Обработка оценок (для студентов)
@dp.message(lambda message: message.text == "Мои оценки")
async def show_grades(message: types.Message, state: FSMContext):
    session = Session()
    user_data = await state.get_data()
    phone_number = user_data.get("phone_number")
    user = session.query(User).filter_by(phone_number=phone_number).first()
    if user and user.role == "student":
        grades = session.query(Grade).filter_by(student_id=user.id).all()
        if not grades:
            await message.answer("📊 Ваши оценки:\n\nОценок пока нет.")
            session.close()
            return

        # Получаем список доступных семестров
        semesters = set(grade.semester for grade in grades)
        if not semesters:
            await message.answer("📊 Ваши оценки:\n\nСеместры не найдены.")
            session.close()
            return

        # Показываем кнопки для выбора семестра
        await message.answer("📊 Выберите семестр для просмотра оценок:", reply_markup=get_semester_inline_keyboard(semesters))
    else:
        await message.answer("Эта команда доступна только студентам.")
    session.close()


# Обработка выбора семестра для оценок студентов
@dp.callback_query(lambda c: c.data.startswith("grades_semester_"))
async def process_grades_semester_callback(callback_query: types.CallbackQuery, state: FSMContext):
    session = Session()
    user_data = await state.get_data()
    phone_number = user_data.get("phone_number")
    user = session.query(User).filter_by(phone_number=phone_number).first()

    if not user or user.role != "student":
        await callback_query.message.edit_text("Эта команда недоступна для вашей роли.")
        session.close()
        return

    semester = int(callback_query.data.split("_")[-1])
    grades = session.query(Grade).filter_by(student_id=user.id, semester=semester).all()

    if not grades:
        response = f"📊 Ваши оценки за {semester}-й семестр:\n\nОценок за этот семестр нет."
    else:
        # Группируем оценки по предметам
        grades_by_subject = {}
        for grade in grades:
            subject = session.get(Subject, grade.subject_id)
            if subject.name not in grades_by_subject:
                grades_by_subject[subject.name] = []
            grades_by_subject[subject.name].append(grade)

        response = f"📊 Ваши оценки за {semester}-й семестр:\n\n"
        for subject_name, subject_grades in sorted(grades_by_subject.items()):
            # Сортируем по дате
            subject_grades = sorted(subject_grades, key=lambda x: x.date)
            response += f"🟦 {subject_name}:\n"
            for grade in subject_grades:
                response += f"{grade.grade} ({grade.date})\n"
            response += "\n"

    # Получаем список доступных семестров для повторного показа кнопок
    all_grades = session.query(Grade).filter_by(student_id=user.id).all()
    semesters = set(grade.semester for grade in all_grades)

    await callback_query.message.edit_text(response, reply_markup=get_semester_inline_keyboard(semesters))
    session.close()
    await callback_query.answer()


# Обработка домашнего задания
@dp.message(lambda message: message.text == "Домашнее задание")
async def show_homework(message: types.Message, state: FSMContext):
    session = Session()
    user_data = await state.get_data()
    phone_number = user_data.get("phone_number")
    user = session.query(User).filter_by(phone_number=phone_number).first()
    if user:
        if user.role == "student":
            homeworks = session.query(Homework).filter_by(student_id=user.id).all()
        elif user.role == "teacher":
            homeworks = session.query(Homework).join(Subject).filter(Subject.teacher_id == user.id).all()
        else:
            await message.answer("Эта команда недоступна для вашей роли.")
            session.close()
            return
        if homeworks:
            response = "📚 Домашнее задание:\n\n"
            for homework in homeworks:
                subject = session.get(Subject, homework.subject_id)
                response += f"{subject.name} (до {homework.due_date}):\n"
                response += f"   {homework.description}\n\n"
        else:
            response = "📚 Домашнее задание:\n\nДомашнего задания нет."
        await message.answer(response)
    session.close()


# Обработка оценок учеников (для учителей)
@dp.message(lambda message: message.text == "Оценки учеников")
async def show_students_grades(message: types.Message, state: FSMContext):
    session = Session()
    user_data = await state.get_data()
    phone_number = user_data.get("phone_number")
    user = session.query(User).filter_by(phone_number=phone_number).first()
    if user and user.role == "teacher":
        subjects = session.query(Subject).filter_by(teacher_id=user.id).all()
        if not subjects:
            await message.answer("📊 Оценки учеников:\n\nУ вас нет предметов для отображения оценок.")
            session.close()
            return

        response = "📊 Оценки учеников:\n\n"
        for subject in sorted(subjects, key=lambda x: x.name):
            grades = session.query(Grade).filter_by(subject_id=subject.id).all()
            if not grades:
                continue

            response += f"🟦 {subject.name}:\n\n"
            # Группируем оценки по ученикам
            grades_by_student = {}
            for grade in grades:
                student = session.get(User, grade.student_id)
                if student.name not in grades_by_student:
                    grades_by_student[student.name] = []
                grades_by_student[student.name].append(grade)

            # Для каждого ученика группируем по семестрам
            for student_name, student_grades in sorted(grades_by_student.items()):
                response += f"👤 {student_name}:\n"
                # Группируем по семестрам
                grades_by_semester = {}
                for grade in student_grades:
                    if grade.semester not in grades_by_semester:
                        grades_by_semester[grade.semester] = []
                    grades_by_semester[grade.semester].append(grade)

                for semester, semester_grades in sorted(grades_by_semester.items()):
                    # Сортируем по дате
                    semester_grades = sorted(semester_grades, key=lambda x: x.date)
                    grades_str = ", ".join(f"{grade.grade} ({grade.date})" for grade in semester_grades)
                    response += f"Семестр {semester}: {grades_str}\n"
                response += "\n"

        if response == "📊 Оценки учеников:\n\n":
            response = "📊 Оценки учеников:\n\nОценок пока нет."
        await message.answer(response)
    else:
        await message.answer("Эта команда доступна только учителям.")
    session.close()


# Обработка обратной связи
@dp.message(lambda message: message.text == "Обратная связь")
async def start_feedback(message: types.Message, state: FSMContext):
    await message.answer("Напишите ваше сообщение для администратора.")
    await state.set_state(FeedbackStates.waiting_for_message)


@dp.message(FeedbackStates.waiting_for_message)
async def process_feedback(message: types.Message, state: FSMContext):
    session = Session()
    user_data = await state.get_data()
    phone_number = user_data.get("phone_number")
    user = session.query(User).filter_by(phone_number=phone_number).first()
    if user:
        feedback = Feedback(
            user_id=user.id,
            message=message.text,
            created_at=datetime.now()
        )
        session.add(feedback)
        session.commit()
        await message.answer("Сообщение отправлено администратору!")
        await state.clear()
    else:
        await message.answer("Ошибка: пользователь не найден.")
    session.close()


# Обработка списка пользователей (для админа)
@dp.message(lambda message: message.text == "Список пользователей")
async def show_users(message: types.Message, state: FSMContext):
    session = Session()
    user_data = await state.get_data()
    phone_number = user_data.get("phone_number")
    user = session.query(User).filter_by(phone_number=phone_number).first()
    print(
        f"Проверка для команды 'Список пользователей': phone_number={phone_number}, user={user.name if user else None}, role={user.role if user else None}")
    if user and user.role == "admin":
        users = session.query(User).all()
        if not users:
            await message.answer("👥 Список пользователей:\n\nПользователей пока нет.")
            session.close()
            return

        # Группируем пользователей по ролям
        users_by_role = {"admin": [], "teacher": [], "student": []}
        for u in users:
            users_by_role[u.role].append(u)

        response = "👥 Список пользователей:\n\n"

        # Администраторы
        if users_by_role["admin"]:
            response += "👑 Администраторы:\n"
            for u in sorted(users_by_role["admin"], key=lambda x: x.id):
                response += f"🟢 ID: {u.id} | {u.name} | {u.phone_number}\n"
            response += "\n"

        # Преподаватели
        if users_by_role["teacher"]:
            response += "👩‍🏫 Преподаватели:\n"
            for u in sorted(users_by_role["teacher"], key=lambda x: x.id):
                response += f"🟢 ID: {u.id} | {u.name} | {u.phone_number}\n"
            response += "\n"

        # Студенты
        if users_by_role["student"]:
            response += "🎓 Студенты:\n"
            for u in sorted(users_by_role["student"], key=lambda x: x.id):
                response += f"🟢 ID: {u.id} | {u.name} | {u.phone_number}\n"

        await message.answer(response)
    else:
        await message.answer("Эта команда доступна только администратору.")
    session.close()


# Обработка предложений (для админа)
@dp.message(lambda message: message.text == "Предложения")
async def show_feedback(message: types.Message, state: FSMContext):
    session = Session()
    user_data = await state.get_data()
    phone_number = user_data.get("phone_number")
    user = session.query(User).filter_by(phone_number=phone_number).first()
    print(
        f"Проверка для команды 'Предложения': phone_number={phone_number}, user={user.name if user else None}, role={user.role if user else None}")
    if user and user.role == "admin":
        feedbacks = session.query(Feedback).all()
        response = "💬 Предложения и обратная связь:\n\n"
        for fb in feedbacks:
            fb_user = session.get(User, fb.user_id)
            response += f"От {fb_user.name} ({fb.created_at}):\n"
            response += f"   {fb.message}\n\n"
        if response == "💬 Предложения и обратная связь:\n\n":
            response = "💬 Предложения и обратная связь:\n\nПредложений пока нет."
        await message.answer(response)
    else:
        await message.answer("Эта команда доступна только администратору.")
    session.close()


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())