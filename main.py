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
from telegram.error import TelegramError

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
whatsapp_collection=db.whatsappLinks
users_collection = db.users
subject_seats_collection = db.subjectSeats

most_recent_document = subject_seats_collection.find_one(filter={"$and": [{"$nor": [{"_id": None}]}, {"_id": {"$ne": None}}]}, sort=[("_id", -1)])
course_map = dict(most_recent_document) if most_recent_document else {}

second_last_document = subject_seats_collection.find_one(filter={"$and": [{"$nor": [{"_id": None}]}, {"_id": {"$ne": None}}]}, sort=[("_id", -1)], skip=1)
previous_map = dict(second_last_document) if second_last_document else {}


user_ids_dict = list(users_collection.find({}, {"_id": 0, "user_id": 1}))
user_ids = list(map(lambda item: item["user_id"], user_ids_dict))


@bot.message_handler(commands=['addwa'])
def addwa(message):
    user_id = message.chat.id
    bot.reply_to(message, '<b>Please provide your subject code.</b>', parse_mode="HTML")
    bot.register_next_step_handler(message, lambda msg: addlink(msg, user_id))

def addlink(message, user_id):
    give_value = message.text.upper()
    bot.reply_to(message, '<b>Please provide the corresponding Whatsapp Group Link.</b>', parse_mode="HTML")
    bot.register_next_step_handler(message, lambda msg: processlink(msg, user_id, give_value))

def processlink(message, user_id, give_value):
    link_info = message.text
    user = {
        "give_value": give_value,
        "whatsapplink": link_info
    }
    whatsapp_collection.insert_one(user)
    bot.send_message(user_id, "<b>Whatsapp Group Added!</b>",parse_mode="HTML")

@bot.message_handler(commands=['getwa'])
def getwa(message):
    user_id = message.chat.id
    bot.reply_to(message, '<b>Please provide the subject code.</b>', parse_mode="HTML")
    bot.register_next_step_handler(message, lambda msg: process_getwa(msg, user_id))

def process_getwa(message, user_id):
    subject_code = message.text.upper()
    links = []
    cursor = whatsapp_collection.find({"give_value": subject_code})
    for document in cursor:
        link_info = document.get("whatsapplink")
        links.append(link_info)
    
    if links:
        response = f"<b>WhatsApp links for subject {subject_code}:</b>\n"
        for link in links:
            response += f"- {link}\n"
        bot.send_message(user_id, response, parse_mode="HTML")
    else:
        bot.send_message(user_id, f"No WhatsApp links found for subject {subject_code}.", parse_mode="HTML")

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
    bot.reply_to(message, '<b>Please provide your contact info either your mail or telegram username or number</b>', parse_mode="HTML")
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
    try:
        bot.send_message(user_id, data, parse_mode="HTML")
    except TelegramError as e:
        users_collection.delete_many({"user_id":user_id})
            
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
        "💡 <b>/exchange -</b> Check subject exchange matches.",
        "🔗 <b>/addwa -</b> Add WhatsApp link to a subject.",
        "🔗 <b>/getwa -</b> Get WhatsApp links of a subject.",
        "<b>PS: Write Subject Code like this CO203</b>"
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
    service = Service(executable_path=r'/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    loginurl = ('https://cumsdtu.in/registration_student/login/login.jsp?courseRegistration')

    # For deployment the path is /usr/bin/chromedriver
    # Login Credentials

    usernameId = str(os.environ['usernameId'])
    passwordId = str(os.environ['passwordId'])
    
    max_retries = 3

    for retry in range(max_retries):
        try:
            # Navigate to the URL
            driver.get(loginurl)

            # Check for error message
            error_message = "Invalid User name or password. Please check."
            if error_message in driver.page_source:
                raise WebDriverException(error_message)

            # If no error, break out of the loop
            break
        except WebDriverException as e:
            # Handle the error
            print(f"Error: {e}")
            print("Retrying...")

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
    
    wait = WebDriverWait(driver, 120)  # Maximum wait time in seconds
    element_locator = (By.CSS_SELECTOR, "div.course.isDisabled")
    element = wait.until(EC.visibility_of_element_located(element_locator))

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

    flag =True;
    if not subject_seats_dict:  
        print("Empty document")
        flag=False;
    else:
        subject_seats_collection.insert_one(subject_seats_dict)

    document =  subject_seats_dict
    
    if flag == True:
        course_map = {subject_code: seats for subject_code, seats in document.items()}

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
        time.sleep(5)
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
