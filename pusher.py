import argparse
import os
import zipfile
import json
import logging
import sys
from telebot import TeleBot, apihelper

# config
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".pusher_config.json")
PUSHER_TMP_DIR = os.path.join(os.path.expanduser("~"), ".pusher_tmp")

BOT_TOKEN = None
CHAT_ID = None
bot = None

B = "\033[01m"
I = "\033[03m"
U = "\033[04m"
R = "\033[07m"
cl = "\033[m"
cy = "\033[38;05;51m"
red = "\033[38;05;196m"
gr = "\033[38;05;46m"
ye = "\033[38;05;226m"
orn = "\033[38;05;214m"

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', stream=sys.stderr)

def load_config():
    global BOT_TOKEN, CHAT_ID, bot
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                BOT_TOKEN = config.get("bot_token")
                telegram_id_str = config.get("telegram_id")
                if telegram_id_str is not None:
                    try:
                        CHAT_ID = int(telegram_id_str)
                    except ValueError:
                        logging.error(f"{B}{red}Warning: {cy}uncorrect Chat ID in config. Set it manually: \"{ye}pusher token <token>{cy}\"{cl}")
                        CHAT_ID = None
        except json.JSONDecodeError:
            logging.error(f"{B}{red}Warning: {cy}config file is not readable. Run \"{ye}pusher setup{cy}\"{cl}")
        except Exception as e:
            logging.error(f"{B}{red}Warning: {cy}error while loading config file ({orn}{e}{cy}){cl}")
    
    if BOT_TOKEN:
        bot = TeleBot(BOT_TOKEN)

def save_config():
    try:
        config_data = {"bot_token": BOT_TOKEN, "telegram_id": str(CHAT_ID) if CHAT_ID is not None else None}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
        logging.info(f"{B}{gr}Config saved to {ye}{CONFIG_FILE}{cl}")
    except Exception as e:
        logging.error(f"{B}{red}Error while saving config file: {orn}{e}{cl}")

def push_file_or_directory(path):

    if not os.path.exists(path):
        logging.error(f"{B}{red}Path \"{ye}{path}{red}\" not found.{cl}")
        sys.exit(1)

    temp_file_to_send = None
    original_file_name = os.path.basename(path)

    file_to_send = path
    if os.path.isdir(path):
        os.makedirs(PUSHER_TMP_DIR, exist_ok=True)
        
        temp_zip_name = f"{original_file_name}_{os.urandom(4).hex()}.zip"
        temp_zip_path = os.path.join(PUSHER_TMP_DIR, temp_zip_name)
        
        logging.info(f"{B}{cy}Zipping \"{ye}{path}{cy}\" -> \"{ye}{temp_zip_path}{cy}\" ...{cl}")
        
        try:
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arcname = os.path.relpath(full_path, os.path.dirname(path))
                        zipf.write(full_path, arcname)
            
            if os.path.getsize(temp_zip_path) == 0:
                logging.error(f"{B}{red}Error: {cy}archive \"{orn}{temp_zip_path}{cy}\" empty{cl}")
                os.remove(temp_zip_path)
                sys.exit(1)

            file_to_send = temp_zip_path
            temp_file_to_send = temp_zip_path
            logging.info(f"{B}{gr}ZIP success")
            
        except Exception as e:
            logging.error(f"{B}{red}ZIP error with path \"{ye}{path}{red}\": {e}{cl}")
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
            sys.exit(1)
    elif not os.path.isfile(path):
        logging.error(f"{B}{red}Error:{cy} Path \"{ye}{path}{cy}\" is not a file/dir{cl}")
        sys.exit(1)

    try:
        with open(file_to_send, 'rb') as f:
            bot.send_document(CHAT_ID, f)
        logging.info(f"{B}{gr}File \"{ye}{os.path.basename(file_to_send)}{gr}\" uploaded{cl}")
    except apihelper.ApiException as e:
        logging.error(f"{B}{red}Telegram API Error: {orn}{e}{cl}")
        logging.error(f"{B}{orn}Check bot token and chat id. Maybe file too big?{cl}")
    except Exception as e:
        logging.error(f"{B}{red}Unknown error while uploading file: {e}{cl}")
    finally:
        if temp_file_to_send and os.path.exists(temp_file_to_send):
            os.remove(temp_file_to_send)
            logging.info(f"{B}{cy}Temporary file removed: {ye}{temp_file_to_send}{cl}")

def pull_file(message_id_str):
    try:
        message_id = int(message_id_str)
    except ValueError:
        logging.error(f"{B}{red}Error: Message ID must be int{cl}")
        sys.exit(1)

    logging.info(f"{B+ye}Searching file by message ID \"{message_id}\"...{cl}")

    try:
        updates = bot.get_updates(offset=-1, allowed_updates=['message'])
        
        file_info = None
        for update in updates:
            if update.message and update.message.message_id == message_id and update.message.document:
                file_info = update.message.document
                break

        if not file_info:
            logging.error(f"{B+red}Error: File not found for message with ID \"{ye}{message_id}\"{cl}")
            sys.exit(1)

        file_id = file_info.file_id
        file_name = file_info.file_name if file_info.file_name else f"downloaded_file_{message_id}"

        file_path_on_telegram = bot.get_file(file_id).file_path
        if not file_path_on_telegram:
            logging.error(f"{B+red}Error: file not found by ID \"{ye}{file_id}\"{cl}")
            sys.exit(1)

        download_destination = os.path.join(os.getcwd(), file_name)
        logging.info(f"{B+cy}Downloading \"{ye}{file_name}{cy}\" -> \"{ye}{os.getcwd()}/{cy}\" ...{cl}")
        
        downloaded_data = bot.download_file(file_path_on_telegram)
        with open(download_destination, 'wb') as f:
            f.write(downloaded_data)
        
        logging.info(f"{B+gr}File \"{ye}{file_name}{gr}\" uploaded successfully{cl}")

    except apihelper.ApiException as e:
        logging.error(f"{B+red}Telegram API error: {e}{cl}")
        logging.error(f"{B+orn}Check bot token and message id{cl}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"{B+red}Unknown error while uploading file: {e}{cl}")
        sys.exit(1)

def set_token(token):
    global BOT_TOKEN, bot
    BOT_TOKEN = token
    try:
        bot = TeleBot(BOT_TOKEN)
        bot_info = bot.get_me()
        logging.info(f"{B+gr}Token updated.{cy} Bot: {U}@{bot_info.username}{cl}")
    except apihelper.ApiException as e:
        logging.error(f"{B+red}Error: Bot Token invalid or Telegram API problem: {e}{cl}")
        BOT_TOKEN = None
        bot = None
        sys.exit(1)
    except Exception as e:
        logging.error(f"{B+red}Unknown error: {e}{cl}")
        BOT_TOKEN = None
        bot = None
        sys.exit(1)
    save_config()


def set_chat_id(chat_id_str):
    global CHAT_ID
    try:
        CHAT_ID = int(chat_id_str)
        save_config()
        logging.info(f"{B+cy}Chat ID set: {U+ye}{CHAT_ID}{cl}")
    except ValueError:
        logging.error(f"{B+red}Error: \"{ye}{chat_id_str}{red}\" is not valid int Chat ID{cl}")
        sys.exit(1)

def setup_pusher():
    global BOT_TOKEN, CHAT_ID, bot
    print(f"{B+cy}Hello to Pusher Setup!\n\n{gr}{'#'*30}{cy}\n\nFirst I need Telegran bot token (use BotFather){cl}")

    while True:
        token = input(f"{B+cy}Token: {cl}")
        try:
            bot = TeleBot(token)
            me = bot.get_me()
            print(f"{B+gr}Bot found, username: {U+ye}@{me.username}{cl}")
            rep = input(f"{B+cy}Is the bot correct? ({gr}y{cy}/{red}n{cy}, default: {gr}y{cy}): {cl}")
            if rep.lower() in ["y",""]:
                BOT_TOKEN = token
                print(f"{B+gr}Token saved{cl}")
                break
        except Exception as e:
            print(f"{B+red}Invalid Bot Token or unknown error ({e}), repeating{cl}")
            pass
    print(f"{B+cy}Now I need your Chat ID to which the bot will send files and download them from.\nMust be int.\nIf supergroup, add {ye}-100{cy} to the beginning of the ID.\nThe bot must have access to the chat (for example, if it is a private chat, send it /start first){cl}")

    while True:
        cid = int(input(f"{cy+B}Chat ID: {cl}"))
        try:
            bot = TeleBot(BOT_TOKEN)
            chat = bot.get_chat(cid)
            print(f"{B+gr}Chat found: {U+ye}{chat.first_name or chat.title}{cl}")
            rep = input(f"{B+cy}Is the chat correct? ({gr}y{cy}/{red}n{cy}, default: {gr}y{cy}): {cl}")
            if rep.lower() in ["y",""]:
                CHAT_ID = cid
                print(f"{B+gr}Chat saved{cl}")
                break
        except Exception as e:
            print(f"{B+red}Invalid Chat ID or unknown error ({e}), repeating{cl}")
            pass

    save_config()
    print(f"{B}{gr}All done. {cy}Now you can use Pusher to send and download files via the specified bot and the specified chat with:\n- {ye}pusher push some_file.txt{cy}\n- {ye}pusher pull 123\n\n{gr}{'#'*30}{cl}")

def check():
    global BOT_TOKEN, CHAT_ID
    _ = 0
    if not BOT_TOKEN:
        print(f"{B+red}[-] {cy}Bot token not found{cl}")
        _ += 1
    if not CHAT_ID:
        print(f"{B+red}[-] {cy}Chat ID not found{cl}")
        _ += 2
    
    match _:
        case 1:
            logging.warning(f"{B+cy}Set new token by \"{ye}pusher token <token>{cy}\" or run setup with \"{ye}pusher setup{cy}\"{cl}")
        case 2:
            logging.warning(f"{B+cy}Set new chat by \"{ye}pusher chat <id>{cy}\" or run setup with \"{ye}pusher setup{cy}\"{cl}")
        case 3:
            logging.warning(f"{B+cy}Pusher not configured, run \"{ye}pusher setup{cy}\"{cl}")
        case 0:
            return True
    return False

if __name__ == "__main__":
    load_config()

    parser = argparse.ArgumentParser(description="Pusher for file managevent with Telegram bot")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Push
    push_parser = subparsers.add_parser("push", help="Send file or dir via Telegram")
    push_parser.add_argument("path", help="Path to file/dir")

    # Pull
    pull_parser = subparsers.add_parser("pull", help="Download file by message id")
    pull_parser.add_argument("message_id", type=str, help="Message id (with file)") 

    # Token
    token_parser = subparsers.add_parser("token", help="Set Telegram bot token.")
    token_parser.add_argument("new_token", help="Telegram bot token")

    # Chat
    chat_parser = subparsers.add_parser("chat", help="Set your Telegram Chat ID.")
    chat_parser.add_argument("new_chat_id", help="Your Telegram Chat ID.")

    setup_parser = subparsers.add_parser("setup", help="Setup Pusher")

    args = parser.parse_args()

    if args.command != "setup":
        c = check()
        if not c: sys.exit(1)

    match args.command:
        case "push":
            push_file_or_directory(args.path)
        case "pull":
            pull_file(args.message_id)
        case "token":
            set_token(args.new_token)
        case "chat":
            set_chat_id(args.new_chat_id)
        case "setup":
            setup_pusher()
        case _:
            parser.print_help()


