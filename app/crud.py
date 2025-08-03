from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload
from .models import CartItem, Product, User, Order, OrderItem
from .utils import hash_password, verify_password

def get_products(db: Session):
    return db.query(Product).all()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, password: str, fname: str, lname: str):
    db_user = User(
        email=email,
        password=hash_password(password),
        fname=fname,
        lname=lname,
        is_admin=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password):
        return None
    return user


# ----- Cart -----
def get_cart_items(db: Session, user_id: int):
    return (
        db.query(CartItem)
          .options(selectinload(CartItem.product))
          .filter(CartItem.user_id == user_id)
          .all()
    )

def cart_total_qty(db: Session, user_id: int):
    total = (
        db.query(func.coalesce(func.sum(CartItem.qty), 0))
          .filter(CartItem.user_id == user_id)
          .scalar()
    )
    return total

def cart_item_exists(db: Session, user_id: int, product_id: int):
    return db.query(CartItem).filter(
        CartItem.user_id == user_id, CartItem.product_id == product_id
    ).first()

def add_to_cart(db: Session, user_id: int, product_id: int):
    item = cart_item_exists(db, user_id, product_id)
    if item:
        item.qty += 1
    else:
        db.add(CartItem(user_id=user_id, product_id=product_id, qty=1))
    db.commit()

def remove_from_cart(db: Session, user_id: int, product_id: int):
    item = cart_item_exists(db, user_id, product_id)
    if item:
        if item.qty > 1:
            item.qty -= 1
        else:
            db.delete(item)
        db.commit()

# ---------- Profile ----------
def update_user(db: Session, user: User, fname: str, lname: str, email: str):
    # اگه ایمیل مال یه کاربر دیگه باشه، خطا بده
    existing = (
        db.query(User)
          .filter(User.email == email, User.id != user.id)
          .first()
    )
    if existing:
        raise ValueError("ایمیل قبلاً توسط کاربر دیگری ثبت شده")

    user.fname, user.lname, user.email = fname, lname, email
    db.commit()
    db.refresh(user)
    return user


def add_balance(db: Session, user: User, amount: int):
    user.balance += amount
    db.commit()
    db.refresh(user)
    return user.balance

# ---------- Checkout ----------
def checkout(db: Session, user: User):
    cart_items = get_cart_items(db, user.id)
    if not cart_items:
        raise ValueError("سبد خرید خالیه")

    # محاسبه مجموع و چک موجودی کالا
    total = 0
    for it in cart_items:
        if it.qty > it.product.stock:
            raise ValueError(f"موجودی «{it.product.name}» کافی نیست")
        total += it.qty * it.product.price

    if user.balance < total:
        raise ValueError("موجودی حساب کافی نیست")

    # کسر موجودی کاربر و استوک محصولات
    user.balance -= total
    for it in cart_items:
        it.product.stock -= it.qty

    # ایجاد Order
    order = Order(user_id=user.id, total=total)
    db.add(order)
    db.flush()  #‌ تا id داشته باشیم

    for it in cart_items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=it.product_id,
            qty=it.qty,
            price=it.product.price,
            seller_id=it.product.seller_id
        ))
        db.delete(it)   # پاک کردن از سبد

    db.commit()
    db.refresh(order)
    return order


# ---------- Product Admin ----------
def inc_stock(db: Session, product_id: int, step: int = 1):
    prod = db.query(Product).get(product_id)
    if not prod:
        raise ValueError("کالا یافت نشد")
    prod.stock += step
    if prod.stock < 0:
        prod.stock = 0
    db.commit()
    db.refresh(prod)
    return prod.stock

def delete_product(db: Session, product_id: int):
    prod = db.query(Product).get(product_id)
    if not prod:
        raise ValueError("کالا یافت نشد")
    db.delete(prod)
    db.commit()

def get_orders_by_user(db:Session, user_id:int):
    return (
        db.query(Order)
          .filter(Order.user_id == user_id)
          .order_by(Order.created_at.desc())
          .options(
              selectinload(Order.items)
              .selectinload(OrderItem.product)
          )
          .all()
    )

def get_order_details(db:Session, order_id:int):
    return (
        db.query(Order)
          .filter(Order.id == order_id)
          .options(
              selectinload(Order.user),
              selectinload(Order.items)
              .selectinload(OrderItem.product)
          )
          .first()
    )

def get_sales_by_seller(db:Session, seller_id:int):
    return (
        db.query(OrderItem)
          .options(
              selectinload(OrderItem.order).selectinload(Order.user),
              selectinload(OrderItem.product)
          )
          .filter(OrderItem.seller_id == seller_id)
          .order_by(OrderItem.order_id.desc())
          .all()
    )


# -- Seller Product CRUD --
def create_product_for_seller(db:Session, seller:User,
                              name:str, price:int, stock:int,
                              description:str, image:str):
    prod = Product(
        name=name, price=price, stock=stock,
        description=description, image=image,
        seller_id=seller.id
    )
    db.add(prod); db.commit(); db.refresh(prod)
    return prod

def get_products_by_seller(db:Session, seller_id:int):
    return db.query(Product).filter(Product.seller_id == seller_id).all()

def update_product_by_seller(db:Session, prod:Product,
                             name:str, price:int, stock:int, description:str):
    prod.name, prod.price, prod.stock, prod.description = \
        name, price, stock, description
    db.commit(); db.refresh(prod); return prod

def delete_product_by_seller(db:Session, prod:Product):
    db.delete(prod); db.commit()

def sales_summary_by_seller(db: Session, seller_id: int):
    """
    برمی‌گرداند:
      [(product_id, product_name, total_qty, total_amount)]
    """
    return (
        db.query(
            Product.id,
            Product.name,
            func.sum(OrderItem.qty).label("qty"),
            func.sum(OrderItem.qty * OrderItem.price).label("amount"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(OrderItem.seller_id == seller_id)
        .group_by(Product.id, Product.name)
        .all()
    )

def get_sales_of_product(db: Session, seller_id: int, product_id: int):
    return (
        db.query(OrderItem)
          .join(Order, OrderItem.order_id == Order.id)
          .join(User,  Order.user_id  == User.id)
          .filter(OrderItem.seller_id == seller_id,
                  OrderItem.product_id == product_id)
          .options(
              selectinload(OrderItem.order),
              selectinload(OrderItem.order).selectinload(Order.user)
          )
          .order_by(Order.id.desc())
          .all()
    )