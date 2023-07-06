import os
import threading
import time
import telebot
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import pymongo

load_dotenv()

# ENVIRONMENT VARIABLES
DB_USERNAME = os.environ['DATABASE']
DB_PASSWORD = os.environ['DB_PASSWORD']
APIKEY = os.environ['API_KEY']
bot = telebot.TeleBot(APIKEY)

course_map = {}
previous_map = {}
user_ids = []
data=""

# DATABASE CONNECTION 
client = pymongo.MongoClient(f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@cluster0.1e3sslc.mongodb.net/?retryWrites=true&w=majority")
db = client.subjectRegistration
give_take_collection=db.giveTake
users_collection = db.users
subject_seats_collection = db.subjectSeats

most_recent_document = subject_seats_collection.find_one({}, sort=[('$natural', -1)])
course_map = dict(most_recent_document) if most_recent_document else {}

second_last_document = subject_seats_collection.find_one({}, sort=[('$natural', -1)], skip=1)
previous_map = dict(second_last_document) if second_last_document else {}


user_ids_dict = list(users_collection.find({}, {"_id": 0, "user_id": 1}))
user_ids = list(map(lambda item: item["user_id"], user_ids_dict))


@bot.message_handler(commands=['register'])
def register(message):
    user_id = message.chat.id
    bot.reply_to(message, '<b>Please provide your give subject code.</b>', parse_mode="HTML")
    bot.register_next_step_handler(message, lambda msg: process_give(msg, user_id))

def process_give(message, user_id):
    give_value = message.text.upper()
    bot.reply_to(message, '<b>Please provide your take subject code.</b>', parse_mode="HTML")
    bot.register_next_step_handler(message, lambda msg: process_take(msg, user_id, give_value))

def process_take(message, user_id, give_value):
    take_value = message.text.upper()
    bot.reply_to(message, '<b>Please provide your contact info.</b>', parse_mode="HTML")
    bot.register_next_step_handler(message, lambda msg: process_contact_info(msg, user_id, give_value, take_value))

def process_contact_info(message, user_id, give_value, take_value):
    contact_info = message.text
    user = {
        "user_id": user_id,
        "give_value": give_value,
        "take_value": take_value,
        "contact_info": contact_info
    }
    give_take_collection.insert_one(user)
    bot.send_message(user_id, "<b>You have been registered successfully!</b>",parse_mode="HTML")
    
@bot.message_handler(commands=['unregister'])
def unregister(message):
    user_id = message.chat.id
    bot.reply_to(message, '<b>Please provide your give subject code to unregister.</b>', parse_mode="HTML")
    bot.register_next_step_handler(message, lambda msg: process_unregister(msg, user_id))

def process_unregister(message, user_id):
    give_value = message.text.upper()
    bot.reply_to(message, '<b>Please provide your take subject code to unregister.</b>', parse_mode="HTML")
    bot.register_next_step_handler(message, lambda msg: confirm_unregister(msg, user_id, give_value))

def confirm_unregister(message, user_id, give_value):
    take_value = message.text.upper()
    result = give_take_collection.delete_many({"user_id": user_id, "give_value": give_value, "take_value": take_value})
    if result.deleted_count > 0:
        bot.send_message(user_id, "<b>You have been unregistered successfully.</b>",parse_mode="HTML")
    else:
        bot.send_message(user_id, "<b>You are not registered.</b>",parse_mode="HTML")

@bot.message_handler(commands=['exchange'])
def find_matches(message):
    user_id = message.chat.id
    bot.reply_to(message, 'Please enter your give subject code:')
    bot.register_next_step_handler(message, lambda msg: process_give_code(msg, user_id))

def process_give_code(message, user_id):
    give_value = message.text.upper()
    bot.reply_to(message, 'Please enter your take subject code:')
    bot.register_next_step_handler(message, lambda msg: process_take_code(msg, user_id, give_value))

def process_take_code(message, user_id, give_value):
    take_value = message.text.upper()
    matches = give_take_collection.count_documents({"give_value": take_value, "take_value": give_value})

    if matches > 0:
        match_info = "Matching users found:\n"
        for user in give_take_collection.find({"give_value": take_value, "take_value": give_value}):
            match_info += f"<b>Contact Info:</b> {user['contact_info']}\n"
        bot.send_message(user_id, match_info,parse_mode="HTML")
    else:
        bot.send_message(user_id, "<b>Sorry, No matching users found.</b>",parse_mode="HTML")


@bot.message_handler(commands=['search'])
def handle_search(message):
    input_text = message.text.replace('/search', '').strip().upper()
    global course_map, previous_map, data
    if input_text:
        groups = course_map.get(input_text)
        if groups is not None:
            subject_code = input_text
            response = f"<b>Subject Code:</b> {subject_code}\n"
            response += f"<b>Available Seats:</b> {groups}\n"
            bot.send_message(message.chat.id, response, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "Subject code not found.")
    else:
        bot.send_message(message.chat.id, "Please provide a subject code after the <b>/search</b> command.",parse_mode="HTML")
            
@bot.message_handler(commands=['update'])
def update(message):
    global user_ids
    user_id = message.chat.id
    user_doc = users_collection.find_one({"user_id": user_id})
    if user_doc is not None:
        bot.reply_to(message, '<b>You have already been granted permission, Press /seats for more information.</b>',parse_mode="HTML")
    else:
        users_collection.insert_one({"user_id": user_id})
        bot.reply_to(message, '<b>You have been granted permission.</b>',parse_mode="HTML")

@bot.message_handler(commands=['seats'])
def seats(message):
    global data
    user_id = message.chat.id
    course_map_string = "<b>Subject Codes: Seats</b>\n"
    for subject_code, seats in course_map.items():
        if seats != "0" and seats!="Not available" and subject_code != "_id" and subject_code != "Group" and subject_code != "Set":
            course_map_string += f"<b>{subject_code}</b>: <b>{seats}</b>\n"
    if course_map_string == "<b>Subject Codes: Seats</b>\n":
        bot.send_message(user_id, "<b>No Seats are Available Right Now, Try Later</b>", parse_mode="HTML")
    else:
        data = course_map_string
        bot.send_message(user_id, course_map_string, parse_mode="HTML")

    
def notify(user_id, data):
  global user_ids, all_data, scraped_data
  user_ids_dict = list(users_collection.find({}, {"_id": 0, "user_id": 1}))
  user_ids = list(map(lambda item: item["user_id"], user_ids_dict))
  print(user_ids)
  for user_id in user_ids:
        bot.send_message(user_id, data, parse_mode="HTML")

@bot.message_handler(commands=['revoke'])
def revoke_permission(message):
  global user_ids
  user_ids_dict = list(users_collection.find({}, {"_id": 0, "user_id": 1}))
  user_ids = list(map(lambda item: item["user_id"], user_ids_dict))
  user_id = message.chat.id
  if user_id in user_ids:
    bot.reply_to(message,
                 '<b>You have revoked permission to receive automated messages.</b>',parse_mode="HTML")
    users_collection.delete_many({"user_id":user_id})
  else:
    bot.reply_to(message, '<b>You have already revoked permission.</b>',parse_mode="HTML")


@bot.message_handler(commands=['start'])
def handle_start(message):
    # Prepare the list of commands
    commands = [
        "👋 <b>/start -</b> Start the bot.",
        "📚 <b>/seats -</b> Check seat availability.",
        "🔔 <b>/update -</b> Subscribe for seat notifications.",
        "🚫 <b>/revoke -</b> Revoke seat notifications.",
        "🔎 <b>/search -</b> Get seat count for a subject.",
        "✏️ <b>/register -</b> Register for subject exchange.",
        "🚫 <b>/unregister -</b> Unregister from subject exchange.",
        "💡 <b>/exchange -</b> Check subject exchange matches."
    ]

    commands_text = '\n'.join(commands)

    bot.send_message(message.chat.id, f'<b>Available commands:</b>\n{commands_text}',parse_mode="HTML")


def update(user_id, data):
  global user_ids, all_data, scraped_data
  user_ids_dict = list(db.user.find({}, {"_id": 0, "user_id": 1}))
  user_ids = list(map(lambda item: item["user_id"], user_ids_dict))
  if user_id in user_ids:
      bot.send_message(user_id, data, parse_mode="HTML")
          
def scrape_function():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    service = Service(executable_path=r'/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    loginurl = ('https://cumsdtu.in/registration_student/login/login.jsp?courseRegistration')

    # For deployment the path is /usr/bin/chromedriver
    # Login Credentials

    usernameId = str(os.environ['usernameId'])
    passwordId = str(os.environ['passwordId'])
    
    driver.get(loginurl)
   
    print(loginurl);
    RN = driver.find_element(
      By.ID, 'usernameId')
    RN.send_keys(usernameId)

    SK = driver.find_element(
      By.ID, 'passwordId')
    SK.send_keys(passwordId)

    submit_button = driver.find_element(
      By.ID, "submitButton"
    )  
    submit_button.send_keys(Keys.ENTER)
    time.sleep(5)

    page_source = driver.page_source

    soup = BeautifulSoup(page_source, 'html.parser')

    course_elements = soup.find_all('div', class_='course')

    global course_map, previous_map, data

    subject_seats_dict = {}

    for course_element in course_elements:
        
        subject_code = course_element.find('div', class_='isChild').text.strip().split(' ')[0]
        group = course_element.find('div', class_='overflow-hidden').text.strip()

        seats_element = course_element.find('span', class_='bolder h3')
        seats = seats_element.text.strip() if seats_element else "Not available"

        subject_seats_dict[subject_code] = seats

    subject_seats_dict_size = len(subject_seats_dict)

    if subject_seats_dict_size == 1:
        scrape_function()

    document =  subject_seats_dict
    
    subject_seats_collection.insert_one(document)
    
    course_map = {subject_code: seats for subject_code, seats in document.items()}
    
    most_recent_document = None if subject_seats_collection.count_documents({}) < 1 else subject_seats_collection.find_one({}, sort=[('$natural', -1)])

    course_map = {} if most_recent_document == None else dict(most_recent_document)
    
    notification_message = "<b>✨ Seats Availability Update</b>\n --------------------------------------------- \n"
    
    count = 0

    for subject_code, current_seats in course_map.items():
        if subject_code == "_id" or subject_code == "Set" or subject_code == "Group":
            continue
        previous_seats = previous_map.get(subject_code)
        if previous_seats is None or (previous_seats is not None and current_seats != previous_seats):
                count += 1
                x = f"<b>{subject_code}</b> -> <b>{current_seats}</b>."
                notification_message += x + "\n"

    if count != 0:
        notify(user_ids, notification_message)
                
    previous_map = course_map
    
    course_map_string = "<b>Subject Codes: Seats</b>\n"
    for subject_code, seats in course_map.items():
        if seats != "0" and seats!="Not available" and subject_code != "_id" and subject_code != "Group" and subject_code != "Set":
            course_map_string += f"<b>{subject_code}</b>: {seats}\n"
    data = course_map_string;
    
    driver.quit()


def task_function():
  global user_ids;
  while True:
      try:
        scrape_function()
        time.sleep(20)
      except Exception as e:
        print(e)
        time.sleep(5)
        continue

task_thread = threading.Thread(target=task_function)
task_thread.daemon = True 

task_thread.start()

while True:
    try:
        bot.polling(non_stop=True, interval=0)
    except Exception as e:
        print(e)
        time.sleep(5)
        continue
