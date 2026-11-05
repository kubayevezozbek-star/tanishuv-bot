import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import database as db
from config import ADMIN_ID, TARIFS
from keyboards import get_main_menu_keyboard

router = Router()

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirm = State()

def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Barchaga xabar yuborish (Reklama)", callback_data="admin_broadcast_start")],
        [InlineKeyboardButton(text="🔄 Statistikani yangilash", callback_data="admin_refresh_stats")]
    ])

# Admin boshqaruv paneli
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        # Oddiy foydalanuvchilarga hech narsa ko'rsatmaymiz
        return

    stats = await db.get_stats()

    text = (
        "👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        "📊 <b>Bot statistikasi:</b>\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total']}</b> ta\n"
        f"👨 Yigitlar: <b>{stats['males']}</b> ta\n"
        f"👩 Qizlar: <b>{stats['females']}</b> ta\n"
        f"⭐ VIP a'zolar: <b>{stats['vip_count']}</b> ta\n"
        f"💬 Hozir suhbatlashayotgan juftliklar: <b>{stats['active_chats']}</b> ta\n"
        f"⏳ Qidiruv navbatidagilar: <b>{stats['searching_count']}</b> ta\n\n"
        "Quyidagi tugmalar orqali xabar tarqatishingiz mumkin:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_refresh_stats")
async def refresh_stats_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer("Statistika yangilandi!")
    stats = await db.get_stats()
    text = (
        "👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        "📊 <b>Bot statistikasi:</b>\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total']}</b> ta\n"
        f"👨 Yigitlar: <b>{stats['males']}</b> ta\n"
        f"👩 Qizlar: <b>{stats['females']}</b> ta\n"
        f"⭐ VIP a'zolar: <b>{stats['vip_count']}</b> ta\n"
        f"💬 Hozir suhbatlashayotgan juftliklar: <b>{stats['active_chats']}</b> ta\n"
        f"⏳ Qidiruv navbatidagilar: <b>{stats['searching_count']}</b> ta\n\n"
        "Quyidagi tugmalar orqali xabar tarqatishingiz mumkin:"
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_keyboard())
    except Exception:
        pass

# 📢 Reklama va xabar tarqatish
@router.message(Command("reklama"))
@router.callback_query(F.data == "admin_broadcast_start")
async def start_broadcast(event: Message | CallbackQuery, state: FSMContext):
    user_id = event.from_user.id
    if user_id != ADMIN_ID:
        return

    if isinstance(event, CallbackQuery):
        await event.answer()
        msg = event.message
    else:
        msg = event

    await state.set_state(BroadcastStates.waiting_for_message)
    await msg.answer(
        "📢 <b>Reklama va xabar tarqatish</b>\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring.\n"
        "<i>(Xabar matn, rasm, video, havola yoki istalgan formatda bo'lishi mumkin)</i>\n\n"
        "Bekor qilish uchun: /cancel",
        parse_mode="HTML"
    )

@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    if message.text in ["/cancel", "/bekor"]:
        await state.clear()
        await message.answer("❌ Xabar tarqatish bekor qilindi.")
        return

    all_users = await db.get_all_user_ids()
    total_count = len(all_users)

    await state.set_state(BroadcastStates.waiting_for_confirm)
    await state.update_data(
        from_chat_id=message.chat.id,
        broadcast_msg_id=message.message_id,
        total_count=total_count
    )

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborilsin", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
        ]
    ])

    await message.reply(
        f"⚠️ <b>Diqqat!</b> Ushbu xabar botning <b>{total_count} ta</b> foydalanuvchisiga yuboriladi.\n\n"
        "Xabarni tarqatishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=ikb
    )

@router.callback_query(BroadcastStates.waiting_for_confirm, F.data == "confirm_broadcast")
async def confirm_broadcast_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()
    from_chat_id = data.get("from_chat_id")
    msg_id = data.get("broadcast_msg_id")
    await state.clear()

    await callback.message.edit_text("⏳ <b>Xabar tarqatish boshlandi...</b>\nIltimos, kuting.", parse_mode="HTML")

    user_ids = await db.get_all_user_ids()
    sent_count = 0
    blocked_count = 0

    for uid in user_ids:
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=from_chat_id,
                message_id=msg_id
            )
            sent_count += 1
            await asyncio.sleep(0.04) # Telegram chekloviga qarshi
        except Exception:
            blocked_count += 1

    report = (
        "✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{len(user_ids)}</b> ta\n"
        f"🟢 Muvaffaqiyatli yetkazildi: <b>{sent_count}</b> ta\n"
        f"🔴 Botni to'xtatganlar/bloklaganlar: <b>{blocked_count}</b> ta"
    )
    await callback.message.answer(report, parse_mode="HTML")

@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Xabar tarqatish bekor qilindi.")

# To'lovni tasdiqlash
@router.callback_query(F.data.startswith("admin_approve_"))
async def approve_payment_handler(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    receipt_id = int(callback.data.split("_")[2])
    receipt = await db.get_receipt(receipt_id)
    if not receipt:
        await callback.answer("Chek topilmadi!", show_alert=True)
        return

    plan_key = receipt.get("plan_key", "3_days")
    days = TARIFS.get(plan_key, TARIFS["3_days"])["days"]

    res = await db.approve_receipt(receipt_id, days)
    if not res:
        await callback.answer("Bu chek allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    user_id, vip_until = res
    await callback.answer("✅ To'lov tasdiqlandi!")
    
    # Admin xabarini yangilash
    new_caption = (
        f"{callback.message.caption or ''}\n\n"
        f"✅ <b>TASDIQLANDI!</b>\n"
        f"Foydalanuvchiga VIP berildi.\nMuddati: <b>{vip_until}</b>"
    )
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchiga xabar yuborish
    try:
        user_msg = (
            "🎉 <b>Tabriklaymiz! Sizning to'lovingiz tasdiqlandi!</b>\n\n"
            f"⭐ <b>VIP maqomingiz faollashtirildi!</b>\n"
            f"⏳ Amal qilish muddati: <b>{vip_until}</b> gacha.\n\n"
            "Endi siz:\n"
            "• Suhbat boshlashda qizlar yoki yigitlarni alohida tanlashingiz;\n"
            "• Suhbatdosh anketasini ko'rishingiz mumkin!"
        )
        await bot.send_message(user_id, user_msg, parse_mode="HTML", reply_markup=get_main_menu_keyboard(is_vip=True))
    except Exception as e:
        print(f"Foydalanuvchiga VIP xabari yetmadi: {e}")

# To'lovni rad etish
@router.callback_query(F.data.startswith("admin_reject_"))
async def reject_payment_handler(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    receipt_id = int(callback.data.split("_")[2])
    user_id = await db.reject_receipt(receipt_id)
    if not user_id:
        await callback.answer("Bu chek allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await callback.answer("❌ To'lov rad etildi.")
    new_caption = (
        f"{callback.message.caption or ''}\n\n"
        f"❌ <b>RAD ETILDI!</b>"
    )
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchiga rad javobini yuborish
    try:
        reject_msg = (
            "⚠️ <b>Afsuski, yuborgan to'lov chekingiz tasdiqlanmadi.</b>\n\n"
            "Agar xatolik yuz bergan bo'lsa, iltimos to'g'ri to'lov chekini qaytadan yuboring."
        )
        await bot.send_message(user_id, reject_msg, parse_mode="HTML")
    except Exception:
        pass
