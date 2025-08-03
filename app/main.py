import uuid

from fastapi import FastAPI, Depends, UploadFile
from fastapi.params import Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.responses import RedirectResponse
from fastapi import HTTPException, status
from fastapi import File, Body
from .database import SessionLocal, engine
from . import models, crud
from .utils import decode_token, create_access_token
from fastapi import Query

# ساخت جداول در اولین اجرا
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
# app.add_middleware(SessionMiddleware, secret_key="🧄secret_key_very_secret🧄")
templates = Jinja2Templates(directory="templates")

# Dependency برای سشن DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db=Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    return db.query(models.User).get(int(user_id))
# dependency قبلی get_current_user داریم؛ یکی برای «باید لاگین باشد» بساز
def require_user(request: Request, db=Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="ابتدا لاگین کن")
    return user

def set_access_cookie(response: Response, token: str):
    response.set_cookie(
        "access_token",
        token,
        max_age=60*60*24,        # یک روز
        httponly=True,
        samesite="lax",
    )


def require_admin(cur=Depends(require_user)):
    if not cur.is_admin:
        raise HTTPException(403, "دسترسی ممنوع")
    return cur


def require_seller(cur=Depends(require_user)):
    if not cur.is_seller and not cur.is_admin:
        raise HTTPException(403, "دسترسی فقط برای فروشنده‌هاست")
    return cur




@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db=Depends(get_db), current_user=Depends(get_current_user)):
    products = crud.get_products(db)
    if current_user:
        cart_count = crud.cart_total_qty(db, current_user.id)
    else:
        cart_count = 0

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "products": products,
            "user": current_user,
            "cart_count": cart_count,
        },
    )


@app.get("/api/products")
def api_products(db=Depends(get_db)):
    return crud.get_products(db)


# صفحه فرم ثبت‌نام
@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# پردازش ثبت‌نام
@app.post("/register")
def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    fname: str = Form(""),
    lname: str = Form(""),
    db=Depends(get_db),
):
    if crud.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="ایمیل قبلاً ثبت شده")
    user = crud.create_user(db, email, password, fname, lname)
    token = create_access_token({"sub": str(user.id)})

    resp = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    set_access_cookie(resp, token)
    return resp

# صفحه فرم لاگین
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# پردازش لاگین
@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    user = crud.authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=401, detail="اطلاعات ورود اشتباه است")

    token = create_access_token({"sub": str(user.id)})
    resp = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    set_access_cookie(resp, token)
    return resp

# خروج
@app.get("/logout")
def logout(request: Request):
    resp = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie("access_token")
    return resp

# --- Cart Endpoints ---

@app.get("/api/cart")
def api_get_cart(cur=Depends(require_user), db=Depends(get_db)):
    return crud.get_cart_items(db, cur.id)

@app.post("/api/cart/add/{product_id}")
def api_add_cart(product_id: int, cur=Depends(require_user), db=Depends(get_db)):
    crud.add_to_cart(db, cur.id, product_id)
    return {"ok": True}

@app.post("/api/cart/remove/{product_id}")
def api_remove_cart(product_id: int, cur=Depends(require_user), db=Depends(get_db)):
    crud.remove_from_cart(db, cur.id, product_id)
    return {"ok": True}


@app.get("/cart", response_class=HTMLResponse)
def show_cart(request: Request, cur=Depends(require_user), db=Depends(get_db)):
    items = crud.get_cart_items(db, cur.id)
    return templates.TemplateResponse(
        "cart.html",
        {"request": request, "items": items, "user": cur},
    )


# ----- پروفایل -----
@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, cur=Depends(require_user)):
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": cur},
    )

@app.post("/profile/update")
def profile_update(
    cur=Depends(require_user),
    db=Depends(get_db),
    fname: str = Form(""),
    lname: str = Form(""),
    email: str = Form(...),
):
    try:
        crud.update_user(db, cur, fname, lname, email)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "ایمیل تکراریه!")
    return RedirectResponse("/profile", status_code=status.HTTP_302_FOUND)


@app.get("/profile/orders", response_class=HTMLResponse)
def profile_orders(
    request: Request,
    cur=Depends(require_user),
    db=Depends(get_db),
):
    orders = crud.get_orders_by_user(db, cur.id)
    return templates.TemplateResponse(
        "profile_orders.html",
        {"request": request, "user": cur, "orders": orders},
    )

@app.post("/profile/topup")
def profile_topup(
    cur=Depends(require_user),
    db=Depends(get_db),
    amount: int = Form(...),
):
    if amount <= 0:
        raise HTTPException(400, "مبلغ نامعتبر")
    crud.add_balance(db, cur, amount)
    return RedirectResponse("/profile", status_code=status.HTTP_302_FOUND)

# ----- Checkout -----
@app.post("/api/checkout")
def api_checkout(cur=Depends(require_user), db=Depends(get_db)):
    try:
        order = crud.checkout(db, cur)
        return {"ok": True, "order_id": order.id}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/admin/product/{pid}/inc")
def admin_inc_stock(
    pid: int,
    step: int = Query(1, gt=0),          # تعداد دلخواه
    cur=Depends(require_admin),
    db=Depends(get_db),
):
    return {"stock": crud.inc_stock(db, pid, step)}

@app.post("/api/admin/product/{pid}/dec")
def admin_dec_stock(
    pid: int,
    step: int = Query(1, gt=0),
    cur=Depends(require_admin),
    db=Depends(get_db),
):
    return {"stock": crud.inc_stock(db, pid, -step)}

@app.delete("/api/admin/product/{pid}")
def admin_del_product(pid: int, cur=Depends(require_admin), db=Depends(get_db)):
    crud.delete_product(db, pid)
    return {"ok": True}

@app.get("/api/admin/users")
def admin_get_users(cur=Depends(require_admin), db=Depends(get_db)):
    return db.query(models.User).all()

@app.post("/api/admin/users/{uid}/promote")
def admin_promote(uid: int, cur=Depends(require_admin), db=Depends(get_db)):
    user = db.query(models.User).get(uid)
    if not user:
        raise HTTPException(404, "یوزر نیست")
    user.is_admin = True
    db.commit()
    return {"ok": True}

@app.delete("/api/admin/users/{uid}")
def admin_delete_user(uid: int, cur=Depends(require_admin), db=Depends(get_db)):
    if uid == cur.id:                      # ⛔ خودت را پاک نکن
        raise HTTPException(400, "خودت را نمی‌توانی حذف کنی")

    user = db.query(models.User).get(uid)
    if not user:
        raise HTTPException(404, "یوزر نیست")

    if user.is_admin:                      # ⛔ ادمینِ دیگر را پاک نکن
        raise HTTPException(400, "ادمین را نمی‌توان حذف کرد")

    db.delete(user)
    db.commit()
    return {"ok": True}

@app.get("/admin/users", response_class=HTMLResponse)
def admin_users_page(request: Request, cur=Depends(require_admin), db=Depends(get_db)):
    users = db.query(models.User).all()
    return templates.TemplateResponse(
        "admin_users.html", {"request": request, "user": cur, "users": users}
    )

@app.get("/admin/orders", response_class=HTMLResponse)
def admin_orders_page(
    request: Request,
    cur=Depends(require_admin),
):
    return templates.TemplateResponse(
        "admin_orders.html",
        {"request": request, "user": cur},
    )


@app.get("/api/admin/order/{oid}")
def admin_order_details(
    oid: int,
    cur=Depends(require_admin),
    db=Depends(get_db),
):
    order = crud.get_order_details(db, oid)
    if not order:
        raise HTTPException(404, "سفارش یافت نشد")
    return order

@app.post("/api/admin/users/{uid}/makeseller")
def admin_make_seller(uid: int, cur=Depends(require_admin), db=Depends(get_db)):
    user = db.query(models.User).get(uid)
    if not user:
        raise HTTPException(404, "یوزر نیست")

    if user.is_admin:                      # ⛔ ادمین را Seller نمی‌کنیم
        raise HTTPException(400, "کاربر ادمین است")

    if user.is_seller:                     # قبلاً Seller شده
        return {"ok": True}

    user.is_seller = True
    db.commit()
    return {"ok": True}

@app.get("/seller/products", response_class=HTMLResponse)
def seller_products_page(
    request: Request,
    cur=Depends(require_seller),
    db=Depends(get_db),
):
    prods = crud.get_products_by_seller(db, cur.id)
    return templates.TemplateResponse(
        "seller_products.html",
        {"request": request, "user": cur, "products": prods},
    )

@app.post("/api/seller/product")
def api_seller_add(
    cur=Depends(require_seller),
    db=Depends(get_db),
    name: str = Form(...),
    price: int = Form(...),
    stock: int = Form(...),
    description: str = Form(""),
    image: UploadFile = File(...),
):
    # ذخیره عکس در /static/images
    fname = f"{uuid.uuid4().hex}_{image.filename}"
    path  = f"static/images/{fname}"
    with open(path, "wb") as f:
        f.write(image.file.read())

    prod = crud.create_product_for_seller(
        db, cur,
        name=name,
        price=price,
        stock=stock,
        description=description,
        image=f"/static/images/{fname}",
    )
    return {"ok": True, "id": prod.id}

# ▶️ افزایش/کاهش موجودی
@app.post("/api/seller/product/{pid}/stock")
def seller_change_stock(
    pid:int,
    step:int = Query(...),
    cur = Depends(require_seller),
    db  = Depends(get_db),
):
    prod = db.query(models.Product).get(pid)
    if not prod or prod.seller_id != cur.id:
        raise HTTPException(403, "دسترسی ندارید")
    prod.stock = max(prod.stock + step, 0)
    db.commit(); db.refresh(prod)
    return {"stock": prod.stock}

# ▶️ حذف
@app.delete("/api/seller/product/{pid}")
def seller_del_product(
    pid:int,
    cur=Depends(require_seller),
    db=Depends(get_db),
):
    prod = db.query(models.Product).get(pid)
    if not prod or prod.seller_id != cur.id:
        raise HTTPException(403, "دسترسی ندارید")
    crud.delete_product_by_seller(db, prod)
    return {"ok":True}

# ▶️ ویرایش
@app.post("/api/seller/product/{pid}/update")
def seller_update_product(
    pid:int,
    cur=Depends(require_seller),
    db=Depends(get_db),
    name:str = Form(...),
    price:int = Form(...),
    stock:int = Form(...),
    description:str = Form(""),
):
    prod = db.query(models.Product).get(pid)
    if not prod or prod.seller_id != cur.id:
        raise HTTPException(403, "دسترسی ندارید")
    crud.update_product_by_seller(db, prod, name, price, stock, description)
    return {"ok":True}

@app.get("/seller/stats", response_class=HTMLResponse)
def seller_stats_page(
    request: Request,
    cur=Depends(require_seller),
    db=Depends(get_db),
):
    summary = crud.sales_summary_by_seller(db, cur.id)
    return templates.TemplateResponse(
        "seller_stats.html",
        {"request": request, "user": cur, "summary": summary},
    )

@app.get("/api/seller/product/{pid}/buyers")
def api_seller_product_buyers(
    pid:int,
    cur=Depends(require_seller),
    db =Depends(get_db),
):
    prod = db.query(models.Product).get(pid)
    if not prod or prod.seller_id != cur.id:
        raise HTTPException(403, "دسترسی ندارید")
    sales = crud.get_sales_of_product(db, cur.id, pid)
    return [{
        "order_id": it.order_id,
        "buyer": it.order.user.email,
        "qty": it.qty,
        "date": it.order.created_at.strftime("%Y-%m-%d %H:%M")
    } for it in sales]
