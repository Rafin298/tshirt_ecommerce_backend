# Bangladesh E-Commerce Backend

Django REST Framework backend for a Bangladesh e-commerce platform.

## Tech Stack

- Django 6.x + Django REST Framework
- PostgreSQL
- JWT Authentication (SimpleJWT)

## Setup

### 1. Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data
python manage.py runserver
```

### 2. Configure environment
Update the `.env` file with your values:

Required variables:
```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/ecommerce_db
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
BKASH_NUMBER=01XXXXXXXXX
```

### 3. Create database
```bash
createdb ecommerce_db
```

### 4. Run migrations
```bash
python manage.py migrate
```

### 5. Create superuser
```bash
python manage.py createsuperuser
```

### 6. Seed data
```bash
python manage.py seed_data
```

### 7. Run dev server
```bash
python manage.py runserver
```

---

## API Endpoints (32 total)

### Auth & Users
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/api/auth/register/` | Public |
| POST | `/api/auth/login/` | Public |
| POST | `/api/auth/logout/` | Required |
| POST | `/api/auth/token/refresh/` | Public |
| GET/PUT/PATCH | `/api/users/me/` | Required |
| GET/POST | `/api/users/addresses/` | Required |
| GET/PUT/PATCH/DELETE | `/api/users/addresses/<id>/` | Required |
| POST | `/api/users/addresses/<id>/set-default/` | Required |

### Products
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/api/categories/` | Public |
| GET | `/api/products/` | Public |
| GET | `/api/products/<slug>/` | Public |

**Product filters:** `?category=<slug>`, `?in_stock=true`, `?min_price=`, `?max_price=`, `?search=`, `?ordering=price`

### Cart & Orders
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/api/cart/` | Required |
| POST | `/api/cart/add/` | Required |
| PUT/DELETE | `/api/cart/items/<id>/` | Required |
| DELETE | `/api/cart/clear/` | Required |
| POST | `/api/cart/apply-coupon/` | Required |
| DELETE | `/api/cart/remove-coupon/` | Required |
| POST | `/api/orders/place/` | Required |
| GET | `/api/orders/` | Required |
| GET | `/api/orders/<order_number>/` | Required |
| POST | `/api/orders/<order_number>/cancel/` | Required |

### Payments
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/api/payments/cod/` | Required |
| POST | `/api/payments/bkash/submit/` | Required |
| GET | `/api/payments/<order_number>/status/` | Required |

---

## Place Order Request
```json
{
  "address_id": 1,
  "payment_method": "COD"
}
```

## bKash Submit Request
```json
{
  "order_number": "ORD-20260410-A3F9K2",
  "bkash_number": "01812345678",
  "bkash_transaction_id": "TRX9B2X3K1"
}
```

---

## Admin Panel
Access at `/admin/` — manage users, products, orders, payments, coupons.

## Key Features
- BD phone number validation (`01XXXXXXXXX`)
- BD divisions as address choices
- Atomic stock decrement on order (prevents overselling)
- Stock restored on order cancellation with audit log
- Image auto-compression via Pillow (70–80% savings)
- JWT with token blacklisting on logout
- Coupon system (flat & percentage discounts)
- Order address snapshots (historical accuracy)
- Manual bKash verification flow
