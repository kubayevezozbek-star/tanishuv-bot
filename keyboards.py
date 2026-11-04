from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from config import TARIFS

def get_gender_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨 Yigitman"), KeyboardButton(text="👩 Qizman")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_main_menu_keyboard(is_vip: bool = False) -> ReplyKeyboardMarkup:
    vip_badge = "⭐ VIP Obuna (Faol)" if is_vip else "⭐ VIP Obuna"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Suhbat boshlash")],
            [KeyboardButton(text=vip_badge), KeyboardButton(text="👤 Profilim")],
            [KeyboardButton(text="✏️ Ma'lumotlarni tahrirlash")]
        ],
        resize_keyboard=True
    )

def get_search_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Qidiruvni bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_chat_keyboard(is_vip: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="❌ Suhbatni to'xtatish"), KeyboardButton(text="➡️ Keyingisi")]
    ]
    if is_vip:
        buttons.append([KeyboardButton(text="👤 Suhbatdosh anketasi")])
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

def get_vip_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Tasodifiy (Ixtiyoriy)", callback_data="filter_any")],
            [InlineKeyboardButton(text="👧 Faqat qizlar bilan", callback_data="filter_female")],
            [InlineKeyboardButton(text="👦 Faqat yigitlar bilan", callback_data="filter_male")]
        ]
    )

def get_tarifs_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for key, item in TARIFS.items():
        text = f"{item['name']} — {item['price']} so'm"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"buy_{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cancel_payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ To'lovni bekor qilish", callback_data="cancel_payment")]
        ]
    )

def get_admin_receipt_keyboard(receipt_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin_approve_{receipt_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admin_reject_{receipt_id}")
            ]
        ]
    )
