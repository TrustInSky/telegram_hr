from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from app.keyboards.catalog_keyboard import catalog_keyboard, buy_product_keyboard, format_product_description, buy_or_select_keyboard
from app.services.catalog_service import CatalogService
from app.utils.message_editor import update_message
from app.decorator.injectors import inject_services

catalog_router = Router()


async def _show_catalog(callback: CallbackQuery, catalogservice: CatalogService):
    image = await catalogservice.get_image_by_name("catalog_menu")
    products = await catalogservice.list_products()
    
    keyboard = catalog_keyboard(products)
    welcome_text = "Добро пожаловать в каталог товаров!\nВыберите товар, который хотите приобрести!"
    
    media = InputMediaPhoto(media=image.url, caption=welcome_text, parse_mode="HTML") if image else None
    
    await update_message(
        msg=callback,
        text=welcome_text if not media else None,
        media=media,
        reply_markup=keyboard
    )

@catalog_router.callback_query(F.data == "open_catalog")
@inject_services(CatalogService)
async def open_catalog(callback: CallbackQuery, catalogservice: CatalogService):
    await _show_catalog(callback, catalogservice)

@catalog_router.callback_query(F.data.startswith("product_"))
@inject_services(CatalogService)
async def show_product(callback: CallbackQuery, catalogservice: CatalogService):
    product_id = int(callback.data.split("_")[1])
    product = await catalogservice.get_product(product_id)

    text = format_product_description(product)
    keyboard = buy_or_select_keyboard(product)

    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")

    await update_message(
        msg=callback,
        media=media,
        reply_markup=keyboard
    )

@catalog_router.callback_query(F.data == "back_to_catalog")
@inject_services(CatalogService)
async def back_to_catalog(callback: CallbackQuery, catalogservice: CatalogService):
    # Получаем данные для каталога
    image = await catalogservice.get_image_by_name("catalog_menu")
    products = await catalogservice.list_products()
    
    keyboard = catalog_keyboard(products)
    welcome_text = "Добро пожаловать в каталог товаров!\nВыберите товар, который хотите приобрести!"
    
    # Создаем новое фото с явным удалением старого
    media = InputMediaPhoto(media=image.url, caption=welcome_text, parse_mode="HTML") if image else None
    
    # Удаляем текущее сообщение
    await callback.message.delete()
    
    # Отправляем новое сообщение с каталогом
    if media:
        await callback.bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=media.media,
            caption=media.caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=welcome_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )