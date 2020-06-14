from config import *
from state import state_handler, to_state
from lang import lang
from telebot import types
from db import db, journal
from flask import Flask
import time
import flask

app = Flask(__name__)


@bot.message_handler(commands=["start"])
def start_cmd(message):
    if message.chat.id < 0:
        return
    user = db.find_one({"chat_id": message.chat.id})
    if user:
        user["state"] = "start"
        db.save(user)
    state_handler(message, True)


@bot.message_handler(commands=["chat_id"])
def chat_id_cmd(message):
    bot.send_message(message.chat.id, text=str(message.chat.id))


@bot.message_handler(content_types=["text", "photo", "contact"])
def all_text(message):
    if message.chat.id < 0:
        return
    state_handler(message)


@bot.callback_query_handler(func=lambda call: True)
def callback(reply):
        cmd, problem_id = reply.data.split(":")[:2]
        problem = journal.find_one({"id": problem_id})
        # notify user
        if cmd in ["success", "decline"]:
            keyboard = types.InlineKeyboardMarkup(row_width=3)
            keyboard.add(*[types.InlineKeyboardButton(text=i,
                                                      callback_data=j.format(problem_id))
                                                      for i, j in lang["rate_btns"].items()])
            bot.send_message(problem["from_user"],
                             lang["callback_msg_user"][cmd].format(problem["id"],
                                                                   problem["place"],
                                                                   problem["problem"]),
                             reply_markup=keyboard,
                             parse_mode="markdown")
        if cmd in ["success", "decline", "inwork"]:
            problem["status"] = cmd
            journal.save(problem)
            msg = lang["request_msg"].format(problem["id"],
                                             problem["type"],
                                             problem["place"],
                                             problem["problem"],
                                             problem["phone"],
                                             problem["first_name"],
                                             problem["from_user"])
            msg += "{} [{}](tg://user?id={})".format(lang["callback_msg_admin"][cmd],
                                                     reply.from_user.first_name,
                                                     reply.from_user.id)
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            if cmd == "inwork":
                keyboard.add(*[types.InlineKeyboardButton(text=list(i.keys())[0], callback_data=i[list(i.keys())[0]].format(problem_id))
                               for i in lang["moderate_btns"] if i[list(i.keys())[0]] != "inwork:{}"])
            if reply.message.photo:
                bot.edit_message_caption(
                    caption=msg,
                    message_id=reply.message.message_id,
                    chat_id=reply.message.chat.id,
                    reply_markup=keyboard,
                    parse_mode="markdown")
            else:
                bot.edit_message_text(text=msg,
                                      message_id=reply.message.message_id,
                                      chat_id=reply.message.chat.id,
                                      reply_markup=keyboard,
                                      parse_mode="markdown")
        if cmd in ["rate"]:
            rating = reply.data.split(":")[2]
            problem["rate"] = rating
            journal.save(problem)
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(*[types.InlineKeyboardButton(text=i,
                                                      callback_data=j.format(problem_id))
                           for i, j in lang["comment_btn"].items()])
            msg = lang["callback_msg_user"][problem["status"]].format(problem["id"],
                                                                      problem["place"],
                                                                      problem["problem"])
            msg += lang["rate_msg"].format(rating)
            bot.edit_message_text(chat_id=problem["from_user"],
                                  text=msg,
                                  message_id=reply.message.message_id,
                                  reply_markup=keyboard,
                                  parse_mode="markdown")

            msg = lang["request_msg"].format(problem["id"],
                                             problem["type"],
                                             problem["place"],
                                             problem["problem"],
                                             problem["phone"],
                                             problem["first_name"],
                                             problem["from_user"])
            msg += "Оценка: {}".format(rating)
            try:
                bot.edit_message_text(chat_id=problem["channel_id"],
                                      message_id=problem["message_id"],
                                      text=msg,
                                      parse_mode="markdown")
            except:
                bot.edit_message_caption(chat_id=problem["channel_id"],
                                         message_id=problem["message_id"],
                                         caption=msg,
                                         parse_mode="markdown")
            bot.answer_callback_query(reply.id, lang["rate_msg"].format(rating))
        if cmd in ["comment"]:
            user = db.find_one({"chat_id": problem["from_user"]})
            if user:
                msg = lang["callback_msg_user"][problem["status"]].format(problem["id"],
                                                                          problem["place"],
                                                                          problem["problem"])
                msg += lang["rate_msg"].format(problem["rate"])
                bot.edit_message_text(chat_id=problem["from_user"],
                                      text=msg,
                                      message_id=reply.message.message_id,
                                      parse_mode="markdown")
                to_state(reply.message, reply.data)




# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)
        
bot.remove_webhook()
print(bot.get_me())

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
               certificate=open(WEBHOOK_SSL_CERT, 'r'))

# if __name__ == "__main__":
    # Start flask server
    # Remove webhook, it fails sometimes the set if there is a previous webhook
    # bot.remove_webhook()
    # print(bot.get_me())
    # #sleep(1)
    # #bot.polling()
    # # Set webhook

    # #while True:
    # #    try:
    # #        bot.polling()
    # #    except:
    # #        time.sleep(1)

    # bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
    #                certificate=open(WEBHOOK_SSL_CERT, 'r'))
    # app.run(host=WEBHOOK_LISTEN,
    #         port=WEBHOOK_PORT,
    #         ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
    #         threaded=True)