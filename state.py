from telebot import types
from config import bot, CHANNELS, ADMIN_CHAT
from lang import lang
from db import db, journal
import string
import random
import re


def to_state(message, state):
    user = db.find_one({"chat_id": message.chat.id})
    user["state"] = state
    db.save(user)
    state_handler(message, first=True)


def state_handler(message, first=False, inline=False):
    data = None
    if inline:
        data = message.data
        message = message.message
    if not db.find_one({"chat_id": message.chat.id}):
        db.insert_one({"chat_id": message.chat.id,
                       "state": "start"})
    user = db.find_one({"chat_id": message.chat.id})
    temp = user["state"].split(":")
    globals()[temp[0]](message, first, *temp[1:])


def start(message, first):
    bot.send_message(message.chat.id, lang["start_msg"], parse_mode="markdown")
    to_state(message, "menu")


def menu(message, first):
    if first:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.add(*[types.KeyboardButton(i) for i in lang["menu_btns"]])
        bot.send_message(message.chat.id, lang["menu_msg"], reply_markup=keyboard, parse_mode="markdown")
    elif message.text == lang["menu_btns"][0]:
        to_state(message, "choose_type")
    elif message.text == lang["menu_btns"][1]:
        msg = lang["list_msg"]
        emojs = { None: "🕔",
                 "success": "✅",
                 "decline": "❌",
                 "inwork": "🕔"}
        for i in journal.find({"from_user": message.chat.id}):
            msg += lang["problem_template"].format(i["id"], emojs[i["status"]], i["problem"])
        if msg == lang["list_msg"]:
            msg = lang["list_empty"]
        bot.send_message(message.chat.id, msg, parse_mode="markdown")
    else:
        bot.send_message(message.chat.id, lang["error_msg"])
        to_state(message, "menu")


def choose_type(message, first):
    user = db.find_one({"chat_id": message.chat.id})
    if first:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.add(*[types.KeyboardButton(i) for i in lang["type_btns"]])
        keyboard.row(types.KeyboardButton(lang["cancel_btn"]))
        bot.send_message(message.chat.id, lang["type_msg"], reply_markup=keyboard, parse_mode="markdown")
    elif message.text == lang["cancel_btn"]:
        to_state(message, "menu")
    elif message.text in lang["type_btns"]:
        user["type"] = message.text
        db.save(user)
        to_state(message, "choose_place")
    else:
        bot.send_message(message.chat.id, lang["error_msg"])
        to_state(message, "choose_type")


def choose_place(message, first):
    user = db.find_one({"chat_id": message.chat.id})
    if first:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.row(types.KeyboardButton(lang["cancel_btn"]))
        bot.send_message(message.chat.id, lang["place_msg"], reply_markup=keyboard, parse_mode="markdown")
    elif message.text == lang["cancel_btn"]:
        to_state(message, "menu")
    else:
        user["hostel_num"] = re.findall('\d+|$', message.text)[0]
        user["place"] = message.text
        db.save(user)
        to_state(message, "choose_problem")


def choose_problem(message, first):
    user = db.find_one({"chat_id": message.chat.id})
    if first:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.row(types.KeyboardButton(lang["cancel_btn"]))
        bot.send_message(message.chat.id, lang["problem_msg"], reply_markup=keyboard, parse_mode="markdown")
    elif message.text == lang["cancel_btn"]:
        to_state(message, "menu")
    else:
        user["problem"] = message.text
        db.save(user)
        to_state(message, "enter_phone")


def enter_phone(message, first):
    user = db.find_one({"chat_id": message.chat.id})
    if first:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.row(types.KeyboardButton(lang["phone_btn"], request_contact=True))
        keyboard.row(types.KeyboardButton(lang["skip_btn"]))
        keyboard.row(types.KeyboardButton(lang["cancel_btn"]))
        bot.send_message(message.chat.id, lang["phone_msg"], reply_markup=keyboard, parse_mode="markdown")
    elif message.text == lang["cancel_btn"]:
        to_state(message, "menu")
    elif message.text == lang["skip_btn"]:
        user["phone"] = None
        db.save(user)
        to_state(message, "choose_photo")
    elif message.entities:
        if message.entities[0].type == "phone_number":
            phone = message.text[message.entities[0].offset: message.entities[0].offset+message.entities[0].length]
            user["phone"] = phone
            db.save(user)
            to_state(message, "choose_photo")
    elif message.content_type == "contact":
        user["phone"] = message.contact.phone_number
        db.save(user)
        to_state(message, "choose_photo")
    else:
        bot.send_message(message.chat.id, lang["phone_err"])


def choose_photo(message, first):
    if first:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.row(types.KeyboardButton(lang["skip_btn"]))
        keyboard.row(types.KeyboardButton(lang["cancel_btn"]))
        bot.send_message(message.chat.id, lang["photo_msg"], reply_markup=keyboard, parse_mode="markdown")
    elif message.text == lang["cancel_btn"]:
        to_state(message, "menu")
    elif message.text == lang["skip_btn"]:
        to_state(message, "create_request")
    elif message.photo:
        to_state(message, "create_request")
    else:
        bot.send_message(message.chat.id, lang["error_msg"])


def create_request(message, first):
    user = db.find_one({"chat_id": message.chat.id})
    gen_id = ''.join(random.choice(string.digits) for _ in range(8))
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[types.InlineKeyboardButton(text=list(i.keys())[0],
                                              callback_data=list(i.values())[0].format(gen_id)) for i in lang["moderate_btns"]])
    try:
        channel_id = CHANNELS[user["hostel_num"]]
    except:
        channel_id = CHANNELS[""]
    msg_text = lang["request_msg"].format(gen_id,
                                          user["type"],
                                          user["place"],
                                          user["problem"],
                                          user["phone"],
                                          message.from_user.first_name,
                                          message.chat.id)
    if message.photo and len(user["problem"]+user["place"]) < 3000:
        message_id = bot.send_photo(channel_id,
                                    caption=msg_text,
                                    photo=message.photo[-1].file_id,
                                    reply_markup=keyboard,
                                    parse_mode="markdown")
    else:
        message_id = bot.send_message(channel_id,
                                      msg_text,
                                      reply_markup=keyboard,
                                      parse_mode="markdown")
    journal.insert_one({
        "id": gen_id,
        "from_user": message.chat.id,
        "first_name": message.from_user.first_name,
        "type": user["type"],
        "message_id": message_id.message_id,
        "place": user["place"],
        "problem": user["problem"],
        "phone": user["phone"],
        "channel_id": channel_id,
        "status": None,
        "rate": None,
    })
    bot.send_message(message.chat.id, lang["success_msg"].format(gen_id), parse_mode="markdown")
    to_state(message, "menu")


def comment(message, first, problem_id=None):
    if first:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.row(types.KeyboardButton(lang["cancel_btn"]))
        bot.send_message(message.chat.id, lang["comment_msg"].format(problem_id),
                         reply_markup=keyboard,
                         parse_mode="markdown")
    elif message.text == lang["cancel_btn"]:
        to_state(message, "menu")
    else:
        bot.send_message(ADMIN_CHAT, lang["admin_comment"].format(message.from_user.first_name,
                                                                  message.chat.id,
                                                                  problem_id,
                                                                  message.text),
                         parse_mode="markdown")
        bot.send_message(message.chat.id, lang["comment_end"], parse_mode="markdown")
        to_state(message, "menu")