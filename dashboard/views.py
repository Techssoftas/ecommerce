from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout,get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from api.models import *
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings


def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

# Authentication Views
@csrf_exempt
def login_view(request):
    if request.user.is_authenticated and request.user.user_type == 'admin':
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        print("Password received:", password)
        print("Login attempt for phone:", phone )
        user = authenticate(request, phone=phone, password=password)
        
        if user and user.user_type == 'admin':
            login(request, user)
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')
    
    return render(request, 'dashboard/auth/login.html')



User = get_user_model()

@csrf_exempt
def forgot_password_view(request):
    if request.method == 'POST':
        print("request.user:", request.user)
        new_password = request.POST.get('new_password')

        if not new_password:
            messages.error(request, "Please provide both email and new password.")
            return redirect('forgot_password_view')

        try:
            user = User.objects.get(email=request.user.email)

            # Set new password
            user.set_password(new_password)
            user.save()

            # Send confirmation email
            subject = "Password Changed Successfully"
            message = f"""
                Hi {user.username},

                Your password has been successfully changed.

                Your new password is: {new_password}

                If you did not request this change, please contact support immediately.
                """
            send_mail(subject, message.strip(), settings.DEFAULT_FROM_EMAIL, [user.email])

            messages.success(request, "Password changed and confirmation email sent.")
            return redirect('login_view')  # Redirect to login or wherever appropriate

        except User.DoesNotExist:
            messages.error(request, "No user found with this email.")
            return redirect('forgot_password_view')

    return render(request, 'dashboard/auth/forgot_password_manual.html')



@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Account Logout successfully..!')
    return redirect('dashboard:login_view')

# Dashboard Home
@login_required
# @user_passes_test(is_admin)
def dashboard(request):
    # Statistics
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_customers = CustomUser.objects.filter(user_type='customer').count()
    total_revenue = Order.objects.filter(status='Delivered').aggregate(
        total=Sum('total_amount'))['total'] or 0
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    
    # Low stock products
    low_stock_products = Product.objects.filter(stock__lt=10).order_by('stock')[:5]
    
    # Fetch orders with related user, payment, and order items
    orders = Order.objects.select_related('user', 'payment').prefetch_related('items__product').all().order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(orders, 10)  # 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    context = {
        'orders': page_obj,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'page_obj': page_obj, 
    }
    return render(request, 'dashboard/dashboard.html', context)

# Product Management
from django.db.models import Count

@login_required
@user_passes_test(is_admin)
def product_list(request):
    products = Product.objects.select_related('category').all().order_by('-created_at')
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search) | 
            Q(category__name__icontains=search)
        )
    
    # Get total product count
    total_products = products.count()
    
    # Get categories with product counts
    categories = Category.objects.annotate(product_count=Count('product')).filter(is_active=True)
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'total_products': total_products,
        'page_obj': page_obj,
        'categories': categories,
    }
    
    return render(request, 'dashboard/products/sub_category_list.html', context)

@login_required
@user_passes_test(is_admin)
def mens_products(request):
    # Filter products only for 'Mens'
    products = Product.objects.select_related('category') \
        .filter(subcategory='Mens') \
        .order_by('-created_at')

    # Search functionality
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(category__name__icontains=search)
        )

    # Get total product count
    total_products = products.count()

    # Only categories that have Mens products
    categories = Category.objects.filter(
        product__subcategory='Mens', is_active=True
    ).annotate(product_count=Count('product')).distinct()

    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'total_products': total_products,
        'page_obj': page_obj,
        'categories': categories,
    }

    
    return render(request, 'dashboard/products/mens_products.html', context)

@login_required
@user_passes_test(is_admin)
def womens_products(request):
    # Filter products only for 'Mens'
    products = Product.objects.select_related('category') \
        .filter(subcategory='Womens') \
        .order_by('-created_at')

    # Search functionality
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(category__name__icontains=search)
        )

    # Get total product count
    total_products = products.count()

    # Only categories that have Mens products
    categories = Category.objects.filter(
        product__subcategory='Womens', is_active=True
    ).annotate(product_count=Count('product')).distinct()

    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'total_products': total_products,
        'page_obj': page_obj,
        'categories': categories,
    }

    
    return render(request, 'dashboard/products/womens_products.html', context)
@login_required
@user_passes_test(is_admin)
def kids_boys_products(request):
    # Filter products only for 'Mens'
    products = Product.objects.select_related('category') \
        .filter(subcategory='Kids(Boys)') \
        .order_by('-created_at')

    # Search functionality
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(category__name__icontains=search)
        )

    # Get total product count
    total_products = products.count()

    # Only categories that have Mens products
    categories = Category.objects.filter(
        product__subcategory='Kids(Boys)', is_active=True
    ).annotate(product_count=Count('product')).distinct()

    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'total_products': total_products,
        'page_obj': page_obj,
        'categories': categories,
    }

    
    return render(request, 'dashboard/products/kids_boys_products.html', context)
@login_required
@user_passes_test(is_admin)
def kids_girls_products(request):
    # Filter products only for 'Mens'
    products = Product.objects.select_related('category') \
        .filter(subcategory='Kids(Girls)') \
        .order_by('-created_at')

    # Search functionality
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(category__name__icontains=search)
        )

    # Get total product count
    total_products = products.count()

    # Only categories that have Mens products
    categories = Category.objects.filter(
        product__subcategory='Kids(Girls)', is_active=True
    ).annotate(product_count=Count('product')).distinct()

    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'total_products': total_products,
        'page_obj': page_obj,
        'categories': categories,
    }

    
    return render(request, 'dashboard/products/kids_girls_products.html', context)

@login_required
@user_passes_test(is_admin)

def product_details(request, product_id):
    # Get product with related data
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related(
            'images', 
            'variants__sizes', 
            'variants__images', 
            'reviews__images'
        ),
        id=product_id
    )

    # Approved reviews
    approved_reviews = product.reviews.filter(is_approved=True)

    # Group active color variants and their active size variants
    color_variants = product.variants.filter(is_active=True)
    size_variants = []  # List of all sizes across variants

    for variant in color_variants:
        sizes = variant.sizes.filter(stock__gt=0)  # Only sizes with stock
        size_variants.extend(sizes)

    # Primary product image
    primary_image = product.primary_image

    # Minimum order total
    minimum_order_total = product.minimum_order_quantity * product.get_price

    # Total revenue
    total_revenue = product.total_sold * product.get_price

    context = {
        'product': product,
        'color_variants': color_variants,
        'size_variants': size_variants,
        'approved_reviews': approved_reviews,
        'primary_image': primary_image,
        'minimum_order_total': minimum_order_total,
        'total_revenue': total_revenue,
    }

    return render(request, 'dashboard/products/product_details.html', context)



@login_required
@csrf_exempt
@user_passes_test(is_admin)
def product_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        subcategory = request.POST.get('subcategory')
        description = request.POST.get('description')
        brand = request.POST.get('brand')
        model_name = request.POST.get('model_name') 
        is_cod_available = request.POST.get('cod_available') == 'on'  
        is_returnable = request.POST.get('is_returnable')   == 'on'
        is_free_shipping = request.POST.get('free_shipping') == 'on'  
        
        discount_price = request.POST.get('discount_price')
        sku = request.POST.get('sku')
        if not sku:
            sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

        short_description = request.POST.get('short_description')
        
        specifications = request.POST.get('specifications')
        key_features = request.POST.get('key_features')
        subcategory = request.POST.get('subcategory')
         
        discount_price = request.POST.get('discount_price')
        product_mrp_price = request.POST.get('product_mrp_price',0)
        product_selling_price = request.POST.get('product_selling_price',0)
        print(product_mrp_price,product_selling_price)
        stock = request.POST.get('stock',0)
        minimum_order_quantity = request.POST.get('minimum_order_quantity')
        maximum_order_quantity = request.POST.get('maximum_order_quantity')
        
        barcode = request.POST.get('barcode')
        hsn_code = request.POST.get('hsn_code')
        weight = request.POST.get('weight')
        dimensions_length = request.POST.get('dimensions_length')
        dimensions_width = request.POST.get('dimensions_width')
        dimensions_height = request.POST.get('dimensions_height')
        condition = request.POST.get('condition')
        availability_status = request.POST.get('availability_status')
        meta_title = request.POST.get('meta_title')
        meta_description = request.POST.get('meta_description')
        tags = request.POST.get('tags')
        #   = request.POST.get('is_free_shipping') == 'on'
        # delivery_time_min = request.POST.get('delivery_time_min')
        # delivery_time_max = request.POST.get('delivery_time_max')
        # is_active = request.POST.get('is_active') == 'on'
        # is_featured = request.POST.get('is_featured') == 'on'
        # is_bestseller = request.POST.get('is_bestseller') == 'on'
        # is_new_arrival = request.POST.get('is_new_arrival') == 'on'
        # is_trending = request.POST.get('is_trending') == 'on'
        # is_deal_of_day = request.POST.get('is_deal_of_day') == 'on'
        # is_replaceable = request.POST.get('is_replaceable') == 'on'
        # warranty_period = request.POST.get('warranty_period')
        # warranty_type = request.POST.get('warranty_type')
        # warranty_description = request.POST.get('warranty_description')
        # return_period = request.POST.get('return_period')
        # return_policy = request.POST.get('return_policy')
        category = get_object_or_404(Category, id=category_id)
        product = Product.objects.create(
            name=name,
            brand=brand,
            model_name=model_name,
            # short_description=short_description,
            description=description,
            # specifications=specifications,
            # key_features=key_features,
            category=category,
            subcategory=subcategory,
            price=product_selling_price,
            discount_price=discount_price,
            mrp=product_mrp_price,
            stock=stock,
            # minimum_order_quantity=minimum_order_quantity,
            # maximum_order_quantity=maximum_order_quantity,
            sku=sku,
            # barcode=barcode,
            hsn_code=hsn_code,
            # weight=weight,
            # dimensions_length=dimensions_length,
            # dimensions_width=dimensions_width,
            # dimensions_height=dimensions_height,
            # condition=condition,
            # availability_status=availability_status,
            # meta_title=meta_title,  
            # meta_description=meta_description,
            # tags=tags,
            is_free_shipping=is_free_shipping,
            # delivery_time_min=delivery_time_min,
            # delivery_time_max=delivery_time_max,
            # is_active=is_active,
            # is_featured=is_featured,
            # is_bestseller=is_bestseller,
            # is_new_arrival=is_new_arrival,
            # is_trending=is_trending,
            # is_deal_of_day=is_deal_of_day,
            is_returnable=is_returnable,
            # is_replaceable=is_replaceable,
            is_cod_available=is_cod_available,
            # warranty_period=warranty_period,
            # warranty_type=warranty_type,
            # warranty_description=warranty_description,
            # return_period=return_period,
            # return_policy=return_policy
        )   
        # Handle product images
        product_images = request.FILES.getlist('product_images')
        print("Images count:", len(product_images))
        for idx, image in enumerate(product_images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(idx == 0)
            )
        # Handle product variants
        variant_sizes = request.POST.getlist('variant_sizes')
        # If it still comes as a single string like "S,M,L,XL"
        if len(variant_sizes) == 1 and "," in variant_sizes[0]:
            variant_sizes = [s.strip() for s in variant_sizes[0].split(",")]

        variant_mrp = request.POST.get('variant_mrp_price')
        variant_selling = request.POST.get('variant_selling_price')
        variant_image = request.FILES.get('variant_image')
        hex_color_code = request.POST.get('hex_color_code')
        variant_value = request.POST.get('variant_value')
        # for size in variant_sizes and hex_color_code:
        ProductVariant.objects.create(product=product,
                                    size=variant_sizes,
                                    variant_value=variant_value,
                                    hex_color_code=hex_color_code,
                                    mrp=variant_mrp,
                                    price=variant_selling,
                                    variant_image=variant_image,
                                    sku =sku,   
                                        )
        # for color in variant_colors:
        #     ProductVariant.objects.create(product=product, variant_type='color', hex_color_code=color)



            
        messages.success(request, 'Product created successfully!')
        return redirect('dashboard:product_list')
    
    
    return render(request, 'dashboard/products/product_create.html', {'categories': categories})
import json
@login_required
@csrf_exempt
@user_passes_test(is_admin)
def mens_product_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        print(request.POST) 
        for key, value in request.POST.items():
            print("RAW POST KEY:", key, "=>", value)
        
        sizes_json = request.POST.get("sizes_json")
        if sizes_json:
            try:
                sizes = json.loads(sizes_json)
                print("✅ Sizes received:", sizes)
                # Example access
                for row in sizes:
                    print(row["size"], row["mrp"], row["price"], row["stock"])
            except json.JSONDecodeError as e:

                print("JSON parse error:", e)
        print("Parsed sizes:", sizes_json)
                
            
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        brand = request.POST.get('brand')
        occasion = request.POST.get('occasion')
        model_name = request.POST.get('model_name') 
        is_cod_available = request.POST.get('cod_available') == 'on'  
        is_returnable = request.POST.get('is_returnable')   == 'on'
        is_free_shipping = request.POST.get('free_shipping') == 'on'  
        is_active = request.POST.get('is_active') == 'on'  
        
        discount_price = request.POST.get('discount_price')
        sku = request.POST.get('sku')
        if not sku:
            sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

        short_description = request.POST.get('short_description')
        
        key_features = {}
        for key, value in request.POST.items():
            if key.startswith("key_features["):
                # extract the field name inside brackets
                field_name = key[len("key_features["):-1]  
                key_features[field_name] = value

        
        key_features = key_features
        subcategory = 'Mens'
         
        discount_price = request.POST.get('discount_price')
        product_mrp_price = request.POST.get('product_mrp_price',0)
        product_selling_price = request.POST.get('product_selling_price',0)
      
        stock = request.POST.get('stock',0)
        minimum_order_quantity = request.POST.get('minimum_order_quantity')
        maximum_order_quantity = request.POST.get('maximum_order_quantity')
        
        barcode = request.POST.get('barcode')
        hsn_code = int(request.POST.get('hsn_code') or 0)
        weight = float(request.POST.get('weight') or 0)
        dimensions_length = float(request.POST.get('dimensions_length') or 0)
        dimensions_width = float(request.POST.get('dimensions_width') or 0)
        dimensions_height = float(request.POST.get('dimensions_height') or 0)

        condition = request.POST.get('condition')
        availability_status = request.POST.get('availability_status')
        meta_title = request.POST.get('meta_title')
        meta_description = request.POST.get('meta_description')
        tags = request.POST.get('tags')
        #   = request.POST.get('is_free_shipping') == 'on'
        # delivery_time_min = request.POST.get('delivery_time_min')
        # delivery_time_max = request.POST.get('delivery_time_max')
        is_active = request.POST.get('is_active') == 'on'
        # is_featured = request.POST.get('is_featured') == 'on'
        # is_bestseller = request.POST.get('is_bestseller') == 'on'
        # is_new_arrival = request.POST.get('is_new_arrival') == 'on'
        # is_trending = request.POST.get('is_trending') == 'on'
        # is_deal_of_day = request.POST.get('is_deal_of_day') == 'on'
        is_replaceable = request.POST.get('is_replaceable') == 'on'
        # warranty_period = request.POST.get('warranty_period')
        # warranty_type = request.POST.get('warranty_type')
        # warranty_description = request.POST.get('warranty_description')
        return_period = int(request.POST.get('return_period') or 0)
        replace_period = int(request.POST.get('replace_period')or 0)
        # return_policy = request.POST.get('return_policy')
        category = get_object_or_404(Category, id=category_id)
        product = Product.objects.create(
            name=name,
            brand=brand,
            model_name=model_name,
            # short_description=short_description,
            description=description,
            # specifications=specifications,
            key_features=key_features,
            category=category,
            subcategory=subcategory,
            occasion = occasion,
            price=product_selling_price,
            discount_price=discount_price,
            mrp=product_mrp_price,
            stock=stock,
            # minimum_order_quantity=minimum_order_quantity,
            # maximum_order_quantity=maximum_order_quantity,
            sku=sku,
            # barcode=barcode,
            hsn_code=hsn_code,
            weight=weight,
            dimensions_length=dimensions_length,
            dimensions_width=dimensions_width,
            dimensions_height=dimensions_height,
            # condition=condition,
            # availability_status=availability_status,
            # meta_title=meta_title,  
            # meta_description=meta_description,
            # tags=tags,
            is_free_shipping=is_free_shipping,
            # delivery_time_min=delivery_time_min,
            # delivery_time_max=delivery_time_max,
            is_active=is_active,
            # is_featured=is_featured,
            # is_bestseller=is_bestseller,
            # is_new_arrival=is_new_arrival,
            # is_trending=is_trending,
            # is_deal_of_day=is_deal_of_day,
            is_returnable=is_returnable,
            is_replaceable=is_replaceable,
            is_cod_available=is_cod_available,
            # warranty_period=warranty_period,
            # warranty_type=warranty_type,
            # warranty_description=warranty_description,
            return_period=return_period,
            replace_period=replace_period,
            # return_policy=return_policy
        )   
        # Handle product images
        product_images = request.FILES.getlist('product_images')
        for idx, image in enumerate(product_images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(idx == 0)
            )
        # Handle product variants
        


        hex_color_code = request.POST.get('hex_color_code')
        variant_value = request.POST.get('variant_value')
        # for size in variant_sizes and hex_color_code:
        variant = ProductVariant.objects.create(product=product,
                                    color_name=variant_value,
                                    hex_color_code=hex_color_code,
                                    )
        
        # ✅ Handle sizes from JSON
        sizes_json = request.POST.get("sizes_json")
        if sizes_json:
            try:
                sizes = json.loads(sizes_json)
                for row in sizes:
                    SizeVariant.objects.create(
                        variant=variant,
                        size=row["size"],
                        sku=f"{product.id}-{variant.id}-{row['size']}",
                        mrp=row["mrp"],
                        price=row["price"],
                        discount_price=row["discount_price"] or None,
                        stock=row["stock"]
                    )
            except json.JSONDecodeError as e:
                print("❌ JSON parse error:", e)
                
        # Step 4: Variant Images save (Dropzone)
        variant_images = request.FILES.getlist("variant_images")

        for idx, image in enumerate(variant_images):
            ProductVariantImage.objects.create(
                variant=variant,
                image=image,
                is_default=True if idx == 0 else False  # first image default
            )


            
        messages.success(request, 'Product created successfully!')
        return redirect('dashboard:mens_products')
    
    
    return render(request, 'dashboard/products/mens_product_create.html', {'categories': categories})

@login_required
@csrf_exempt
@user_passes_test(is_admin)
def womens_product_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        brand = request.POST.get('brand')
        occasion = request.POST.get('occasion')
        model_name = request.POST.get('model_name') 
        is_cod_available = request.POST.get('cod_available') == 'on'  
        is_returnable = request.POST.get('is_returnable')   == 'on'
        is_free_shipping = request.POST.get('free_shipping') == 'on'  
        is_active = request.POST.get('is_active') == 'on'  
        discount_price = request.POST.get('discount_price')
        sku = request.POST.get('sku')
        if not sku:
            sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

        short_description = request.POST.get('short_description')
        
        key_features = {}
        for key, value in request.POST.items():
            if key.startswith("key_features["):
                # extract the field name inside brackets
                field_name = key[len("key_features["):-1]  
                key_features[field_name] = value

        
        key_features = key_features
        subcategory = 'Womens'
         
        discount_price = request.POST.get('discount_price')
        product_mrp_price = request.POST.get('product_mrp_price',0)
        product_selling_price = request.POST.get('product_selling_price',0)
      
        stock = request.POST.get('stock',0)
        minimum_order_quantity = request.POST.get('minimum_order_quantity')
        maximum_order_quantity = request.POST.get('maximum_order_quantity')
        
        barcode = request.POST.get('barcode')
        hsn_code = int(request.POST.get('hsn_code') or 0)
        weight = float(request.POST.get('weight') or 0)
        dimensions_length = float(request.POST.get('dimensions_length') or 0)
        dimensions_width = float(request.POST.get('dimensions_width') or 0)
        dimensions_height = float(request.POST.get('dimensions_height') or 0)
        return_period = int(request.POST.get('return_period') or 0)
        replace_period = int(request.POST.get('replace_period')or 0)
        condition = request.POST.get('condition')
        availability_status = request.POST.get('availability_status')
        meta_title = request.POST.get('meta_title')
        meta_description = request.POST.get('meta_description')
        tags = request.POST.get('tags')
        #   = request.POST.get('is_free_shipping') == 'on'
        # delivery_time_min = request.POST.get('delivery_time_min')
        # delivery_time_max = request.POST.get('delivery_time_max')
        # is_active = request.POST.get('is_active') == 'on'
        # is_featured = request.POST.get('is_featured') == 'on'
        # is_bestseller = request.POST.get('is_bestseller') == 'on'
        # is_new_arrival = request.POST.get('is_new_arrival') == 'on'
        # is_trending = request.POST.get('is_trending') == 'on'
        # is_deal_of_day = request.POST.get('is_deal_of_day') == 'on'
        # is_replaceable = request.POST.get('is_replaceable') == 'on'
        # warranty_period = request.POST.get('warranty_period')
        # warranty_type = request.POST.get('warranty_type')
        # warranty_description = request.POST.get('warranty_description')
        category = get_object_or_404(Category, id=category_id)
        product = Product.objects.create(
            name=name,
            brand=brand,
            model_name=model_name,
            # short_description=short_description,
            description=description,
            # specifications=specifications,
            key_features=key_features,
            category=category,
            subcategory=subcategory,
            occasion = occasion,
            price=product_selling_price,
            discount_price=discount_price,
            mrp=product_mrp_price,
            stock=stock,
            # minimum_order_quantity=minimum_order_quantity,
            # maximum_order_quantity=maximum_order_quantity,
            sku=sku,
            # barcode=barcode,
            hsn_code=hsn_code,
            weight=weight,
            dimensions_length=dimensions_length,
            dimensions_width=dimensions_width,
            dimensions_height=dimensions_height,
            # condition=condition,
            # availability_status=availability_status,
            # meta_title=meta_title,  
            # meta_description=meta_description,
            # tags=tags,
            is_free_shipping=is_free_shipping,
            # delivery_time_min=delivery_time_min,
            # delivery_time_max=delivery_time_max,
            is_active=is_active,
            # is_featured=is_featured,
            # is_bestseller=is_bestseller,
            # is_new_arrival=is_new_arrival,
            # is_trending=is_trending,
            # is_deal_of_day=is_deal_of_day,
            is_returnable=is_returnable,
            # is_replaceable=is_replaceable,
            is_cod_available=is_cod_available,
            # warranty_period=warranty_period,
            # warranty_type=warranty_type,
            # warranty_description=warranty_description,
            return_period=return_period,
            replace_period=replace_period,
            # return_policy=return_policy
        )   
        # Handle product images
        product_images = request.FILES.getlist('product_images')
        print("Images count:", len(product_images))
        for idx, image in enumerate(product_images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(idx == 0)
            )
        # Handle product variants
        variant_sizes = request.POST.getlist('variant_sizes')
        # If it still comes as a single string like "S,M,L,XL"
        if len(variant_sizes) == 1 and "," in variant_sizes[0]:
            variant_sizes = [s.strip() for s in variant_sizes[0].split(",")]

        variant_mrp = request.POST.get('variant_mrp_price')
        variant_selling = request.POST.get('variant_selling_price')
        variant_image = request.FILES.get('variant_image')
        hex_color_code = request.POST.get('hex_color_code')
        variant_value = request.POST.get('variant_value')
        # for size in variant_sizes and hex_color_code:
        ProductVariant.objects.create(product=product,
                                    size=variant_sizes,
                                    variant_value=variant_value,
                                    hex_color_code=hex_color_code,
                                    mrp=variant_mrp,
                                    price=variant_selling,
                                    variant_image=variant_image,
                                    sku =sku,   
                                        )
        # for color in variant_colors:
        #     ProductVariant.objects.create(product=product, variant_type='color', hex_color_code=color)



            
        messages.success(request, 'Product created successfully!')
        return redirect('dashboard:womens_products')
    
    
    return render(request, 'dashboard/products/womens_product_create.html', {'categories': categories})

@login_required
@csrf_exempt
@user_passes_test(is_admin)
def kids_boys_product_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        brand = request.POST.get('brand')
        occasion = request.POST.get('occasion')
        model_name = request.POST.get('model_name') 
        is_cod_available = request.POST.get('cod_available') == 'on'  
        is_returnable = request.POST.get('is_returnable')   == 'on'
        is_free_shipping = request.POST.get('free_shipping') == 'on'  
        
        discount_price = request.POST.get('discount_price')
        sku = request.POST.get('sku')
        if not sku:
            sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

        short_description = request.POST.get('short_description')
        
        key_features = {}
        for key, value in request.POST.items():
            if key.startswith("key_features["):
                # extract the field name inside brackets
                field_name = key[len("key_features["):-1]  
                key_features[field_name] = value

        
        key_features = key_features
        subcategory = 'Kids(Boys)'
         
        discount_price = request.POST.get('discount_price')
        product_mrp_price = request.POST.get('product_mrp_price',0)
        product_selling_price = request.POST.get('product_selling_price',0)
      
        stock = request.POST.get('stock',0)
        minimum_order_quantity = request.POST.get('minimum_order_quantity')
        maximum_order_quantity = request.POST.get('maximum_order_quantity')
        
        barcode = request.POST.get('barcode')
        hsn_code = int(request.POST.get('hsn_code') or 0)
        weight = float(request.POST.get('weight') or 0)
        dimensions_length = float(request.POST.get('dimensions_length') or 0)
        dimensions_width = float(request.POST.get('dimensions_width') or 0)
        dimensions_height = float(request.POST.get('dimensions_height') or 0)
        condition = request.POST.get('condition')
        availability_status = request.POST.get('availability_status')
        meta_title = request.POST.get('meta_title')
        meta_description = request.POST.get('meta_description')
        tags = request.POST.get('tags')
        #   = request.POST.get('is_free_shipping') == 'on'
        # delivery_time_min = request.POST.get('delivery_time_min')
        # delivery_time_max = request.POST.get('delivery_time_max')
        is_active = request.POST.get('is_active') == 'on'
        # is_featured = request.POST.get('is_featured') == 'on'
        # is_bestseller = request.POST.get('is_bestseller') == 'on'
        # is_new_arrival = request.POST.get('is_new_arrival') == 'on'
        # is_trending = request.POST.get('is_trending') == 'on'
        # is_deal_of_day = request.POST.get('is_deal_of_day') == 'on'
        # is_replaceable = request.POST.get('is_replaceable') == 'on'
        # warranty_period = request.POST.get('warranty_period')
        # warranty_type = request.POST.get('warranty_type')
        # warranty_description = request.POST.get('warranty_description')
        return_period = int(request.POST.get('return_period') or 0)
        replace_period = int(request.POST.get('replace_period')or 0)
        # return_policy = request.POST.get('return_policy')
        category = get_object_or_404(Category, id=category_id)
        product = Product.objects.create(
            name=name,
            brand=brand,
            model_name=model_name,
            # short_description=short_description,
            description=description,
            # specifications=specifications,
            key_features=key_features,
            category=category,
            subcategory=subcategory,
            occasion = occasion,
            price=product_selling_price,
            discount_price=discount_price,
            mrp=product_mrp_price,
            stock=stock,
            # minimum_order_quantity=minimum_order_quantity,
            # maximum_order_quantity=maximum_order_quantity,
            sku=sku,
            # barcode=barcode,
            hsn_code=hsn_code,
            weight=weight,
            dimensions_length=dimensions_length,
            dimensions_width=dimensions_width,
            dimensions_height=dimensions_height,
            # condition=condition,
            # availability_status=availability_status,
            # meta_title=meta_title,  
            # meta_description=meta_description,
            # tags=tags,
            is_free_shipping=is_free_shipping,
            # delivery_time_min=delivery_time_min,
            # delivery_time_max=delivery_time_max,
            is_active=is_active,
            # is_featured=is_featured,
            # is_bestseller=is_bestseller,
            # is_new_arrival=is_new_arrival,
            # is_trending=is_trending,
            # is_deal_of_day=is_deal_of_day,
            is_returnable=is_returnable,
            # is_replaceable=is_replaceable,
            is_cod_available=is_cod_available,
            # warranty_period=warranty_period,
            # warranty_type=warranty_type,
            # warranty_description=warranty_description,
            return_period=return_period,
            replace_period=replace_period,
            # return_policy=return_policy
        )   
        # Handle product images
        product_images = request.FILES.getlist('product_images')
        print("Images count:", len(product_images))
        for idx, image in enumerate(product_images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(idx == 0)
            )
        # Handle product variants
        variant_sizes = request.POST.getlist('variant_sizes')
        # If it still comes as a single string like "S,M,L,XL"
        if len(variant_sizes) == 1 and "," in variant_sizes[0]:
            variant_sizes = [s.strip() for s in variant_sizes[0].split(",")]

        variant_mrp = request.POST.get('variant_mrp_price')
        variant_selling = request.POST.get('variant_selling_price')
        variant_image = request.FILES.get('variant_image')
        hex_color_code = request.POST.get('hex_color_code')
        variant_value = request.POST.get('variant_value')
        # for size in variant_sizes and hex_color_code:
        ProductVariant.objects.create(product=product,
                                    size=variant_sizes,
                                    variant_value=variant_value,
                                    hex_color_code=hex_color_code,
                                    mrp=variant_mrp,
                                    price=variant_selling,
                                    variant_image=variant_image,
                                    sku =sku,   
                                        )
        # for color in variant_colors:
        #     ProductVariant.objects.create(product=product, variant_type='color', hex_color_code=color)



            
        messages.success(request, 'Product created successfully!')
        return redirect('dashboard:kids_boys_products')
    
    
    return render(request, 'dashboard/products/kids_boys_product_create.html', {'categories': categories})

@login_required
@csrf_exempt
@user_passes_test(is_admin)
def kids_girls_product_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        brand = request.POST.get('brand')
        occasion = request.POST.get('occasion')
        model_name = request.POST.get('model_name') 
        is_cod_available = request.POST.get('cod_available') == 'on'  
        is_returnable = request.POST.get('is_returnable')   == 'on'
        is_free_shipping = request.POST.get('free_shipping') == 'on'  
        
        discount_price = request.POST.get('discount_price')
        sku = request.POST.get('sku')
        if not sku:
            sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

        short_description = request.POST.get('short_description')
        
        key_features = {}
        for key, value in request.POST.items():
            if key.startswith("key_features["):
                # extract the field name inside brackets
                field_name = key[len("key_features["):-1]  
                key_features[field_name] = value

        
        key_features = key_features
        subcategory = 'Kids(Girls)'
         
        discount_price = request.POST.get('discount_price')
        product_mrp_price = request.POST.get('product_mrp_price',0)
        product_selling_price = request.POST.get('product_selling_price',0)
      
        stock = request.POST.get('stock',0)
        minimum_order_quantity = request.POST.get('minimum_order_quantity')
        maximum_order_quantity = request.POST.get('maximum_order_quantity')
        
        barcode = request.POST.get('barcode')
        hsn_code = int(request.POST.get('hsn_code') or 0)
        weight = float(request.POST.get('weight') or 0)
        dimensions_length = float(request.POST.get('dimensions_length') or 0)
        dimensions_width = float(request.POST.get('dimensions_width') or 0)
        dimensions_height = float(request.POST.get('dimensions_height') or 0)
        condition = request.POST.get('condition')
        availability_status = request.POST.get('availability_status')
        meta_title = request.POST.get('meta_title')
        meta_description = request.POST.get('meta_description')
        tags = request.POST.get('tags')
        #   = request.POST.get('is_free_shipping') == 'on'
        # delivery_time_min = request.POST.get('delivery_time_min')
        # delivery_time_max = request.POST.get('delivery_time_max')
        is_active = request.POST.get('is_active') == 'on'
        # is_featured = request.POST.get('is_featured') == 'on'
        # is_bestseller = request.POST.get('is_bestseller') == 'on'
        # is_new_arrival = request.POST.get('is_new_arrival') == 'on'
        # is_trending = request.POST.get('is_trending') == 'on'
        # is_deal_of_day = request.POST.get('is_deal_of_day') == 'on'
        # is_replaceable = request.POST.get('is_replaceable') == 'on'
        # warranty_period = request.POST.get('warranty_period')
        # warranty_type = request.POST.get('warranty_type')
        # warranty_description = request.POST.get('warranty_description')
        return_period = int(request.POST.get('return_period') or 0)
        replace_period = int(request.POST.get('replace_period')or 0)
        # return_policy = request.POST.get('return_policy')
        category = get_object_or_404(Category, id=category_id)
        product = Product.objects.create(
            name=name,
            brand=brand,
            model_name=model_name,
            # short_description=short_description,
            description=description,
            # specifications=specifications,
            key_features=key_features,
            category=category,
            subcategory=subcategory,
            occasion = occasion,
            price=product_selling_price,
            discount_price=discount_price,
            mrp=product_mrp_price,
            stock=stock,
            # minimum_order_quantity=minimum_order_quantity,
            # maximum_order_quantity=maximum_order_quantity,
            sku=sku,
            # barcode=barcode,
            hsn_code=hsn_code,
            weight=weight,
            dimensions_length=dimensions_length,
            dimensions_width=dimensions_width,
            dimensions_height=dimensions_height,
            # condition=condition,
            # availability_status=availability_status,
            # meta_title=meta_title,  
            # meta_description=meta_description,
            # tags=tags,
            is_free_shipping=is_free_shipping,
            # delivery_time_min=delivery_time_min,
            # delivery_time_max=delivery_time_max,
            is_active=is_active,
            # is_featured=is_featured,
            # is_bestseller=is_bestseller,
            # is_new_arrival=is_new_arrival,
            # is_trending=is_trending,
            # is_deal_of_day=is_deal_of_day,
            is_returnable=is_returnable,
            # is_replaceable=is_replaceable,
            is_cod_available=is_cod_available,
            # warranty_period=warranty_period,
            # warranty_type=warranty_type,
            # warranty_description=warranty_description,
            return_period=return_period,
            replace_period=replace_period,
            # return_policy=return_policy
        )   
        # Handle product images
        product_images = request.FILES.getlist('product_images')
        print("Images count:", len(product_images))
        for idx, image in enumerate(product_images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(idx == 0)
            )
        # Handle product variants
        variant_sizes = request.POST.getlist('variant_sizes')
        # If it still comes as a single string like "S,M,L,XL"
        if len(variant_sizes) == 1 and "," in variant_sizes[0]:
            variant_sizes = [s.strip() for s in variant_sizes[0].split(",")]

        variant_mrp = request.POST.get('variant_mrp_price')
        variant_selling = request.POST.get('variant_selling_price')
        variant_image = request.FILES.get('variant_image')
        hex_color_code = request.POST.get('hex_color_code')
        variant_value = request.POST.get('variant_value')
        # for size in variant_sizes and hex_color_code:
        ProductVariant.objects.create(product=product,
                                    size=variant_sizes,
                                    variant_value=variant_value,
                                    hex_color_code=hex_color_code,
                                    mrp=variant_mrp,
                                    price=variant_selling,
                                    variant_image=variant_image,
                                    sku =sku,   
                                        )
        # for color in variant_colors:
        #     ProductVariant.objects.create(product=product, variant_type='color', hex_color_code=color)



            
        messages.success(request, 'Product created successfully!')
        return redirect('dashboard:kids_girls_products')
    
    
    return render(request, 'dashboard/products/kids_girls_product_create.html', {'categories': categories})

@login_required
@csrf_exempt
@user_passes_test(is_admin)
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        subcategory = request.POST.get('subcategory')
        description = request.POST.get('description')
        brand = request.POST.get('brand')
        model_name = request.POST.get('model_name')
        is_cod_available = request.POST.get('cod_available') == 'on'
        is_returnable = request.POST.get('is_returnable') == 'on'
        is_free_shipping = request.POST.get('free_shipping') == 'on'
        is_active = request.POST.get('is_active') == 'on'  

        discount_price = request.POST.get('discount_price') or 0
        mrp_price = request.POST.get('product_mrp_price') or 0
        selling_price = request.POST.get('product_selling_price') or 0
        stock = request.POST.get('stock') or 0
        sku = request.POST.get('sku') or product.sku  # Preserve existing SKU

        hsn_code = request.POST.get('hsn_code')
        short_description = request.POST.get('short_description')
        condition = request.POST.get('condition')
        availability_status = request.POST.get('availability_status')

        # Fetch category
        category = get_object_or_404(Category, id=category_id)

        # Update product fields
        product.name = name
        product.brand = brand
        product.model_name = model_name
        product.description = description
        product.category = category
        product.subcategory = subcategory
        product.price = selling_price
        product.discount_price = discount_price
        product.mrp = mrp_price
        product.stock = stock
        product.sku = sku
        product.hsn_code = hsn_code
        product.is_cod_available = is_cod_available
        product.is_returnable = is_returnable
        product.is_free_shipping = is_free_shipping
        product.is_active = is_active

        product.save()

        # Handle product images
        product_images = request.FILES.getlist('product_images')
        print("Uploaded images count:", len(product_images))
        if product_images:
            # Check if a primary image already exists for the product
            primary_exists = product.images.filter(is_primary=True).exists()
            for idx, image in enumerate(product_images):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=(not primary_exists and idx == 0)
                )

        messages.success(request, 'Product updated successfully!')
        return redirect('dashboard:product_list')

    return render(request, 'dashboard/products/product_update.html', {
        'product': product,
        'categories': categories,
        'variants': product.variants.all(),
    })



@login_required
@csrf_exempt
@user_passes_test(is_admin)
def product_delete(request, pk):
    product = get_object_or_404(Product, id=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect("dashboard:product_list")

@login_required
@user_passes_test(is_admin)
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    # Only the user who created the review can delete it
    if request.user == review.user or request.user.is_superuser:
        review.delete()
        return redirect('dashboard:product_details', product_id=review.product.id)  # or wherever you want to redirect
    else:
        return redirect('unauthorized')
    
from datetime import datetime, timedelta
# Order Management
@login_required
@csrf_exempt
@user_passes_test(is_admin)
def orders_list(request):
    # Fetch orders with related user, payment, and order items
    orders = Order.objects.select_related('user', 'payment').prefetch_related('items__product').all().order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(orders, 10)  # 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all status choices for filter
    status_choices = Order.ORDER_STATUS
    
    # Calculate counts for dashboard cards
    total_orders = Order.objects.count()
    processing = Order.objects.filter(status='Processing').count()
    pending_orders = Order.objects.filter(status='Pending').count()
    delivered_orders = Order.objects.filter(status='Delivered').count()
    cancelled_orders = Order.objects.filter(status='Cancelled').count()
    
    return render(request, 'dashboard/orders/orders_list.html', {
        'orders': page_obj,  # Use page_obj for paginated orders
        'status_choices': status_choices,
        'current_status': status_filter,
        'total_orders': total_orders,
        'processing': processing,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'page_obj': page_obj,  # Pass page_obj for pagination
    })

from django.db.models import Prefetch, Q
@login_required
@user_passes_test(is_admin)
def return_orders(request):
    # Prefetch only ReturnRequest objects where request_type is 'Return'
    # Filter ReturnRequest for only 'Return' type requests
    orders = ReturnRequest.objects.filter(request_type='Return') \
        .select_related('user', 'order_item__order') \
        .prefetch_related('order_item__product') \
        .order_by('-requested_at')
    
    # Paginate results - 10 per page
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Status choices for filtering or UI display
    status_choices = ReturnRequest.STATUS_CHOICES

    return render(request, 'dashboard/orders/return_orders.html', {
        'orders': page_obj,
        'page_obj': page_obj,
        'status_choices': status_choices,
    })

def exchange_orders(request):
    # Prefetch only ReturnRequest objects where request_type is 'Exchange'
    exchange_requests = ReturnRequest.objects.filter(request_type='Exchange')

    exchanged_orders = Order.objects.filter(
        items__returns__in=exchange_requests
    ).distinct().select_related(
        'user', 'payment'
    ).prefetch_related(
        'items__product',
        Prefetch('items__returns', queryset=exchange_requests),
        'items__returns__scans'
    ).order_by('-created_at')

    paginator = Paginator(exchanged_orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_exchanged = exchanged_orders.count()

    return render(request, 'dashboard/orders/exchange_orders.html', {
        'orders': page_obj,
        'page_obj': page_obj,
        'total_exchanged': total_exchanged
    })


@login_required
@csrf_exempt
@user_passes_test(is_admin)
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.ORDER_STATUS):
            order.status = new_status
            order.save()
            messages.success(request, 'Order status updated successfully!')
            return redirect('dashboard:order_detail', order_number=order_number)
        
    return render(request, 'dashboard/orders/order_detail.html', {
        'order': order,
        'status_choices': Order.ORDER_STATUS,
       
    })


@login_required
def order_delete(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if request.method == "POST":
        # Delete the order
        order.delete()
        # Add a success message
        messages.success(request, f"Order #{order.order_number} has been deleted successfully.")
        # Redirect to the orders list page
        return redirect('dashboard:orders_list')  # Adjust to your orders list URL name
   


from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os

def download_invoice(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Company Header with Logo
    header = Paragraph("INVOICE", styles['Heading1'])
    elements.append(header)
    
    # Company Info and Logo
    company_info = Paragraph("""
    A Company<br/>
    8023695957<br/>
    soldopps5957<br/>
    Minsk, Belarus, 220040
    """, styles['Normal'])
    
    # Add logo (assuming logo is stored in static or media, adjust path accordingly)
    # logo_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'company_logo.png')  # Update path
    logo_path = r"D:/GitHub/ecommerce/static/dashboard/images/company_logo.png"  # Updated path
    print(logo_path)
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
        logo.hAlign = 'RIGHT'
        elements.append(logo)
    
    elements.append(company_info)
    
    # Bill To, Ship To, and Invoice Details
    bill_to = Paragraph(f"""
    Bill To:<br/>
    {order.user.username}<br/>
    {order.billing_address}<br/>
    {order.phone}<br/>
    {order.email}
    """, styles['Normal'])
    
    ship_to = Paragraph(f"""
    Ship To:<br/>
    {order.shipping_address.address_line1 if order.shipping_address else ''}<br/>
    {order.shipping_address.city if order.shipping_address else ''}, {order.shipping_address.state if order.shipping_address else ''}<br/>
    {order.shipping_address.postal_code if order.shipping_address else ''}
    """, styles['Normal'])
    
    invoice_details = Paragraph(f"""
    Invoice No: {order.order_number}<br/>
    Date: {order.created_at.date()}<br/>
    Due Date: {order.delivery_date.date() if order.delivery_date else ''}
    """, styles['Normal'])
    
    info_table_data = [[bill_to, ship_to, invoice_details]]
    info_table = Table(info_table_data, colWidths=[2.5*inch, 2.5*inch, 1.5*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(info_table)
    
    # Items Table
    data = [['Description', 'Rate (CAD)', 'Qty', 'Tax %', 'Disc %', 'Amount (CAD)']]
    for item in order.items.all():
        desc = item.product.name
        if item.variant:
            desc += f" ({item.variant.variant_value})"
        
        rate = item.price
        qty = item.quantity
        tax_percent = 20.00  # Placeholder; adjust as per your model
        disc_percent = item.product.discount_percentage if item.product else 0
        if item.variant:
            disc_percent = item.variant.discount_percentage
        amount = item.subselling_price
        data.append([desc, f"{rate:.2f}", qty, f"{tax_percent:.2f}", f"{disc_percent:.2f}", f"{amount:.2f}"])
    
    table = Table(data, colWidths=[2.8*inch, 0.9*inch, 0.6*inch, 0.7*inch, 0.7*inch, 1.1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(table)
    
    # Totals
    subtotal = order.total_selling or 0
    discount = order.total_discount or 0
    shipping = 0  # Placeholder; adjust if available
    sales_tax = 0  # Placeholder; calculate based on tax %
    total = order.total_amount
    balance_due = total  # Assuming paid 0
    
    totals_data = [
        ['Subtotal', '', '', '', '', f"{subtotal:.2f}"],
        ['Discount', '', '', '', '', f"{discount:.2f}"],
        ['Shipping Cost', '', '', '', '', f"{shipping:.2f}"],
        ['Sales Tax', '', '', '', '', f"{sales_tax:.2f}"],
        ['Amount Paid', '', '', '', '', "0.00"],
        ['Balance Due', '', '', '', '', f"{balance_due:.2f}"]
    ]
    totals_table = Table(totals_data, colWidths=[2.8*inch, 0.9*inch, 0.6*inch, 0.7*inch, 0.7*inch, 1.1*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (5,0), (5,-1), 'RIGHT'),
        ('FONTNAME', (5,0), (5,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(totals_table)
    
    # Payment Instruction
    payment_info = Paragraph("""
    Payment Instruction<br/>
    Paypal email<br/>
    Make checks payable to<br/>
    Glad Norbay<br/>
    Bank Transfer (ABA) 09102084
    """, styles['Normal'])
    elements.append(payment_info)
    
    # Notes
    notes = Paragraph("Notes<br/>Prototype-based programming is a style of<br/>object-oriented programming in which behaviour", styles['Normal'])
    elements.append(notes)
    
    # Manager Signature
    # signature_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'manager_signature.png')  # Update path
    signature_path = r"D:/GitHub/ecommerce/static/dashboard/images/manager_signature.png"  # Updated path
    print(signature_path)
    if os.path.exists(signature_path):
        signature = Image(signature_path, width=2*inch, height=0.7*inch)
        signature.hAlign = 'RIGHT'
        elements.append(signature)
    
    # Add spacing to ensure full page
    elements.append(Paragraph("<br/><br/><br/>", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_number}.pdf"'
    return response


# Payment Management
@login_required
@user_passes_test(is_admin)
def payment_list(request):
    # Fetch payments with related order and user data
    payments = Payment.objects.select_related('order', 'order__user').all().order_by('-created_at')
    
    # Apply status filter if provided
    status_filter = request.GET.get('status')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    # Pagination: 10 payments per page
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate payment metrics
    payment_stats = Payment.objects.aggregate(
        total_payments=Count('id'),
        successful_payments=Count('id', filter=models.Q(status='completed')),
        pending_payments=Count('id', filter=models.Q(status='pending')),
        completed_payments=Count('id', filter=models.Q(status='completed')),  # Same as successful for consistency with HTML
        refunded_payments=Count('id', filter=models.Q(status='refunded'))
    )
    
    # Context for template
    context = {
        'page_obj': page_obj,
        'payments': page_obj.object_list,
        'status_choices': Payment.PAYMENT_STATUS,
        'current_status': status_filter,
        'total_payments': payment_stats['total_payments'],
        'successful_payments': payment_stats['successful_payments'],
        'pending_payments': payment_stats['pending_payments'],
        'completed_payments': payment_stats['completed_payments'],
        'refunded_payments': payment_stats['refunded_payments']
    }
    
    return render(request, 'dashboard/payments/payment_list.html', context)

# Stock Management
@login_required
@user_passes_test(is_admin)
def stock_management(request):
    products = Product.objects.all().order_by('stock')
    
    # Filter low stock items
    low_stock_filter = request.GET.get('low_stock')
    if low_stock_filter:
        products = products.filter(stock__lt=10)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    return render(request, 'dashboard/stock/list.html', {
        'products': products,
        'low_stock_filter': low_stock_filter
    })

@login_required
@csrf_exempt
@user_passes_test(is_admin)
def update_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        new_stock = request.POST.get('stock')
        try:
            product.stock = int(new_stock)
            product.save()
            return JsonResponse({
                'success': True,
                'message': 'Stock updated successfully!',
                'new_stock': product.stock
            })
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'Invalid stock value'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

# Product Variant Management
@login_required
@csrf_exempt
@user_passes_test(is_admin)

def variant_create(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        # Main variant (color)
        color_name = request.POST.get('color_name')
        hex_color_code = request.POST.get('hex_color_code')
        print("Color Name:", color_name)
        print("Hex Color Code:", hex_color_code)
        # Images (can be multiple)
        variant_images = request.FILES.getlist('variant_images')
        print("Variant Images:", variant_images)
        # Sizes (multiple with pricing)
       

        # Check duplicate variant (same product + color)
        if ProductVariant.objects.filter(product=product, color_name=color_name).exists():
            messages.warning(request, "This color variant already exists for this product.")
            return redirect('dashboard:product_edit', pk=product_id)

        # Create Variant (color-level)
        variant = ProductVariant.objects.create(
            product=product,
            color_name=color_name,
            hex_color_code=hex_color_code
        )

        # Save Variant Images
        for i, image in enumerate(variant_images):
            ProductVariantImage.objects.create(
                variant=variant,
                image=image,
                is_default=(i == 0)  # first image = default
            )
        sizes_json = request.POST.get("sizes_json")
        if sizes_json:
            try:
                sizes = json.loads(sizes_json)  # list of dict
                for size_data in sizes:
                    sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"
                    SizeVariant.objects.create(
                        variant=variant,
                        size=size_data["size"],
                        mrp=size_data["mrp"],
                        price=size_data["price"],
                        discount_price=size_data.get("discount_price", 0),
                        stock=size_data["stock"],
                        sku=sku
                    )
            except json.JSONDecodeError:
                pass  # invalid JSON skip
        messages.success(request, "Variant created successfully.")
        return redirect('dashboard:product_edit', pk=product_id)

    return render(request, 'dashboard/products/variant_create.html', {
        'product': product
    })


@login_required
@csrf_exempt
@user_passes_test(is_admin)
def variant_edit(request, product_id, variant_id):
    product = get_object_or_404(Product, pk=product_id)
    variant = get_object_or_404(ProductVariant, pk=variant_id, product=product)

    if request.method == 'POST':
        # Get form fields
        color_name = request.POST.get('color_name', '').strip()
        hex_color_code = request.POST.get('hex_color_code', '').strip()
        variant_images = request.FILES.getlist('variant_images')  # multiple files
        print("variant_images", variant_images)
        # Update fields
        variant.color_name = color_name
        variant.hex_color_code = hex_color_code
        variant.save()

        # Handle image uploads
        if variant_images:
            for image_file in variant_images:
                ProductVariantImage.objects.create(
                    variant=variant,
                    image=image_file
                )

        messages.success(request, 'Product variant updated successfully!')
        return redirect('dashboard:product_edit', pk=product_id)

    return render(request, 'dashboard/products/variant_edit.html', {
        'product': product,
        'variant': variant
    })


@login_required
@user_passes_test(is_admin)
def variant_delete(request, product_id, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id, product_id=product_id)
    product_pk = variant.product.pk  # get the related product's ID
    variant.delete()
    messages.success(request, "Variant deleted successfully.")
    return redirect('dashboard:product_edit', pk=product_pk)


@csrf_exempt
def delete_product_image(request, image_id):
    print('DELETE')
    if request.method == "DELETE":
        try:
            product_image = get_object_or_404(ProductImage, id=image_id)

            # Optional: delete the file from storage too
            if product_image.image:
                product_image.image.delete(save=False)

            product_image.delete()
            return JsonResponse({"message": "Image deleted successfully"}, status=200)

        except Exception as e:
            print('error',e)
            return JsonResponse({"error": str(e)}, status=400)


# Customer Management
@login_required
@user_passes_test(is_admin)
def customers_list(request):
    # Fetch customers (users with user_type='customer')
    customers = CustomUser.objects.filter(user_type='customer').order_by('-date_joined')
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        customers = customers.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        if status_filter == 'Active':
            customers = customers.filter(is_active=True)
        elif status_filter == 'Unactive':
            customers = customers.filter(is_active=False)
    
    # Pagination: 10 customers per page
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Context for template
    context = {
        'page_obj': page_obj,
        'customers': page_obj.object_list,
        'current_status': status_filter,
        'search_query': search,
    }
    
    return render(request, 'dashboard/customers/customers_list.html', context)


@login_required
@csrf_exempt
@user_passes_test(is_admin)
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        discription = request.POST.get('description', '')
        image = request.POST.get('image')
        if name:
            category = Category.objects.create(name=name, description=discription, image=image)
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('dashboard:product_create')
        else:
            messages.error(request, 'Category name is required.')        


from django.http import JsonResponse

from django.db import IntegrityError

@csrf_exempt
def api_add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        image = request.FILES.get('image')
        subcategory = request.POST.get('subcategory')

        if not name:
            return JsonResponse({'status': 'error', 'message': 'Category name is required.'})

        try:
            # Try to create the category
            category = Category.objects.create(
                name=name,
                description=description,
                image=image,
                subcategory=subcategory
            )
            return JsonResponse({
                'status': 'success',
                'message': f'Category "{category.name}" created successfully!'
            })

        except IntegrityError:
            return JsonResponse({
                'status': 'error',
                'message': f'Category with name "{name}" and subcategory "{subcategory}" already exists.'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            })



from django.views.generic import DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib import messages

CustomUser = get_user_model()

class CustomerDetailView(DetailView):
    model = CustomUser
    template_name = 'dashboard/customers/customer_detail.html'
    context_object_name = 'customer'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return CustomUser.objects.filter(user_type='customer')

class CustomerEditView(UpdateView):
    model = CustomUser
    fields = ['username', 'email', 'phone', 'is_active']
    template_name = 'dashboard/customers/customers_list.html'
    success_url = reverse_lazy('dashboard:customers_list')
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return CustomUser.objects.filter(user_type='customer')

    def form_valid(self, form):
        messages.success(self.request, 'Customer updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating customer. Please check the form.')
        return super().form_invalid(form)

class CustomerDeleteView(DeleteView):
    model = CustomUser
    template_name = 'dashboard/customers/customers_list.html'
    success_url = reverse_lazy('dashboard:customers_list')
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return CustomUser.objects.filter(user_type='customer')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Customer deleted successfully.')
        return super().delete(request, *args, **kwargs)


def size_variant_edit(request, product_id, pk):
    size_variant = get_object_or_404(SizeVariant, pk=pk)

    if request.method == "POST":
        sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"
        price = request.POST.get("price")
        discount_price = request.POST.get("discount_price")
        mrp = request.POST.get("mrp")
        stock = request.POST.get("stock")

  
        size_variant.sku = sku
        size_variant.price = price or 0
        size_variant.discount_price = discount_price or None
        size_variant.mrp = mrp or None
        size_variant.stock = stock or 0
        size_variant.save()

        messages.success(request, "Size variant updated successfully!")
        return redirect('dashboard:product_edit', pk=product_id)
        # 👆 change redirect according to your flow

    return render(request, "dashboard/size_variant_edit.html", {"size_variant": size_variant})


def size_variant_delete(request, product_id, pk):
    product = get_object_or_404(Product, pk=product_id)
    size_variant = get_object_or_404(SizeVariant, pk=pk)

    if request.method == "POST":
        size_variant.delete()
        return JsonResponse({
            "success": True,
            "message": "Size variant deleted successfully!"
        })

    # If GET request or others, can return error or redirect
    return JsonResponse({
        "success": False,
        "message": "Invalid request."
    })

from django.views.decorators.http import require_POST
@csrf_exempt
@require_POST
def delete_variant_image(request, pk):
    try:
        img = ProductVariantImage.objects.get(pk=pk)
        img.delete()
        return JsonResponse({'success': True, 'message': 'Image deleted successfully.'})
    except ProductVariantImage.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Image not found.'}, status=404)
    
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from .services.delhivery_service import DelhiveryService
import json
import logging

logger = logging.getLogger('dashboard')
@csrf_exempt
def create_shipping_label(request, order_id):
    """Create shipping label for an order"""
    if request.method == 'POST':
        try:
            logger.info(f"Creating shipping label for order {order_id}")
            
            delhivery = DelhiveryService()

            
            # ✅ Proceed shipment
            result = delhivery.create_shipment(order_id)

            if result.get("success"):
                return JsonResponse({
                    "status": "success",
                    "success": True,
                    "message": f"✅ Shipment created successfully! Waybill: {result.get('waybill')}"
                })
            else:
                return JsonResponse({
                "status": "fail",
                "message": f"❌shipment {result.get('error')}"
            })
                
        except Exception as e:
            logger.error(f"Exception in create_shipping_label: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


from datetime import datetime, timedelta
import requests


logger = logging.getLogger(__name__)
@csrf_exempt
def create_pickup(request, order_id):
    """Create pickup for a shipped order"""

    if request.method == 'POST':
        try: 

            # ✅ Load order to verify existence
            order = Order.objects.get(id=order_id)

            pickup_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            pickup_time = "14:00:00"

            pickup_payload = {
                "pickup_time": pickup_time,
                "pickup_date": pickup_date,
                "pickup_location": "M TEX",
                "expected_package_count": 1,
            }

            pickup_url = "https://track.delhivery.com/fm/request/new/"
            pickup_headers = {
                "Authorization": f"Token {settings.DELHIVERY_TOKEN}",  # Replace with your token
                "Content-Type": "application/json"
            }

        
            pickup_resp = requests.post(
                pickup_url,
                json=pickup_payload,
                headers=pickup_headers,
                timeout=30
            )

            
            print("Pickup API response:", pickup_resp.status_code, pickup_resp.text)
            if pickup_resp.status_code == 201 or 200 :
                pickup_result = pickup_resp.json()
                print("Pickup Result:", pickup_resp.status_code, pickup_resp)
                # Check if response contains success indication
                order.status = "Processing"
                order.save()

                return JsonResponse({
                    'status': 'success',
                    'message': '✅ Pickup created successfully.'
                })
            else:
                return JsonResponse({
                    'status': 'fail',
                   'message': f"❌ Pickup request failed: {pickup_resp.text}"
                
                })

        except Order.DoesNotExist:
            return JsonResponse({'status': 'fail', 'message': 'Order not found'}, status=404)

        except Exception as e:
            logger.error(f"Exception in create_pickup: {str(e)}")
            return JsonResponse({'status': 'fail', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def download_shipping_label(request, tracking_id):
    """Download shipping label PDF"""
    try:
        tracking = OrderTracking.objects.get(id=tracking_id)
        
        if tracking.label_file:
            response = HttpResponse(
                tracking.label_file.read(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="shipping_label_{tracking.awb_number}.pdf"'
            return response
        else:
            return HttpResponse('Label file not found', status=404)
            
    except OrderTracking.DoesNotExist:
        return HttpResponse('Tracking record not found', status=404)
    except Exception as e:
        logger.error(f"Error downloading label: {str(e)}")
        return HttpResponse(f'Error: {str(e)}', status=500)

@csrf_exempt
def create_return_shipment(request, item_id):
    try:
        if request.method == 'POST':

            order_item = get_object_or_404(OrderItem, id=item_id)

            # Find active ReturnRequest for this order_item
            return_request_qs = order_item.returns.filter(status='Requested').order_by('-requested_at')
            if not return_request_qs.exists():
                messages.error(request,'No active return request found for this item.')
                return redirect("return_orders")

            return_request = return_request_qs.first()
            order = return_request.order_item.order
            shipping_address = order.shipping_address

            # Calculate weight & quantity
            quantity = return_request.quantity
            weight_per_item = float(order_item.product.weight or 0.5)
            total_weight = max(0.5, weight_per_item * quantity)

            # Your warehouse / pickup location details
            pickup_location_name = "M TEX"  # warehouse registered name with Delhivery
            pickup_address = "Your Warehouse Address Here"
            pickup_pin = 641606
            pickup_city = "Tiruppur"
            pickup_state = "Tamil Nadu"
            pickup_country = "India"
            pickup_phone = ["9487332244"]

            shipment_data = {
                "shipments": [{
                    "name": shipping_address.contact_person_name or order.user.username,
                    "add": f"{shipping_address.address_line1}, {shipping_address.address_line2 or ''}".strip(', '),
                    "pin": int(shipping_address.postal_code),
                    "city": shipping_address.city,
                    "state": shipping_address.state,
                    "country": shipping_address.country or "India",
                    "phone": [shipping_address.contact_person_number or shipping_address.phone or order.phone],
                    "order": str(order.order_number),
                    "payment_mode": "Pickup",  # For return shipments
                    "return_pin": pickup_pin,
                    "return_city": pickup_city,
                    "return_phone": pickup_phone,
                    "return_add": pickup_address,
                    "return_state": pickup_state,
                    "return_country": pickup_country,
                    "products_desc": "Returned items",
                    "hsn_code": order_item.product.hsn_code or "6109",
                    "cod_amount": 0,
                    "order_date": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_amount": str(order.total_amount),
                    "seller_add": pickup_address,
                    "seller_name": "M TEX",
                    "seller_gst_tin": "33FLMPM1010A1ZY",
                    "quantity": quantity,
                    "waybill": "",
                    "shipment_width": 18,
                    "shipment_height": 1,
                    "shipment_length": 27,
                    "weight": total_weight,
                    "shipping_mode": "Surface",
                    "address_type": shipping_address.type_of_address or "home"
                }],
                "pickup_location": {
                    "name": 'M TEX',
                }
            }

            payload = {
                "format": "json",
                "data": json.dumps(shipment_data)
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Token {settings.DELHIVERY_TOKEN}"
            }

            try:
                response = requests.post(
                    "https://track.delhivery.com/api/cmu/create.json",
                    headers=headers,
                    data=payload,
                    timeout=30
                )
                logger.info(f"Delhivery return shipment response: {response.status_code} {response.text}")

                if response.status_code in (200, 201):
                    result = response.json()
                    if result.get("success"):
                        waybill = result.get("packages", [{}])[0].get("waybill")
                        if waybill:
                            # Update return request status and AWB
                            return_request.pickup_awb = waybill
                            return_request.status = "Approved"
                            return_request.save()

                            messages.success(request, "Return shipment created successfully. Waybill: " + waybill)
                            # Redirect to return_orders page
                            return redirect("dashboard:return_orders")
                        else:
                            messages.error(request, "Waybill missing in response")
                            return redirect("dashboard:return_orders")
                    else:
                        messages.error(request,result.get("rmk", "Unknown error"))
                        return redirect("dashboard:return_orders")
                else:
                    messages.error(request, f"Delhivery API failed with status {response.status_code}")
                    return redirect("dashboard:return_orders")
            except Exception as e:
                logger.error(f"Error in return shipment creation (Delhivery API): {e}")
                messages.error(request, f"Error in return shipment creation (API): {str(e)}")
                return redirect("dashboard:return_orders")

    except Exception as e:
        logger.error(f"Error in create_return_shipment view: {e}")
        messages.error(request, f"Something went wrong: {str(e)}")
        return redirect("dashboard:return_orders")


from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import requests
from api.models import Order
from .services.delhivery_service import DelhiveryService

@login_required
@csrf_exempt
def bulk_create_shipments_view(request):
    try:
        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")

        if not from_date or not to_date:
            return JsonResponse({"success": False, "error": "from_date and to_date required"}, status=400)

        start = datetime.strptime(from_date, "%Y-%m-%d")
        end = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
        
        # Make timezone-aware
        start = timezone.make_aware(start)
        end = timezone.make_aware(end)

        orders = Order.objects.filter(
            status="Confirmed",
            payment__status="Completed",
            created_at__range=[start, end]
        ).select_related("shipping_address", "user")

        if not orders.exists():
            return JsonResponse({"success": False, "error": "No eligible orders found"}, status=404)

        delhivery = DelhiveryService()
        result = delhivery.create_bulk_shipments(orders)
        # Pickup request if shipment success
        pickup_data = None
        if result.get("success"):
            pickup_payload = {
                "pickup_time": "14:00:00",
                "pickup_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "pickup_location": delhivery.pickup_location,
                "expected_package_count": len(result.get("waybills", []))
            }

            pickup_response = requests.post(
                "https://track.delhivery.com/fm/request/new/",
                json=pickup_payload,
                headers={"Authorization": f"Token {delhivery.token}", "Content-Type": "application/json"},
                timeout=30
            )

            pickup_data = pickup_response.json() if pickup_response.status_code == 200 else {"error": pickup_response.text}

        return JsonResponse({
            "success": True,
            "message": "Bulk shipment process completed",
            "shipment_result": result,
            "pickup_response": pickup_data
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def update_return_payment(request, request_id):
    try:
        return_request = get_object_or_404(ReturnRequest, id=request_id)

        # ✅ Update ReturnRequest
        return_request.status = 'Refunded'
        return_request.processed_at = timezone.now()
        return_request.save()

        # ✅ Get the associated Order
        order = return_request.order_item.order

        # ✅ Update Payment
        try:
            payment = order.payment
            payment.status = 'Refunded'
            payment.save()  # ✅ auto_now=True will update updated_at
        except Payment.DoesNotExist:
            messages.warning(request, "Payment record not found for this order.")

        # ✅ Update Order
        order.status = 'Refunded'
        order.save()  # ✅ auto_now=True will update updated_at

        messages.success(request, "Refund updated successfully.")
        return redirect('dashboard:return_orders')

    except Exception as e:
        messages.error(request, f"Error updating refund: {str(e)}")
        return redirect('dashboard:return_orders')

def track_order(request, order_id):
    """Track order status from Delhivery"""
    try:
        order = Order.objects.get(id=order_id)
        tracking = OrderTracking.objects.get(order=order)
        
        delhivery = DelhiveryService()
        track_data = delhivery.track_shipment(tracking.awb_number)
        
        if track_data:
            # Update tracking status
            tracking.raw_data = track_data
            tracking.save()
            
            return JsonResponse({
                'status': 'success',
                'waybill': tracking.awb_number,
                'tracking_data': track_data
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to fetch tracking data from Delhivery'
            })
            
    except Order.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Order not found'
        }, status=404)
    except OrderTracking.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'Tracking record not found for this order'
        }, status=404)
    except Exception as e:
        logger.error(f"Error tracking order: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
