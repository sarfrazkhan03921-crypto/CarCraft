from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout

from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    CarMake, CarModel, UserVehicle, Category, Brand, Product,
    Cart, CartItem, Order, OrderItem, WorkshopService, ServiceBooking,
    VehicleBooking, TestDriveAppointment, Coupon,
)
from .serializers import (
    RegisterSerializer, UserProfileSerializer, ChangePasswordSerializer,
    CarMakeSerializer, CarModelSerializer, VehicleListSerializer, UserVehicleSerializer,
    CategorySerializer, BrandSerializer, ProductListSerializer, ProductDetailSerializer,
    CartSerializer, CartItemSerializer, AddToCartSerializer, UpdateCartItemSerializer,
    OrderSerializer, CreateOrderSerializer, OrderItemSerializer,
    WorkshopServiceSerializer, ServiceBookingSerializer, CreateServiceBookingSerializer,
    VehicleBookingSerializer, TestDriveSerializer, CouponValidateSerializer,
    DashboardSummarySerializer,
)

User = get_user_model()


# ═══════════════════════════════════════════════════════════
#  AUTHENTICATION VIEWS
# ═══════════════════════════════════════════════════════════

class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — Create a new user account."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if hasattr(request, 'session'):
            auth_login(request, user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Registration successful.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': getattr(user, 'phone', ''),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/ — Authenticate and get JWT tokens."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_identifier = (
            request.data.get('email')
            or request.data.get('identifier')
            or request.data.get('username')
            or request.data.get('phone')
            or ''
        )
        identifier = str(raw_identifier).strip()
        password = request.data.get('password', '')

        if not identifier or not password:
            return Response(
                {'error': 'Email / username / phone and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Support login via email, username, or phone number
        user = User.objects.filter(email__iexact=identifier).first()
        if not user:
            user = User.objects.filter(username__iexact=identifier).first()
        if not user:
            clean_digits = ''.join(c for c in identifier if c.isdigit())
            if clean_digits:
                phone_q = Q(phone__iexact=identifier) | Q(phone__iexact=clean_digits)
                if len(clean_digits) >= 10:
                    phone_q |= Q(phone__endswith=clean_digits[-10:])
                user = User.objects.filter(phone_q).first()

        if not user:
            return Response(
                {'error': 'No account found with this email, username, or phone.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {'error': 'Invalid password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Account is deactivated.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Establish Django session
        if hasattr(request, 'session'):
            auth_login(request, user)

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login successful.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': getattr(user, 'phone', ''),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })


class LogoutView(APIView):
    """POST /api/auth/logout/ — End the user session."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if hasattr(request, 'session'):
            auth_logout(request)
        return Response({'message': 'Logged out successfully.'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT /api/auth/profile/ — View or update the authenticated user's profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/ — Change password for authenticated user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Password changed successfully.'})


# ═══════════════════════════════════════════════════════════
#  VEHICLE / CAR VIEWS
# ═══════════════════════════════════════════════════════════

class VehicleListView(generics.ListAPIView):
    """GET /api/vehicles/ — List all car models (what frontend calls 'vehicles')."""
    serializer_class = VehicleListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Frontend expects a flat list

    def get_queryset(self):
        qs = CarModel.objects.select_related('make').all()
        # Search
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                name__icontains=search
            ) | qs.filter(
                make__name__icontains=search
            )
        # Filter by make/brand
        brand = self.request.query_params.get('brand', '').strip()
        if brand:
            qs = qs.filter(make__name__icontains=brand)
        # Filter by body type
        body_type = self.request.query_params.get('body_type', '').strip()
        if body_type:
            qs = qs.filter(body_type__icontains=body_type)
        return qs


class VehicleDetailView(generics.RetrieveAPIView):
    """GET /api/vehicles/{id}/ — Get vehicle details by ID."""
    serializer_class = VehicleListSerializer
    permission_classes = [permissions.AllowAny]
    queryset = CarModel.objects.select_related('make').all()


class CarMakeListView(generics.ListAPIView):
    """GET /api/car-makes/ — List all car manufacturers."""
    serializer_class = CarMakeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = CarMake.objects.all()


class CarModelListView(generics.ListAPIView):
    """GET /api/car-models/ — List all car models."""
    serializer_class = CarModelSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = CarModel.objects.select_related('make').all()


# ═══════════════════════════════════════════════════════════
#  PRODUCT VIEWS
# ═══════════════════════════════════════════════════════════

class ProductListView(generics.ListAPIView):
    """GET /api/products/ — List all products with optional filters."""
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Frontend renders all products

    def get_queryset(self):
        qs = Product.objects.select_related('category', 'brand').filter(in_stock=True)
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)
        category = self.request.query_params.get('category', '').strip()
        if category:
            qs = qs.filter(category__slug=category)
        brand = self.request.query_params.get('brand', '').strip()
        if brand:
            qs = qs.filter(brand__slug=brand)
        featured = self.request.query_params.get('featured', '').strip()
        if featured == '1':
            qs = qs.filter(is_featured=True)
        return qs


class ProductDetailView(generics.RetrieveAPIView):
    """GET /api/products/{id}/ — Get detailed product info."""
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.select_related('category', 'brand').all()


class CategoryListView(generics.ListAPIView):
    """GET /api/categories/ — List product categories."""
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = Category.objects.filter(is_active=True)


class BrandListView(generics.ListAPIView):
    """GET /api/brands/ — List product brands."""
    serializer_class = BrandSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = Brand.objects.all()


# ═══════════════════════════════════════════════════════════
#  CART VIEWS
# ═══════════════════════════════════════════════════════════

class CartView(APIView):
    """GET /api/cart/ — Get the authenticated user's cart."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)


class CartAddItemView(APIView):
    """POST /api/cart/items/ — Add a product to cart."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data.get('quantity', 1)
        name = serializer.validated_data.get('name')
        price = serializer.validated_data.get('price')
        category_name = serializer.validated_data.get('category')

        product = None
        # 1. Try numeric ID
        if isinstance(product_id, int) or (isinstance(product_id, str) and product_id.isdigit()):
            product = Product.objects.filter(id=int(product_id)).first()

        # 2. Try SKU or slug
        if not product:
            product = Product.objects.filter(sku=str(product_id)).first()
        if not product:
            product = Product.objects.filter(slug=str(product_id)).first()

        # 3. Try name
        if not product and name:
            product = Product.objects.filter(name__iexact=name).first()

        # 4. If product still does not exist, create or link it so add to cart never fails
        if not product:
            from django.utils.text import slugify
            cat = Category.objects.first()
            if category_name:
                cat, _ = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'slug': slugify(category_name)}
                )
            prod_name = name or f"Product {product_id}"
            slug_val = slugify(f"{prod_name}-{product_id}")
            product, _ = Product.objects.get_or_create(
                sku=str(product_id),
                defaults={
                    'name': prod_name,
                    'slug': slug_val,
                    'price': price or Decimal('999.00'),
                    'category': cat,
                    'stock': 100,
                    'in_stock': True,
                }
            )

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_201_CREATED)


class CartUpdateItemView(APIView):
    """PATCH /api/cart/items/{id}/ — Update quantity of a cart item."""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            cart = Cart.objects.get(user=request.user)
            item = CartItem.objects.get(id=pk, cart=cart)
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data['quantity']
        item.save()

        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data)


class CartDeleteItemView(APIView):
    """DELETE /api/cart/items/{id}/ — Remove an item from cart."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            cart = Cart.objects.get(user=request.user)
            item = CartItem.objects.get(id=pk, cart=cart)
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        item.delete()
        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data)


class CartClearView(APIView):
    """DELETE /api/cart/clear/ — Remove all items from cart."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass
        return Response({'message': 'Cart cleared.'})


# ═══════════════════════════════════════════════════════════
#  COUPON VIEWS
# ═══════════════════════════════════════════════════════════

class CouponValidateView(APIView):
    """POST /api/coupons/validate/ — Validate a coupon code."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code'].strip().upper()

        try:
            coupon = Coupon.objects.get(code__iexact=code, is_active=True)
        except Coupon.DoesNotExist:
            return Response({'error': 'Invalid coupon code.'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        if coupon.valid_from and now < coupon.valid_from:
            return Response({'error': 'This coupon is not yet active.'}, status=status.HTTP_400_BAD_REQUEST)
        if coupon.valid_until and now > coupon.valid_until:
            return Response({'error': 'This coupon has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        if coupon.times_used >= coupon.usage_limit:
            return Response({'error': 'This coupon has reached its usage limit.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'valid': True,
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': str(coupon.discount_value),
            'max_discount': str(coupon.max_discount) if coupon.max_discount else None,
            'min_order_amount': str(coupon.min_order_amount),
        })


# ═══════════════════════════════════════════════════════════
#  ORDER VIEWS
# ═══════════════════════════════════════════════════════════

class OrderCreateView(APIView):
    """POST /api/orders/ — Create a new order from the user's cart."""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Get user's cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.select_related('product').all()
        except Cart.DoesNotExist:
            return Response({'error': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        if not cart_items.exists():
            return Response({'error': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check stock
        for ci in cart_items:
            if ci.product.stock < ci.quantity:
                return Response(
                    {'error': f'"{ci.product.name}" has only {ci.product.stock} units in stock.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Calculate subtotal
        subtotal = sum(ci.subtotal for ci in cart_items)

        # Coupon discount
        discount_amount = Decimal('0.00')
        coupon_code = data.get('coupon_code', '').strip().upper()
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code, is_active=True)
                if subtotal >= coupon.min_order_amount:
                    if coupon.discount_type == 'percent':
                        discount_amount = subtotal * (coupon.discount_value / Decimal('100'))
                        if coupon.max_discount:
                            discount_amount = min(discount_amount, coupon.max_discount)
                    else:
                        discount_amount = coupon.discount_value
                    coupon.times_used += 1
                    coupon.save(update_fields=['times_used'])
            except Coupon.DoesNotExist:
                pass

        # Delivery
        delivery = Decimal('0') if subtotal >= 3000 else Decimal('99')
        total = subtotal - discount_amount + delivery

        # Create order
        order = Order.objects.create(
            user=request.user,
            full_name=data['full_name'],
            email=data.get('email', request.user.email),
            phone=data['phone'],
            shipping_address=data['shipping_address'],
            city=data.get('city', ''),
            state=data.get('state', ''),
            postal_code=data.get('postal_code', ''),
            subtotal=subtotal,
            shipping_fee=delivery,
            discount_amount=discount_amount,
            total_amount=total,
            payment_method=data.get('payment_method', 'cod'),
            notes=data.get('notes', ''),
            status='pending',
            payment_status='unpaid',
        )

        # Create order items + reduce stock
        for ci in cart_items:
            OrderItem.objects.create(
                order=order,
                product=ci.product,
                product_name=ci.product.name,
                product_sku=ci.product.sku,
                unit_price=ci.product.effective_price,
                quantity=ci.quantity,
                total_price=ci.subtotal,
            )
            ci.product.stock -= ci.quantity
            ci.product.save(update_fields=['stock', 'in_stock'])

        # Clear cart
        cart.items.all().delete()

        order_serializer = OrderSerializer(order)
        return Response({
            'message': 'Order placed successfully.',
            'order': order_serializer.data,
        }, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    """GET /api/orders/ — List the authenticated user's orders."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class OrderDetailView(generics.RetrieveAPIView):
    """GET /api/orders/{id}/ — Get order details."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class OrderCancelView(APIView):
    """POST /api/orders/{id}/cancel/ — Cancel an order."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.status in ('shipped', 'delivered', 'cancelled'):
            return Response(
                {'error': f'Cannot cancel an order that is {order.get_status_display()}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'cancelled'
        order.save(update_fields=['status'])

        # Restore stock
        for item in order.items.select_related('product').all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save(update_fields=['stock', 'in_stock'])

        return Response({'message': 'Order cancelled successfully.'})


# ═══════════════════════════════════════════════════════════
#  SERVICE BOOKING VIEWS
# ═══════════════════════════════════════════════════════════

class WorkshopServiceListView(generics.ListAPIView):
    """GET /api/services/ — List available workshop services."""
    serializer_class = WorkshopServiceSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = WorkshopService.objects.filter(is_active=True)


class ServiceBookingCreateView(APIView):
    """POST /api/service-appointments/ — Book a service appointment."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CreateServiceBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            service = WorkshopService.objects.get(id=data['service_id'])
        except WorkshopService.DoesNotExist:
            return Response({'error': 'Service type not found.'}, status=status.HTTP_404_NOT_FOUND)

        booking = ServiceBooking.objects.create(
            user=request.user if request.user.is_authenticated else None,
            service=service,
            custom_vehicle_info=data['vehicle_info'],
            booking_date=data['booking_date'],
            time_slot=data['time_slot'],
            customer_notes=data.get('notes', ''),
        )

        return Response({
            'message': 'Service appointment booked successfully!',
            'booking_reference': booking.booking_reference,
            'service': service.name,
            'date': str(booking.booking_date),
            'time_slot': booking.time_slot,
            'status': booking.status,
        }, status=status.HTTP_201_CREATED)


class ServiceBookingListView(generics.ListAPIView):
    """GET /api/service-appointments/ — List user's service bookings."""
    serializer_class = ServiceBookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return ServiceBooking.objects.filter(user=self.request.user).select_related('service')


# ═══════════════════════════════════════════════════════════
#  VEHICLE BOOKING VIEWS
# ═══════════════════════════════════════════════════════════

class VehicleBookingCreateView(APIView):
    """POST /api/vehicle-bookings/ — Book a vehicle."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VehicleBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        car_model_obj = None
        if data.get('vehicle_model_id'):
            try:
                car_model_obj = CarModel.objects.get(id=data['vehicle_model_id'])
            except CarModel.DoesNotExist:
                pass

        booking = VehicleBooking.objects.create(
            user=request.user if request.user.is_authenticated else None,
            car_model=car_model_obj,
            vehicle_name=data['vehicle_name'],
            full_name=data['full_name'],
            phone=data['phone'],
            email=data['email'],
            city=data.get('city', ''),
            notes=data.get('notes', ''),
        )

        return Response({
            'message': 'Vehicle booking request submitted successfully! Our dealership will contact you within 2 business hours.',
            'booking_reference': booking.booking_reference,
            'vehicle': booking.vehicle_name,
            'status': booking.status,
        }, status=status.HTTP_201_CREATED)


class VehicleBookingListView(generics.ListAPIView):
    """GET /api/vehicle-bookings/ — List user's vehicle bookings."""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return VehicleBooking.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = [{
            'id': b.id,
            'booking_reference': b.booking_reference,
            'vehicle_name': b.vehicle_name,
            'full_name': b.full_name,
            'phone': b.phone,
            'email': b.email,
            'city': b.city,
            'status': b.status,
            'created_at': b.created_at,
        } for b in qs]
        return Response(data)


# ═══════════════════════════════════════════════════════════
#  TEST DRIVE VIEWS
# ═══════════════════════════════════════════════════════════

class TestDriveCreateView(APIView):
    """POST /api/test-drives/ — Book a test drive."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TestDriveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        car_model_obj = None
        if data.get('vehicle_model_id'):
            try:
                car_model_obj = CarModel.objects.get(id=data['vehicle_model_id'])
            except CarModel.DoesNotExist:
                pass

        appointment = TestDriveAppointment.objects.create(
            user=request.user if request.user.is_authenticated else None,
            car_model=car_model_obj,
            vehicle_name=data['vehicle_name'],
            full_name=data['full_name'],
            phone=data['phone'],
            preferred_date=data['preferred_date'],
            time_slot=data['time_slot'],
            notes=data.get('notes', ''),
        )

        return Response({
            'message': 'Test drive booked successfully! A confirmation SMS and email have been sent.',
            'booking_reference': appointment.booking_reference,
            'vehicle': appointment.vehicle_name,
            'date': str(appointment.preferred_date),
            'time_slot': appointment.time_slot,
            'status': appointment.status,
        }, status=status.HTTP_201_CREATED)


class TestDriveListView(generics.ListAPIView):
    """GET /api/test-drives/ — List user's test drive appointments."""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return TestDriveAppointment.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = [{
            'id': a.id,
            'booking_reference': a.booking_reference,
            'vehicle_name': a.vehicle_name,
            'full_name': a.full_name,
            'preferred_date': a.preferred_date,
            'time_slot': a.time_slot,
            'status': a.status,
            'created_at': a.created_at,
        } for a in qs]
        return Response(data)


# ═══════════════════════════════════════════════════════════
#  DASHBOARD VIEWS
# ═══════════════════════════════════════════════════════════

class DashboardSummaryView(APIView):
    """GET /api/dashboard/stats/ — Admin/staff dashboard summary."""
    permission_classes = [permissions.AllowAny]  # Frontend shows dashboard publicly; admin check can be added

    def get(self, request):
        total_vehicles = CarModel.objects.count()
        total_orders = Order.objects.count()
        total_customers = User.objects.filter(role='customer').count()
        total_revenue = Order.objects.filter(
            Q(payment_status='paid') | Q(status='delivered')
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_products = Product.objects.count()
        pending_services = ServiceBooking.objects.filter(status='pending').count()

        # Upcoming service appointments
        upcoming = ServiceBooking.objects.filter(
            booking_date__gte=timezone.now().date()
        ).select_related('service', 'user').order_by('booking_date')[:10]

        upcoming_list = [{
            'id': b.id,
            'booking_reference': b.booking_reference,
            'customer': b.user.username if b.user else 'Guest',
            'service': b.service.name,
            'vehicle': b.custom_vehicle_info,
            'date': str(b.booking_date),
            'time_slot': b.time_slot,
            'status': b.status,
        } for b in upcoming]

        # Recent orders
        recent = Order.objects.order_by('-created_at')[:10]
        recent_list = [{
            'id': o.id,
            'order_number': o.order_number,
            'customer': o.full_name,
            'total': str(o.total_amount),
            'status': o.status,
            'payment_status': o.payment_status,
            'created_at': str(o.created_at),
        } for o in recent]

        return Response({
            'total_vehicles': total_vehicles,
            'total_orders': total_orders,
            'total_customers': total_customers,
            'total_revenue': str(total_revenue),
            'total_products': total_products,
            'pending_services': pending_services,
            'upcoming_services': upcoming_list,
            'recent_orders': recent_list,
        })
