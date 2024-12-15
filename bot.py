import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, CallbackContext, ContextTypes
from datetime import datetime
import hashlib
import db_functions
import os


#таблицы перед запуском бота
db_functions.create_tables()

# этапы 
ASK_NAME, CHOOSE_STATUS, ENTER_CODE, ADD_GROUP, ENTER_GROUP, ENTER_ANOTHER_MEMBER, CONFIRM_GROUP, MAIN_MENU, JOIN_SUBJECT, SELECT_SUBJECT_FOR_JOIN, CREATE_SUBJECT, SELECT_SUBJECT_FOR_PAIR, CONDUCT_A_LESSON, CHOOSE_GROUP, MARK_STUDENT, CHOOSE_ADD_METHOD, PROCESS_FILE = range(17)

# коды 
codes = {
    "👨‍💻 Администратор": "1",
    "👨‍🎓 Староста": "2",
    "👩‍🏫 Преподаватель": "3",
}

# логирование
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger()
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

# стартовое сообщение
async def start(update: Update, context):
    print(" Функция start ")
    logger.info("Пользователь начал работу с ботом.")
    await update.message.reply_text("👋  Пожалуйста, введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())
    return ASK_NAME

async def ask_name(update: Update, context):
    print(" Функция ask_name ")
    context.user_data['full_name'] = update.message.text
    message = "👇 Выберите свой статус:"
    reply_keyboard = [
        ['🎓 Студент', '👨‍🎓 Староста'],
        ['👩‍🏫 Преподаватель', '👨‍💻 Администратор'],
        ['◀️']
    ]
    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    )
    logger.info("Пользователь выбрал статус.")
    return CHOOSE_STATUS

async def choose_status(update: Update, context):
    print(" Функция choose_status ")
    user_status = update.message.text
    logger.info(f"Пользователь выбрал статус: {user_status}")

    if user_status == '◀️':
        await update.message.reply_text("👋 Пожалуйста, введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())
        return ASK_NAME

    context.user_data['status'] = user_status

    if user_status == '🎓 Студент':
        full_name = context.user_data['full_name']
        group_info = db_functions.get_student_group_info(full_name)

        if group_info:
            await update.message.reply_text(
                f"Вы успешно вошли как {user_status}. Ваше ФИО: {full_name}\n\nИнформация о вашей группе:\n{group_info}",
                parse_mode="HTML"
            )
            await update.message.reply_text(
                "Выберите действие:",
                reply_markup=ReplyKeyboardMarkup([['🔍 Посмотреть оценки']], resize_keyboard=True)
            )
        else:
            await update.message.reply_text(
                f"Вы успешно вошли как {user_status}. Ваше ФИО: {full_name}\n\nК сожалению, информация о вашей группе не найдена."
            )
        return ConversationHandler.END

    await update.message.reply_text("Введите код доступа:", reply_markup=ReplyKeyboardMarkup([['◀️']], resize_keyboard=True))
    return ENTER_CODE
# ввод кода доступа
async def enter_code(update: Update, context):

    entered_code = update.message.text
    user_status = context.user_data['status']
    correct_code = codes.get(user_status)

    if entered_code == '◀️':
        message = "👇 Выберите свой статус:"
        reply_keyboard = [['🎓 Студент', '👨‍🎓 Староста'], ['👩‍🏫 Преподаватель', '👨‍💻 Администратор']]
        await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True))
        return CHOOSE_STATUS

    # проверка кода доступа
    if entered_code == correct_code:
        full_name = context.user_data['full_name']
        chat_id = update.message.chat_id
        logger.info(f"Успешная аутентификация: {user_status}, ФИО: {full_name}")

        if user_status == '👩‍🏫 Преподаватель':
            db_functions.add_teacher(full_name, chat_id)

        if user_status == '👨‍🎓 Староста':
            await update.message.reply_text(f"Вы успешно вошли как {user_status}.\nВаше ФИО: {full_name}")
            await update.message.reply_text("Введите номер группы:")
            return ENTER_GROUP

        elif user_status == '👩‍🏫 Преподаватель':
            await update.message.reply_text("Выберите действие:",
                                            reply_markup=ReplyKeyboardMarkup([
                                            ['📚 Добавить дисциплину', '📅 Провести занятие'],
                                            ['1234']
                                            ], resize_keyboard=True))
            return MAIN_MENU

        return ConversationHandler.END
    
    # неверный код
    await update.message.reply_text("❌ Неверный код! Попробуйте снова или вернитесь назад:",
                                    reply_markup=ReplyKeyboardMarkup([['◀️']], resize_keyboard=True))
    return ENTER_CODE
# добавление группы
async def add_group(update: Update, context):
    await update.message.reply_text("Введите номер группы:")
    return ENTER_GROUP

async def enter_group(update: Update, context):
    group_number = update.message.text
    context.user_data['group_number'] = group_number
    db_functions.create_group(group_number, context.user_data['full_name'])
    logger.info(f"Группа создана: {group_number}")

    chat_id = update.message.chat_id
    db_functions.add_teacher(context.user_data['full_name'], chat_id)
    logger.info(f"Chat ID старосты {context.user_data['full_name']} успешно сохранен: {chat_id}")

    await update.message.reply_text(
        "Выберите, как вы хотите добавить участников группы:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🖊 Вручную", callback_data="manual")],
            [InlineKeyboardButton("📄 Файлом (txt)", callback_data="file")]
        ])
    )
    return CHOOSE_ADD_METHOD

async def choose_add_method(update: Update, context):
    query = update.callback_query
    await query.answer()
    method = query.data

    if method == "manual":
        await query.message.reply_text(
            "Введите ФИО участника группы или нажмите '✅ Завершить':",
            reply_markup=ReplyKeyboardMarkup([['✅ Завершить']], resize_keyboard=True)
        )
        context.user_data['members'] = []
        return ENTER_ANOTHER_MEMBER

    elif method == "file":
        await query.edit_message_text("Пожалуйста, отправьте файл в формате .txt с ФИО студентов (каждый на новой строке).")
        return PROCESS_FILE

async def process_file(update: Update, context):
    document = update.message.document

    if not document:
        await update.message.reply_text("Ошибка: Пожалуйста, отправьте файл в формате .txt.")
        return

    if not document.file_name.endswith(".txt"):
        await update.message.reply_text("Ошибка: Файл должен быть в формате .txt.")
        return

    os.makedirs("downloads", exist_ok=True)

    file_path = f"downloads/{document.file_name}"

    try:
        # загрузка файла
        file = await document.get_file()
        await file.download_to_drive(file_path)

        # чтение файла
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            students = [line.strip() for line in lines if line.strip()]

        if not students:
            await update.message.reply_text("Ошибка: Файл пуст или содержит только пробелы.")
            return

        # добавление студентов
        for student in students:
            db_functions.add_member(student, context.user_data['group_number'])
            context.user_data.setdefault('members', []).append(student)

        await update.message.reply_text(f"✅ Успешно добавлено {len(students)} участников из файла.")
        return await confirm_group(update, context)
        
    except Exception as e:
        logging.error(f"Ошибка при обработке файла: {e}")
        await update.message.reply_text("Произошла ошибка при обработке файла. Попробуйте снова.")
        return

# добавление участников группы 
async def enter_another_member(update: Update, context):
    member_name = update.message.text

    if member_name == '✅ Завершить':
        return await confirm_group(update, context)

    context.user_data['members'].append(member_name.strip())
    db_functions.add_member(member_name.strip(), context.user_data['group_number'])
    await update.message.reply_text("Введите ФИО следующего участника или нажмите '✅ Завершить':")
    return ENTER_ANOTHER_MEMBER

# вывод инфы о группе 
async def confirm_group(update: Update, context):
    group_number = context.user_data['group_number']
    members = context.user_data['members'] 
    leader = context.user_data['full_name'] 
    number_of_members = len(members) + 1
    group_info = f"     <u>{group_number}</u>     \n" 
    group_info += "\n" 
    group_info += f"<i>Список группы ({number_of_members})</i>\n" 
    group_info += "\n" 
    sorted_members = sorted([leader] + members) 
    for member in sorted_members:
        if member == leader:
            group_info += f"<b>{member}</b>  👨‍🎓\n"  
        else:
            group_info += f"{member}\n"

    await update.message.reply_text(group_info, parse_mode="HTML")
    await update.message.reply_text("Подтвердите сохранение группы:", reply_markup=ReplyKeyboardMarkup([['✅ Подтвердить', '❌ Отменить']], resize_keyboard=True))
    return CONFIRM_GROUP

async def confirm_group_action(update: Update, context):
    action = update.message.text

    if action == '✅ Подтвердить':
        await update.message.reply_text("✅ Группа успешно сохранена.")
        await update.message.reply_text("Выберите действие:", 
                                        reply_markup=ReplyKeyboardMarkup([['📚 Присоединиться к дисциплине', '🔍 Посмотреть оценки']], resize_keyboard=True))
        return JOIN_SUBJECT

    elif action == '❌ Отменить':
        await update.message.reply_text("❌ Отменено. Начните заново.")
        return ADD_GROUP

# присоединение к дисциплине
async def join_subject(update: Update, context):
    logger.debug("Join subject function triggered.")
    if update.message.text != "📚 Присоединиться к дисциплине":
        logger.info(f"Неверная кнопка нажата: {update.message.text}. Ожидалась кнопка '📚 Присоединиться к дисциплине'.")
        return

    subjects_with_teachers = db_functions.get_all_subjects_with_teachers()

    if not subjects_with_teachers:
        logger.info("Нет дисциплин с преподавателями.")
        await update.message.reply_text("⚠️ Дисциплины пока не добавлены.")
        return ConversationHandler.END

    subjects_with_teachers.sort(key=lambda x: x[0].lower())  # Сортируем по имени дисциплины (без учета регистра)

    keyboard = [
        [InlineKeyboardButton(f"{subject} — {teacher}", callback_data=subject)]
        for subject, teacher in subjects_with_teachers
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    logger.info("Отправка кнопок выбора дисциплины пользователю.")
    await update.message.reply_text("Выберите дисциплину для присоединения:", reply_markup=reply_markup)
    return SELECT_SUBJECT_FOR_JOIN

# обработка выбора дисциплины для присоединения
async def select_subject_for_join(update: Update, context):
    print(" Функция select_subject_for_join ")
    query = update.callback_query
    await query.answer()

    selected_subject = query.data
    context.user_data['selected_subject'] = selected_subject
    group_number = context.user_data.get('group_number')

    # ПРОВЕРКА!!!     присоединилась ли УЖЕ эта группа к этой дисциплине
    if db_functions.is_group_already_joined(group_number, selected_subject):
        await query.message.reply_text("⚠️ Ваша группа уже присоединилась к этой дисциплине.")
        await query.message.edit_reply_markup(None)
        return JOIN_SUBJECT

    teacher_name = db_functions.get_teacher_by_subject(selected_subject)
    if not teacher_name:
        await query.message.reply_text("⚠️ Преподаватель для выбранной дисциплины не найден.")
        return JOIN_SUBJECT

    # если еще не присоединилась - отправляем запрос на присоединение преподу
    teacher_chat_id = db_functions.get_teacher_chat_id(teacher_name)
    if teacher_chat_id:
        await query.message.reply_text(f"Вы выбрали дисциплину '{selected_subject}'. Ожидайте подтверждения преподавателем.")
        await context.bot.send_message(
            teacher_chat_id,
            f"Группа {group_number} хочет присоединиться к дисциплине '{selected_subject}'.\n\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Подтвердить", callback_data=f"approve_{group_number}_{selected_subject}"),
                                                InlineKeyboardButton("Отклонить", callback_data=f"reject_{group_number}_{selected_subject}")]]),
        )
    else:
        await query.message.reply_text("⚠️ У преподавателя нет сохраненного chat_id.")

    await query.message.edit_reply_markup(None)

    # возврат к меню старосты
    await query.message.reply_text("Выберите действие:",
                                   reply_markup=ReplyKeyboardMarkup([['📚 Присоединиться к дисциплине', '🔍 Посмотреть оценки']], resize_keyboard=True))
    return JOIN_SUBJECT

# обработка ответа препода
async def handle_teacher_response(update: Update, context):
    print(" Функция handle_teacher_response ")
    query = update.callback_query
    await query.answer()

    data = query.data
    logger.debug(f"Преподаватель ответил: {data}")

    if data.startswith("approve_"):
        _, group_number, subject = data.split("_")
        logger.debug(f"Подтверждение дисциплины: группа {group_number}, дисциплина {subject}")

        # связываем группу с дисциплиной в бд
        db_functions.add_group_to_subject(group_number, subject)
        logger.debug(f"Группа {group_number} добавлена к дисциплине {subject}")

        # обновляем сообщение препода, информируя его о подтверждении
        await query.edit_message_text(
            text=f"✅ Заявка группы {group_number} на дисциплину '{subject}' одобрена.",
            reply_markup=None
        )

        # увед старосте о подтверждении
        leader_chat_id = db_functions.get_leader_chat_id(group_number)
        logger.debug(f"Чат старосты: {leader_chat_id}")
        if leader_chat_id:
            await context.bot.send_message(leader_chat_id, f"✅ Ваша группа успешно присоединилась к дисциплине '{subject}'.")

    elif data.startswith("reject_"):
        _, group_number, subject = data.split("_")
        logger.debug(f"Отклонение дисциплины: группа {group_number}, дисциплина {subject}")

        # обновляем сообщение преподавателя
        await query.edit_message_text(
            text=f"❌ Заявка группы {group_number} на дисциплину '{subject}' отклонена.",
            reply_markup=None
        )

        # увед старосте об отклонении
        leader_chat_id = db_functions.get_leader_chat_id(group_number)
        if leader_chat_id:
            await context.bot.send_message(leader_chat_id, f"❌ Заявка вашей группы на дисциплину '{subject}' отклонена.")
    return JOIN_SUBJECT

# обработка кнопки посмотреть оценки
async def view_grades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Функция view_grades")
    full_name = context.user_data.get('full_name')

    if not full_name:
        logger.error("Не удалось найти полное имя пользователя в контексте.")
        await update.message.reply_text("⚠️ Не удалось получить информацию о группе.")
        return

    group_number = db_functions.get_student_group(full_name)
    if not group_number:
        logger.error(f"Группа не найдена для пользователя: {full_name}")
        await update.message.reply_text("⚠️ Ваша группа не привязана к дисциплинам.")
        return

    subjects = db_functions.get_subjects_for_group(group_number)
    if not subjects:
        logger.info(f"Дисциплины не найдены для группы {group_number}.")
        await update.message.reply_text("❌ Ваша группа не присоединилась ни к одной дисциплине.")
        return

    keyboard = [[InlineKeyboardButton(subject, callback_data=f"view_grades_{subject}")] for subject in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите предмет:", reply_markup=reply_markup)

async def view_grades_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_subject = query.data.split("_")[2]
    full_name = context.user_data.get("full_name", None)

    if not full_name:
        await query.message.reply_text("⚠️ Не удалось определить пользователя.")
        return

    grades_info = db_functions.get_marks_for_subject(selected_subject, student_name=full_name)
    if not grades_info:
        await query.message.reply_text("⚠️ Нет оценок для выбранной дисциплины.")
        return

    message = f"<b>{selected_subject}</b>\n"
    for grade in grades_info:
        message += f"Дата: {grade['date']}\n"
        message += f"Оценка: {grade['mark']}\n\n"

    await query.message.edit_text(message, parse_mode="HTML")

async def cancel(update: Update, context):
    await update.message.reply_text("❌ Операция отменена.")
    return ConversationHandler.END

async def navigate_student(update: Update, context, direction):
    query = update.callback_query
    await query.answer()  # Подтверждение обработки

    sorted_students = context.user_data.get('sorted_students', [])
    current_index = context.user_data.get('current_student_index', 0)
    current_group_number = context.user_data.get('current_group_number', "Неизвестная группа")
    selected_groups = context.user_data.get('selected_groups', [])
    current_group_index = context.user_data.get('current_group_index', 0)

    # Рассчитываем новый индекс студента
    new_index = current_index + direction

    if new_index < 0:  # Если идём назад за начало группы
        if current_group_index > 0:  # Есть предыдущая группа
            await navigate_group(update, context, -1)
            # Переключаемся на последнего студента новой группы
            context.user_data['current_student_index'] = len(context.user_data['sorted_students']) - 1
        else:  # Невозможно перейти назад, остаться на текущем студенте
            return
    elif new_index >= len(sorted_students):  # Если идём дальше конца группы
        if current_group_index < len(selected_groups) - 1:  # Есть следующая группа
            await navigate_group(update, context, 1)
            # Переключаемся на первого студента новой группы
            context.user_data['current_student_index'] = 0
        else:  # Невозможно перейти вперёд, остаться на текущем студенте
            return
    else:
        # Обновляем текущий индекс студента
        context.user_data['current_student_index'] = new_index

    # Получаем данные текущего студента и группы
    sorted_students = context.user_data.get('sorted_students', [])
    current_index = context.user_data['current_student_index']
    student_name = sorted_students[current_index]

    # Получаем оценки
    selected_marks = context.user_data.get('marks', {})
    mark_text = selected_marks.get(student_name, "")

    # Генерация клавиатуры
    keyboard = generate_student_keyboard(generate_student_id(student_name))

    # Обновляем сообщение
    current_group_number = context.user_data['current_group_number']
    await query.edit_message_text(
        f"Группа: <b>{current_group_number}</b>\n\n<i>{student_name}</i> {mark_text}",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def navigate_group(update: Update, context, direction):
    selected_groups = context.user_data.get('selected_groups', [])
    current_group_index = context.user_data.get('current_group_index', 0)
    new_index = current_group_index + direction

    if 0 <= new_index < len(selected_groups):
        context.user_data['current_group_index'] = new_index
        new_group = selected_groups[new_index]
        context.user_data['current_group_number'] = new_group  

        students = db_functions.get_students_by_group(new_group)
        if not students:
            await update.callback_query.edit_message_text("⚠️ В группе нет студентов.")
            return

        sorted_students = sorted(students, key=lambda x: x[0])
        context.user_data['sorted_students'] = sorted_students
        context.user_data['current_student_index'] = 0  
        student_mapping = {generate_student_id(name): name for name in sorted_students}
        context.user_data['student_mapping'] = student_mapping
        student_name = sorted_students[0]
        selected_marks = context.user_data.get('marks', {})
        mark_text = selected_marks.get(student_name, "")
        keyboard = generate_student_keyboard(generate_student_id(student_name))

        await update.callback_query.edit_message_text(
            f"Группа: <b>{new_group}</b>\n\n<i>{student_name}</i> {mark_text}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

async def handle_marking(update: Update, context):
    print(" Функция handle_marking ")
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    action = parts[0]
    mark = parts[1]
    student_id = parts[2]  # тут id вместо имени

    student_mapping = context.user_data.get('student_mapping', {})
    student_name = student_mapping.get(student_id)

    if not student_name: 
        await query.edit_message_text("⚠️ Ошибка: студент не найден.")
        return

    MARK_EMOJIS = {
        "2": "2️⃣",
        "3": "3️⃣",
        "4": "4️⃣",
        "5": "5️⃣",
        "present": "✅",
        "absent": "❌",
    }

    selected_marks = context.user_data.get('marks', {})
    if action == "mark":
        if selected_marks.get(student_name) == MARK_EMOJIS[mark]:
            selected_marks.pop(student_name, None)  # убираем оценку, если та же самая
        else:
            selected_marks[student_name] = MARK_EMOJIS[mark]  # а тут сохраняем новую 

        context.user_data['marks'] = selected_marks

    # обновляем текущую группу и отображаем информацию
    current_group_number = context.user_data.get('current_group_number', "Неизвестная группа")
    current_mark = selected_marks.get(student_name, "")

    # обновляем сообщение с текущей информацией
    keyboard = generate_student_keyboard(student_id)
    await query.edit_message_text(
        f"Группа: <b>{current_group_number}</b>\n\n<i>{student_name}</i> {current_mark}",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def main_menu_teacher(update: Update, context):
    print("Функция main_menu_teacher")
    text = update.message.text

    if text == "📚 Добавить дисциплину":
        print("нажал на 📚 Добавить дисциплину")
        await update.message.reply_text("Введите название новой дисциплины:")
        return CREATE_SUBJECT

    elif text == "🔍 Посмотреть оценки":
        await update.message.reply_text("Функция по просмотру оценок пока не реализована.")
        return MAIN_MENU

    elif text == "📅 Провести занятие":
        print("нажал на 📅 Провести занятие")
        teacher_name = context.user_data.get('full_name', 'Преподаватель')
        subjects = db_functions.get_subjects_by_teacher(teacher_name)

        if not subjects:
            await update.message.reply_text("❌ У вас нет добавленных дисциплин. Пожалуйста, сначала добавьте дисциплину.")
            return MAIN_MENU

        await conduct_class(update, context)
        return SELECT_SUBJECT_FOR_PAIR

    await update.message.reply_text("⚠️ Выберите действие из меню.")
    return MAIN_MENU

async def save_subject(update: Update, context):
    print(" Функция save_subject ")
    subject_name = update.message.text
    teacher_name = context.user_data['full_name']
    db_functions.add_subject(subject_name, teacher_name)
    await update.message.reply_text(f"✅ Дисциплина '{subject_name}' успешно добавлена.")
    await update.message.reply_text("Выберите действие:",
                                            reply_markup=ReplyKeyboardMarkup([
                                            ['📚 Добавить дисциплину', '📅 Провести занятие'],
                                            ['🔍 Посмотреть оценки']
                                            ], resize_keyboard=True))
    return MAIN_MENU

async def conduct_class(update: Update, context):
    print("Функция conduct_class")
    teacher_name = context.user_data['full_name']
    subjects = sorted(db_functions.get_subjects_by_teacher(teacher_name))

    if not subjects:
        await update.message.reply_text("❌ У вас нет добавленных дисциплин.")
        return MAIN_MENU

    keyboard = [
        [InlineKeyboardButton(subject, callback_data=f"conduct_{subject}")] for subject in subjects
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите дисциплину для проведения занятия:",
        reply_markup=reply_markup
    )
    return SELECT_SUBJECT_FOR_PAIR

async def select_class_subject(update: Update, context):
    print(" Функция select_class_subject ")
    query = update.callback_query
    await query.answer()
    selected_subject = query.data.split("_", 1)[1]
    context.user_data['selected_subject'] = selected_subject
    groups = sorted(db_functions.get_groups_by_subject(selected_subject))

    if not groups:
        await query.edit_message_text(f"⚠️ Нет групп, связанных с дисциплиной '{selected_subject}'.")
        return MAIN_MENU

    group_buttons = [
        [InlineKeyboardButton(group, callback_data=f"group_{group}")] for group in groups
    ]
    group_buttons.append([InlineKeyboardButton("✅", callback_data="confirm"),
                          InlineKeyboardButton("◀️", callback_data="back_to_subjects")])

    context.user_data['selected_groups'] = []

    await query.edit_message_text(
        "Выберите группу для проведения занятия:",
        reply_markup=InlineKeyboardMarkup(group_buttons)
    )
    return CHOOSE_GROUP  # хз по другому не робило, в падлу думать как сделать как и остлаьное 

async def toggle_group_selection(update: Update, context):
    print(" Функция toggle_group_selection ")
    query = update.callback_query
    await query.answer()
    callback_data = query.data

    if callback_data.startswith("group_"):
        group_name = callback_data.split("_")[1]
        selected_groups = context.user_data.get('selected_groups', [])

        if group_name in selected_groups:
            selected_groups.remove(group_name)
        else:
            selected_groups.append(group_name)

        context.user_data['selected_groups'] = selected_groups

        # отображение списка выбранных групп
        selected_text = "\n".join([f"<i>{group}</i>" for group in selected_groups]) if selected_groups else "<i>Нет выбранных групп.</i>"
        await query.edit_message_text(
            f"Выбранные группы:\n\n{selected_text}",
            reply_markup=query.message.reply_markup,
            parse_mode="HTML"
        )

    elif callback_data == "confirm":
        # подтверждение групп
        selected_groups = context.user_data.get('selected_groups', [])
        if not selected_groups:
            await query.answer("⚠️ Вы не выбрали ни одной группы!")
            return 

        selected_groups_text = "<i>" + "</i>, <i>".join(selected_groups) + "</i>"
        await query.edit_message_text(
            f"✅ Группы выбраны:\n\n{selected_groups_text}.",
            reply_markup=None,
            parse_mode="HTML"
        )
        await start_marking_students(query, context)
  
    elif callback_data == "back_to_subjects":
        # возврат к выбору дисциплины
        teacher_name = context.user_data.get('full_name')
        subjects = db_functions.get_subjects_by_teacher(teacher_name)

        if not subjects:
            await query.edit_message_text("❌ У вас нет добавленных дисциплин.")
            return MAIN_MENU

        keyboard = [
            [InlineKeyboardButton(subject, callback_data=f"conduct_{subject}")] for subject in subjects
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Выберите дисциплину для проведения занятия:",
            reply_markup=reply_markup
        )

        return SELECT_SUBJECT_FOR_PAIR
    return CHOOSE_GROUP

def generate_student_id(student_name):
    # генерация короткого хэша для имени
    return hashlib.md5(student_name.encode()).hexdigest()[:8]

def generate_student_keyboard(student_id):
    keyboard = [
        [
            InlineKeyboardButton("2️⃣", callback_data=f"mark_2_{student_id}"),
            InlineKeyboardButton("3️⃣", callback_data=f"mark_3_{student_id}"),
            InlineKeyboardButton("4️⃣", callback_data=f"mark_4_{student_id}"),
            InlineKeyboardButton("5️⃣", callback_data=f"mark_5_{student_id}"),
            InlineKeyboardButton("✅", callback_data=f"mark_present_{student_id}"),
            InlineKeyboardButton("❌", callback_data=f"mark_absent_{student_id}")
        ],
        [
            InlineKeyboardButton("<<", callback_data="move_back"),
            InlineKeyboardButton("<", callback_data="prev_student"),
            InlineKeyboardButton(">", callback_data="next_student"),
            InlineKeyboardButton(">>", callback_data="move_forward")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_marking_students(query: Update, context):
    print(" Функция start_marking_students ")
    selected_groups = context.user_data.get('selected_groups', [])
    if not selected_groups:
        await query.edit_message_text("⚠️ Нет выбранных групп для проведения занятия.")
        return

    group_number = selected_groups[0]
    context.user_data['current_group_number'] = group_number 
    students = db_functions.get_students_by_group(group_number)

    if not students:  
        await query.edit_message_text("⚠️ В группе нет студентов.")
        return

    logger.info(f"Студенты в группе {group_number}: {students}")

    sorted_students = sorted(students, key=lambda x: x[0])
    context.user_data['sorted_students'] = sorted_students
    context.user_data['current_student_index'] = 0  
    student_mapping = {generate_student_id(name): name for name in sorted_students}
    context.user_data['student_mapping'] = student_mapping
    student_name = sorted_students[0]
    selected_marks = context.user_data.get('marks', {})
    keyboard = generate_student_keyboard(generate_student_id(student_name))
    mark_text = selected_marks.get(student_name, "")
    await query.edit_message_text(
        f"Группа: <b>{group_number}</b>\n\n<i>{student_name}</i> {mark_text}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    logger.info(f"Сообщение успешно отправлено: {group_number}, {student_name}")
    
    # Добавим кнопку завершения занятия
    await show_finish_button(query, context)  # Эта функция должна отображать кнопку завершения занятия

async def show_finish_button(update: Update, context):
    print(" Функция show_finish_button ")
 
    finish_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Завершить занятие", callback_data="finish_session")]
    ])
    await update.message.reply_text("Для завершения занятия нажмите кнопку ниже:", reply_markup=finish_keyboard)

async def cancel_finish_session(update: Update, context):
    print(" Функция cancel_finish_session ")
    query = update.callback_query
    await query.answer()
    await show_finish_button(query, context)

async def handle_finish_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Функция handle_finish_session")
    query = update.callback_query
    await query.answer()

    # Отправка сообщения с подтверждением завершения занятия
    confirm_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Подтвердить", callback_data="confirm_finish")],
        [InlineKeyboardButton("Отмена", callback_data="cancel_finish")]
    ])
    await query.edit_message_text(
        "Вы уверены, что хотите завершить занятие и сохранить оценки?",
        reply_markup=confirm_keyboard
    )

async def confirm_finish_session(update: Update, context):
    print("Функция confirm_finish_session")
    query = update.callback_query
    await query.answer()
    selected_marks = context.user_data.get('marks', {})
    selected_subject = context.user_data.get('selected_subject')
    for student, mark in selected_marks.items():
        db_functions.save_mark(student, selected_subject, mark)
    context.user_data.clear()
    await query.edit_message_text("✅ Занятие завершено. Оценки сохранены.")
    text = query.message.text 

    if text == "📚 Добавить дисциплину":
        print("нажал на 📚 Добавить дисциплину")
        await update.message.reply_text("Введите название новой дисциплины:")
        return CREATE_SUBJECT
    elif text == "📅 Провести занятие":
        print("нажал на 📅 Провести занятие")
        teacher_name = context.user_data.get('full_name', 'Преподаватель')
        subjects = db_functions.get_subjects_by_teacher(teacher_name)

        if not subjects:
            await update.message.reply_text("❌ У вас нет добавленных дисциплин. Пожалуйста, сначала добавьте дисциплину.")
            return MAIN_MENU

        await conduct_class(update, context)
        return SELECT_SUBJECT_FOR_PAIR
        
    else:
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ['📚 Добавить дисциплину', '📅 Провести занятие'],
                    ['🔍 Посмотреть оценки']
                ],
                resize_keyboard=True
            )
        )
        return MAIN_MENU  

def main():

    application = ApplicationBuilder().token("7500268240:AAEtuPOniFFCnaHSW55eUfe392egvxDONWU").build()
    application.add_handler(MessageHandler(filters.Regex('^🔍 Посмотреть оценки$'), view_grades)) # выводит неверную дату 
    application.add_handler(CallbackQueryHandler(view_grades_detail, pattern=r"^view_grades_.*"))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT, ask_name)],
            CHOOSE_STATUS: [MessageHandler(filters.TEXT, choose_status)],
            ENTER_CODE: [MessageHandler(filters.TEXT, enter_code)],
            ADD_GROUP: [MessageHandler(filters.TEXT, add_group)],
            ENTER_GROUP: [MessageHandler(filters.TEXT, enter_group)],
            ENTER_ANOTHER_MEMBER: [MessageHandler(filters.TEXT, enter_another_member)],
            CHOOSE_ADD_METHOD: [CallbackQueryHandler(choose_add_method)],
            PROCESS_FILE: [MessageHandler(filters.Document.ALL, process_file)],
            CONFIRM_GROUP: [MessageHandler(filters.TEXT, confirm_group_action)],
            MAIN_MENU: [
                MessageHandler(filters.TEXT, main_menu_teacher),
                MessageHandler(filters.Regex('^📚 Добавить дисциплину$'), save_subject),
                MessageHandler(filters.Regex('^📅 Провести занятие$'), conduct_class),
            ],
            JOIN_SUBJECT: [
                MessageHandler(filters.TEXT, join_subject),
                CallbackQueryHandler(select_subject_for_join)  
            ],
            SELECT_SUBJECT_FOR_JOIN: [
                CallbackQueryHandler(select_subject_for_join)    # сука из-за этого ничё не работало, какой идиот убрал?
            ],
            CREATE_SUBJECT: [MessageHandler(filters.TEXT, save_subject)],
            SELECT_SUBJECT_FOR_PAIR: [CallbackQueryHandler(select_class_subject, pattern="^conduct_")],
            CONDUCT_A_LESSON: [MessageHandler(filters.TEXT, conduct_class)],
            CHOOSE_GROUP: [CallbackQueryHandler(toggle_group_selection)],
            MARK_STUDENT: [MessageHandler(filters.TEXT, start_marking_students)],
            },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    # обработка подтверждения или отклонения запроса преподавателем
    application.add_handler(CallbackQueryHandler(handle_teacher_response, pattern="^(approve_|reject_)"))
    application.add_handler(CallbackQueryHandler(handle_marking, pattern=r"mark_\w+_\w+"))
    application.add_handler(CallbackQueryHandler(lambda u, c: navigate_student(u, c, -1), pattern="^prev_student$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: navigate_student(u, c, 1), pattern="^next_student$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: navigate_group(u, c, -1), pattern="^move_back$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: navigate_group(u, c, 1), pattern="^move_forward$"))
    application.add_handler(CallbackQueryHandler(handle_finish_session, pattern="^finish_session$"))
    application.add_handler(CallbackQueryHandler(confirm_finish_session, pattern="^confirm_finish$"))
    application.add_handler(CallbackQueryHandler(cancel_finish_session, pattern="^cancel_finish$"))
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
     
      