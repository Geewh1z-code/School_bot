# School Bot

A Telegram bot for school management, allowing students, teachers, and administrators to interact with a MySQL database for schedules, grades, homework, and feedback.

## Features

- **Students**:
  - View personal grades by semester.
  - Check daily or weekly schedules.
  - Access assigned homework with due dates.
  - Submit feedback to administrators.
- **Teachers**:
  - View schedules for their subjects.
  - Check grades of their students, organized by subject and semester.
  - Review homework assigned to students.
  - Submit feedback.
- **Administrators**:
  - List all users by role (admin, teacher, student).
  - View feedback and suggestions from users.

## Technologies Used

- **Python 3.8+**: Core programming language.
- **aiogram**: Asynchronous Telegram Bot API framework.
- **SQLAlchemy**: ORM for MySQL database interactions.
- **MySQL**: Database for storing user data, grades, schedules, etc.
- **pymysql**: MySQL driver for Python.

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd school-bot
   ```

2. **Install Dependencies**:
   ```bash
   pip install aiogram sqlalchemy pymysql
   ```

3. **Set Up MySQL Database**:
   - Install MySQL if not already installed.
   - Create a database named `school_bot`.
   - Run the SQL script `database_bot.sql` to set up tables and populate initial data:
     ```bash
     mysql -u root -p school_bot < database_bot.sql
     ```

4. **Configure the Bot**:
   - Replace `API_TOKEN` in `alex_bot_new.py` with your Telegram Bot token (obtain from [@BotFather](https://t.me/BotFather)).
   - Update MySQL credentials (`MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_DATABASE`) in `alex_bot_new.py`.

5. **Run the Bot**:
   ```bash
   python alex_bot_new.py
   ```

## Usage

1. **Start the Bot**:
   - Send `/start` in Telegram to begin.
   - If unregistered, share your phone number for authentication.

2. **Available Commands** (based on role):
   - **Students**: "Мои оценки" (Grades), "Расписание" (Schedule), "Домашнее задание" (Homework), "Обратная связь" (Feedback).
   - **Teachers**: "Моё расписание" (Schedule), "Оценки учеников" (Student Grades), "Домашнее задание" (Homework), "Обратная связь" (Feedback).
   - **Admins**: "Список пользователей" (User List), "Предложения" (Feedback).

3. **Inline Keyboards**:
   - Choose days or weeks for schedules.
   - Select semesters for grades.

## Database Schema

The database (`school_bot`) includes the following tables:
- `users`: Stores user details (telegram_id, phone_number, role, name).
- `subjects`: Lists subjects with associated teacher IDs.
- `grades`: Records student grades by subject and semester.
- `schedule`: Contains class schedules (subject, day, time, location).
- `homework`: Tracks homework assignments with due dates.
- `feedback`: Stores user feedback with timestamps.

See `database_bot.sql` for the full schema and sample data.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit changes (`git commit -m 'Add feature'`).
4. Push to the branch (`git push origin feature-name`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.