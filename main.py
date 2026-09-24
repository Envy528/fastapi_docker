from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from src.models.product_model import Product, ProductCategories
from src.shared.database.session_db import SessionDep, get_session

app = FastAPI()


class CreateProduct(BaseModel):
    name: str
    price: float
    quantity: int
    category: ProductCategories


@app.post("/product", status_code=201)
def create_product(product: CreateProduct, session: SessionDep):
    # 1. Buscar si el producto existe
    product_inDb = session.exec(
        select(Product).where(Product.name == product.name.lower().strip())
    ).one_or_none()

    # 2.1 Si existe enviar mensaje de error
    if product_inDb == None:

        if product.price <= 0:
            raise HTTPException(
                status_code=422,
                detail="El precio del producto debe ser superior a 0",
            )

        if product.quantity <= 0:
            raise HTTPException(
                status_code=422,
                detail="La cantidad del producto debe ser superior a 0",
            )

        product = Product(
            name=product.name,
            category=product.category,
            price=product.price,
            quantity=product.quantity,
        )
        session.add(product)
        session.commit()
        session.refresh(product)

        return product
    # 2.2 Si no existe continuar con la creacion
    else:
        raise HTTPException(
            status_code=409, detail="El producto ya existe en la base de datos"
        )


@app.get("/product")
def get_products(session: SessionDep):
    products = session.exec(select(Product)).all()

    return products


@app.delete("/product/{id}")
def delete_product(product_id: int, session: SessionDep):
    product = session.exec(select(Product).where(Product.id == product_id)).one()
    session.delete(product)
    session.commit()
