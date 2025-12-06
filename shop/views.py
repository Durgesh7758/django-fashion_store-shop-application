import uuid
from datetime import timedelta
from io import BytesIO
from math import ceil
from urllib import request

from django.shortcuts import get_object_or_404, render, redirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum, IntegerField
from django.db.models.functions import Cast
from django.utils import timezone
from django.template.loader import get_template
from reportlab.pdfgen import canvas
from .models import Product, Order, OrderItem, Cart, UserAddress, Rating
from django.contrib.auth.decorators import user_passes_test
from collections import defaultdict

# Create your views here.

def index(request):
 
    allprods = []

    # Filters
    category_filter = request.GET.getlist('category')  # yaha Python me allowed hai
    price_filter = request.GET.get('price')

    catprods = Product.objects.values('category', 'id')
    categories = {item['category'] for item in catprods}

    price_ranges = {
        'Under 500': '0-500',
        '500-1000': '500-1000',
        '1000-2000': '1000-2000',
        'Above 2000': '2000-1000000'
    }

    for cat in categories:
        prod = Product.objects.filter(category=cat)

        # Apply category filter
        if category_filter and cat not in category_filter:
            continue

        # Apply price filter
        if price_filter:
            p_min, p_max = map(int, price_filter.split('-'))
            prod = prod.filter(price__gte=p_min, price__lte=p_max)

        n = len(prod)
        if n == 0:
            continue
        nSlides = ceil(n/4)
        allprods.append([prod, range(1, nSlides+1), nSlides])

    cart_count = 0
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()

    params = {
        'allprods': allprods,
        'categories': categories,
        'price_ranges': price_ranges,
        'cart_count': cart_count,
        'category_filter': category_filter,   # template me use karenge
        'price_filter': price_filter
    }
    return render(request, 'shop/index.html', params)

def about(request):
    return render(request, 'shop/about.html')

def contact(request):
    return HttpResponse('we are at contact')

def tracker(request):
    return HttpResponse('we are at tracker')


from django.db.models import Q  # already import nahi hua hoga

def search(request):
    query = request.GET.get('query', '')  # search input value

    products = []
    if query:
        # Search in product_name, desc, category
        products = Product.objects.filter(
            Q(product_name__icontains=query) |
            Q(desc__icontains=query) |
            Q(category__icontains=query)
        )

    context = {
        'products': products,
        'query': query
    }
    return render(request, 'shop/search.html', context)

def productView(request, id):
    product = Product.objects.get(id=id)
    return render(request, "shop/productview.html", {'product': product})

@login_required
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        size = request.POST.get("size")

        if not size:
            messages.error(request, "Please select a size before buying.")
            return redirect('shop:product_detail', product_id)

        # store to cart (same as add_to_cart)
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            size=size
        )
        cart_item.quantity = 1
        cart_item.save()

        return redirect("shop:checkout")   # 👈 NOW IT WILL GO TO NEXT STEP

    return redirect("shop:product_detail", product_id)


# def checkout(request):
#     return HttpResponse('we are at checkout')

def backupindex(request):
    return HttpResponse('we are at backupindex')


def copyindex(request):
    
    return render(request, 'shop/copyindex.html')

from .models import UserAddress

@login_required
def checkout(request):
    saved_addresses = UserAddress.objects.filter(user=request.user)

    if request.method == "POST":
        selected_address_id = request.POST.get("selected_address")

        if selected_address_id:
            addr = UserAddress.objects.get(id=selected_address_id)
        else:
            addr = UserAddress.objects.create(
                user=request.user,
                name=request.POST.get("name"),
                email=request.POST.get("email"),
                phone=request.POST.get("phone"),
                address=request.POST.get("address"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                pincode=request.POST.get("pincode"),
            )

        # ✅ Save selected address in session for payment page
        request.session['billing_address'] = str(addr)
        return redirect("shop:payment")

    return render(request, "shop/checkout.html", {"saved_addresses": saved_addresses})


@login_required
def payment(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty!")
        return redirect('shop:ShopHome')

    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    billing_address = request.session.get('billing_address', '')

    if request.method == "POST":
        method = request.POST.get('payment_method')
        billing_addr_post = request.POST.get('billing_address') or billing_address

        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            billing_address=billing_addr_post,
            status='Pending'
        )

        # Merge cart items with same product + size
        cart_dict = defaultdict(lambda: {'quantity': 0, 'size': '', 'product': None})
        for item in cart_items:
            key = (item.product.id, item.size)
            cart_dict[key]['product'] = item.product
            cart_dict[key]['size'] = item.size
            cart_dict[key]['quantity'] += item.quantity

        # Create OrderItem from merged data
        for (prod_id, size), data in cart_dict.items():
            OrderItem.objects.create(
                order=order,
                product=data['product'],
                user=request.user,
                quantity=data['quantity'],
                size=data['size']
            )

        # Handle payment method
        if method == "COD":
            order.payment_method = "COD"
            order.paid = False
            order.status = "Pending"
            order.save()
            cart_items.delete()
            messages.success(request, f"Order placed (COD). Order ID: {order.id}")
            return redirect('shop:order_detail', order_id=order.id)

        elif method == "Online":
            txn = str(uuid.uuid4()).replace('-', '')[:20]
            order.payment_method = "Online"
            order.txn_id = txn
            order.paid = True
            order.status = "Paid"
            order.save()
            cart_items.delete()
            messages.success(request, f"Payment successful. Order ID: {order.id}")
            return redirect('shop:invoice', order_id=order.id)

        else:
            messages.error(request, "Select a payment method.")
            return redirect('shop:payment')

    return render(request, 'shop/payment.html', {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'billing_address': billing_address
    })

@login_required
def invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)

    return render(request, 'shop/invoice.html', {
        'order': order,
        'cart_items': order_items,
        'total_price': order.total_amount
    })


@login_required
def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=(595, 842))  # A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, 800, f"Invoice - Order #{order.id}")
    p.setFont("Helvetica", 10)
    p.drawString(40, 780, f"Customer: {order.user.username}")
    p.drawString(300, 780, f"Date: {order.ordered_on.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(40, 760, "Billing Address:")

    text = p.beginText(40, 745)
    text.setFont("Helvetica", 9)
    for line in (order.billing_address or "").splitlines():
        text.textLine(line)
    p.drawText(text)

    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, 700, "Item")
    p.drawString(250, 700, "Size")   # 👈 NEW
    p.drawString(350, 700, "Qty")
    p.drawString(420, 700, "Price")
    p.drawString(500, 700, "Subtotal")

    y = 680
    p.setFont("Helvetica", 10)

    for item in order_items:
        p.drawString(40, y, item.product.product_name[:40])
        p.drawString(250, y, item.size if item.size else "—")   # 👈 SIZE
        p.drawString(350, y, str(item.quantity))
        p.drawString(420, y, f"₹{item.product.price}")

        subtotal = float(item.product.price) * item.quantity
        p.drawString(500, y, f"₹{subtotal:.2f}")
        y -= 18
        if y < 80:
            p.showPage()
            y = 800

    p.setFont("Helvetica-Bold", 12)
    p.drawString(400, y-10, "Total:")
    p.drawString(500, y-10, f"₹{order.total_amount:.2f}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')



@login_required
def payment_process(request):
    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        billing_address = request.POST.get("billing_address")

        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            messages.error(request, "Your cart is empty!")
            return redirect("shop:cart")

        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=sum(item.product.price * item.quantity for item in cart_items),
            payment_method=payment_method,
            billing_address=billing_address or "",
            ordered_on=timezone.now(),
            status="Pending"
        )

        # Move cart items to order items
                # Move cart items to order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                size=item.size   # <-- ADD THIS
            )


        cart_items.delete()  # Clear the cart

        # Redirect **directly to Order Detail / Confirmation**
        return redirect("shop:order_confirmation", order_id=order.id)

    return redirect("shop:cart")


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    return render(request, 'shop/order_confirmation.html', {
        'order': order,
        'order_items': order_items
    })

def admin_check(user):
    return user.is_staff

@login_required
@user_passes_test(admin_check)
def admin_dashboard(request):
    products = Product.objects.all()
    orders = Order.objects.all()
    users = User.objects.all() 
    return render(request, 'shop/admin_dashboard.html', {
        'products': products,
        'orders': orders,
        'users': users,
    })

@login_required
@user_passes_test(admin_check)
def edit_product(request, prod_id):
    product = Product.objects.get(id=prod_id)   # Correct Model name
    print("products :",product)
    
    if request.method == 'POST':
        product.product_name = request.POST.get('product_name')
        product.price = request.POST.get('price')
        product.category = request.POST.get('category')
        product.save()
        return redirect('shop:admin_dashboard')
    
    return render(request, 'shop/edit_product.html', {'product': product})


@login_required
@user_passes_test(admin_check)
def delete_product(request, prod_id):
    product = get_object_or_404(Product, id=prod_id)
    product.delete()
    return redirect('shop:admin_dashboard')


@login_required
@user_passes_test(admin_check)
def manage_users(request):
    users = User.objects.filter(is_staff=False)
    return render(request, 'shop/manage_users.html', {'users': users})

# ----------------- Admin Check -----------------

def admin_check(user):
    return user.is_staff  # sirf staff/admin users ke liye access

@login_required
@user_passes_test(admin_check)
def manage_users(request):
    users = User.objects.all()
    return render(request, 'shop/manage_users.html', {'users': users})

@login_required
@user_passes_test(admin_check)
def edit_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user_obj.username = request.POST['username']
        user_obj.email = request.POST['email']
        user_obj.is_staff = request.POST.get('is_staff') == 'on'
        user_obj.save()
        messages.success(request, f"User {user_obj.username} updated successfully!")
        return redirect('shop:admin_dashboard')
    return render(request, 'shop/edit_user.html', {'user_obj': user_obj})

@login_required
@user_passes_test(admin_check)
def delete_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    user_obj.delete()
    messages.success(request, "User deleted successfully!")
    return redirect('shop:admin_dashboard')

# ----------------- Add Product -----------------

@login_required
@user_passes_test(admin_check)
def add_product(request):
    if request.method == 'POST':
        name = request.POST['product_name']
        price = request.POST['price']
        category = request.POST['category']
        Product.objects.create(product_name=name, price=price, category=category)
        return redirect('shop:admin_dashboard')
    return render(request, 'shop/add_product.html')

# ----------------- Edit Product -----------------

# ----------------- Delete Product -----------------
@login_required
@user_passes_test(admin_check)
def delete_product(request, prod_id):
    product = get_object_or_404(Product, id=prod_id)
    product.delete()
    return redirect('shop:admin_dashboard')

# ----------------- Manage Users -----------------
@login_required
@user_passes_test(admin_check)
def manage_users(request):
    users = User.objects.filter(is_staff=False)
    return render(request, 'shop/manage_users.html', {'users': users})

# ----------------- Update Order Status -----------------
@login_required
@user_passes_test(admin_check)
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        order.status = status
        order.save()
    return redirect('shop:manage_orders')

# ================= AUTHENTICATION VIEWS =================

def register_user(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match...!")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Registration Successfull. Please Login.")
        return redirect('shop:login')

    return render(request, 'shop/register.html')

def login_user(request):
    if request.method == "POST":
        login_input = request.POST['username']  # username ya email
        password = request.POST['password']

        try:
            user_obj = User.objects.get(email=login_input)
            username = user_obj.username
        except User.DoesNotExist:
            username = login_input  # assume username

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('shop:ShopHome')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('shop:login')

    return render(request, 'shop/login.html')

def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out")
    # After logout also redirect to home page
    return redirect('shop:ShopHome')
  
@login_required
def add_to_cart(request, prod_id):
    product = get_object_or_404(Product, id=prod_id)

    # Home page se size nahi milta → None save karo
    size = request.POST.get("size", "")  # empty size allowed

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        size=size if size else None
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # Always go to cart page after adding
    return redirect('shop:view_cart')

@login_required
def update_cart_size(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)

    if request.method == "POST":
        size = request.POST.get('size')
        if size:
            cart_item.size = size
            cart_item.save()
            messages.success(request, f"Size updated to {size} for {cart_item.product.product_name}.")
    return redirect('shop:view_cart')


@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def increase_quantity(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    cart_item.quantity += 1
    cart_item.save()
    return redirect('shop:view_cart')

@login_required
def decrease_quantity(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()  # agar quantity 1 hai aur decrease karna chahen → remove from cart
    return redirect('shop:view_cart')

@login_required
def create_order(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        messages.error(request, "Your cart is empty!")
        return redirect('ShopHome')

    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    order = Order.objects.create(user=request.user, total_amount=total_amount)

    for item in cart_items:
        OrderItem.objects.create(
        order=order,
        product=item.product,
        quantity=item.quantity,
        size=item.size   # <-- ADD THIS
    )


    # Clear cart after order
    cart_items.delete()
    messages.success(request, f"Order #{order.id} placed successfully!")
    return redirect('order_detail', order_id=order.id)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    
    # Calculate subtotal for each item
    for item in order_items:
        item.subtotal = item.product.price * item.quantity

    # Handle status update
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if order.status == 'Pending':  #for pend.ordr
            order.status = new_status
            order.save()
        return redirect('shop:order_detail', order_id=order.id)

    return render(request, 'shop/order_detail.html', {
        'order': order,
        'order_items': order_items
    })

@login_required
def order_history(request):
# Logged-in user ke saare orders
    orders = Order.objects.filter(user=request.user).order_by('-ordered_on')
    return render(request, 'shop/order_history.html', {'orders': orders})

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shop_home_api(request):
    return Response({
        "message": "Welcome to Shop Home API!",
        "user": request.user.username
    })

def fashion(request):
    # All products
    all_products = Product.objects.all()

    # Optional: cart count for navbar
    cart_count = 0
    if request.user.is_authenticated:
        from .models import Cart
        cart_count = Cart.objects.filter(user=request.user).count()

    return render(request, 'shop/fashion.html', {
        'all_products': all_products,
        'cart_count': cart_count,
    })

from django.shortcuts import get_object_or_404, render
from .models import Product, Rating

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    comments = Rating.objects.filter(product=product).order_by('-id')  # newest first

    context = {
        'product': product,
        'comments': comments,
    }
    return render(request, 'shop/product_detail.html', context)

@login_required
def add_rating(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        review = request.POST.get("review", "")
        existing = Rating.objects.filter(user=request.user, product=product).first()

        if existing:
            existing.rating = rating
            existing.review = review
            existing.save()
        else:
            Rating.objects.create(
                user=request.user,
                product=product,
                rating=rating,
                review=review,
            )

    return redirect('shop:product_detail', product_id=product.id)

def bestseller(request):
    # Aggregate total quantity sold per product
    bestseller_qs = (
        OrderItem.objects
        .annotate(quantity_int=Cast('quantity', IntegerField()))
        .values('product')
        .annotate(total_sold=Sum('quantity_int'))
        .order_by('-total_sold')[:10]
    )

    product_order = {row['product']: (row['total_sold'] or 0) for row in bestseller_qs}

    products = list(Product.objects.filter(id__in=product_order.keys()))
    products.sort(key=lambda p: product_order[p.id], reverse=True)

    # Add total_sold as attribute for template
    for p in products:
        p.total_sold = product_order[p.id]

    return render(request, 'shop/bestseller.html', {'products': products})

def trending(request):
    trending_products = Product.objects.order_by('-id')[:12]  # latest 12 products
    return render(request, 'shop/trending.html', {'trending_products': trending_products})

def newlyadded(request):
    today = timezone.now().date()  # correct
    seven_days_ago = today - timedelta(days=7)

    new_products = Product.objects.filter(pub_date__gte=seven_days_ago).order_by('-pub_date')

    return render(request, 'shop/newlyadded.html', {'new_products': new_products})