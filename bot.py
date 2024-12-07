import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from datetime import datetime
import hashlib
import db_functions

#таблицы перед запуском бота
db_functions.create_tables()

# этапы 
ASK_NAME, CHOOSE_STATUS, ENTER_CODE, ADD_GROUP, ENTER_GROUP, ENTER_ANOTHER_MEMBER, CONFIRM_GROUP, ADD_SUBJECT, JOIN_SUBJECT, SELECT_SUBJECT, CREATE_SUBJECT, CHOOSE_GROUP,MARK_STUDENT = range(13)

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
    logger.info("Пользователь начал работу с ботом.")
    await update.message.reply_text("👋  Пожалуйста, введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())
    return ASK_NAME

async def ask_name(update: Update, context):
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
                reply_markup=ReplyKeyboardMarkup([['🔍 Выбрать предмет']], resize_keyboard=True)
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
                                            reply_markup=ReplyKeyboardMarkup([['📚 Добавить дисциплину', '📅 Провести занятие']], resize_keyboard=True))
            return ADD_SUBJECT

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

    # сохранение chat id старосты
    chat_id = update.message.chat_id
    db_functions.add_teacher(context.user_data['full_name'], chat_id)
    logger.info(f"Chat ID старосты {context.user_data['full_name']} успешно сохранен: {chat_id}")

    await update.message.reply_text("Введите ФИО участника группы:", reply_markup=ReplyKeyboardMarkup([['✅ Завершить']], resize_keyboard=True))
    context.user_data['members'] = []
    return ENTER_ANOTHER_MEMBER

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
                                        reply_markup=ReplyKeyboardMarkup([['📚 Присоединиться к дисциплине', '🔍 Выбрать предмет']], resize_keyboard=True))
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
    return SELECT_SUBJECT

# обработка выбора дисциплины
async def select_subject(update: Update, context):
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
                                   reply_markup=ReplyKeyboardMarkup([['📚 Присоединиться к дисциплине', '🔍 Выбрать предмет']], resize_keyboard=True))
    return JOIN_SUBJECT

# обработка ответа препода
async def handle_teacher_response(update: Update, context):
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

        # Обновляем сообщение преподавателя
        await query.edit_message_text(
            text=f"❌ Заявка группы {group_number} на дисциплину '{subject}' отклонена.",
            reply_markup=None
        )

        # увед старосте об отклонении
        leader_chat_id = db_functions.get_leader_chat_id(group_number)
        if leader_chat_id:
            await context.bot.send_message(leader_chat_id, f"❌ Заявка вашей группы на дисциплину '{subject}' отклонена.")
    return JOIN_SUBJECT

# обработка кнопки - Добавить дисциплину
async def add_subject(update: Update, context):
    if update.message.text == "📚 Добавить дисциплину":
        await update.message.reply_text("Введите название новой дисциплины:")
        return CREATE_SUBJECT
    await update.message.reply_text("⚠️ Выберите действие из меню.")
    return ADD_SUBJECT 

async def save_subject(update: Update, context):
    subject_name = update.message.text
    teacher_name = context.user_data['full_name']
    db_functions.add_subject(subject_name, teacher_name)
    await update.message.reply_text(f"✅ Дисциплина '{subject_name}' успешно добавлена.")
    await update.message.reply_text("Выберите действие:",
                                    reply_markup=ReplyKeyboardMarkup([['📚 Добавить дисциплину', '📅 Провести занятие']], resize_keyboard=True))
    return ADD_SUBJECT

# показать дисциплины к которые присоединена группа 
async def view_subjects(update: Update, context):
    full_name = context.user_data['full_name']
    group_number = db_functions.get_student_group(full_name)
    if not group_number:
        logger.error("Group number not found for the user.")
        await update.message.reply_text("⚠️ Не удалось получить информацию о группе.")
        return

    subjects = db_functions.get_subjects_for_group(group_number)
    if not subjects:
        logger.info(f"No subjects found for group {group_number}.")
        await update.message.reply_text("❌ Ваша группа не присоединилась ни к одной дисциплине.")
        return

    keyboard = [
        [InlineKeyboardButton(subject, callback_data=subject)] for subject in subjects
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите предмет:", reply_markup=reply_markup)

async def cancel(update: Update, context):
    await update.message.reply_text("❌ Операция отменена.")
    return ConversationHandler.END

async def conduct_class(update: Update, context):
    teacher_name = context.user_data['full_name']

    subjects = sorted(db_functions.get_subjects_by_teacher(teacher_name)) 

    if not subjects:
        await update.message.reply_text("❌ У вас нет добавленных дисциплин.")
        return ADD_SUBJECT
 
    keyboard = [
        [InlineKeyboardButton(subject, callback_data=f"conduct_{subject}")] for subject in subjects
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите дисциплину для проведения занятия:",
        reply_markup=reply_markup
    )
    return SELECT_SUBJECT 

async def select_class_subject(update: Update, context):
    query = update.callback_query
    await query.answer()
    selected_subject = query.data.split("_", 1)[1]
    context.user_data['selected_subject'] = selected_subject
    groups = sorted(db_functions.get_groups_by_subject(selected_subject))

    if not groups:
        await query.edit_message_text(f"⚠️ Нет групп, связанных с дисциплиной '{selected_subject}'.")
        return ADD_SUBJECT

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
    query = update.callback_query
    await query.answer()
    callback_data = query.data

    if callback_data.startswith("group_"):
        # выбор группы
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

        return MARK_STUDENT 

    elif callback_data == "back_to_subjects":
        # возврат к выбору дисциплины
        teacher_name = context.user_data.get('full_name')
        subjects = db_functions.get_subjects_by_teacher(teacher_name)

        if not subjects:
            await query.edit_message_text("❌ У вас нет добавленных дисциплин.")
            return ADD_SUBJECT

        keyboard = [
            [InlineKeyboardButton(subject, callback_data=f"conduct_{subject}")] for subject in subjects
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Выберите дисциплину для проведения занятия:",
            reply_markup=reply_markup
        )

        return SELECT_SUBJECT
    return CHOOSE_GROUP

def generate_student_id(student_name):
    # Генерация короткого хэша для имени
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
    selected_groups = context.user_data.get('selected_groups', [])
    if not selected_groups:
        await query.edit_message_text("⚠️ Нет выбранных групп для проведения занятия.")
        return

    group_number = selected_groups[0]
    context.user_data['current_group_number'] = group_number  # Сохраняем номер текущей группы
    students = db_functions.get_students_by_group(group_number)

    if not students:  
        await query.edit_message_text("⚠️ В группе нет студентов.")
        return

    logger.info(f"Студенты в группе {group_number}: {students}")

    # Сортируем студентов
    sorted_students = sorted(students, key=lambda x: x[0])
    context.user_data['sorted_students'] = sorted_students
    context.user_data['current_student_index'] = 0  # Индекс первого студента

    # Создаем отображение student_id -> student_name
    student_mapping = {generate_student_id(name): name for name in sorted_students}
    context.user_data['student_mapping'] = student_mapping

    # Первый студент
    student_name = sorted_students[0]

    # Получаем оценки
    selected_marks = context.user_data.get('marks', {})

    # Генерация клавиатуры
    keyboard = generate_student_keyboard(generate_student_id(student_name))

    # Отображаем первого студента с его оценкой
    mark_text = selected_marks.get(student_name, "")
    await query.edit_message_text(
        f"Группа: <b>{group_number}</b>\n\n<i>{student_name}</i> {mark_text}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    logger.info(f"Сообщение успешно отправлено: {group_number}, {student_name}")
    
    # Добавим кнопку завершения занятия
    await show_finish_button(query, context)  # Эта функция должна отображать кнопку завершения занятия

async def handle_marking(update: Update, context):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    action = parts[0]
    mark = parts[1]
    student_id = parts[2]  # Используем ID вместо имени

    # Восстанавливаем имя студента из student_mapping
    student_mapping = context.user_data.get('student_mapping', {})
    student_name = student_mapping.get(student_id)

    if not student_name:  # Если имя студента не найдено
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

    # Сохраняем или убираем оценку
    selected_marks = context.user_data.get('marks', {})
    if action == "mark":
        if selected_marks.get(student_name) == MARK_EMOJIS[mark]:
            selected_marks.pop(student_name, None)  # Убираем оценку, если та же самая
        else:
            selected_marks[student_name] = MARK_EMOJIS[mark]  # Сохраняем новую оценку

        context.user_data['marks'] = selected_marks

    # Обновляем текущую группу и отображаем информацию
    current_group_number = context.user_data.get('current_group_number', "Неизвестная группа")
    current_mark = selected_marks.get(student_name, "")

    # Обновляем сообщение с текущей информацией
    keyboard = generate_student_keyboard(student_id)
    await query.edit_message_text(
        f"Группа: <b>{current_group_number}</b>\n\n<i>{student_name}</i> {current_mark}",
        parse_mode="HTML",
        reply_markup=keyboard
    )

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
        context.user_data['current_group_number'] = new_group  # Сохраняем номер текущей группы

        # Получаем список студентов новой группы
        students = db_functions.get_students_by_group(new_group)
        if not students:
            await update.callback_query.edit_message_text("⚠️ В группе нет студентов.")
            return

        # Сортируем и сохраняем в контексте
        sorted_students = sorted(students, key=lambda x: x[0])
        context.user_data['sorted_students'] = sorted_students
        context.user_data['current_student_index'] = 0  # Сбрасываем на первого студента

        # Обновляем отображение student_id → student_name
        student_mapping = {generate_student_id(name): name for name in sorted_students}
        context.user_data['student_mapping'] = student_mapping

        # Отображаем первого студента из новой группы
        student_name = sorted_students[0]
        selected_marks = context.user_data.get('marks', {})
        mark_text = selected_marks.get(student_name, "")

        # Используем функцию для генерации клавиатуры
        keyboard = generate_student_keyboard(generate_student_id(student_name))

        await update.callback_query.edit_message_text(
            f"Группа: <b>{new_group}</b>\n\n<i>{student_name}</i> {mark_text}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

async def show_finish_button(update: Update, context):
    # Отобразить кнопку завершения занятия
    finish_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Завершить занятие", callback_data="finish_session")]
    ])
    await update.message.reply_text("Для завершения занятия нажмите кнопку ниже:", reply_markup=finish_keyboard)

async def handle_finish_session(update: Update, context):
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
    query = update.callback_query
    await query.answer()

    # Сохранение оценок в базу данных
    selected_marks = context.user_data.get('marks', {})
    selected_subject = context.user_data.get('selected_subject')
    for student, mark in selected_marks.items():
        db_functions.save_mark(student, selected_subject, mark)

    # Удаление временных данных
    context.user_data.clear()

    # Возвращение клавиатуры преподавателя
    reply_markup = ReplyKeyboardMarkup(
        [['📚 Добавить дисциплину', '📅 Провести занятие']],
        resize_keyboard=True
    )
    await query.edit_message_text("✅ Занятие завершено. Оценки сохранены.")
    await query.message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def cancel_finish_session(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Вернуть клавиатуру с кнопкой завершения занятия
    await show_finish_button(query, context)


def main():
    application = ApplicationBuilder().token("7500268240:AAEtuPOniFFCnaHSW55eUfe392egvxDONWU").build()

    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("🔍 Выбрать предмет"), view_subjects))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT, ask_name)],
            CHOOSE_STATUS: [MessageHandler(filters.TEXT, choose_status)],
            ENTER_CODE: [MessageHandler(filters.TEXT, enter_code)],
            ADD_GROUP: [MessageHandler(filters.TEXT, add_group)],
            ENTER_GROUP: [MessageHandler(filters.TEXT, enter_group)],
            ENTER_ANOTHER_MEMBER: [MessageHandler(filters.TEXT, enter_another_member)],
            CONFIRM_GROUP: [MessageHandler(filters.TEXT, confirm_group_action)],
            ADD_SUBJECT: [
                MessageHandler(filters.TEXT & filters.Regex("📅 Провести занятие"), conduct_class),
                MessageHandler(filters.TEXT, add_subject),
            ],
            JOIN_SUBJECT: [
                MessageHandler(filters.TEXT, join_subject),
                CallbackQueryHandler(select_subject)  
            ],

            SELECT_SUBJECT: [
                CallbackQueryHandler(select_class_subject, pattern="^conduct_"),
                CallbackQueryHandler(select_subject)    # сука из-за этого ничё не работало, какой идиот убрал?
            ],
            CREATE_SUBJECT: [MessageHandler(filters.TEXT, save_subject)],
            CHOOSE_GROUP: [CallbackQueryHandler(toggle_group_selection)],
            MARK_STUDENT: [MessageHandler(filters.TEXT, start_marking_students)],  # Добавлен обработчик для MARK_STUDENT
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
     
      