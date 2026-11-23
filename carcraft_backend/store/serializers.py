from decimal import Decimal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import (
    CarMake, CarModel, UserVehicle, Category, Brand, Product,
    ProductImage, ProductReview, Cart, CartItem, Order, OrderItem,
    WorkshopService, ServiceBooking, CustomBuild, CustomBuildPart,
    CustomQuoteRequest,
)

User = get_user_model()


# ═══════════════════════════════════════════════════════
#  AUTH SERIALIZERS
# ═══════════════════════════════════════════════════════

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=6, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'password', 'password2')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        # Use email as username if username not provided
        if not validated_data.get('username'):
            base_user = validated_data['email'].split('@')[0]
            candidate = base_user
            idx = 1
            while User.objects.filter(username=candidate).exists():
                candidate = f"{base_user}{idx}"
                idx += 1
            validated_data['username'] = candidate
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'avatar', 'address', 'city', 'state', 'postal_code',
            'bio', 'role', 'date_joined',
        )
        read_only_fields = ('id', 'username', 'role', 'date_joined')

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


# ═══════════════════════════════════════════════════════
#  VEHICLE / CAR SERIALIZERS
# ═══════════════════════════════════════════════════════

class CarMakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarMake
        fields = '__all__'


class CarModelSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.name', read_only=True)

    class Meta:
        model = CarModel
        fields = '__all__'


class VehicleListSerializer(serializers.ModelSerializer):
    """Flat serializer used by vehicles page — maps CarModel fields to what frontend expects."""
    make = serializers.CharField(source='make.name', read_only=True)
    make_slug = serializers.CharField(source='make.slug', read_only=True)
    make_logo = serializers.ImageField(source='make.logo', read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = CarModel
        fields = (
            'id', 'name', 'slug', 'make', 'make_slug', 'make_logo',
            'body_type', 'year_start', 'year_end', 'image',
        )

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        name_lower = (obj.name or '').lower()
        if 'city' in name_lower:
            return 'https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1200&q=80'
        if 'creta' in name_lower:
            return 'https://tse4.mm.bing.net/th/id/OIP.x1xxZrR8jbBV-4qBHEMWgQHaEK?r=0&pid=Api&h=220&P=0'
        if 'verna' in name_lower:
            return 'https://th.bing.com/th/id/OIP.jIRbGvu58yAk9sq9JRHW2gHaE0?w=280&h=181&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3'
        if 'brezza' in name_lower:
            return 'https://tse4.mm.bing.net/th/id/OIP.fJLUZZgEL0fwCdcp4qr78AHaE8?r=0&pid=Api&h=220&P=0'
        if 'xuv' in name_lower or '700' in name_lower:
            return 'https://images.91wheels.com/assets/uploads/swatchs/XUV_7X0_NebulaBlue1767697427.jpg?w=900&q=80'
        if 'nexon' in name_lower:
            return 'https://tse1.mm.bing.net/th/id/OIP.TFEpr3jnLP_hQ4ITs8hnBQHaEK?r=0&pid=Api&h=220&P=0'
        if 'dzire' in name_lower:
            return 'https://tse3.mm.bing.net/th/id/OIP.t2vEAwrVpow0MujR9uNSWQAAAA?r=0&pid=Api&h=220&P=0'
        if 'swift' in name_lower:
            return 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1200&q=80'
        if 'fortuner' in name_lower:
            return 'https://th.bing.com/th/id/OIP.jIRbGvu58yAk9sq9JRHW2gHaE0?w=280&h=181&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3'
        return 'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80'


class UserVehicleSerializer(serializers.ModelSerializer):
    display_name = serializers.ReadOnlyField()

    class Meta:
        model = UserVehicle
        fields = '__all__'
        read_only_fields = ('user',)


# ═══════════════════════════════════════════════════════
#  PRODUCT SERIALIZERS
# ═══════════════════════════════════════════════════════

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'order')


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True, default='')
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    main_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'sku', 'category', 'category_name',
            'brand', 'brand_name', 'short_description', 'price',
            'discount_price', 'effective_price', 'discount_percent',
            'stock', 'in_stock', 'is_featured', 'is_bestseller',
            'main_image', 'main_image_url', 'rating_average', 'review_count',
        )

    def get_main_image_url(self, obj):
        if obj.main_image:
            img_val = str(obj.main_image)
            if img_val.startswith('http://') or img_val.startswith('https://'):
                return img_val
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        name_lower = (obj.name or '').lower()
        if 'tyre' in name_lower or 'tire' in name_lower:
            return 'https://images.unsplash.com/photo-1578844251758-2f71da64c96f?auto=format&fit=crop&w=600&q=80'
        if 'spoiler' in name_lower:
            return 'https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=600&q=80'
        if 'bulb' in name_lower or 'headlight' in name_lower:
            return 'https://tse4.mm.bing.net/th/id/OIP.LRl0E8f_QO2wGAkOAtKmVwHaGl?r=0&pid=Api&h=220&P=0'
        if 'mat' in name_lower:
            return 'https://tse3.mm.bing.net/th/id/OIP.m1oMg_0dcie_XtNxTt7k-gHaE8?r=0&pid=Api&h=220&P=0'
        if 'seat' in name_lower:
            return 'https://m.media-amazon.com/images/I/719X-dibmOL.jpg'
        if 'brake' in name_lower:
            return 'https://images.unsplash.com/photo-1600790142055-619df03207e6?auto=format&fit=crop&w=600&q=80'
        if 'oil' in name_lower and 'filter' not in name_lower:
            return 'https://tse3.mm.bing.net/th/id/OIP.S0Bd2IJ-4v1Jqz3La5-hcgHaEK?r=0&pid=Api&h=220&P=0'
        if 'filter' in name_lower and 'cabin' in name_lower:
            return 'https://tse1.mm.bing.net/th/id/OIP.XcXwqGi6Tyyb5Jh1gTi8NQHaHa?r=0&pid=Api&h=220&P=0'
        if 'filter' in name_lower:
            return 'https://tse3.mm.bing.net/th/id/OIP.p7QSlmV_CeEJUUEHcoGHWgHaHa?r=0&pid=Api&h=220&P=0'
        return getattr(obj, 'image_url', '') or 'https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=600&q=80'


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True, default='')
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProductReview
        fields = '__all__'
        read_only_fields = ('user', 'verified_purchase')


# ═══════════════════════════════════════════════════════
#  CART SERIALIZERS
# ═══════════════════════════════════════════════════════

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.effective_price', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.SerializerMethodField()
    product_category = serializers.CharField(source='product.category.name', read_only=True)
    product_desc = serializers.CharField(source='product.short_description', read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = (
            'id', 'product', 'product_name', 'product_price',
            'product_image', 'product_category', 'product_desc',
            'quantity', 'subtotal',
        )

    def get_product_image(self, obj):
        if obj.product.main_image:
            img_val = str(obj.product.main_image)
            if img_val.startswith('http://') or img_val.startswith('https://'):
                return img_val
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.product.main_image.url)
            return obj.product.main_image.url
        name_lower = (obj.product.name or '').lower()
        if 'tyre' in name_lower or 'tire' in name_lower:
            return 'https://images.unsplash.com/photo-1578844251758-2f71da64c96f?auto=format&fit=crop&w=300&q=80'
        if 'spoiler' in name_lower:
            return 'https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=300&q=80'
        if 'bulb' in name_lower or 'headlight' in name_lower:
            return 'https://tse4.mm.bing.net/th/id/OIP.LRl0E8f_QO2wGAkOAtKmVwHaGl?r=0&pid=Api&h=220&P=0'
        if 'mat' in name_lower:
            return 'https://tse3.mm.bing.net/th/id/OIP.m1oMg_0dcie_XtNxTt7k-gHaE8?r=0&pid=Api&h=220&P=0'
        if 'seat' in name_lower:
            return 'https://m.media-amazon.com/images/I/719X-dibmOL.jpg'
        if 'brake' in name_lower:
            return 'https://images.unsplash.com/photo-1600790142055-619df03207e6?auto=format&fit=crop&w=300&q=80'
        if 'oil' in name_lower and 'filter' not in name_lower:
            return 'https://tse3.mm.bing.net/th/id/OIP.S0Bd2IJ-4v1Jqz3La5-hcgHaEK?r=0&pid=Api&h=220&P=0'
        if 'filter' in name_lower and 'cabin' in name_lower:
            return 'https://tse1.mm.bing.net/th/id/OIP.XcXwqGi6Tyyb5Jh1gTi8NQHaHa?r=0&pid=Api&h=220&P=0'
        if 'filter' in name_lower:
            return 'https://tse3.mm.bing.net/th/id/OIP.p7QSlmV_CeEJUUEHcoGHWgHaHa?r=0&pid=Api&h=220&P=0'
        return getattr(obj.product, 'image_url', '') or 'https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=150&q=80'


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    delivery_charge = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'items', 'total_items', 'subtotal', 'delivery_charge', 'total', 'updated_at')

    def get_delivery_charge(self, obj):
        return 0 if obj.subtotal >= 3000 else 99

    def get_total(self, obj):
        delivery = 0 if obj.subtotal >= 3000 else 99
        return float(obj.subtotal) + delivery


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.CharField(required=False, allow_blank=True, default='')
    name = serializers.CharField(required=False, allow_blank=True, default='')
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=Decimal('0.00'))
    category = serializers.CharField(required=False, allow_blank=True, default='PARTS')
    quantity = serializers.IntegerField(default=1, min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


# ═══════════════════════════════════════════════════════
#  ORDER SERIALIZERS
# ═══════════════════════════════════════════════════════

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'product_sku', 'unit_price', 'quantity', 'total_price')
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = (
            'id', 'order_number', 'user', 'subtotal', 'tax',
            'shipping_fee', 'discount_amount', 'total_amount',
            'status', 'payment_status', 'items', 'created_at', 'updated_at',
        )


class CreateOrderSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20)
    shipping_address = serializers.CharField()
    city = serializers.CharField(max_length=100, required=False, default='')
    state = serializers.CharField(max_length=100, required=False, default='')
    postal_code = serializers.CharField(max_length=20, required=False, default='')
    payment_method = serializers.ChoiceField(choices=['cod', 'upi', 'card', 'paypal'], default='cod')
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    notes = serializers.CharField(required=False, allow_blank=True, default='')


# ═══════════════════════════════════════════════════════
#  SERVICE BOOKING SERIALIZERS
# ═══════════════════════════════════════════════════════

class WorkshopServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkshopService
        fields = '__all__'


class ServiceBookingSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = ServiceBooking
        fields = '__all__'
        read_only_fields = ('user', 'booking_reference', 'estimated_cost', 'mechanic_notes', 'created_at', 'updated_at')


class CreateServiceBookingSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()
    vehicle_info = serializers.CharField(max_length=200)
    registration_number = serializers.CharField(max_length=30)
    booking_date = serializers.DateField()
    time_slot = serializers.CharField(max_length=50)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


# ═══════════════════════════════════════════════════════
#  VEHICLE BOOKING SERIALIZER  (new model needed)
# ═══════════════════════════════════════════════════════

class VehicleBookingSerializer(serializers.Serializer):
    """Frontend vehicle booking from vehicle-details page."""
    vehicle_model_id = serializers.IntegerField(required=False)
    vehicle_name = serializers.CharField(max_length=200)
    full_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    city = serializers.CharField(max_length=100)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


# ═══════════════════════════════════════════════════════
#  TEST DRIVE SERIALIZER
# ═══════════════════════════════════════════════════════

class TestDriveSerializer(serializers.Serializer):
    """Frontend test drive from vehicle-details page."""
    vehicle_model_id = serializers.IntegerField(required=False)
    vehicle_name = serializers.CharField(max_length=200)
    full_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    preferred_date = serializers.DateField()
    time_slot = serializers.CharField(max_length=50)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


# ═══════════════════════════════════════════════════════
#  COUPON SERIALIZER
# ═══════════════════════════════════════════════════════

class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)


# ═══════════════════════════════════════════════════════
#  DASHBOARD SERIALIZER
# ═══════════════════════════════════════════════════════

class DashboardSummarySerializer(serializers.Serializer):
    total_vehicles = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_products = serializers.IntegerField()
    pending_services = serializers.IntegerField()
    upcoming_services = serializers.ListField(child=serializers.DictField())
    recent_orders = serializers.ListField(child=serializers.DictField())
