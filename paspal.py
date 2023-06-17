import logging
import string
import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Global dictionary to store passwords
passwords = {}

# Global dictionary to store locked state
locked = {}

# Handler for the /start command
def start(update: Update, context):
    chat_id = update.effective_chat.id
    if chat_id not in passwords:
        context.bot.send_message(chat_id=chat_id, text="Welcome to the Password Manager Bot!")
        context.bot.send_message(chat_id=chat_id, text="Please create a password using /createpass command.")
    else:
        context.bot.send_message(chat_id=chat_id, text="Welcome back to the Password Manager Bot!")

# Handler for the /createpass command
def create_password(update: Update, context):
    chat_id = update.effective_chat.id
    if chat_id in passwords:
        context.bot.send_message(chat_id=chat_id, text="You have already set a password. Use /changepass command to change it.")
    else:
        context.bot.send_message(chat_id=chat_id, text="Enter your new password.")
        context.user_data['state'] = 'CREATE_PASSWORD'

# Handler for the /changepass command
def change_password(update: Update, context):
    chat_id = update.effective_chat.id
    if chat_id not in passwords:
        context.bot.send_message(chat_id=chat_id, text="You haven't set a password yet. Use /createpass command to create one.")
    else:
        context.bot.send_message(chat_id=chat_id, text="Enter your new password.")
        context.user_data['state'] = 'CHANGE_PASSWORD'

# Handler for the /lock command
def lock(update: Update, context):
    chat_id = update.effective_chat.id
    if chat_id not in passwords:
        context.bot.send_message(chat_id=chat_id, text="You haven't set a password yet. Use /createpass command to create one.")
    else:
        context.bot.send_message(chat_id=chat_id, text="Enter your password to lock the commands.")
        context.user_data['state'] = 'LOCK'

# Handler for the /unlock command
def unlock(update: Update, context):
    chat_id = update.effective_chat.id
    if chat_id in passwords:
        if locked.get(chat_id):
            context.bot.send_message(chat_id=chat_id, text="Enter your password to unlock the commands.")
            context.user_data['state'] = 'UNLOCK'
        else:
            context.bot.send_message(chat_id=chat_id, text="Commands are already unlocked.")
    else:
        context.bot.send_message(chat_id=chat_id, text="You haven't set a password yet. Use /createpass command to create one.")

# Handler for the /add command
def add_password(update: Update, context):
    chat_id = update.effective_chat.id
    if locked.get(chat_id):
        context.bot.send_message(chat_id=chat_id, text="Commands are locked. Use /unlock command to unlock.")
    else:
        context.bot.send_message(chat_id=chat_id, text="Enter the key for the password.")

        # Set the conversation state to wait for the key
        context.user_data['state'] = 'ADD_KEY'

# Handler for the /show command
def show_passwords(update: Update, context):
    chat_id = update.effective_chat.id
    if locked.get(chat_id):
        context.bot.send_message(chat_id=chat_id, text="Commands are locked. Use /unlock command to unlock.")
    else:
        if chat_id in passwords:
            password_list = "\n".join([f"{key}: {value}" for key, value in passwords[chat_id].items()])
            context.bot.send_message(chat_id=chat_id, text=f"Your saved passwords:\n{password_list}")
        else:
            context.bot.send_message(chat_id=chat_id, text="You haven't saved any passwords yet.")

# Handler for the /delete command
def delete_password(update: Update, context):
    chat_id = update.effective_chat.id
    if locked.get(chat_id):
        context.bot.send_message(chat_id=chat_id, text="Commands are locked. Use /unlock command to unlock.")
    else:
        context.bot.send_message(chat_id=chat_id, text="Enter the key of the password to delete.")

        # Set the conversation state to wait for the key
        context.user_data['state'] = 'DELETE_KEY'

# Handler for the /random command
def generate_random_password(update: Update, context):
    chat_id = update.effective_chat.id
    if locked.get(chat_id):
        context.bot.send_message(chat_id=chat_id, text="Commands are locked. Use /unlock command to unlock.")
    else:
        generated_password = generate_password(length=10)
        context.bot.send_message(chat_id=chat_id, text=f"Generated password: {generated_password}")

# Generate a random password with numbers, special characters, and capital letters
def generate_password(length=10):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

# Handler for text messages
def save_password(update: Update, context):
    chat_id = update.effective_chat.id
    message_text = update.message.text

    if chat_id not in passwords:
        passwords[chat_id] = {}

    if context.user_data.get('state') == 'ADD_KEY':
        # Set the key for the password
        context.user_data['key'] = message_text
        context.bot.send_message(chat_id=chat_id, text="Enter the password.")

        # Set the conversation state to wait for the password
        context.user_data['state'] = 'ADD_PASSWORD'
    elif context.user_data.get('state') == 'ADD_PASSWORD':
        # Retrieve the key and password from the user data
        key = context.user_data.get('key')
        password = message_text

        passwords[chat_id][key] = password
        context.bot.send_message(chat_id=chat_id, text=f"Password '{key}' has been saved.")

        # Reset the conversation state
        context.user_data.clear()
    elif context.user_data.get('state') == 'DELETE_KEY':
        key = message_text
        if key in passwords.get(chat_id, {}):
            del passwords[chat_id][key]
            context.bot.send_message(chat_id=chat_id, text=f"Password '{key}' has been deleted.")
        else:
            context.bot.send_message(chat_id=chat_id, text=f"Password '{key}' does not exist.")
        # Reset the conversation state
        context.user_data.clear()
    elif context.user_data.get('state') == 'CREATE_PASSWORD':
        # Set the password for the user
        passwords[chat_id] = message_text
        context.bot.send_message(chat_id=chat_id, text="Password has been created.")

        # Reset the conversation state
        context.user_data.clear()
    elif context.user_data.get('state') == 'CHANGE_PASSWORD':
        # Set the new password for the user
        passwords[chat_id] = message_text
        context.bot.send_message(chat_id=chat_id, text="Password has been changed.")

        # Reset the conversation state
        context.user_data.clear()
    elif context.user_data.get('state') == 'LOCK':
        # Check if the entered password matches the saved password
        if passwords[chat_id] == message_text:
            locked[chat_id] = True
            context.bot.send_message(chat_id=chat_id, text="Commands are locked.")
        else:
            context.bot.send_message(chat_id=chat_id, text="Invalid password.")

        # Reset the conversation state
        context.user_data.clear()
    elif context.user_data.get('state') == 'UNLOCK':
        # Check if the entered password matches the saved password
        if passwords[chat_id] == message_text:
            locked[chat_id] = False
            context.bot.send_message(chat_id=chat_id, text="Commands are unlocked.")
        else:
            context.bot.send_message(chat_id=chat_id, text="Invalid password.")

        # Reset the conversation state
        context.user_data.clear()
    else:
        context.bot.send_message(chat_id=chat_id, text="Invalid command.")

# Handler for unknown commands
def unknown(update: Update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

def main():
    # Token for your bot obtained from BotFather
    token = '5979829091:AAErSi8p5neaC83GmsI13BkLz9UWggNkt3s'

    # Create the Updater and pass it your bot's token
    updater = Updater(token=token, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("createpass", create_password))
    dispatcher.add_handler(CommandHandler("changepass", change_password))
    dispatcher.add_handler(CommandHandler("lock", lock))
    dispatcher.add_handler(CommandHandler("unlock", unlock))
    dispatcher.add_handler(CommandHandler("add", add_password))
    dispatcher.add_handler(CommandHandler("show", show_passwords))
    dispatcher.add_handler(CommandHandler("delete", delete_password))
    dispatcher.add_handler(CommandHandler("random", generate_random_password))

    # Register message handler
    dispatcher.add_handler(MessageHandler(Filters.text, save_password))

    # Register unknown command handler
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
