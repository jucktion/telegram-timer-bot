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
# import logging
# telebot.logger.setLevel(logging.DEBUG)

tick_icon = u"\u2714"
globe_icon = u"\U0001F310"
end_time = 0
done = 0

option_messages = []
remaining_messages = []

def delete_old_msg(chat_id, messages):
    if len(messages) > 0:
        bot.delete_message(chat_id, messages[0])
        messages.pop(0)

def remain(time):
    t = int(time)
    return str(f"{int(t/3600)}H {int((t/60)%60) if (int(t/3600)>0) else int(t/60)}m {int(t%60)}s")

def get_end_time():
    return time.mktime((datetime.now() + timedelta(seconds=int(TIMER))).timetuple())

def valid_url(url):
    result = urlparse(url)
    if (all([result.scheme, result.netloc])):
        return True
    else:
        raise Exception("Not a valid url")


def show_options(text='Start'):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(text=f"Change Timer Duration: {remain(TIMER)} | ({TIMER} seconds)",
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


def set_timer(message):
    global TIMER
    try:
        if type(int(message.text)) == int:
            TIMER = int(message.text)
            bot.send_message(chat_id=message.chat.id,
                                    text=f'Timer set to: {remain(TIMER)}',
                                    reply_markup=show_options(),
                                    parse_mode='HTML')
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
    text = f"Let's start" if (done == 0) else f"It's time:"
    option = 'Start' if (done == 0) else 'Done'
    if done <= 1:
        #print('option id: ',option_messages, len(option_messages))
        try:
            delete_old_msg(message.chat.id, option_messages)
        except Exception as e:
            print("option message not deleted",e)
    option_message = bot.send_message(chat_id=message.chat.id,
                                      text= text,
                                      reply_markup=show_options(option),
                                      parse_mode='HTML')
    if done <= 1:
        option_messages.append(option_message.message_id)



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
    remaining = end_time-time.time()
    remaining_string = remain(end_time-time.time()) if (remaining > 0) else str(timedelta(seconds = time.time() - end_time)).split('.')[0]

    isitgone = 'remaining' if (remaining > 0) else 'not set' if (end_time == 0) else 'elapsed'
    #print('before remaining id: ',message.message_id, remaining_messages, len(remaining_messages))
    if remaining > 0 or message.message_id == remaining_messages[0]:
        remaining_message = bot.edit_message_text(chat_id=message.chat.id,
                    reply_markup=check_remaining(),
                    text=f"Time {isitgone}: {remaining_string}",
                    message_id=message.message_id,
                    parse_mode='HTML')
    else:
        remaining_message = bot.send_message(chat_id=message.chat.id,
                    reply_markup=check_remaining(),
                    text=f"Time {isitgone}: {remaining_string}",
                    parse_mode='HTML')
    if remaining_message.message_id not in remaining_messages:
        if len(remaining_messages) > 0:
                remaining_messages[0] = remaining_message.message_id
        else:
            remaining_messages.append(remaining_message.message_id)
        #print('after remaining id: ',remaining_messages, len(remaining_messages))


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    global end_time
    global done
    if (call.data.startswith("['done'")):
        remaining_message = bot.edit_message_text(chat_id=call.message.chat.id,
                              text=f"Time remaining: {remain(int(TIMER))}",
                              reply_markup=check_remaining(),
                              message_id=call.message.message_id)
        if remaining_message.message_id not in remaining_messages:
            if len(remaining_messages) > 0:
                remaining_messages[0] = remaining_message.message_id
            else:
                remaining_messages.append(remaining_message.message_id)
        end_time = get_end_time()
        time.sleep(int(TIMER))
        done = done + 1
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # try:
        #     delete_old_msg(call.message.chat.id, remaining_message_id)
        # except Exception as e:
        #     print("remainder message deleted",e)
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
            print(f"LINK: {URL}")
            bot.polling(none_stop=True, interval=0, timeout=0)
        except:
            time.sleep(10)
    else:
        print('SET THE TELEGRAM API FIRST')