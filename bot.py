import telebot
from telebot import types

# Токен твоего бота «Абылайхан»
TOKEN = '8912780604:AAG-IvjACCuX0Kw3YGdk5btZXPEzZ6oPMXI'
bot = telebot.TeleBot(TOKEN)

# ⚠️ ВНИМАНИЕ: Вставь сюда свой Telegram ID (цифрами), чтобы видеть все анкеты и анонимки!
ADMIN_ID = 000000000  # Замени нули на свой ID

# Хранилище анкет в памяти: user_id -> {name, age, bio, photo}
users_profiles = {}

# Состояния пользователей
user_states = {}
# Кому отправляется анонимное сообщение: user_id -> target_id
chat_targets = {}

# Главная клавиатура
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_profile = types.KeyboardButton("👤 Моя анкета")
    btn_search = types.KeyboardButton("👀 Смотреть анкеты")
    markup.add(btn_profile, btn_search)
    return markup

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Добро пожаловать в бот знакомств **«Абылайхан»** 🥷\n\n"
        "Здесь ты можешь создать свою анкету с фото, смотреть других участников и отправлять им анонимные сообщения.\n\n"
        "Выбери нужный раздел внизу:",
        reply_markup=get_main_keyboard()
    )

# Обработка главных кнопок меню
@bot.message_handler(func=lambda message: message.text in ["👤 Моя анкета", "👀 Смотреть анкеты"])
def handle_menu(message):
    user_id = message.from_user.id
    
    if message.text == "👤 Моя анкета":
        if user_id in users_profiles:
            p = users_profiles[user_id]
            text = f"📄 **Твоя анкета:**\n\nИмя: {p['name']}\nВозраст: {p['age']}\nО себе: {p['bio']}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔄 Изменить анкету", callback_data="edit_profile"))
            
            if p.get('photo'):
                bot.send_photo(message.chat.id, p['photo'], caption=text, reply_markup=markup, parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')
        else:
            user_states[user_id] = "waiting_name"
            bot.send_message(message.chat.id, "Давай создадим анкету! Как тебя зовут (или какой псевдоним)?")

    elif message.text == "👀 Смотреть анкеты":
        other_users = [uid for uid in users_profiles.keys() if uid != user_id]
        
        if not other_users:
            bot.send_message(message.chat.id, "😔 Пока что нет других анкет. Загляни чуть позже или позови друзей!")
            return
            
        target_id = other_users[0]
        p = users_profiles[target_id]
        
        text = f"👤 **Анкета участника:**\n\nИмя: {p['name']}\nВозраст: {p['age']}\nО себе: {p['bio']}"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🥷 Написать анонимно", callback_data=f"anon_msg_{target_id}"))
        
        if p.get('photo'):
            bot.send_photo(message.chat.id, p['photo'], caption=text, reply_markup=markup, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# Обработка нажатий на инлайн-кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id
    
    if call.data == "edit_profile":
        user_states[user_id] = "waiting_name"
        bot.send_message(call.message.chat.id, "Как тебя зовут (или какой псевдоним)?")
        
    elif call.data.startswith("anon_msg_"):
        target_id = int(call.data.split("_")[2])
        chat_targets[user_id] = target_id
        user_states[user_id] = "waiting_anon_text"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_anon"))
        
        bot.send_message(
            call.message.chat.id, 
            "✉️ Введи текст анонимного сообщения. Этот человек получит его, но **не узнает твое имя**:",
            reply_markup=markup
        )
        
    elif call.data == "cancel_anon":
        if user_id in chat_targets:
            del chat_targets[user_id]
        if user_id in user_states:
            del user_states[user_id]
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Отправка сообщения отменена."
        )

# Обработка всех входящих сообщений (текст и фото)
@bot.message_handler(content_types=['text', 'photo'])
def handle_all_messages(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    
    if state == "waiting_name":
        if message.content_type == 'text':
            users_profiles[user_id] = {"name": message.text.strip()}
            user_states[user_id] = "waiting_age"
            bot.send_message(message.chat.id, "Отлично! Теперь укажи свой возраст:")
        else:
            bot.send_message(message.chat.id, "Пожалуйста, отправь текстом свое имя или псевдоним.")
            
    elif state == "waiting_age":
        if message.content_type == 'text':
            users_profiles[user_id]["age"] = message.text.strip()
            user_states[user_id] = "waiting_bio"
            bot.send_message(message.chat.id, "Напиши пару слов о себе (увлечения, класс или хобби):")
        else:
            bot.send_message(message.chat.id, "Пожалуйста, укажи возраст цифрами.")
            
    elif state == "waiting_bio":
        if message.content_type == 'text':
            users_profiles[user_id]["bio"] = message.text.strip()
            user_states[user_id] = "waiting_photo"
            bot.send_message(message.chat.id, "📸 Отправь фотографию для своей анкеты (или нажми /skip, если без фото):")
        else:
            bot.send_message(message.chat.id, "Пожалуйста, напиши текст о себе.")
            
    elif state == "waiting_photo":
        profile_completed = False
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            users_profiles[user_id]["photo"] = file_id
            profile_completed = True
        elif message.content_type == 'text' and message.text.lower() == '/skip':
            users_profiles[user_id]["photo"] = None
            profile_completed = True
        else:
            bot.send_message(message.chat.id, "Пожалуйста, отправь фотографию или напиши /skip, чтобы пропустить.")
            return

        if profile_completed:
            del user_states[user_id]
            bot.send_message(message.chat.id, "✅ Анкета успешно сохранена!", reply_markup=get_main_keyboard())
            
            # Уведомление админу о новой анкете
            if ADMIN_ID != 000000000:
                p = users_profiles[user_id]
                admin_text = (
                    f"🚨 **Новая анкета в боте!**\n\n"
                    f"👤 Юзер: @{message.from_user.username or 'нет юзернейма'} (ID: {user_id})\n"
                    f"Имя: {p['name']}\nВозраст: {p['age']}\nО себе: {p['bio']}"
                )
                try:
                    if p.get('photo'):
                        bot.send_photo(ADMIN_ID, p['photo'], caption=admin_text, parse_mode='Markdown')
                    else:
                        bot.send_message(ADMIN_ID, admin_text, parse_mode='Markdown')
                except Exception:
                    pass

    elif state == "waiting_anon_text":
        if message.content_type == 'text':
            target_id = chat_targets.get(user_id)
            if target_id:
                try:
                    # Отправляем получателю
                    bot.send_message(
                        target_id,
                        f"🥷 **Тебе пришло новое анонимное сообщение!**\n\n💬 Текст:\n{message.text}\n\n*(Отправитель остался неизвестным)*",
                        parse_mode='Markdown'
                    )
                    bot.send_message(message.chat.id, "✅ Твое анонимное сообщение успешно доставлено!", reply_markup=get_main_keyboard())
                    
                    # 🕵️ Отправляем копию АДМИНУ (тебе)
                    if ADMIN_ID != 000000000:
                        sender_name = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"
                        bot.send_message(
                            ADMIN_ID,
                            f"🕵️ **Лог анонимки:**\n\n"
                            f"📤 От кого: {sender_name} (ID: {user_id})\n"
                            f"📥 Кому (ID): {target_id}\n"
                            f"💬 Текст: {message.text}",
                            parse_mode='Markdown'
                        )
                except Exception:
                    bot.send_message(message.chat.id, "❌ Не удалось отправить сообщение (пользователь мог заблокировать бота).", reply_markup=get_main_keyboard())
                    
            if user_id in chat_targets:
                del chat_targets[user_id]
            if user_id in user_states:
                del user_states[user_id]
        else:
            bot.send_message(message.chat.id, "Пожалуйста, отправь текстовое анонимное сообщение.")
    else:
        if message.content_type == 'text':
            bot.send_message(message.chat.id, "Воспользуйся кнопками меню ниже 👇", reply_markup=get_main_keyboard())

if __name__ == '__main__':
    print("Бот знакомств с админ-панелью запущен...")
    bot.infinity_polling()
