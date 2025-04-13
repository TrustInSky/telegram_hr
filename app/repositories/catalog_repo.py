from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Product, CommonImage
from typing import List, Dict, Any, Optional

class CatalogRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_products(self) -> List[Product]:
        """Get all products from database"""
        query = select(Product).order_by(Product.id)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_available_products(self) -> List[Product]:
        """Get only available products"""
        query = select(Product).where(Product.is_available == True).order_by(Product.id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        query = select(Product).where(Product.id == product_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_image_by_name(self, name: str) -> Optional[CommonImage]:
        """Get common image by name"""
        query = select(CommonImage).where(CommonImage.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create_or_update_products(self, products_data: List[Dict[str, Any]]) -> int:
        """Create or update products from list of dictionaries
        
        Args:
            products_data: List of product dictionaries
            
        Returns:
            Number of products created/updated
        """
        updated_count = 0
        
        for product_data in products_data:
            product_id = product_data.get('id')
            
            if product_id:
                # Update existing product
                product = await self.get_product_by_id(product_id)
                if product:
                    # Remove id from data to be updated
                    update_data = {k: v for k, v in product_data.items() if k != 'id'}
                    
                    # Update product
                    stmt = (
                        update(Product)
                        .where(Product.id == product_id)
                        .values(**update_data)
                    )
                    await self.session.execute(stmt)
                    updated_count += 1
                else:
                    # Create new product with specified ID
                    new_product = Product(**product_data)
                    self.session.add(new_product)
                    updated_count += 1
            else:
                # Create new product without ID
                new_product_data = {k: v for k, v in product_data.items() if k != 'id'}
                new_product = Product(**new_product_data)
                self.session.add(new_product)
                updated_count += 1
        
        # Commit all changes
        await self.session.commit()
        return updated_count