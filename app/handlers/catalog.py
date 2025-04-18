from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from app.keyboards.catalog_keyboard import (
    catalog_keyboard, format_product_description, 
    product_navigation_keyboard, buy_options_keyboard,
    size_selection_keyboard, color_selection_keyboard,
    quantity_selection_keyboard, product_final_options_keyboard,
    after_cart_add_keyboard
)
from app.services.catalog_service import CatalogService
from app.services.cart_service import CartService
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
    # Check if it's a navigation callback or a regular product callback
    callback_parts = callback.data.split("_")
    
    # Handle "product_nav_ID_INDEX" format
    if len(callback_parts) > 2 and callback_parts[1] == "nav":
        product_id = int(callback_parts[2])
        current_index = int(callback_parts[3])
    else:
        # Handle regular "product_ID" format
        product_id = int(callback_parts[1])
        products = await catalogservice.list_products()
        current_index = next((i for i, p in enumerate(products) if p.id == product_id), 0)
    
    product = await catalogservice.get_product(product_id)
    products = await catalogservice.list_products()
    
    text = format_product_description(product)
    keyboard = product_navigation_keyboard(product.id, products, current_index)

    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")

    await update_message(
        msg=callback,
        media=media,
        reply_markup=keyboard
    )
    
@catalog_router.callback_query(F.data.startswith("product_nav_"))
@inject_services(CatalogService)
async def navigate_products(callback: CallbackQuery, catalogservice: CatalogService):
    # Формат: product_nav_ID_INDEX
    parts = callback.data.split("_")
    product_id = int(parts[2])
    current_index = int(parts[3])
    
    # Получаем список всех продуктов
    products = await catalogservice.list_products()
    product = await catalogservice.get_product(product_id)
    
    text = format_product_description(product)
    keyboard = product_navigation_keyboard(product.id, products, current_index)
    
    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")
    
    await update_message(
        msg=callback,
        media=media,
        reply_markup=keyboard
    )

@catalog_router.callback_query(F.data.startswith("buy_product_show_options_"))
@inject_services(CatalogService)
async def show_product_options(callback: CallbackQuery, catalogservice: CatalogService, state: FSMContext):
    """Показываем первый экран с опциями товара"""
    # Получаем данные callback
    callback_data = callback.data
    
    # Извлекаем ID продукта после префикса "buy_product_show_options_"
    prefix = "buy_product_show_options_"
    product_id_str = callback_data[len(prefix):]
    
    try:
        product_id = int(product_id_str)
    except ValueError:
        await callback.answer("Ошибка при получении информации о товаре", show_alert=True)
        return
    
    product = await catalogservice.get_product(product_id)
    
    # Инициализируем или сбрасываем состояние для выбора товара
    await state.update_data(
        product_id=product_id,
        selected_size=None,
        selected_color=None,
        quantity=1
    )
    
    # Если у продукта только один размер/цвет, автоматически выбираем его
    if product.sizes and len(product.sizes.split(',')) == 1:
        await state.update_data(selected_size=product.sizes.split(',')[0].strip())
    
    if hasattr(product, "colors") and product.colors and len(product.colors.split(',')) == 1:
        await state.update_data(selected_color=product.colors.split(',')[0].strip())
    
    text = format_product_description(product)
    keyboard = buy_options_keyboard(product)
    
    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")
    
    await update_message(
        msg=callback,
        media=media,
        reply_markup=keyboard
    )

@catalog_router.callback_query(F.data.startswith("show_sizes_"))
@inject_services(CatalogService)
async def show_sizes_selection(callback: CallbackQuery, catalogservice: CatalogService, state: FSMContext):
    """Показываем экран выбора размера"""
    product_id = int(callback.data.split("_")[2])
    product = await catalogservice.get_product(product_id)
    
    # Получаем текущие данные из state
    user_data = await state.get_data()
    selected_size = user_data.get("selected_size")
    
    text = f"{format_product_description(product)}\n\n<b>Выберите размер товара:</b>"
    keyboard = size_selection_keyboard(product, selected_size)
    
    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")
    
    await update_message(
        msg=callback,
        media=media,
        reply_markup=keyboard
    )

@catalog_router.callback_query(F.data.startswith("select_size_"))
@inject_services(CatalogService)
async def select_size(callback: CallbackQuery, catalogservice: CatalogService, state: FSMContext):
    """Обработка выбора размера"""
    # Формат: select_size_ID_SIZE
    parts = callback.data.split("_")
    product_id = int(parts[2])
    selected_size = parts[3]
    
    # Обновляем данные в state
    await state.update_data(selected_size=selected_size)
    
    # Обновляем клавиатуру с выбранным размером
    product = await catalogservice.get_product(product_id)
    text = f"{format_product_description(product)}\n\n<b>Размер выбран: {selected_size} ✅</b>"
    keyboard = size_selection_keyboard(product, selected_size)
    
    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")
    
    await update_message(
        msg=callback,
        media=media,
        reply_markup=keyboard
    )

@catalog_router.callback_query(F.data.startswith("show_colors_"))
@inject_services(CatalogService)
async def show_colors_selection(callback: CallbackQuery, catalogservice: CatalogService, state: FSMContext):
    """Показываем экран выбора цвета"""
    product_id = int(callback.data.split("_")[2])
    product = await catalogservice.get_product(product_id)
    
    # Получаем текущие данные из state
    user_data = await state.get_data()
    selected_color = user_data.get("selected_color")
    
    text = f"{format_product_description(product)}\n\n<b>Выберите цвет товара:</b>"
    keyboard = color_selection_keyboard(product, selected_color)
    
    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")
    
    await update_message(
        msg=callback,
        media=media,
        reply_markup=keyboard
    )

@catalog_router.callback_query(F.data.startswith("select_color_"))
@inject_services(CatalogService)
async def select_color(callback: CallbackQuery, catalogservice: CatalogService, state: FSMContext):
    """Обработка выбора цвета"""
    # Формат: select_color_ID_COLOR
    parts = callback.data.split("_")
    product_id = int(parts[2])
    selected_color = parts[3]
    
    # Обновляем данные в state
    await state.update_data(selected_color=selected_color)
    
    # Обновляем клавиатуру с выбранным цветом
    product = await catalogservice.get_product(product_id)
    text = f"{format_product_description(product)}\n\n<b>Цвет выбран: {selected_color} ✅</b>"
    keyboard = color_selection_keyboard(product, selected_color)
    
    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")
    
    await update_message(
        msg=callback,
        media=media,
        reply_markup=keyboard
    )

@catalog_router.callback_query(F.data.startswith("show_quantity_"))
@inject_services(CatalogService)
async def show_quantity_selection(callback: CallbackQuery, catalogservice: CatalogService, state: FSMContext):
    """Показываем экран выбора количества"""
    # Формат: show_quantity_ID_CURRENT
    parts = callback.data.split("_")
    product_id = int(parts[2])
    current_quantity = int(parts[3])
    
    # Обновляем данные в state
    await state.update_data(quantity=current_quantity)
    
    # Обновляем клавиатуру с текущим количеством
    product = await catalogservice.get_product(product_id)
    max_quantity = product.stock if hasattr(product, "stock") and product.stock is not None else 10
    
    text = f"{format_product_description(product)}\n\n<b>Выберите количество товара:</b>\nМаксимальное количество: {max_quantity} шт."
    keyboard = quantity_selection_keyboard(product, current_quantity)
    
    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")
    
    await update_message(
        msg=callback,
        media=media,
        reply_markup=keyboard
    )

@catalog_router.callback_query(F.data.startswith("change_quantity_"))
@inject_services(CatalogService)
async def change_quantity(callback: CallbackQuery, catalogservice: CatalogService, state: FSMContext):
    """Обработка изменения количества"""
    # Формат: change_quantity_ID_NEW_QUANTITY
    parts = callback.data.split("_")
    product_id = int(parts[2])
    new_quantity = int(parts[3])
    
    # Получаем информацию о продукте для проверки максимального количества
    product = await catalogservice.get_product(product_id)
    max_quantity = product.stock if hasattr(product, "stock") and product.stock is not None else 10
    
    # Проверяем и ограничиваем количество
    if new_quantity < 1:
        new_quantity = 1
    elif new_quantity > max_quantity:
        new_quantity = max_quantity
        await callback.answer(f"Максимальное количество: {max_quantity} шт.", show_alert=True)
    
    # Обновляем данные в state
    await state.update_data(quantity=new_quantity)
    
    # Обновляем клавиатуру с новым количеством
    text = f"{format_product_description(product)}\n\n<b>Выберите количество товара:</b>\nМаксимальное количество: {max_quantity} шт."
    keyboard = quantity_selection_keyboard(product, new_quantity)
    
    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")
    
    await update_message(
        msg=callback,
        media=media,
        reply_markup=keyboard
    )

@catalog_router.callback_query(F.data.startswith("confirm_quantity_"))
@inject_services(CatalogService)
async def confirm_quantity(callback: CallbackQuery, catalogservice: CatalogService, state: FSMContext):
    """Подтверждение выбранного количества"""
    # Формат: confirm_quantity_ID_QUANTITY
    parts = callback.data.split("_")
    product_id = int(parts[2])
    quantity = int(parts[3])
    
    # Обновляем данные в state
    await state.update_data(quantity=quantity)
    
    # Возвращаемся к экрану с опциями товара, но уже с выбранным количеством
    user_data = await state.get_data()
    product = await catalogservice.get_product(product_id)
    
    text = format_product_description(product)
    keyboard = product_final_options_keyboard(
        product, 
        user_data.get("selected_size"), 
        user_data.get("selected_color"), 
        quantity
    )
    
    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")
    
    await update_message(
        msg=callback,
        media=media,
        reply_markup=keyboard
    )

@catalog_router.callback_query(F.data.startswith("add_to_cart_"))
@inject_services(CatalogService, CartService)
async def add_to_cart(callback: CallbackQuery, catalogservice: CatalogService, cartservice: CartService, state: FSMContext):
    # Парсим данные из callback
    try:
        parts = callback.data.split("_")
        if len(parts) < 5:
            await callback.answer("Ошибка: неверный формат данных", show_alert=True)
            return
            
        product_id = int(parts[3])
        quantity = int(parts[4]) if len(parts) > 4 else 1
        
        # Обрабатываем дополнительные параметры, если они есть
        size = None
        color = None
        
        if len(parts) > 5 and parts[5] != "None":
            size = parts[5]
        
        if len(parts) > 6 and parts[6] != "None":
            color = parts[6]
        
        # Если параметры не переданы напрямую, пытаемся получить их из состояния
        if not size or not color:
            user_data = await state.get_data()
            if not size and "selected_size" in user_data:
                size = user_data.get("selected_size")
            if not color and "selected_color" in user_data:
                color = user_data.get("selected_color")
        
        # Получаем информацию о продукте
        product = await catalogservice.get_product(product_id)
        
        # Проверяем наличие товара на складе
        max_quantity = product.stock if hasattr(product, "stock") and product.stock is not None else 10
        if quantity > max_quantity:
            await callback.answer(f"Доступно только {max_quantity} шт.", show_alert=True)
            quantity = max_quantity
        
        # Добавляем товар в корзину
        user_id = callback.from_user.id
        await cartservice.add_to_cart(user_id, product_id, quantity, size, color)
        
        # Формируем сообщение об успешном добавлении в корзину
        success_text = f"✅ Товар успешно добавлен в корзину!\n\n<b>{product.name}</b>"
        if size:
            success_text += f"\nРазмер: {size}"
        if color:
            success_text += f"\nЦвет: {color}"
        success_text += f"\nКоличество: {quantity}"
        
        # Показываем клавиатуру для продолжения покупок или перехода в корзину
        await callback.message.answer(text=success_text, reply_markup=after_cart_add_keyboard(), parse_mode="HTML")
        await callback.answer("Товар добавлен в корзину!")
        
        # Очищаем состояние после добавления в корзину
        await state.clear()
        
    except Exception as e:
        print(f"Ошибка при добавлении товара в корзину: {e}")
        await callback.answer(f"Произошла ошибка: {str(e)}", show_alert=True)
        
@catalog_router.callback_query(F.data.startswith("back_to_product_"))
@inject_services(CatalogService)
async def back_to_product(callback: CallbackQuery, catalogservice: CatalogService):
    product_id = int(callback.data.split("_")[2])
    product = await catalogservice.get_product(product_id)
    products = await catalogservice.list_products()
    current_index = next((i for i, p in enumerate(products) if p.id == product_id), 0)

    text = format_product_description(product)
    keyboard = product_navigation_keyboard(product.id, products, current_index)
    media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")

    await update_message(msg=callback, media=media, reply_markup=keyboard)


@catalog_router.callback_query(F.data == "back_to_catalog")
@inject_services(CatalogService)
async def back_to_catalog(callback: CallbackQuery, catalogservice: CatalogService, state: FSMContext = None):
    # Очищаем состояние, если оно доступно
    if state:
        await state.clear()
    
    # Получаем данные для каталога
    image = await catalogservice.get_image_by_name("catalog_menu")
    products = await catalogservice.list_products()
    keyboard = catalog_keyboard(products)
    welcome_text = "Добро пожаловать в каталог товаров!\nВыберите товар, который хотите приобрести!"
    
    # Удаляем текущее сообщение
    await callback.message.delete()
    
    # Отправляем новое сообщение с каталогом
    if image:
        await callback.bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=image.url,
            caption=welcome_text,
            reply_markup=keyboard
        )
    else:
        # Если изображение не найдено, отправляем только текст
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=welcome_text,
            reply_markup=keyboard
        )
    
    # Отвечаем на callback, чтобы убрать загрузку с кнопки
    await callback.answer()