from app.repositories.catalog_repo import CatalogRepo
from aiogram.types import InlineKeyboardMarkup, InputMediaPhoto
from app.database.models import CommonImage, Product
from app.keyboards.catalog import catalog_keyboard
import os
import pandas as pd
from datetime import datetime
import re
from io import BytesIO

class CatalogService:
    def __init__(self, catalog_repo: CatalogRepo):
        self.catalog_repo = catalog_repo
        self.excel_folder = "temp_excel"
        
        os.makedirs(self.excel_folder, exist_ok=True)

    async def list_products(self) -> list[Product]:
        """Get all products from database"""
        return await self.catalog_repo.get_all_products()

    async def get_product(self, product_id: int) -> Product | None:
        """Get product by ID"""
        return await self.catalog_repo.get_product_by_id(product_id)

    async def get_image_by_name(self, name: str) -> CommonImage | None:
        """Get common image by name"""
        return await self.catalog_repo.get_image_by_name(name)

    async def get_catalog_with_image(self) -> tuple[InputMediaPhoto, InlineKeyboardMarkup]:
        """Get catalog display with image and keyboard"""
        # Get image with name 'catalog_menu'
        image = await self.get_image_by_name("catalog_menu")

        media = InputMediaPhoto(
            media=image.url if image else "https://example.com/default_image.jpg",
            caption=(
                "<b>Добро пожаловать в наш каталог!</b>\n\n"
                "🎁 Здесь вы можете обменять свои T-поинты на классные подарки!\n"
                "Выберите интересующий вас товар из списка ниже ⬇️"
            )
        )

        products = await self.list_products()
        keyboard = catalog_keyboard(products)

        return media, keyboard

    async def create_catalog_excel(self) -> str:
        """Create Excel file with product catalog data"""
        # Get all products from DB
        products = await self.list_products()
        
        # Convert ORM objects to dictionaries for pandas
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'image_url': product.image_url,
                'is_available': 1 if product.is_available else 0,
                'sizes': product.sizes if product.sizes else "",
                'colors': product.colors if product.colors else ""
            })
        
        # Create DataFrame
        df = pd.DataFrame(products_data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.excel_folder, f"catalog_{timestamp}.xlsx")
        
        # Write to Excel
        df.to_excel(filename, index=False)
        
        return filename
    
    async def create_catalog_excel_bytes(self) -> bytes:
        """Create Excel file with product catalog data and return as bytes"""
        # Get all products from DB
        products = await self.list_products()
        
        # Convert ORM objects to dictionaries for pandas
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'image_url': product.image_url,
                'is_available': 1 if product.is_available else 0,
                'sizes': product.sizes if product.sizes else "",
                'colors': product.colors if product.colors else ""
            })
        
        # Create DataFrame
        df = pd.DataFrame(products_data)
        
        # Create Excel in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Каталог товаров')
            
            # Adjust column widths
            worksheet = writer.sheets['Каталог товаров']
            for idx, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(column_width, 50)
        
        output.seek(0)
        return output.getvalue()

    async def import_catalog_from_excel(self, file_path: str) -> dict:
        """Process product import from Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Convert DataFrame to list of dictionaries
            raw_products_data = df.to_dict('records')
            products_data = []
            
            # Validate data and process image links
            for product in raw_products_data:
                # Check required fields
                if 'name' not in product or 'price' not in product:
                    return {
                        "success": False, 
                        "message": "В Excel файле отсутствуют обязательные поля (name, price)"
                    }
                
                # Convert is_available to boolean
                is_available = product.get('is_available', True)
                product['is_available'] = self._parse_bool(is_available)
            
                # Process Google Drive image link
                image_raw = product.get('image_url')

                try:
                    if image_raw is not None:
                        print(f"[DEBUG] Обработка изображения для продукта '{product.get('name')}'")
                        product['image_url'] = self._extract_google_drive_image_url(image_raw)
                    else:
                        product['image_url'] = None
                except Exception as e:
                    print(f"[ERROR] Ошибка обработки URL для '{product.get('name')}': {e}")
                    product['image_url'] = None

                # Create new dictionary with required fields
                products_data.append({
                    'id': product.get('id'),
                    'name': product['name'],
                    'description': product.get('description', ''),
                    'price': product['price'],
                    'image_url': product['image_url'],
                    'is_available': product['is_available'],
                    'sizes': product.get('sizes', ''),
                    'colors': product.get('colors', '')
                })
                
            # Save products to DB
            result = await self.catalog_repo.create_or_update_products(products_data)
            return {"success": True, "updated": result}
        
        except Exception as e:
            print(f"Error during import: {e}")
            return {"success": False, "message": f"Ошибка при импорте: {str(e)}"}
    
    def _parse_bool(self, value) -> bool:
        """Convert various types to boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in ['true', '1', 'yes', 'да', 'истина']
        return False
        
    import re
    
    def _extract_google_drive_image_url(self, url: str) -> str:
        """
        Преобразовать ссылку Google Drive в прямую ссылку на изображение
        """
        try:
            if not isinstance(url, str):
                url = str(url)
    
            print(f"[DEBUG] Исходный URL: {url}")
    
            # Если уже правильный формат — возвращаем как есть
            if "drive.google.com/uc?export=view&id=" in url:
                return url
    
            # Пробуем вытащить ID из разных форматов
            patterns = [
                r'drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)',            # стандартный формат /file/d/ID/
                r'drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)',            # формат open?id=ID
                r'drive\.google\.com\/uc\?id=([a-zA-Z0-9_-]+)',              # uc?id=ID
                r'id=([a-zA-Z0-9_-]{10,})'                                   # запасной вариант — просто id=ID
            ]
    
            file_id = None
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    file_id = match.group(1)
                    break
                
            if file_id:
                direct_url = f"https://drive.google.com/uc?export=view&id={file_id}"
                print(f"[DEBUG] Преобразованный URL: {direct_url}")
                return direct_url
            else:
                print("[WARN] ID не найден, возвращаю оригинал")
                return url
    
        except Exception as e:
            print(f"[ERROR] Ошибка при обработке ссылки: {e}")
            return url
    