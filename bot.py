import os
import telebot
from telebot import types
from PIL import Image
from dotenv import load_dotenv
from docx2pdf import convert

load_dotenv()

TOKEN = os.getenv('TOKEN')
admin = os.getenv('ADMIN')
bot = telebot.TeleBot(TOKEN)
pdf_images = dict()



@bot.message_handler(commands=['start', 'help'])
def start(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    bot.send_chat_action(chat_id, 'typing')
    bot.send_message(chat_id, f"*🤖 Assalomu alaykum* [{user_name}](tg://user?id={chat_id})!\n\n"
                              f"⚠️ Botdan foydalanish uchun unga PDF qilishni istayotgan rasmlaringizni tartib bilan "
                              f"yuboring\n\n"
                              f"Aloqa uchun {admin}",
                     parse_mode='Markdown')


@bot.message_handler(content_types=['photo'])
def get_photo(message):
    chat_id = message.chat.id
    if chat_id not in pdf_images.keys():
        pdf_images[chat_id] = []
    file = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file.file_path)
    f = open('image.jpg', 'wb')
    f.write(downloaded_file)
    image = Image.open('image.jpg').convert('RGB')
    pdf_images[chat_id].append(image)

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton('PDF ga aylantirish', callback_data='convert_to_pdf'),
        types.InlineKeyboardButton("Qo'shilgan rasmlarni o'chirish", callback_data='delete_images'),
    )
    bot.send_chat_action(chat_id, 'typing')
    bot.reply_to(message,
                 f"*✅ Rasm muvaffaqiyatli saqlandi*\nJami qo'shilgan rasmlar soni *{len(pdf_images[chat_id])}* ta",
                 reply_markup=markup,
                 parse_mode='Markdown')


@bot.message_handler(content_types=['document'])
def word_to_pdf(message):
    try:
        chat_id = message.chat.id
        file_name, file_type = os.path.splitext(message.document.file_name)
        if file_type == '.docx':
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, '*Iltimos biroz kuting ...*', parse_mode='Markdown')
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            f = open(f'{file_name}.docx', 'wb')
            f.write(downloaded_file)
            f.close()
            convert(f'{file_name}.docx')
            PDF = open(f'{file_name}.pdf', 'rb')
            bot.send_document(chat_id, PDF)
            PDF.close()
            os.remove(f'{file_name}.pdf')
            os.remove(f'{file_name}.docx')
        elif file_type in ['.jpg','.jpeg','.png']:
            bot.send_chat_action(chat_id, 'typing')
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            f = open('image.jpg', 'wb')
            f.write(downloaded_file)
            image = Image.open('image.jpg').convert('RGB')
            pdf_images[chat_id].append(image)

            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton('PDF ga aylantirish', callback_data='convert_to_pdf'),
                types.InlineKeyboardButton("Qo'shilgan rasmlarni o'chirish", callback_data='delete_images'),
            )
            bot.send_chat_action(chat_id, 'typing')
            bot.reply_to(message,
                         f"*✅ Rasm muvaffaqiyatli saqlandi*\nJami qo'shilgan rasmlar soni *{len(pdf_images[chat_id])}* ta",
                         reply_markup=markup,
                         parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "*🤖 Bu turdagi hujjat qo'llab quvvatlanmaydi*", parse_mode='Markdown')
    except Exception:
        bot.send_message(chat_id, "*🚫 Serverda xatolik kuzatildi*", parse_mode='Markdown')


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    chat_id = call.message.chat.id
    if data == 'convert_to_pdf':
        if chat_id not in pdf_images.keys() or len(pdf_images[chat_id]) == 0:
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, "*⁉️ Siz hali birorta rasm yuklamagansiz*", parse_mode='Markdown')
        else:
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, "*📚 PDF fayl tayyor*. \nFayl nomini kiriting", parse_mode='Markdown')
            bot.register_next_step_handler(call.message, to_pdf)
    elif data == 'delete_images':
        if chat_id in pdf_images.keys():
            del pdf_images[chat_id]
        bot.send_message(chat_id, "*❌ Qo'shilgan rasmlar o'chirib tashlandi.*\n"
                                  "Rasmlarni qaytadan qo'shishingiz mumkin",
                         parse_mode='Markdown')
    else:
        pass


def to_pdf(message):
    chat_id = message.chat.id
    text = message.text
    images = pdf_images[chat_id]
    first_image = images[0]
    first_image.save(f'{text}.pdf', save_all=True, append_images=images[1:])

    pdf = open(f'{text}.pdf', 'rb')
    bot.send_document(chat_id, pdf)
    pdf.close()

    os.remove(f'{text}.pdf')
    del pdf_images[chat_id]


@bot.message_handler(func=lambda message: True)
def other(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')
    bot.send_message(chat_id, "*🤖 Bot haqida bilish uchun /help ni bosing*", parse_mode='Markdown')


bot.polling(none_stop=True)
