from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from src.models.product_model import Product, ProductCategories
from src.shared.database.session_db import SessionDep, get_session
import os
import uuid
import boto3
from fastapi import File, UploadFile

app = FastAPI()
s3_client = boto3.client("s3", region_name="us-east-2")
S3_BUCKET_NAME = "proyecto-aws-jorge"
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


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
    
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/images", status_code=201)
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail="Tipo de archivo no permitido. Solo JPEG, PNG o WEBP.",
        )

    extension = file.filename.split(".")[-1]
    key = f"images/{uuid.uuid4()}.{extension}"

    s3_client.upload_fileobj(file.file, S3_BUCKET_NAME, key)

    return {
        "message": "Imagen subida correctamente",
        "key": key,
        "url": f"https://{S3_BUCKET_NAME}.s3.us-east-2.amazonaws.com/{key}",
    }
