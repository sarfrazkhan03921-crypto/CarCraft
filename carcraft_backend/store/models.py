import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify


class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('mechanic', 'Mechanic/Technician'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class CarMake(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to='makes/', blank=True, null=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CarModel(models.Model):
    BODY_TYPES = (
        ('Coupe', 'Coupe'),
        ('Sedan', 'Sedan'),
        ('SUV', 'SUV / Crossover'),
        ('Hatchback', 'Hatchback'),
        ('Convertible', 'Convertible'),
        ('Truck', 'Truck / Pickup'),
        ('Supercar', 'Supercar / Exotic'),
    )
    make = models.ForeignKey(CarMake, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True)
    year_start = models.PositiveIntegerField(default=2015)
    year_end = models.PositiveIntegerField(null=True, blank=True)
    body_type = models.CharField(max_length=50, choices=BODY_TYPES, default='Coupe')
    image = models.ImageField(upload_to='models/', blank=True, null=True)

    class Meta:
        ordering = ['make__name', 'name']
        unique_together = ('make', 'name')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.make.name}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        end_yr = self.year_end if self.year_end else "Present"
        return f"{self.make.name} {self.name} ({self.year_start}-{end_yr})"


class UserVehicle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    car_make = models.ForeignKey(CarMake, on_delete=models.SET_NULL, null=True, blank=True)
    car_model = models.ForeignKey(CarModel, on_delete=models.SET_NULL, null=True, blank=True)
    custom_make = models.CharField(max_length=100, blank=True, null=True)
    custom_model = models.CharField(max_length=100, blank=True, null=True)
    year = models.PositiveIntegerField(default=2022)
    color = models.CharField(max_length=50, blank=True)
    license_plate = models.CharField(max_length=30, blank=True)
    vin = models.CharField(max_length=50, blank=True)
    current_mileage = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', '-id']

    @property
    def display_name(self):
        make_str = self.car_make.name if self.car_make else (self.custom_make or "Unknown Make")
        model_str = self.car_model.name if self.car_model else (self.custom_model or "")
        return f"{self.year} {make_str} {model_str}".strip()

    def __str__(self):
        return f"{self.user.username}'s {self.display_name}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon identifier e.g. Wrench, Gauge, Flame, Sparkles")
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=10)
    in_stock = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    specifications = models.JSONField(default=dict, blank=True, help_text="e.g. {'Material': 'Dry Carbon Fiber', 'Warranty': '3 Years'}")
    compatible_models = models.ManyToManyField(CarModel, blank=True, related_name='compatible_products')
    universal_fit = models.BooleanField(default=False)
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if self.stock <= 0:
            self.in_stock = False
        else:
            self.in_stock = True
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def discount_percent(self):
        if self.discount_price and self.discount_price < self.price:
            diff = self.price - self.discount_price
            return int(round((diff / self.price) * 100))
        return 0

    def update_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            total = sum(r.rating for r in reviews)
            self.rating_average = round(Decimal(total) / Decimal(reviews.count()), 2)
            self.review_count = reviews.count()
        else:
            self.rating_average = Decimal('0.00')
            self.review_count = 0
        self.save(update_fields=['rating_average', 'review_count'])

    def __str__(self):
        return f"{self.name} ({self.sku})"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, f"{i} Stars") for i in range(1, 6)])
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating()

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        product.update_rating()

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}/5)"


class CustomBuild(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Drafting / Concept'),
        ('saved', 'Saved in Garage'),
        ('quote_requested', 'Quote Requested'),
        ('in_progress', 'Building in Workshop'),
        ('completed', 'Build Completed'),
    )
    FINISH_TYPES = (
        ('Gloss', 'Gloss'),
        ('Matte', 'Matte'),
        ('Satin', 'Satin'),
        ('Metallic', 'Metallic'),
        ('Chrome', 'Chrome'),
        ('Carbon Finish', 'Carbon Finish'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_builds')
    title = models.CharField(max_length=200, default='Custom Car Project')
    base_vehicle = models.ForeignKey(UserVehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='builds')
    car_model = models.ForeignKey(CarModel, on_delete=models.SET_NULL, null=True, blank=True)
    paint_color = models.CharField(max_length=50, default='#1e1e24')
    finish_type = models.CharField(max_length=50, choices=FINISH_TYPES, default='Gloss')
    wheel_specs = models.JSONField(default=dict, blank=True, help_text="e.g. {'model': 'BBS LM', 'size': '20 inch', 'color': 'Satin Bronze'}")
    suspension_setup = models.CharField(max_length=150, blank=True, default='KW V3 Adjustable Coilovers')
    exhaust_setup = models.CharField(max_length=150, blank=True, default='Valvetronic Titanium Cat-Back')
    aero_package = models.JSONField(default=dict, blank=True, help_text="e.g. {'splitter': true, 'side_skirts': true, 'diffuser': true, 'gt_wing': 'Carbon Spec'}")
    interior_setup = models.CharField(max_length=150, blank=True, default='Alcantara & Carbon Fiber Trim')
    engine_tune_stage = models.CharField(max_length=100, blank=True, default='Stage 2 ECU + Downpipe')
    notes = models.TextField(blank=True)
    estimated_parts_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estimated_labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    is_public = models.BooleanField(default=False)
    likes_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def recalculate_costs(self):
        parts_total = sum(p.total_price for p in self.parts.all())
        self.estimated_parts_cost = parts_total
        # Auto estimate labor if 0
        if self.estimated_labor_cost == Decimal('0.00') and parts_total > 0:
            self.estimated_labor_cost = round(parts_total * Decimal('0.20'), 2)
        self.total_cost = self.estimated_parts_cost + self.estimated_labor_cost
        self.save(update_fields=['estimated_parts_cost', 'estimated_labor_cost', 'total_cost'])

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class CustomBuildPart(models.Model):
    build = models.ForeignKey(CustomBuild, on_delete=models.CASCADE, related_name='parts')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    custom_part_name = models.CharField(max_length=200)
    part_type = models.CharField(max_length=50, blank=True) # Aero, Exhaust, Engine, Wheels, Suspension, Interior
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        if self.product and not self.custom_part_name:
            self.custom_part_name = self.product.name
        if self.product and self.price == Decimal('0.00'):
            self.price = self.product.effective_price
        super().save(*args, **kwargs)
        self.build.recalculate_costs()

    def delete(self, *args, **kwargs):
        build = self.build
        super().delete(*args, **kwargs)
        build.recalculate_costs()

    def __str__(self):
        return f"{self.custom_part_name} for {self.build.title}"


class WorkshopService(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_duration_hours = models.DecimalField(max_digits=4, decimal_places=1, default=2.0)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)

    class Meta:
        ordering = ['base_price']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (from Rs. {self.base_price})"


class ServiceBooking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'Vehicle in Workshop'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    booking_reference = models.CharField(max_length=30, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_bookings')
    service = models.ForeignKey(WorkshopService, on_delete=models.PROTECT, related_name='bookings')
    vehicle = models.ForeignKey(UserVehicle, on_delete=models.SET_NULL, null=True, blank=True)
    custom_vehicle_info = models.CharField(max_length=200, blank=True)
    booking_date = models.DateField()
    time_slot = models.CharField(max_length=50) # e.g. '10:00 AM - 12:00 PM'
    customer_notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    mechanic_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_date', '-id']

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = f"CC-SRV-{uuid.uuid4().hex[:8].upper()}"
        if not self.estimated_cost and self.service:
            self.estimated_cost = self.service.base_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_reference} - {self.service.name} for {self.user.username}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    @property
    def subtotal(self):
        return self.product.effective_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing / Packing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Payment Failed'),
    )
    PAYMENT_METHODS = (
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI / NetBanking'),
        ('cod', 'Cash on Delivery'),
        ('paypal', 'PayPal'),
    )
    order_number = models.CharField(max_length=40, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='card')
    tracking_number = models.CharField(max_length=100, blank=True)
    courier = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"CC-ORD-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} ({self.user.username})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} in {self.order.order_number}"


class CustomQuoteRequest(models.Model):
    STATUS_CHOICES = (
        ('new', 'New Request'),
        ('reviewed', 'Under Review'),
        ('quote_sent', 'Quote Sent to Customer'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quote_requests', null=True, blank=True)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    vehicle_details = models.CharField(max_length=255, help_text="e.g. 2023 BMW M3 Competition")
    project_type = models.CharField(max_length=120, help_text="e.g. Widebody Kit & Carbon Fiber Aero, Engine Stage 3, Track Build")
    estimated_budget = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='new')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Quote from {self.name} - {self.vehicle_details}"


class VehicleBooking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    booking_reference = models.CharField(max_length=30, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_bookings', null=True, blank=True)
    car_model = models.ForeignKey(CarModel, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle_name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    city = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = f"CC-VBK-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_reference} - {self.vehicle_name} for {self.full_name}"


class TestDriveAppointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    booking_reference = models.CharField(max_length=30, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_drives', null=True, blank=True)
    car_model = models.ForeignKey(CarModel, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle_name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    preferred_date = models.DateField()
    time_slot = models.CharField(max_length=50)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = f"CC-TD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_reference} - Test Drive {self.vehicle_name} for {self.full_name}"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=(('percent', 'Percentage'), ('fixed', 'Fixed Amount')), default='percent')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage value or fixed amount")
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum discount cap for percentage coupons")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_limit = models.PositiveIntegerField(default=100)
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'percent' else ' flat'})"
