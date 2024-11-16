import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
from telegram import BotCommand
import os


# Configurazione del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect('usernames.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            balance FLOAT DEFAULT 0,
            role TEXT DEFAULT 'user'  -- Default role is 'user'
        )
    ''')
    conn.commit()
    bot_user_id = 0  # Use 0 or a reserved ID for the bot
    cursor.execute('SELECT * FROM users WHERE username = ?', ('Baicassa',))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)', (bot_user_id, 'Baicassa', 0))
        conn.commit()
    conn.close()


def add_username(user_id, username):
    conn = sqlite3.connect('usernames.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def username_exists(username):
    conn = sqlite3.connect('usernames.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

# Recupera l'username associato a un user_id
def get_username(user_id):
    conn = sqlite3.connect('usernames.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_user_role(user_id):
    conn = sqlite3.connect('usernames.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None  # Return the role or None if the user does not exist

def get_balance_by_username(username):
    conn = sqlite3.connect('usernames.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    print(result)
    return result[0] if result else 0

def update_balance_by_username(username, amount):
    conn = sqlite3.connect('usernames.db')
    cursor = conn.cursor() 
    try:
        cursor.execute('UPDATE users SET balance = balance + ? WHERE username = ?', (amount, username))
        conn.commit()
    except Exception as e:
        print(f"Errore durante l'aggiornamento del balance: {e}")
    finally:
        conn.close()
    #cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    #conn.commit()
    #conn.close()
# Inizializza il database
init_db()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user_id = update.effective_user.id
    username = get_username(user_id)
    if username:
        await update.message.reply_text(f"Welcome back, {username}!")
    else:
        await update.message.reply_text(
            "Welcome! Please choose a unique username by typing /setusername <your_username>."
        )



#async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#    """Gestisce il comando /start inviato dai nuovi membri."""
#    user_id = update.effective_user.id
#    await update.message.reply_text(
#        "Benvenuto! Per favore, scegli un username univoco digitando /setusername <il_tuo_username>."
#   )

async def set_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce il comando /setusername per impostare un nuovo username."""
    user_id = update.effective_user.id
    if get_username(user_id) != None:
        await update.message.reply_text("You have already set an username. your username is: " + get_username(user_id))
        return
    if len(context.args) != 1:
        await update.message.reply_text(
            "Per favore, utilizza il comando nel formato: /setusername <il_tuo_username>"
        )
        return

    new_username = context.args[0]
    if username_exists(new_username):
        await update.message.reply_text(
            "Questo username è già in uso. Per favore, scegline un altro."
        )
    else:
        if add_username(user_id, new_username):
            await update.message.reply_text(
                f"Hey '{new_username}' happy to have you here!"
            )
        else:
            await update.message.reply_text(
                "There was an error during the username assignement. Please try again."
            )
# Gestisce il comando /help


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides information about available commands."""
    user_id = update.effective_user.id
    username = get_username(user_id)
    help_text = (
        "/start - Initiate interaction with the bot.\n"
        "/setusername <your_username> - Set a unique username.\n"
        "/help - Display this help message."
    )
    if username:
        help_text = f"Hello {username}!\n\n" + help_text
    await update.message.reply_text(help_text)


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra il balance dell'utente."""
    user_id = update.effective_user.id
    balance = get_balance_by_username(user_id)
    if balance is not None:
        await update.message.reply_text(f"Il tuo balance attuale è: {balance:.2f}")
    else:
        await update.message.reply_text("Non sei registrato. Usa /setusername per registrarti.")

async def aggiorna_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Aggiorna il balance dell'utente."""
    if len(context.args) != 1:
        await update.message.reply_text("Utilizzo: /aggiorna_balance <importo>")
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text("L'importo deve essere un numero.")
        return

    user_id = update.effective_user.id
    if get_username(user_id) is not None:
        update_balance(user_id, amount)
        balance = get_balance(user_id)
        await update.message.reply_text(f"balance aggiornato con successo! Il tuo nuovo balance è: {balance:.2f}")
    else:
        await update.message.reply_text("Non sei registrato. Usa /setusername per registrarti.")


async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce l'evento di aggiunta di un nuovo membro al gruppo."""
    for member in update.message.new_chat_members:
        if not member.is_bot:
            await context.bot.send_message(
                chat_id=member.id,
                text=(
                    "Benvenuto nel gruppo! Per favore, avvia una chat privata con me e "
                    "digita /start per scegliere un username univoco."
                )
            )
async def charge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Incrementa il balance dell'utente del valore specificato."""
    if len(context.args) != 1:
        await update.message.reply_text("Utilizzo: /charge <importo>")
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text("L'importo deve essere un numero.")
        return

    user_id = update.effective_user.id
    username = get_username(user_id)
    if username:
        update_balance_by_username(username, amount)
        update_balance_by_username('Baicassa', amount)
        balance = get_balance_by_username(username)
        balance_baicassa = get_balance_by_username('Baicassa')
        await update.message.reply_text(
            f"{username}, il tuo balance è stato incrementato di €{amount:.2f}. balance attuale: €{balance:.2f}. Baicassa, il tuo balance è stato aggiornato: €{balance_baicassa:.2f}"
        )
        print(f"Baicassa, il tuo balance è stato aggiornato: €{balance_baicassa:.2f}")
    else:
        await update.message.reply_text("Non sei registrato. Usa /setusername per registrarti.")

async def caffe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Decrement €0.50 from the user's balance for a coffee."""
    user_id = update.effective_user.id
    username = get_username(user_id)
    if username:
        update_balance_by_username(username, -0.50)  # Decrement €0.50
        balance = get_balance_by_username(username)  # Fetch updated balance
        await update.message.reply_text(
            f"{username}, hai preso un caffè! €0.50 sono stati detratti. balance attuale: €{balance:.2f}."
        )
        update_balance_by_username('Baicassa', 0.50)  # Increment Baicassa balance
    else:
        await update.message.reply_text("Non sei registrato. Usa /setusername per registrarti.")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subtract the specified amount from the user's balance for a purchase."""
    if len(context.args) < 2:
        await update.message.reply_text("Utilizzo: /buy <descrizione> <importo>")
        return

    try:
        description = " ".join(context.args[:-1])  # Description of the item
        amount = float(context.args[-1])  # Amount to deduct
    except ValueError:
        await update.message.reply_text("L'importo deve essere un numero.")
        return

    user_id = update.effective_user.id
    username = get_username(user_id)
    if username:
        update_balance_by_username(username, -amount)  # Deduct the specified amount
        balance = get_balance_by_username(username)  # Fetch updated balance
        await update.message.reply_text(
            f"{username}, hai acquistato {description} per €{amount:.2f}. balance attuale: €{balance:.2f}."
        )
        update_balance_by_username('Baicassa', amount)  # Increment Baicassa balance
    else:
        await update.message.reply_text("Non sei registrato. Usa /setusername per registrarti.")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Decrementa il balance dell'utente del valore specificato."""
    if len(context.args) != 1:
        await update.message.reply_text("Utilizzo: /withdraw <importo>")
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text("L'importo deve essere un numero.")
        return

    user_id = update.effective_user.id
    username = get_username(user_id)
    if username:
        update_balance_by_username(username, -amount)
        #update_balance_by_username('Baicassa', -amount)
        balance = get_balance_by_username(username)
        balance_baicassa = get_balance_by_username('Baicassa')
        await update.message.reply_text(
            f"{username}, il tuo balance è stato decrementato di €{amount:.2f}. balance attuale: €{balance:.2f}. Baicassa, il tuo balance è stato aggiornato: €{balance_baicassa:.2f}"
        )
        print(f"Baicassa, il tuo balance è stato aggiornato: €{balance_baicassa:.2f}")
    else:
        await update.message.reply_text("Non sei registrato. Usa /setusername per registrarti.")

async def set_bot_commands(application):
    commands = [
        BotCommand(command="start", description="Inizia l'interazione con il bot."),
        BotCommand(command="setusername", description="Imposta un username univoco."),
        BotCommand(command="help", description="Mostra informazioni sui comandi disponibili."),
        BotCommand(command="balance", description="Show your current balance."),
        BotCommand(command="withdraw", description="Insert the amout of money you want to withdraw."),
        BotCommand(command="recharge", description="Insert the amount of money you spent for Baita."),
        BotCommand(command="buy", description="Insert the object you bought and the amount of money."),
        BotCommand(command="caffe", description="pay for a coffee."),
    ]
    await application.bot.set_my_commands(commands)

async def modify_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Modify the balance of a specific user by an authorized user."""
    # Check if the user is authorized
    user_id = update.effective_user.id
    user_role = get_user_role(user_id)
    if user_role != 'admin':
        await update.message.reply_text("Non sei autorizzato a utilizzare questo comando.")
        return

    # Check arguments
    if len(context.args) != 2:
        await update.message.reply_text("Utilizzo: /modify_balance <username> <importo>")
        return

    try:
        target_username = context.args[0]  # Username to modify
        amount = float(context.args[1])  # Amount to modify the balance by
    except ValueError:
        await update.message.reply_text("L'importo deve essere un numero.")
        return

    # Check if the target user exists
    if not username_exists(target_username):
        await update.message.reply_text(f"L'utente '{target_username}' non esiste.")
        return

    # Modify the balance
    update_saldo_by_username(target_username, amount)
    new_balance = get_saldo_by_username(target_username)
    await update.message.reply_text(
        f"Il saldo di {target_username} è stato modificato di €{amount:.2f}. Saldo attuale: €{new_balance:.2f}."
    )

def main() -> None:
    """Avvia il bot."""
    # Inserisci qui il token del tuo bot
    ##token = 'IL_TUO_TOKEN_DEL_BOT'
    token = os.getenv('TELEGRAM_BOT_TOKEN')

    application = ApplicationBuilder().token(token).build()

    # Gestori per i comandi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setusername", set_username))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("recharge", charge))
    application.add_handler(CommandHandler("withdraw", withdraw))
    application.add_handler(CommandHandler("caffe", caffe))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("modify_balance", modify_balance))  

    # Gestore per l'evento di nuovi membri aggiunti al gruppo
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))

    # Imposta i comandi del bot
    application.post_init = set_bot_commands

    # Avvia il bot
    application.run_polling()

if __name__ == '__main__':
    main()
