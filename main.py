import os
import time
import telebot
from telebot import types
from urllib.parse import urlparse
from datetime import datetime,timedelta

# Initial idea from
# https://stackoverflow.com/posts/51904640/revisions
#
try:
   URL = os.environ['URL']
   TIMER = os.environ['TIMER']
except:
    from env import URL,TIMER

try:
   TG_API = os.environ['TG_API']
except:
   from env import TG_API
   

bot = telebot.TeleBot(TG_API)

tick_icon = u"\u2714"
globe_icon = u"\U0001F310"
end_time = 0
done = 0

option_message_id = []
remaining_message_id = []

def remain(t):
  return str(f"{int(t/3600)}H {int((t/60)%60) if t/3600>0 else int(t/60)}m {int(t%60)}s")

def get_end_time():
    return time.mktime((datetime.now() + timedelta(seconds=int(TIMER))).timetuple())

def valid_url(url):
    result = urlparse(url)
    if (all([result.scheme, result.netloc])):
        return True
    else:
        raise Exception("Not a valid url")


def show_options():
    text = 'Start' if (done == 0) else 'Done'
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(text=f"Change Duration ({TIMER})",
                                    callback_data="['change']"))
    markup.add(
        types.InlineKeyboardButton(text=f"{tick_icon} {text}",
                                   callback_data="['done']"),
        types.InlineKeyboardButton(text=f"{globe_icon} Open",
                                   url=URL))
    return markup

def check_remaining():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(text=f"Check remaining",
                                    callback_data="['check']"))
    return markup

def delete_old_msg(chat_id, message_ids):
    if len(message_ids) > 0:
        bot.delete_message(chat_id, message_ids[0])
        message_ids.pop(0)


def set_timer(message):
    global TIMER
    try:
        if type(int(message.text)) == int:
            TIMER = int(message.text)
            bot.send_message(chat_id=message.chat.id,
                     text=f'Timer set to:{TIMER} seconds', parse_mode='HTML')
    except:
        handle_command_set_time(message)
    

def set_url(message):
    global URL
    try:
        if valid_url(message.text):
            URL = message.text
            bot.send_message(chat_id=message.chat.id,
                     text=f'Link set to:{URL}', parse_mode='HTML')
    except:
        handle_command_set_url(message)
    


@bot.message_handler(commands=['start','go'])
@bot.message_handler(func=lambda message: True, content_types=["text"], is_chat_admin=True)
def handle_command_start(message):
    delete_old_msg(message.chat.id, option_message_id)
    option_message = bot.send_message(chat_id=message.chat.id,
                                      text=f"It's time:",
                                      reply_markup=show_options(),
                                      parse_mode='HTML')
    option_message_id.append(option_message.message_id)


@bot.message_handler(commands=['set'])
@bot.message_handler(func=lambda message: True, content_types=["text"], is_chat_admin=True)
def handle_command_set_time(message):
    bot.send_message(chat_id=message.chat.id,
                     text='Set the time interval (in seconds):', parse_mode='HTML')
    bot.register_next_step_handler(message, set_timer)


@bot.message_handler(commands=['link'])
@bot.message_handler(func=lambda message: True, content_types=["text"], is_chat_admin=True)
def handle_command_set_url(message):
    bot.send_message(chat_id=message.chat.id,
                     text='Set a new valid link:', parse_mode='HTML')
    bot.register_next_step_handler(message, set_url)
    


@bot.message_handler(commands=['check'])
@bot.message_handler(func=lambda message: True, content_types=["text"], is_chat_admin=True)
def handle_command_check(message):
    delete_old_msg(message.chat.id, remaining_message_id)
    remaining = end_time-time.time()
    remaining_string = remain(end_time-time.time()) if (end_time > 0) else 0

    isitgone = 'remaining' if (remaining > 0) else 'not set' if (end_time == 0) else 'elapsed'

    remaining_message = bot.send_message(chat_id=message.chat.id,
                    reply_markup=check_remaining(),
                    text=f"Time {isitgone}: {remaining_string}",
                    parse_mode='HTML')

    remaining_message_id.append(remaining_message.message_id)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    global end_time
    global done
    if (call.data.startswith("['done'")):
        done = done + 1
        bot.edit_message_text(chat_id=call.message.chat.id,
                              text=f"Waiting for: {remain(int(TIMER))}",
                              reply_markup=check_remaining(),
                              message_id=call.message.message_id)
        end_time = get_end_time()
        time.sleep(int(TIMER))
        handle_command_start(call.message)

    if (call.data.startswith("['change'")):
        handle_command_set_time(call.message)
    
    if (call.data.startswith("['check'")):
        handle_command_check(call.message)


if __name__ == "__main__":
    if(TG_API):
        try:
            print("Running Timer...")
            print(f"API: {TG_API}")
            print(f"DURATION: {TIMER}")
            bot.polling(none_stop=True, interval=0, timeout=0)
        except:
            time.sleep(10)
    else:
        print('SET THE TELEGRAM API FIRST')

