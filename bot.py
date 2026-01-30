import os
import json
import random
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# Конфигурация
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8535491689
USER_DATA_FILE = "user_data.json"
CLANS_DATA_FILE = "clans_data.json"
MAX_BALANCE = 100_000_000_000_000_000_000
MATTER_PRICE = 1_000_000_000  # 1 материя = 1,000,000,000 монет
CLAN_CREATE_COST = 1_000_000_000_000  # Стоимость создания клана
CLAN_CREATE_MATTER = 10_000  # Материя для создания клана
CLAN_RENAME_COST = 10_000_000_000_000  # Стоимость переименования клана

# Состояния для ConversationHandler
BUSINESS_ID, BUSINESS_QUANTITY = range(2)
MATTER_ID, MATTER_QUANTITY = range(2, 4)
SELL_MATTER = 5
CLAN_NAME, CLAN_JOIN = range(6, 8)
CLAN_NEW_NAME = 9
CONTRIBUTE_AMOUNT = 10
TRANSFER_TARGET = 11
TRANSFER_AMOUNT = 12
DEPOSIT_AMOUNT = 13
WITHDRAW_AMOUNT = 14
ROULETTE_BET = 15
INVEST_AMOUNT = 16
SELECT_ACHIEVEMENT = 17
QUEST_ID = 18

# Бизнесы
BUSINESSES = {
    "1": {"name": "Ларёк", "price": 10_000, "income": 500, "emoji": "🏪"},
    "2": {"name": "Кафе", "price": 50_000, "income": 2_500, "emoji": "☕"},
    "3": {"name": "Магазин", "price": 200_000, "income": 10_000, "emoji": "🛒"},
    "4": {"name": "Ресторан", "price": 1_000_000, "income": 50_000, "emoji": "🍽️"},
    "5": {"name": "Автосалон", "price": 5_000_000, "income": 250_000, "emoji": "🚗"},
    "6": {"name": "Отель", "price": 25_000_000, "income": 1_250_000, "emoji": "🏨"},
    "7": {"name": "Завод", "price": 100_000_000, "income": 5_000_000, "emoji": "🏭"},
    "8": {"name": "Сеть ресторанов", "price": 500_000_000, "income": 25_000_000, "emoji": "🍴"},
    "9": {"name": "IT компания", "price": 2_000_000_000, "income": 100_000_000, "emoji": "💻"},
    "10": {"name": "Корпорация", "price": 10_000_000_000, "income": 500_000_000, "emoji": "🏢"},
}

# Фермы материи
MATTER_FARMS = {
    "1": {"name": "Малая ферма", "price": 1_000_000_000, "production": 0.1, "emoji": "🔬"},
    "2": {"name": "Средняя ферма", "price": 5_000_000_000, "production": 0.5, "emoji": "🧪"},
    "3": {"name": "Большая ферма", "price": 25_000_000_000, "production": 2.5, "emoji": "⚗️"},
    "4": {"name": "Гигантская ферма", "price": 100_000_000_000, "production": 10, "emoji": "🧫"},
    "5": {"name": "Квантовая ферма", "price": 500_000_000_000, "production": 50, "emoji": "🌌"},
}

# Описание ежедневных заданий
DAILY_QUESTS = [
    {"name": "Собрать доход", "key": "collected_income", "target": 3},
    {"name": "Сделать ставку", "key": "bets_made", "target": 1},
    {"name": "Купить бизнес", "key": "businesses_bought", "target": 1},
    {"name": "Продать материю", "key": "matter_sold", "target": 1},
    {"name": "Внести вклад в клан", "key": "clan_contributed", "target": 1}
]

# Описание ачивок
ACHIEVEMENTS = [
    {"name": "Миллионер", "check": lambda data: data["balance"] >= 1_000_000},
    {"name": "Материальный бог", "check": lambda data: data["matter"] >= 1000},
    {"name": "Казино-маньяк", "check": lambda data: data.get("bets_made", 0) >= 50},
    {"name": "Фермер", "check": lambda data: sum(data.get("matter_farms", {}).values()) >= 10},
    {"name": "Клан-лидер", "check": lambda data: data.get("clan_contribution", 0) >= 10_000_000},
    {"name": "Фермер-легенда", "check": lambda data: sum(data.get("matter_farms", {}).values()) >= 1000},
    {"name": "Казино-гений", "check": lambda data: data.get("bets_made", 0) >= 1000},
    {"name": "Бог материи", "check": lambda data: data["matter"] >= 100_000}
]

# Описание квестов
QUESTS = [
    {"name": "Собрать доход 5 раз", "type": "collect_income", "target": 5, "reward": 0.05},  # 5% от баланса
    {"name": "Сыграть в казино 3 раза", "type": "bet", "target": 3, "reward": 100000}
]

def load_user_data():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_clans_data():
    if not os.path.exists(CLANS_DATA_FILE):
        return {}
    try:
        with open(CLANS_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_clans_data(data):
    with open(CLANS_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def format_number(number):
    return "{:,}".format(number).replace(",", ".")

def ensure_user_data(user_data):
    defaults = {
        "username": "Unknown",
        "nickname": f"Игрок_{random.randint(1000, 9999)}",
        "balance": 1000,
        "businesses": {},
        "matter_farms": {},
        "matter": 0,
        "last_bonus": None,
        "last_bet": None,
        "last_income_collect": None,
        "last_matter_collect": None,
        "register_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "clan_id": None,
        "clan_contribution": 0,
        # Новые поля
        "daily_quests": {q["key"]: 0 for q in DAILY_QUESTS},
        "last_daily_reset": datetime.now().strftime("%Y-%m-%d"),
        "achievements": [],
        "last_transfer": None,
        "bets_made": 0,
        "businesses_bought": 0,
        "matter_sold": 0,
        "clan_contributed": 0,
        # Улучшения
        "business_upgrades": {},
        "farm_upgrades": {},
        # Банк
        "bank_balance": 0,
        "last_bank_collect": None,
        # Рулетка, инвестиции, квесты
        "investments": [],
        "current_quests": [],
        "quests_completed": [],
        "income_collected_today": 0,
        "selected_achievement": None
    }
    for key, value in defaults.items():
        if key not in user_data:
            user_data[key] = value
    return user_data

def reset_daily_quests_if_needed(user_data):
    today = datetime.now().strftime("%Y-%m-%d")
    last_reset = user_data.get("last_daily_reset", "")
    if last_reset != today:
        user_data["daily_quests"] = {q["key"]: 0 for q in DAILY_QUESTS}
        user_data["last_daily_reset"] = today
        user_data["income_collected_today"] = 0
    return user_data

def check_achievements(user_data):
    unlocked = []
    for ach in ACHIEVEMENTS:
        if ach["name"] not in user_data["achievements"] and ach["check"](user_data):
            user_data["achievements"].append(ach["name"])
            unlocked.append(ach["name"])
    return unlocked

def calculate_income_with_upgrades(user_data, biz_id, base_income):
    upgrades = user_data.get("business_upgrades", {})
    level = upgrades.get(biz_id, 0)
    multiplier = 1 + (0.10 * level)
    return base_income * multiplier

def calculate_production_with_upgrades(user_data, farm_id, base_production):
    upgrades = user_data.get("farm_upgrades", {})
    level = upgrades.get(farm_id, 0)
    multiplier = 1 + (0.10 * level)
    return base_production * multiplier

def collect_bank_interest(user_data):
    now = datetime.now()
    last_collect = user_data.get("last_bank_collect")
    if last_collect is None:
        user_data["last_bank_collect"] = now.strftime("%Y-%m-%d %H:%M:%S")
        return 0
    try:
        last = datetime.strptime(last_collect, "%Y-%m-%d %H:%M:%S")
        elapsed_hours = (now - last).total_seconds() / 3600
        interest = user_data["bank_balance"] * elapsed_hours * 0.01
        if interest > user_data["bank_balance"] * 10:  # Максимум 1000%
            interest = user_data["bank_balance"] * 10
        user_data["balance"] += interest
        user_data["last_bank_collect"] = now.strftime("%Y-%m-%d %H:%M:%S")
        return interest
    except ValueError:
        user_data["last_bank_collect"] = now.strftime("%Y-%m-%d %H:%M:%S")
        return 0

def check_quests(user_data):
    completed = []
    for quest in user_data.get("current_quests", []):
        if quest["type"] == "collect_income":
            current = user_data.get("income_collected_today", 0)
        elif quest["type"] == "bet":
            current = user_data.get("bets_made", 0)
        else:
            continue
        if current >= quest["target"]:
            completed.append(quest)
    for q in completed:
        if q not in user_data["current_quests"]:
            continue
        user_data["current_quests"].remove(q)
        user_data["quests_completed"].append(q)
        reward = q["reward"]
        if isinstance(reward, float):  # процент от баланса
            reward = int(user_data["balance"] * reward)
        user_data["balance"] += reward
        if user_data["balance"] > MAX_BALANCE:
            user_data["balance"] = MAX_BALANCE
    return completed

def update_clan_activity(clan_id, clans_data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if clan_id in clans_data:
        clans_data[clan_id]["last_activity"] = now

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    username = user.username or user.first_name
    data = load_user_data()
    if user_id not in data:
        data[user_id] = ensure_user_data({})
        data[user_id]["username"] = username
        save_user_data(data)
        welcome_text = (
            f"👋 Добро пожаловать, {username}!\n"
            f"🎮 Вы получили стартовый бонус: 1,000 монет\n"
            f"💡 Используйте кнопки ниже для управления ботом"
        )
    else:
        data[user_id] = ensure_user_data(data[user_id])
        save_user_data(data)
        welcome_text = f"🔄 С возвращением, {data[user_id]['nickname']}!"
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return
    user_data = ensure_user_data(data[user_id])
    # Проверка ачивок
    unlocked = check_achievements(user_data)
    if unlocked:
        save_user_data(data)
    total_income = 0
    businesses_text = "У вас нет бизнесов"
    if user_data.get("businesses"):
        businesses_text = "Ваши бизнесы:\n"
        for biz_id, quantity in user_data["businesses"].items():
            if biz_id in BUSINESSES:
                biz = BUSINESSES[biz_id]
                base_income = biz["income"] * quantity
                income = calculate_income_with_upgrades(user_data, biz_id, base_income)
                total_income += income
                businesses_text += f"{biz['emoji']} {biz['name']}: {quantity} шт. (+{format_number(income)}/час)\n"
    total_matter_production = 0
    matter_farms_text = "У вас нет ферм материи"
    if user_data.get("matter_farms"):
        matter_farms_text = "Ваши фермы материи:\n"
        for farm_id, quantity in user_data["matter_farms"].items():
            if farm_id in MATTER_FARMS:
                farm = MATTER_FARMS[farm_id]
                base_production = farm["production"] * quantity
                production = calculate_production_with_upgrades(user_data, farm_id, base_production)
                total_matter_production += production
                matter_farms_text += f"{farm['emoji']} {farm['name']}: {quantity} шт. (+{production:.1f} материи/час)\n"
    clan_info = ""
    if user_data["clan_id"]:
        clans_data = load_clans_data()
        clan = clans_data.get(user_data["clan_id"])
        if clan:
            clan_info = f"\n👥 Клан: {clan['name']} (вклад: {format_number(user_data.get('clan_contribution', 0))} монет)"
        else:
            user_data["clan_id"] = None
            save_user_data(data)
    achievements_text = "🏆 Ачивки: "
    if user_data["achievements"]:
        ach_list = user_data["achievements"]
        if user_data.get("selected_achievement"):
            ach_list = [a for a in ach_list if a == user_data["selected_achievement"]]
        achievements_text += ", ".join(ach_list)
    else:
        achievements_text += "Пока нет"
    profile_text = (
        f"👤 Профиль: {user_data['nickname']}\n"
        f"💰 Баланс: {format_number(user_data['balance'])} монет\n"
        f"💎 Материя: {user_data['matter']:.2f}"
        f"{clan_info}\n"
        f"📅 Дата регистрации: {user_data['register_date']}\n"
        f"{businesses_text}\n"
        f"💸 Общий доход: {format_number(total_income)}/час\n"
        f"{matter_farms_text}\n"
        f"🌀 Производство материи: {total_matter_production:.1f}/час\n"
        f"🏦 Банк: {format_number(user_data['bank_balance'])} монет\n"
        f"🏅 {achievements_text}"
    )
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(profile_text, reply_markup=reply_markup)

async def casino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["10", "100", "1,000"],
        ["10,000", "100,000", "1,000,000"],
        ["🎯 Рулетка", "🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🎰 Добро пожаловать в казино!\n"
        "💰 Введите сумму ставки или выберите из предложенных:\n"
        "Возможные множители:\n"
        "❌ 0x\n"
        "😕 0.5x\n"
        "✅ 2x\n"
        "💰💰 5x\n"
        "💰💰💰 25x",
        reply_markup=reply_markup
    )

async def process_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, не находится ли пользователь в процессе внесения вклада в клан
    if context.user_data.get('contributing'):
        await process_contribution(update, context)
        return
    user_id = str(update.message.from_user.id)
    bet_text = update.message.text.replace(".", "").replace(",", "")
    try:
        bet_amount = int(bet_text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректную сумму ставки!")
        return
    data = load_user_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return
    user_data = ensure_user_data(data[user_id])
    if bet_amount <= 0:
        await update.message.reply_text("Ставка должна быть больше 0!")
        return
    if user_data["balance"] < bet_amount:
        await update.message.reply_text("Недостаточно средств для ставки!")
        return

    rand = random.random()
    if rand < 0.5:  # 50% шанс
        multiplier = 0
        win_amount = 0
        result_text = f"❌ Вы проиграли {format_number(bet_amount)} монет (0x)"
    elif rand < 0.59:  # 9% шанс (70-79)
        multiplier = 0.5
        win_amount = int(bet_amount * multiplier)
        result_text = f"😕 Вы получили назад {format_number(win_amount)} монет (0.5x)"
    elif rand < 0.9:  # 40% шанс (79-89)
        multiplier = 2
        win_amount = bet_amount * multiplier
        result_text = f"✅ Вы выиграли {format_number(win_amount)} монет (2x)"
    elif rand < 0.99:  # 9% шанс (89-99)
        multiplier = 5
        win_amount = bet_amount * multiplier
        result_text = f"💰💰 Вы выиграли {format_number(win_amount)} монет (5x)"
    else:  # 1% шанс (99-100)
        multiplier = 25
        win_amount = bet_amount * multiplier
        result_text = f"💰💰💰 ДЖЕКПОТ! Вы выиграли {format_number(win_amount)} монет (25x) 💰💰💰"

    if multiplier > 0:
        user_data["balance"] += win_amount
        if user_data["balance"] > MAX_BALANCE:
            user_data["balance"] = MAX_BALANCE
            result_text += "\n⚠️ Достигнут максимальный лимит баланса!"
    else:
        user_data["balance"] -= bet_amount

    user_data["last_bet"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_data["bets_made"] = user_data.get("bets_made", 0) + 1
    user_data["daily_quests"]["bets_made"] = min(DAILY_QUESTS[1]["target"], user_data["daily_quests"]["bets_made"] + 1)
    check_quests(user_data)  # проверяем квесты
    data[user_id] = user_data
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"{result_text}\n💰 Ваш баланс: {format_number(user_data['balance'])}",
        reply_markup=reply_markup
    )

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return
    user_data = ensure_user_data(data[user_id])
    now = datetime.now()
    if user_data["last_bonus"]:
        try:
            last_bonus = datetime.strptime(user_data["last_bonus"], "%Y-%m-%d %H:%M:%S")
            if (now - last_bonus) < timedelta(hours=24):
                next_bonus = last_bonus + timedelta(hours=24)
                await update.message.reply_text(
                    f"⏳ Вы уже получали бонус сегодня!\n"
                    f"🕒 Следующий бонус будет доступен: {next_bonus.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                return
        except ValueError:
            pass
    bonus_amount = random.randint(100, 10000)
    user_data["balance"] += bonus_amount
    if user_data["balance"] > MAX_BALANCE:
        user_data["balance"] = MAX_BALANCE
        limit_msg = "\n⚠️ Достигнут максимальный лимит баланса!"
    else:
        limit_msg = ""
    user_data["last_bonus"] = now.strftime("%Y-%m-%d %H:%M:%S")
    data[user_id] = user_data
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"🎁 Вы получили бонус: {format_number(bonus_amount)} монет!{limit_msg}\n"
        f"💰 Ваш баланс: {format_number(user_data['balance'])}",
        reply_markup=reply_markup
    )

async def top_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🏆 Топ по балансу", "💎 Топ по материи"],
        ["🏆 Топ кланов", "🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите тип топа:",
        reply_markup=reply_markup
    )

async def top_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_user_data()
    if not data:
        await update.message.reply_text("Пока нет игроков в рейтинге!")
        return
    sorted_players = sorted(
        data.items(),
        key=lambda x: x[1].get("balance", 0),
        reverse=True
    )[:10]
    top_text = "🏆 Топ игроков по балансу:\n"
    for idx, (user_id, user_data) in enumerate(sorted_players, 1):
        user_data = ensure_user_data(user_data)
        top_text += f"{idx}. {user_data['nickname']} - {format_number(user_data['balance'])} монет\n"
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(top_text, reply_markup=reply_markup)

async def top_matter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_user_data()
    if not data:
        await update.message.reply_text("Пока нет игроков в рейтинге!")
        return
    sorted_players = sorted(
        data.items(),
        key=lambda x: x[1].get("matter", 0),
        reverse=True
    )[:10]
    top_text = "💎 Топ игроков по материи:\n"
    for idx, (user_id, user_data) in enumerate(sorted_players, 1):
        user_data = ensure_user_data(user_data)
        top_text += f"{idx}. {user_data['nickname']} - {user_data['matter']:.2f} материи\n"
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(top_text, reply_markup=reply_markup)

async def top_clans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clans_data = load_clans_data()
    if not clans_data:
        await update.message.reply_text("Пока нет созданных кланов!")
        return
    sorted_clans = sorted(
        clans_data.items(),
        key=lambda x: x[1]["total_contribution"],
        reverse=True
    )[:10]
    top_text = "🏆 Топ кланов по общему вкладу:\n"
    for idx, (clan_id, clan) in enumerate(sorted_clans, 1):
        top_text += (
            f"{idx}. {clan['name']} (ID: {clan_id})\n"
            f"👑 Создатель: {clan['owner_name']}\n"
            f"👥 Участников: {len(clan['members'])}\n"
            f"💹 Вклад: {format_number(clan['total_contribution'])}\n"
        )
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(top_text, reply_markup=reply_markup)

async def change_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Введите новый никнейм (или нажмите '🏠 Главное меню' для отмены):", reply_markup=reply_markup)
    return "WAITING_NICKNAME"

async def process_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    new_nick = update.message.text.strip()
    if new_nick == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    if len(new_nick) > 20:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Никнейм слишком длинный (макс. 20 символов)!", reply_markup=reply_markup)
        return "WAITING_NICKNAME"
    data = load_user_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return ConversationHandler.END
    data[user_id] = ensure_user_data(data[user_id])
    data[user_id]["nickname"] = new_nick
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Ваш никнейм изменен на: {new_nick}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def collect_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return
    user_data = ensure_user_data(data[user_id])
    now = datetime.now()

    # Собираем доход от бизнесов
    total_income = 0
    income_collected = False
    if user_data.get("businesses"):
        last_collect = user_data.get("last_income_collect")
        if last_collect is None or (now - datetime.strptime(last_collect, "%Y-%m-%d %H:%M:%S")) >= timedelta(hours=1):
            income_collected = True
            for biz_id, quantity in user_data["businesses"].items():
                if biz_id in BUSINESSES:
                    base_income = BUSINESSES[biz_id]["income"] * quantity
                    income = calculate_income_with_upgrades(user_data, biz_id, base_income)
                    total_income += income
            user_data["balance"] += total_income
            user_data["last_income_collect"] = now.strftime("%Y-%m-%d %H:%M:%S")
            user_data["daily_quests"]["collected_income"] = min(DAILY_QUESTS[0]["target"], user_data["daily_quests"]["collected_income"] + 1)
            user_data["income_collected_today"] = user_data.get("income_collected_today", 0) + 1
            check_quests(user_data)  # проверяем квесты

    # Собираем материю с ферм
    total_matter = 0
    matter_collected = False
    if user_data.get("matter_farms"):
        last_collect = user_data.get("last_matter_collect")
        if last_collect is None or (now - datetime.strptime(last_collect, "%Y-%m-%d %H:%M:%S")) >= timedelta(hours=1):
            matter_collected = True
            for farm_id, quantity in user_data["matter_farms"].items():
                if farm_id in MATTER_FARMS:
                    base_production = MATTER_FARMS[farm_id]["production"] * quantity
                    production = calculate_production_with_upgrades(user_data, farm_id, base_production)
                    total_matter += production
            user_data["matter"] += total_matter
            user_data["last_matter_collect"] = now.strftime("%Y-%m-%d %H:%M:%S")

    # Собираем проценты с банка
    bank_interest = collect_bank_interest(user_data)

    if not income_collected and not matter_collected and not bank_interest:
        next_collect_time = None
        if user_data.get("last_income_collect"):
            last_collect = datetime.strptime(user_data["last_income_collect"], "%Y-%m-%d %H:%M:%S")
            next_collect_time = last_collect + timedelta(hours=1)
        if user_data.get("last_matter_collect"):
            last_collect = datetime.strptime(user_data["last_matter_collect"], "%Y-%m-%d %H:%M:%S")
            matter_time = last_collect + timedelta(hours=1)
            if next_collect_time is None or matter_time > next_collect_time:
                next_collect_time = matter_time
        if next_collect_time:
            await update.message.reply_text(
                f"⏳ Вы уже собирали доход и материю в последний час!\n"
                f"🕒 Следующий сбор будет доступен: {next_collect_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            await update.message.reply_text("У вас нет бизнесов или ферм для сбора!")
        return

    response_text = ""
    if income_collected and total_income > 0:
        response_text += f"💰 Вы собрали доход: {format_number(total_income)} монет!\n"
    if matter_collected and total_matter > 0:
        response_text += f"💎 Вы собрали материю: {total_matter:.2f}!\n"
    if bank_interest > 0:
        response_text += f"🏦 Вы получили проценты с банка: {format_number(bank_interest)} монет!\n"

    if user_data["balance"] > MAX_BALANCE:
        user_data["balance"] = MAX_BALANCE
        response_text += "\n⚠️ Достигнут максимальный лимит баланса!"

    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"{response_text}\n"
        f"💵 Ваш баланс: {format_number(user_data['balance'])}\n"
        f"💎 Ваша материя: {user_data['matter']:.2f}\n"
        f"🏦 Банк: {format_number(user_data['bank_balance'])} монет",
        reply_markup=reply_markup
    )

async def buy_business_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    # Создаем кнопки для бизнесов (по 2 в ряд)
    for i in range(1, 11, 2):
        row = []
        biz1 = BUSINESSES[str(i)]
        btn1 = f"{biz1['emoji']} {biz1['name']} - {format_number(biz1['price'])} (+{format_number(biz1['income'])}/час)"
        row.append(btn1)
        if i+1 <= 10:
            biz2 = BUSINESSES[str(i+1)]
            btn2 = f"{biz2['emoji']} {biz2['name']} - {format_number(biz2['price'])} (+{format_number(biz2['income'])}/час)"
            row.append(btn2)
        keyboard.append(row)
    keyboard.append(["🏠 Главное меню"])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🏢 Выберите бизнес для покупки:\n"
        "💰 Цена указана за 1 единицу\n"
        "💵 Доход указан в час",
        reply_markup=reply_markup
    )
    return BUSINESS_ID

async def business_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    business_id = None
    # Ищем ID бизнеса по emoji или названию
    for biz_id, biz in BUSINESSES.items():
        if biz['emoji'] in text or biz['name'] in text:
            business_id = biz_id
            break
    if not business_id:
        keyboard = []
        for i in range(1, 11, 2):
            row = []
            biz1 = BUSINESSES[str(i)]
            btn1 = f"{biz1['emoji']} {biz1['name']} - {format_number(biz1['price'])} (+{format_number(biz1['income'])}/час)"
            row.append(btn1)
            if i+1 <= 10:
                biz2 = BUSINESSES[str(i+1)]
                btn2 = f"{biz2['emoji']} {biz2['name']} - {format_number(biz2['price'])} (+{format_number(biz2['income'])}/час)"
                row.append(btn2)
            keyboard.append(row)
        keyboard.append(["🏠 Главное меню"])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, выберите бизнес из списка! (или нажмите '🏠 Главное меню' для отмены)", reply_markup=reply_markup)
        return BUSINESS_ID
    context.user_data["business_id"] = business_id
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"Введите количество бизнесов '{BUSINESSES[business_id]['name']}' для покупки (или нажмите '🏠 Главное меню' для отмены):",
        reply_markup=reply_markup
    )
    return BUSINESS_QUANTITY

async def business_quantity_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    business_id = context.user_data["business_id"]
    try:
        quantity = int(text)
        if quantity <= 0:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Количество должно быть больше 0!", reply_markup=reply_markup)
            return BUSINESS_QUANTITY
    except ValueError:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, введите число!", reply_markup=reply_markup)
        return BUSINESS_QUANTITY

    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    business = BUSINESSES[business_id]
    total_price = business["price"] * quantity
    if user_data["balance"] < total_price:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ Недостаточно средств! Вам нужно ещё {format_number(total_price - user_data['balance'])} монет",
            reply_markup=reply_markup
        )
        return BUSINESS_QUANTITY

    user_data["balance"] -= total_price
    if business_id in user_data["businesses"]:
        user_data["businesses"][business_id] += quantity
    else:
        user_data["businesses"][business_id] = quantity
    user_data["businesses_bought"] = user_data.get("businesses_bought", 0) + quantity
    user_data["daily_quests"]["businesses_bought"] = min(DAILY_QUESTS[2]["target"], user_data["daily_quests"]["businesses_bought"])
    data[user_id] = user_data
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Вы успешно купили {quantity} {business['name']} за {format_number(total_price)} монет!\n"
        f"💰 Ваш баланс: {format_number(user_data['balance'])}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def buy_matter_farm_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    # Создаем кнопки для ферм материи (по 2 в ряд)
    for i in range(1, 6, 2):
        row = []
        farm1 = MATTER_FARMS[str(i)]
        btn1 = f"{farm1['emoji']} {farm1['name']} - {format_number(farm1['price'])} (+{farm1['production']:.1f}/час)"
        row.append(btn1)
        if i+1 <= 5:
            farm2 = MATTER_FARMS[str(i+1)]
            btn2 = f"{farm2['emoji']} {farm2['name']} - {format_number(farm2['price'])} (+{farm2['production']:.1f}/час)"
            row.append(btn2)
        keyboard.append(row)
    keyboard.append(["🏠 Главное меню"])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🔬 Выберите ферму материи для покупки:\n"
        "💰 Цена указана за 1 единицу\n"
        "💎 Производство указано в час",
        reply_markup=reply_markup
    )
    return MATTER_ID

async def matter_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    matter_id = None
    # Ищем ID фермы по emoji или названию
    for farm_id, farm in MATTER_FARMS.items():
        if farm['emoji'] in text or farm['name'] in text:
            matter_id = farm_id
            break
    if not matter_id:
        keyboard = []
        for i in range(1, 6, 2):
            row = []
            farm1 = MATTER_FARMS[str(i)]
            btn1 = f"{farm1['emoji']} {farm1['name']} - {format_number(farm1['price'])} (+{farm1['production']:.1f}/час)"
            row.append(btn1)
            if i+1 <= 5:
                farm2 = MATTER_FARMS[str(i+1)]
                btn2 = f"{farm2['emoji']} {farm2['name']} - {format_number(farm2['price'])} (+{farm2['production']:.1f}/час)"
                row.append(btn2)
            keyboard.append(row)
        keyboard.append(["🏠 Главное меню"])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, выберите ферму из списка! (или нажмите '🏠 Главное меню' для отмены):", reply_markup=reply_markup)
        return MATTER_ID
    context.user_data["matter_id"] = matter_id
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"Введите количество ферм '{MATTER_FARMS[matter_id]['name']}' для покупки (или нажмите '🏠 Главное меню' для отмены):",
        reply_markup=reply_markup
    )
    return MATTER_QUANTITY

async def matter_quantity_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    matter_id = context.user_data["matter_id"]
    try:
        quantity = int(text)
        if quantity <= 0:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Количество должно быть больше 0!", reply_markup=reply_markup)
            return MATTER_QUANTITY
    except ValueError:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, введите число!", reply_markup=reply_markup)
        return MATTER_QUANTITY

    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    farm = MATTER_FARMS[matter_id]
    total_price = farm["price"] * quantity
    if user_data["balance"] < total_price:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ Недостаточно средств! Вам нужно ещё {format_number(total_price - user_data['balance'])} монет",
            reply_markup=reply_markup
        )
        return MATTER_QUANTITY

    user_data["balance"] -= total_price
    if matter_id in user_data["matter_farms"]:
        user_data["matter_farms"][matter_id] += quantity
    else:
        user_data["matter_farms"][matter_id] = quantity
    data[user_id] = user_data
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Вы успешно купили {quantity} {farm['name']} за {format_number(total_price)} монет!\n"
        f"💰 Ваш баланс: {format_number(user_data['balance'])}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def sell_matter_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return ConversationHandler.END
    user_data = ensure_user_data(data[user_id])
    if user_data["matter"] <= 0:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("У вас нет материи для продажи!", reply_markup=reply_markup)
        return ConversationHandler.END
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"💎 У вас есть {user_data['matter']:.2f} материи\n"
        f"💰 Курс: 1 материя = {format_number(MATTER_PRICE)} монет\n"
        f"Введите количество материи для продажи (или нажмите '🏠 Главное меню' для отмены):",
        reply_markup=reply_markup
    )
    return SELL_MATTER

async def sell_matter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    try:
        amount = float(text)
        if amount <= 0:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Количество должно быть больше 0!", reply_markup=reply_markup)
            return SELL_MATTER
    except ValueError:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, введите число!", reply_markup=reply_markup)
        return SELL_MATTER

    if user_data["matter"] < amount:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ У вас недостаточно материи! Доступно: {user_data['matter']:.2f}",
            reply_markup=reply_markup
        )
        return SELL_MATTER

    total_price = int(amount * MATTER_PRICE)
    user_data["matter"] -= amount
    user_data["balance"] += total_price
    if user_data["balance"] > MAX_BALANCE:
        user_data["balance"] = MAX_BALANCE
        limit_msg = "\n⚠️ Достигнут максимальный лимит баланса!"
    else:
        limit_msg = ""
    user_data["matter_sold"] = user_data.get("matter_sold", 0) + amount
    user_data["daily_quests"]["matter_sold"] = min(DAILY_QUESTS[3]["target"], user_data["daily_quests"]["matter_sold"] + amount)
    data[user_id] = user_data
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Вы продали {amount:.2f} материи за {format_number(total_price)} монет!{limit_msg}\n"
        f"💰 Ваш баланс: {format_number(user_data['balance'])}\n"
        f"💎 Осталось материи: {user_data['matter']:.2f}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def clans_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    clans_data = load_clans_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return
    user_data = ensure_user_data(data[user_id])
    if user_data["clan_id"]:
        # Пользователь уже в клане
        clan_id = user_data["clan_id"]
        clan = clans_data.get(clan_id)
        if clan:
            keyboard = [
                ["👥 Инфо о клане", "📊 Топ кланов"],
                ["💹 Внести вклад", "🏠 Главное меню"]
            ]
            if clan["owner_id"] == user_id:
                keyboard.insert(1, ["✏️ Переименовать клан"])
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                f"👥 Вы состоите в клане: {clan['name']} (ID: {clan_id})\n"
                f"👑 Создатель: {clan['owner_name']}\n"
                f"👥 Участников: {len(clan['members'])}\n"
                f"💹 Общий вклад: {format_number(clan['total_contribution'])}",
                reply_markup=reply_markup
            )
        else:
            user_data["clan_id"] = None
            data[user_id] = user_data
            save_user_data(data)
            await clans_menu(update, context)
    else:
        # Пользователь не в клане
        keyboard = [
            ["🏆 Создать клан", "📊 Топ кланов"],
            ["🔍 Вступить в клан", "🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "👥 Система кланов\n"
            "Вы не состоите в клане. Вы можете:\n"
            f"🏆 Создать свой клан за {format_number(CLAN_CREATE_COST)} монет и {CLAN_CREATE_MATTER} материи\n"
            "🔍 Вступить в существующий клан по ID",
            reply_markup=reply_markup
        )

async def create_clan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return
    user_data = ensure_user_data(data[user_id])
    if user_data["clan_id"]:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Вы уже состоите в клане!", reply_markup=reply_markup)
        return
    if user_data["balance"] < CLAN_CREATE_COST:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ Недостаточно монет! Нужно ещё {format_number(CLAN_CREATE_COST - user_data['balance'])}",
            reply_markup=reply_markup
        )
        return
    if user_data["matter"] < CLAN_CREATE_MATTER:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ Недостаточно материи! Нужно ещё {CLAN_CREATE_MATTER - user_data['matter']:.2f}",
            reply_markup=reply_markup
        )
        return
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"🏆 Создание клана\n"
        f"Для создания клана требуется:\n"
        f"💰 {format_number(CLAN_CREATE_COST)} монет\n"
        f"💎 {CLAN_CREATE_MATTER} материи\n"
        "Введите название вашего клана (или нажмите '🏠 Главное меню' для отмены):",
        reply_markup=reply_markup
    )
    return CLAN_NAME

async def create_clan_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    clan_name = text.strip()
    if len(clan_name) > 20:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Название клана слишком длинное (макс. 20 символов)!", reply_markup=reply_markup)
        return CLAN_NAME
    data = load_user_data()
    clans_data = load_clans_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return ConversationHandler.END
    user_data = ensure_user_data(data[user_id])
    if user_data["clan_id"]:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Вы уже состоите в клане!", reply_markup=reply_markup)
        return ConversationHandler.END
    if user_data["balance"] < CLAN_CREATE_COST:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ Недостаточно монет! Нужно ещё {format_number(CLAN_CREATE_COST - user_data['balance'])}",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    if user_data["matter"] < CLAN_CREATE_MATTER:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ Недостаточно материи! Нужно ещё {CLAN_CREATE_MATTER - user_data['matter']:.2f}",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    # Создаем клан
    clan_id = str(random.randint(100000, 999999))
    while clan_id in clans_data:
        clan_id = str(random.randint(100000, 999999))
    clans_data[clan_id] = {
        "name": clan_name,
        "owner_id": user_id,
        "owner_name": user_data["nickname"],
        "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "members": [user_id],
        "total_contribution": 0,
        "last_activity": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Новое поле
    }

    # Списание ресурсов
    user_data["balance"] -= CLAN_CREATE_COST
    user_data["matter"] -= CLAN_CREATE_MATTER
    user_data["clan_id"] = clan_id
    user_data["clan_contribution"] = CLAN_CREATE_COST // 100  # Начальный вклад
    clans_data[clan_id]["total_contribution"] += user_data["clan_contribution"]
    data[user_id] = user_data
    save_user_data(data)
    save_clans_data(clans_data)
    keyboard = [
        ["👥 Инфо о клане", "📊 Топ кланов"],
        ["💹 Внести вклад", "🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Клан '{clan_name}' успешно создан!\n"
        f"🆔 ID вашего клана: {clan_id}\n"
        f"👥 Теперь вы можете приглашать других игроков в свой клан, сообщив им этот ID",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def join_clan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🔍 Вступление в клан\n"
        "Введите ID клана, в который хотите вступить (или нажмите '🏠 Главное меню' для отмены):",
        reply_markup=reply_markup
    )
    return CLAN_JOIN

async def join_clan_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    clan_id = text.strip()
    data = load_user_data()
    clans_data = load_clans_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return ConversationHandler.END
    user_data = ensure_user_data(data[user_id])
    if user_data["clan_id"]:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Вы уже состоите в клане!", reply_markup=reply_markup)
        return ConversationHandler.END
    if clan_id not in clans_data:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Клан с таким ID не найден!", reply_markup=reply_markup)
        return CLAN_JOIN

    clan = clans_data[clan_id]
    clan["members"].append(user_id)
    user_data["clan_id"] = clan_id
    user_data["clan_contribution"] = 0
    update_clan_activity(clan_id, clans_data)  # Обновляем активность
    data[user_id] = user_data
    save_user_data(data)
    save_clans_data(clans_data)
    keyboard = [
        ["👥 Инфо о клане", "📊 Топ кланов"],
        ["💹 Внести вклад", "🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Вы вступили в клан '{clan['name']}'!\n"
        f"👑 Создатель: {clan['owner_name']}\n"
        f"👥 Участников: {len(clan['members'])}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def clan_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    clans_data = load_clans_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return
    user_data = ensure_user_data(data[user_id])
    if not user_data["clan_id"]:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Вы не состоите в клане!", reply_markup=reply_markup)
        return
    clan_id = user_data["clan_id"]
    if clan_id not in clans_data:
        user_data["clan_id"] = None
        data[user_id] = user_data
        save_user_data(data)
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Ваш клан был расформирован!", reply_markup=reply_markup)
        return
    clan = clans_data[clan_id]
    # Получаем топ 5 участников по вкладу
    members_data = []
    for member_id in clan["members"]:
        if member_id in data:
            member_data = data[member_id]
            members_data.append({
                "nickname": member_data["nickname"],
                "contribution": member_data.get("clan_contribution", 0)
            })
    members_data.sort(key=lambda x: x["contribution"], reverse=True)
    top_members_text = "\n".join(
        f"{idx+1}. {member['nickname']} - {format_number(member['contribution'])} монет"
        for idx, member in enumerate(members_data[:5])
    )
    activity = clan.get("last_activity", "Неизвестно")
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"👥 Информация о клане {clan['name']} (ID: {clan_id})\n"
        f"👑 Создатель: {clan['owner_name']}\n"
        f"📅 Дата создания: {clan['created_date']}\n"
        f"👥 Участников: {len(clan['members'])}\n"
        f"📈 Последняя активность: {activity}\n"
        f"💹 Общий вклад: {format_number(clan['total_contribution'])}\n"
        f"🏆 Топ участников по вкладу:\n{top_members_text}\n"
        f"Ваш вклад: {format_number(user_data['clan_contribution'])} монет",
        reply_markup=reply_markup
    )

async def contribute_to_clan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    clans_data = load_clans_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return
    user_data = ensure_user_data(data[user_id])
    if not user_data["clan_id"]:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Вы не состоите в клане!", reply_markup=reply_markup)
        return
    clan_id = user_data["clan_id"]
    if clan_id not in clans_data:
        user_data["clan_id"] = None
        data[user_id] = user_data
        save_user_data(data)
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Ваш клан был расформирован!", reply_markup=reply_markup)
        return
    keyboard = [
        ["10,000", "100,000", "1,000,000"],
        ["10,000,000", "100,000,000", "🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "💹 Внесение вклада в клан\n"
        "Введите сумму, которую хотите внести в клан (или выберите из предложенных):\n"
        "Каждый внесённый рубль увеличивает ваш личный вклад на 1",
        reply_markup=reply_markup
    )
    # Устанавливаем флаг, что пользователь вносит вклад
    context.user_data['contributing'] = True
    return CONTRIBUTE_AMOUNT

async def process_contribution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    amount_text = text.replace(".", "").replace(",", "")
    try:
        amount = int(amount_text)
    except ValueError:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, введите корректную сумму!", reply_markup=reply_markup)
        return CONTRIBUTE_AMOUNT

    data = load_user_data()
    clans_data = load_clans_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return ConversationHandler.END
    user_data = ensure_user_data(data[user_id])
    if not user_data["clan_id"]:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Вы не состоите в клане!", reply_markup=reply_markup)
        return ConversationHandler.END
    clan_id = user_data["clan_id"]
    if clan_id not in clans_data:
        user_data["clan_id"] = None
        data[user_id] = user_data
        save_user_data(data)
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Ваш клан был расформирован!", reply_markup=reply_markup)
        return ConversationHandler.END
    if amount <= 0:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Сумма должна быть больше 0!", reply_markup=reply_markup)
        return CONTRIBUTE_AMOUNT
    if user_data["balance"] < amount:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ Недостаточно средств! Вам нужно ещё {format_number(amount - user_data['balance'])} монет",
            reply_markup=reply_markup
        )
        return CONTRIBUTE_AMOUNT

    user_data["balance"] -= amount
    user_data["clan_contribution"] += amount
    clans_data[clan_id]["total_contribution"] += amount
    user_data["clan_contributed"] = user_data.get("clan_contributed", 0) + amount
    user_data["daily_quests"]["clan_contributed"] = min(DAILY_QUESTS[4]["target"], user_data["daily_quests"]["clan_contributed"] + amount)
    update_clan_activity(clan_id, clans_data)  # Обновляем активность
    save_user_data(data)
    save_clans_data(clans_data)

    # Убираем флаг внесения вклада
    if 'contributing' in context.user_data:
        del context.user_data['contributing']
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Вы внесли вклад в размере {format_number(amount)} монет в клан {clans_data[clan_id]['name']}!\n"
        f"📈 Последняя активность: {clans_data[clan_id]['last_activity']}\n"
        f"💹 Ваш общий вклад: {format_number(user_data['clan_contribution'])} монет\n"
        f"💰 Ваш баланс: {format_number(user_data['balance'])}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def rename_clan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    clans_data = load_clans_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return
    user_data = ensure_user_data(data[user_id])
    if not user_data["clan_id"]:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Вы не состоите в клане!", reply_markup=reply_markup)
        return
    clan_id = user_data["clan_id"]
    if clan_id not in clans_data:
        user_data["clan_id"] = None
        data[user_id] = user_data
        save_user_data(data)
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Ваш клан был расформирован!", reply_markup=reply_markup)
        return
    if clans_data[clan_id]["owner_id"] != user_id:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Только создатель клана может его переименовать!", reply_markup=reply_markup)
        return
    if user_data["balance"] < CLAN_RENAME_COST:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ Недостаточно средств для переименования клана! Нужно {format_number(CLAN_RENAME_COST)} монет",
            reply_markup=reply_markup
        )
        return
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✏️ Переименование клана\n"
        f"Текущее название: {clans_data[clan_id]['name']}\n"
        f"Стоимость: {format_number(CLAN_RENAME_COST)} монет\n"
        "Введите новое название клана (или нажмите '🏠 Главное меню' для отмены):",
        reply_markup=reply_markup
    )
    return CLAN_NEW_NAME

async def rename_clan_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    new_name = text.strip()
    if len(new_name) > 20:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Название клана слишком длинное (макс. 20 символов)!", reply_markup=reply_markup)
        return CLAN_NEW_NAME
    data = load_user_data()
    clans_data = load_clans_data()
    if user_id not in data:
        await update.message.reply_text("Сначала нажмите /start")
        return ConversationHandler.END
    user_data = ensure_user_data(data[user_id])
    if not user_data["clan_id"]:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Вы не состоите в клане!", reply_markup=reply_markup)
        return ConversationHandler.END
    clan_id = user_data["clan_id"]
    if clan_id not in clans_data:
        user_data["clan_id"] = None
        data[user_id] = user_data
        save_user_data(data)
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Ваш клан был расформирован!", reply_markup=reply_markup)
        return ConversationHandler.END
    if clans_data[clan_id]["owner_id"] != user_id:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Только создатель клана может его переименовать!", reply_markup=reply_markup)
        return ConversationHandler.END
    if user_data["balance"] < CLAN_RENAME_COST:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ Недостаточно средств для переименования клана! Нужно {format_number(CLAN_RENAME_COST)} монет",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    old_name = clans_data[clan_id]["name"]
    user_data["balance"] -= CLAN_RENAME_COST
    clans_data[clan_id]["name"] = new_name
    update_clan_activity(clan_id, clans_data)  # Обновляем активность
    save_user_data(data)
    save_clans_data(clans_data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Вы успешно переименовали клан с '{old_name}' на '{new_name}'!\n"
        f"📈 Последняя активность: {clans_data[clan_id]['last_activity']}\n"
        f"💰 Ваш баланс: {format_number(user_data['balance'])}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# === НОВЫЕ ФУНКЦИИ ===
async def transfer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    now = datetime.now()
    last_transfer = user_data.get("last_transfer")
    if last_transfer:
        try:
            last = datetime.strptime(last_transfer, "%Y-%m-%d %H:%M:%S")
            if (now - last) < timedelta(hours=1):
                next_transfer = last + timedelta(hours=1)
                keyboard = [
                    ["🏠 Главное меню"]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                await update.message.reply_text(
                    f"⏰ Переводы можно делать раз в 1 час!\n"
                    f"Следующий перевод можно будет сделать: {next_transfer.strftime('%Y-%m-%d %H:%M:%S')}",
                    reply_markup=reply_markup
                )
                return
        except ValueError:
            pass
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Введите ID пользователя, которому хотите перевести (или нажмите '🏠 Главное меню' для отмены):", reply_markup=reply_markup)
    return TRANSFER_TARGET

async def transfer_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    target_id = text.strip()
    context.user_data["target_id"] = target_id
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Введите сумму перевода (или нажмите '🏠 Главное меню' для отмены):", reply_markup=reply_markup)
    return TRANSFER_AMOUNT

async def transfer_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    target_id = context.user_data.get("target_id")
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    amount_text = text.replace(".", "").replace(",", "")
    try:
        amount = int(amount_text)
        if amount < 1000:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Минимальная сумма перевода — 1000 монет!", reply_markup=reply_markup)
            return TRANSFER_AMOUNT
    except ValueError:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, введите корректную сумму!", reply_markup=reply_markup)
        return TRANSFER_AMOUNT

    data = load_user_data()
    if user_id not in data or target_id not in data:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Один из пользователей не найден!", reply_markup=reply_markup)
        return ConversationHandler.END
    sender_data = ensure_user_data(data[user_id])
    target_data = ensure_user_data(data[target_id])
    if sender_data["balance"] < amount:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Недостаточно средств для перевода!", reply_markup=reply_markup)
        return TRANSFER_AMOUNT

    sender_data["balance"] -= amount
    target_data["balance"] += amount
    if target_data["balance"] > MAX_BALANCE:
        target_data["balance"] = MAX_BALANCE
    now = datetime.now()
    sender_data["last_transfer"] = now.strftime("%Y-%m-%d %H:%M:%S")
    data[user_id] = sender_data
    data[target_id] = target_data
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Переведено {format_number(amount)} монет пользователю {target_data['nickname']}!",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def daily_quests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    user_data = reset_daily_quests_if_needed(user_data)
    # Проверим, выполнены ли все задания
    all_completed = all(
        user_data["daily_quests"][q["key"]] >= q["target"] for q in DAILY_QUESTS
    )
    quests_text = "📊 Ежедневные задания:\n"
    for idx, q in enumerate(DAILY_QUESTS):
        current = user_data["daily_quests"][q["key"]]
        target = q["target"]
        status = "✅" if current >= target else "⏳"
        quests_text += f"{status} {q['name']}: {current}/{target}\n"
    # Если все задания выполнены — даем награду
    reward_given = False
    if all_completed:
        reward = 50_000_000  # 50 млн монет за выполнение всех заданий
        user_data["balance"] += reward
        if user_data["balance"] > MAX_BALANCE:
            user_data["balance"] = MAX_BALANCE
        reward_msg = f"\n🎉 Поздравляем! Вы выполнили все задания и получили награду: {format_number(reward)} монет!"
        # Сбросим задания принудительно, чтобы не дать получить награду дважды
        user_data["daily_quests"] = {q["key"]: 0 for q in DAILY_QUESTS}
        reward_given = True
    else:
        reward_msg = ""
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(quests_text + reward_msg, reply_markup=reply_markup)
    if reward_given:
        data[user_id] = user_data
        save_user_data(data)

# === УЛУЧШЕНИЯ ===
async def upgrade_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🏢 Улучшить бизнес", "🔬 Улучшить ферму"],
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("📈 Меню улучшений", reply_markup=reply_markup)

async def upgrade_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    businesses_text = "📈 Выберите бизнес для улучшения:\n"
    for biz_id, quantity in user_data.get("businesses", {}).items():
        if biz_id in BUSINESSES:
            biz = BUSINESSES[biz_id]
            level = user_data.get("business_upgrades", {}).get(biz_id, 0)
            cost = 500_000_000 * (level + 1)
            businesses_text += f"{biz['emoji']} {biz['name']} (уровень {level}) - {format_number(cost)} монет\n"
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(businesses_text + "\nВведите ID бизнеса (например, '1') или нажмите '🏠 Главное меню' для отмены:", reply_markup=reply_markup)
    return BUSINESS_ID

async def upgrade_business_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    user_id = str(update.message.from_user.id)
    biz_id = text.strip()
    if biz_id not in BUSINESSES:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Неверный ID бизнеса. Попробуйте снова.", reply_markup=reply_markup)
        return BUSINESS_ID
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    if biz_id not in user_data.get("businesses", {}):
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ У вас нет этого бизнеса.", reply_markup=reply_markup)
        return BUSINESS_ID
    level = user_data.get("business_upgrades", {}).get(biz_id, 0)
    cost = 500_000_000 * (level + 1)
    if user_data["balance"] < cost:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"❌ Недостаточно средств. Нужно ещё {format_number(cost - user_data['balance'])} монет.", reply_markup=reply_markup)
        return BUSINESS_ID

    user_data["balance"] -= cost
    upgrades = user_data.get("business_upgrades", {})
    upgrades[biz_id] = level + 1
    user_data["business_upgrades"] = upgrades
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Улучшено! {BUSINESSES[biz_id]['name']} теперь уровня {level + 1}.\n"
        f"💰 Ваш баланс: {format_number(user_data['balance'])}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def upgrade_farm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    farms_text = "📈 Выберите ферму для улучшения:\n"
    for farm_id, quantity in user_data.get("matter_farms", {}).items():
        if farm_id in MATTER_FARMS:
            farm = MATTER_FARMS[farm_id]
            level = user_data.get("farm_upgrades", {}).get(farm_id, 0)
            cost = 500_000_000_000 * (level + 1)
            farms_text += f"{farm['emoji']} {farm['name']} (уровень {level}) - {format_number(cost)} монет\n"
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(farms_text + "\nВведите ID фермы (например, '1') или нажмите '🏠 Главное меню' для отмены:", reply_markup=reply_markup)
    return MATTER_ID

async def upgrade_farm_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    user_id = str(update.message.from_user.id)
    farm_id = text.strip()
    if farm_id not in MATTER_FARMS:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Неверный ID фермы. Попробуйте снова.", reply_markup=reply_markup)
        return MATTER_ID
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    if farm_id not in user_data.get("matter_farms", {}):
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ У вас нет этой фермы.", reply_markup=reply_markup)
        return MATTER_ID
    level = user_data.get("farm_upgrades", {}).get(farm_id, 0)
    cost = 500_000_000_000 * (level + 1)
    if user_data["balance"] < cost:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"❌ Недостаточно средств. Нужно ещё {format_number(cost - user_data['balance'])} монет.", reply_markup=reply_markup)
        return MATTER_ID

    user_data["balance"] -= cost
    upgrades = user_data.get("farm_upgrades", {})
    upgrades[farm_id] = level + 1
    user_data["farm_upgrades"] = upgrades
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Улучшено! {MATTER_FARMS[farm_id]['name']} теперь уровня {level + 1}.\n"
        f"💰 Ваш баланс: {format_number(user_data['balance'])}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# === БАНК ===
async def bank_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    collect_bank_interest(user_data)
    save_user_data(data)
    bank_text = (
        f"🏦 Информация о банке:\n"
        f"💰 В банке: {format_number(user_data['bank_balance'])} монет\n"
        f"📈 Процент: +1%/час (до 1000%)"
    )
    keyboard = [
        ["💰 Положить", "💸 Снять"],
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(bank_text, reply_markup=reply_markup)

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Введите сумму для вклада в банк (или нажмите '🏠 Главное меню' для отмены):", reply_markup=reply_markup)
    return DEPOSIT_AMOUNT

async def deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    amount_text = text.replace(".", "").replace(",", "")
    try:
        amount = int(amount_text)
        if amount <= 0:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Сумма должна быть больше 0!", reply_markup=reply_markup)
            return DEPOSIT_AMOUNT
    except ValueError:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, введите число!", reply_markup=reply_markup)
        return DEPOSIT_AMOUNT

    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    if user_data["balance"] < amount:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Недостаточно средств на балансе!", reply_markup=reply_markup)
        return DEPOSIT_AMOUNT

    user_data["balance"] -= amount
    user_data["bank_balance"] += amount
    user_data["last_bank_collect"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Положено в банк: {format_number(amount)} монет!\n"
        f"💰 Ваш баланс: {format_number(user_data['balance'])}\n"
        f"🏦 В банке: {format_number(user_data['bank_balance'])} монет",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Введите сумму для снятия из банка (или нажмите '🏠 Главное меню' для отмены):", reply_markup=reply_markup)
    return WITHDRAW_AMOUNT

async def withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    amount_text = text.replace(".", "").replace(",", "")
    try:
        amount = int(amount_text)
        if amount <= 0:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Сумма должна быть больше 0!", reply_markup=reply_markup)
            return WITHDRAW_AMOUNT
    except ValueError:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, введите число!", reply_markup=reply_markup)
        return WITHDRAW_AMOUNT

    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    if user_data["bank_balance"] < amount:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Недостаточно средств в банке!", reply_markup=reply_markup)
        return WITHDRAW_AMOUNT

    user_data["bank_balance"] -= amount
    user_data["balance"] += amount
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Снято из банка: {format_number(amount)} монет!\n"
        f"💰 Ваш баланс: {format_number(user_data['balance'])}\n"
        f"🏦 В банке: {format_number(user_data['bank_balance'])} монет",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# === РУЛЕТКА ===
async def roulette_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("🎯 Добро пожаловать в рулетку!\nВведите число от 1 до 10 (или нажмите '🏠 Главное меню' для отмены):", reply_markup=reply_markup)
    return ROULETTE_BET

async def roulette_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    try:
        bet_num = int(text)
        if bet_num < 1 or bet_num > 10:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Число должно быть от 1 до 10!", reply_markup=reply_markup)
            return ROULETTE_BET
    except ValueError:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, введите число!", reply_markup=reply_markup)
        return ROULETTE_BET

    win_num = random.randint(1, 10)
    if bet_num == win_num:
        win_amount = 100_000  # фиксированная награда за выигрыш
        user_data["balance"] += win_amount
        result_text = f"🎉 Вы выиграли! Выпало число {win_num}. Награда: {format_number(win_amount)} монет!"
    else:
        result_text = f"❌ Вы проиграли. Выпало число {win_num}."

    if user_data["balance"] > MAX_BALANCE:
        user_data["balance"] = MAX_BALANCE
    data[user_id] = user_data
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"{result_text}\n💰 Ваш баланс: {format_number(user_data['balance'])}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# === ИНВЕСТИЦИИ ===
async def invest_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("💼 Инвестиции\nВведите сумму для вложения (возврат через 24 часа с 70% шансом x2) (или нажмите '🏠 Главное меню' для отмены):", reply_markup=reply_markup)
    return INVEST_AMOUNT

async def invest_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    try:
        amount = int(text.replace(".", "").replace(",", ""))
        if amount <= 0:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Сумма должна быть больше 0!", reply_markup=reply_markup)
            return INVEST_AMOUNT
    except ValueError:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, введите число!", reply_markup=reply_markup)
        return INVEST_AMOUNT

    if user_data["balance"] < amount:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Недостаточно средств!", reply_markup=reply_markup)
        return INVEST_AMOUNT

    user_data["balance"] -= amount
    now = datetime.now()
    end_time = now + timedelta(hours=24)
    user_data["investments"].append({
        "amount": amount,
        "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S")
    })
    data[user_id] = user_data
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Вы вложили {format_number(amount)} монет. Возврат через 24 часа.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def check_investments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    now = datetime.now()
    completed = []
    for inv in user_data.get("investments", []):
        end_time = datetime.strptime(inv["end_time"], "%Y-%m-%d %H:%M:%S")
        if now >= end_time:
            completed.append(inv)
    if not completed:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Нет завершённых инвестиций.", reply_markup=reply_markup)
        return
    total_reward = 0
    for inv in completed:
        user_data["investments"].remove(inv)
        if random.random() < 0.7:  # 70% шанс успеха
            reward = inv["amount"] * 2
            user_data["balance"] += reward
            total_reward += reward
        # 30% шанс — потеря
    if user_data["balance"] > MAX_BALANCE:
        user_data["balance"] = MAX_BALANCE
    save_user_data(data)
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"💼 Инвестиции завершены!\n"
        f"Вы получили: {format_number(total_reward)} монет (или потеряли всё, если не повезло).\n"
        f"💰 Ваш баланс: {format_number(user_data['balance'])}",
        reply_markup=reply_markup
    )

# === АЧИВКИ ===
async def achievements_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    ach_list = user_data.get("achievements", [])
    if not ach_list:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ У вас пока нет ачивок.", reply_markup=reply_markup)
        return
    ach_text = "🏆 Ваши ачивки:\n" + "\n".join([f"- {a}" for a in ach_list])
    ach_text += "\nВведите название ачивки, чтобы установить её как отображаемую в профиле (или нажмите '🏠 Главное меню' для отмены):"
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(ach_text, reply_markup=reply_markup)
    return SELECT_ACHIEVEMENT

async def select_achievement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 Главное меню":
        await start(update, context)
        return ConversationHandler.END
    user_id = str(update.message.from_user.id)
    ach_name = text.strip()
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    if ach_name not in user_data.get("achievements", []):
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ У вас нет такой ачивки. Попробуйте снова.", reply_markup=reply_markup)
        return SELECT_ACHIEVEMENT
    user_data["selected_achievement"] = ach_name
    save_user_data(data)
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Установлена ачивка: {ach_name}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# === КВЕСТЫ ===
async def quests_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    user_data = ensure_user_data(data.get(user_id, {}))
    # Проверяем выполненные квесты
    completed = check_quests(user_data)
    if completed:
        save_user_data(data)
    active_quests = user_data.get("current_quests", [])
    if not active_quests:
        # Выдаем новый квест, если нет активных
        available = [q for q in QUESTS if q not in user_data.get("quests_completed", [])]
        if available:
            new_quest = random.choice(available)
            user_data["current_quests"].append(new_quest)
            save_user_data(data)
            active_quests = [new_quest]
    if not active_quests:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Нет доступных квестов.", reply_markup=reply_markup)
        return
    quest_text = "📋 Активные квесты:\n"
    for idx, q in enumerate(active_quests):
        quest_text += f"{idx+1}. {q['name']}\n"
    keyboard = [
        ["💰 Профиль", "🎰 Казино"],
        ["🎁 Бонус", "🏆 Топ игроков"],
        ["📝 Сменить ник", "🏢 Бизнесы"],
        ["🔬 Фермы материи", "💰 Собрать доход"],
        ["💎 Продать материю", "👥 Кланы"],
        ["📤 Перевести", "📊 Ежедневные задания"],
        ["🏦 Банк", "📈 Улучшения"],
        ["🎯 Рулетка", "💼 Инвестиции"],
        ["🏆 Ачивки", "📋 Квесты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(quest_text, reply_markup=reply_markup)

# === СТАТИСТИКА ===
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id != str(ADMIN_ID):
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Эта команда только для администратора!", reply_markup=reply_markup)
        return
    data = load_user_data()
    clans_data = load_clans_data()
    total_players = len(data)
    total_balance = sum(d.get("balance", 0) for d in data.values())
    total_matter = sum(d.get("matter", 0) for d in data.values())
    total_clans = len(clans_data)
    stats_text = (
        f"📊 Статистика сервера:\n"
        f"👥 Игроков: {total_players}\n"
        f"💰 Общий баланс: {format_number(total_balance)} монет\n"
        f"💎 Общая материя: {total_matter:.2f}\n"
        f"👥 Кланов: {total_clans}"
    )
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(stats_text, reply_markup=reply_markup)

# === /КОНЕЦ НОВЫХ ФУНКЦИЙ ===
async def cancel_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Убираем флаг внесения вклада, если он был
    if 'contributing' in context.user_data:
        del context.user_data['contributing']
    await start(update, context)
    return ConversationHandler.END

async def give_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id != str(ADMIN_ID):
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Эта команда только для администратора!", reply_markup=reply_markup)
        return
    try:
        args = context.args
        if len(args) != 2:
            raise ValueError
        target_id = args[0]
        amount = int(args[1].replace(".", "").replace(",", ""))
        if amount <= 0:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Сумма должна быть больше 0!", reply_markup=reply_markup)
            return
        data = load_user_data()
        if target_id not in data:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Пользователь не найден!", reply_markup=reply_markup)
            return
        data[target_id] = ensure_user_data(data[target_id])
        data[target_id]["balance"] += amount
        if data[target_id]["balance"] > MAX_BALANCE:
            data[target_id]["balance"] = MAX_BALANCE
        save_user_data(data)
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"✅ Выдали {format_number(amount)} монет пользователю {data[target_id]['nickname']}\n"
            f"💰 Его баланс: {format_number(data[target_id]['balance'])}",
            reply_markup=reply_markup
        )
    except (ValueError, IndexError):
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Использование: /give <user_id> <amount>", reply_markup=reply_markup)

async def give_matter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id != str(ADMIN_ID):
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Эта команда только для администратора!", reply_markup=reply_markup)
        return
    try:
        args = context.args
        if len(args) != 2:
            raise ValueError
        target_id = args[0]
        amount = float(args[1])
        if amount <= 0:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Количество должно быть больше 0!", reply_markup=reply_markup)
            return
        data = load_user_data()
        if target_id not in data:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Пользователь не найден!", reply_markup=reply_markup)
            return
        data[target_id] = ensure_user_data(data[target_id])
        data[target_id]["matter"] += amount
        save_user_data(data)
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"✅ Выдали {amount:.2f} материи пользователю {data[target_id]['nickname']}\n"
            f"💎 Его материя: {data[target_id]['matter']:.2f}",
            reply_markup=reply_markup
        )
    except (ValueError, IndexError):
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Использование: /givematter <user_id> <amount>", reply_markup=reply_markup)

async def show_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id != str(ADMIN_ID):
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Эта команда только для администратора!", reply_markup=reply_markup)
        return
    data = load_user_data()
    if not data:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Нет зарегистрированных игроков", reply_markup=reply_markup)
        return
    players_text = "Список игроков:\n"
    for uid, user_data in data.items():
        players_text += (
            f"👤 {user_data.get('nickname', 'Unknown')} (ID: {uid})\n"
            f"💰 Баланс: {format_number(user_data.get('balance', 0))}\n"
            f"💎 Материя: {user_data.get('matter', 0):.2f}\n"
            f"📅 Регистрация: {user_data.get('register_date', 'Unknown')}\n"
        )
    keyboard = [
        ["🏠 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(players_text[:4000], reply_markup=reply_markup)  # Ограничение Telegram на длину сообщения

async def reset_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id != str(ADMIN_ID):
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ Эта команда только для администратора!", reply_markup=reply_markup)
        return
    try:
        target_id = context.args[0]
        data = load_user_data()
        if target_id not in data:
            keyboard = [
                ["🏠 Главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Пользователь не найден!", reply_markup=reply_markup)
            return
        old_nick = data[target_id].get("nickname", "Unknown")
        data[target_id] = ensure_user_data({})
        data[target_id]["nickname"] = old_nick
        save_user_data(data)
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"✅ Данные пользователя {old_nick} (ID: {target_id}) сброшены!\n"
            f"💰 Новый баланс: {format_number(data[target_id]['balance'])}",
            reply_markup=reply_markup
        )
    except IndexError:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Использование: /reset <user_id>", reply_markup=reply_markup)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Ошибка: {context.error}")
    if update.message:
        keyboard = [
            ["🏠 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.", reply_markup=reply_markup)

def main():
    app = Application.builder().token(TOKEN).build()

    buy_business_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏢 Бизнесы$"), buy_business_start)],
        states={
            BUSINESS_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, business_id_received)],
            BUSINESS_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, business_quantity_received)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    buy_matter_farm_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔬 Фермы материи$"), buy_matter_farm_start)],
        states={
            MATTER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, matter_id_received)],
            MATTER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, matter_quantity_received)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    sell_matter_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💎 Продать материю$"), sell_matter_start)],
        states={
            SELL_MATTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_matter_quantity)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    nickname_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Сменить ник$"), change_nickname)],
        states={
            "WAITING_NICKNAME": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_nickname)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    # Обработчики для кланов
    clan_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^👥 Кланы$"), clans_menu)],
        states={
            CLAN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_clan_name)],
            CLAN_JOIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_clan_id)],
            CLAN_NEW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, rename_clan_finish)],
            CONTRIBUTE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_contribution)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    # Обработчик для создания клана
    create_clan_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏆 Создать клан$"), create_clan_start)],
        states={
            CLAN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_clan_name)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    # Обработчик для переименования клана
    rename_clan_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✏️ Переименовать клан$"), rename_clan_start)],
        states={
            CLAN_NEW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, rename_clan_finish)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    # Обработчик для вступления в клан
    join_clan_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍 Вступить в клан$"), join_clan_start)],
        states={
            CLAN_JOIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_clan_id)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    # Обработчик для внесения вклада
    contribute_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💹 Внести вклад$"), contribute_to_clan)],
        states={
            CONTRIBUTE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_contribution)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    # === НОВЫЙ ConversationHandler для перевода ===
    transfer_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📤 Перевести$"), transfer_start)],
        states={
            TRANSFER_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_target)],
            TRANSFER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_amount)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    # === УЛУЧШЕНИЯ ===
    upgrade_business_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏢 Улучшить бизнес$"), upgrade_business)],
        states={
            BUSINESS_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, upgrade_business_id)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    upgrade_farm_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔬 Улучшить ферму$"), upgrade_farm)],
        states={
            MATTER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, upgrade_farm_id)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    # === БАНК ===
    deposit_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Положить$"), deposit_start)],
        states={
            DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    withdraw_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💸 Снять$"), withdraw_start)],
        states={
            WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    # === РУЛЕТКА ===
    roulette_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎯 Рулетка$"), roulette_start)],
        states={
            ROULETTE_BET: [MessageHandler(filters.TEXT & ~filters.COMMAND, roulette_bet)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    # === ИНВЕСТИЦИИ ===
    invest_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💼 Инвестиции$"), invest_start)],
        states={
            INVEST_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, invest_amount)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )
    # === АЧИВКИ ===
    ach_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏆 Ачивки$"), achievements_menu)],
        states={
            SELECT_ACHIEVEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_achievement)]
        },
        fallbacks=[CommandHandler("cancel", cancel_buy)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^💰 Профиль$"), profile))
    app.add_handler(MessageHandler(filters.Regex("^🎰 Казино$"), casino))
    app.add_handler(MessageHandler(filters.Regex("^🎁 Бонус$"), bonus))
    app.add_handler(MessageHandler(filters.Regex("^🏆 Топ игроков$"), top_players))
    app.add_handler(MessageHandler(filters.Regex("^🏆 Топ по балансу$"), top_balance))
    app.add_handler(MessageHandler(filters.Regex("^💎 Топ по материи$"), top_matter))
    app.add_handler(MessageHandler(filters.Regex("^📊 Топ кланов$"), top_clans))
    app.add_handler(nickname_conv)
    app.add_handler(buy_business_conv)
    app.add_handler(buy_matter_farm_conv)
    app.add_handler(sell_matter_conv)
    app.add_handler(clan_conv)
    app.add_handler(create_clan_conv)
    app.add_handler(rename_clan_conv)
    app.add_handler(join_clan_conv)
    app.add_handler(contribute_conv)
    app.add_handler(transfer_conv)  # <-- НОВОЕ
    app.add_handler(upgrade_business_conv)  # <-- НОВОЕ
    app.add_handler(upgrade_farm_conv)  # <-- НОВОЕ
    app.add_handler(deposit_conv)  # <-- НОВОЕ
    app.add_handler(withdraw_conv)  # <-- НОВОЕ
    app.add_handler(roulette_conv)  # <-- НОВОЕ
    app.add_handler(invest_conv)  # <-- НОВОЕ
    app.add_handler(ach_conv)  # <-- НОВОЕ
    app.add_handler(MessageHandler(filters.Regex("^💰 Собрать доход$"), collect_income))
    app.add_handler(MessageHandler(filters.Regex("^🏠 Главное меню$"), start))
    app.add_handler(MessageHandler(filters.Regex(r"^[\d.,]+$"), process_bet))
    app.add_handler(MessageHandler(filters.Regex("^👥 Инфо о клане$"), clan_info))
    app.add_handler(MessageHandler(filters.Regex("^📊 Ежедневные задания$"), daily_quests))  # <-- НОВОЕ
    app.add_handler(MessageHandler(filters.Regex("^📈 Улучшения$"), upgrade_menu))  # <-- НОВОЕ
    app.add_handler(MessageHandler(filters.Regex("^🏦 Банк$"), bank_menu))  # <-- НОВОЕ
    app.add_handler(MessageHandler(filters.Regex("^📋 Квесты$"), quests_menu))  # <-- НОВОЕ
    app.add_handler(CommandHandler("stats", stats))  # <-- НОВОЕ
    app.add_handler(CommandHandler("check_investments", check_investments))  # <-- НОВОЕ
    app.add_handler(CommandHandler("give", give_money))
    app.add_handler(CommandHandler("givematter", give_matter))
    app.add_handler(CommandHandler("players", show_players))
    app.add_handler(CommandHandler("reset", reset_player))
    if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ BOT_TOKEN не установлен в переменных окружения!")
        exit(1)

    PORT = int(os.environ.get("PORT", 8000))

    print(f"✅ Запуск бота через webhook на порту {PORT}...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://my-telegram-bot5-cg6d.onrender.com/{TOKEN}",
        allowed_updates=Update.ALL_UPDATE_TYPES,
        drop_pending_updates=True
    )
