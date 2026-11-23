from django.urls import path
from .views import (
    # Vehicles
    VehicleListView, VehicleDetailView, CarMakeListView, CarModelListView,
    # Products
    ProductListView, ProductDetailView, CategoryListView, BrandListView,
    # Cart
    CartView, CartAddItemView, CartUpdateItemView, CartDeleteItemView, CartClearView,
    # Coupons
    CouponValidateView,
    # Orders
    OrderCreateView, OrderListView, OrderDetailView, OrderCancelView,
    # Services
    WorkshopServiceListView, ServiceBookingCreateView, ServiceBookingListView,
    # Vehicle Booking
    VehicleBookingCreateView, VehicleBookingListView,
    # Test Drive
    TestDriveCreateView, TestDriveListView,
    # Dashboard
    DashboardSummaryView,
)

urlpatterns = [
    # Vehicles
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    path('car-makes/', CarMakeListView.as_view(), name='car-make-list'),
    path('car-models/', CarModelListView.as_view(), name='car-model-list'),

    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('brands/', BrandListView.as_view(), name='brand-list'),

    # Cart
    path('cart/', CartView.as_view(), name='cart-view'),
    path('cart/items/', CartAddItemView.as_view(), name='cart-add-item'),
    path('cart/items/<int:pk>/', CartUpdateItemView.as_view(), name='cart-update-item'),
    path('cart/items/<int:pk>/delete/', CartDeleteItemView.as_view(), name='cart-delete-item'),
    path('cart/clear/', CartClearView.as_view(), name='cart-clear'),

    # Coupons
    path('coupons/validate/', CouponValidateView.as_view(), name='coupon-validate'),

    # Orders
    path('orders/', OrderCreateView.as_view(), name='order-create'),
    path('orders/list/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),

    # Services
    path('services/', WorkshopServiceListView.as_view(), name='service-list'),
    path('service-appointments/', ServiceBookingCreateView.as_view(), name='service-booking-create'),
    path('service-appointments/list/', ServiceBookingListView.as_view(), name='service-booking-list'),
    path('bookings/', ServiceBookingCreateView.as_view(), name='booking-create-alias'),

    # Vehicle Booking
    path('vehicle-bookings/', VehicleBookingCreateView.as_view(), name='vehicle-booking-create'),
    path('vehicle-bookings/list/', VehicleBookingListView.as_view(), name='vehicle-booking-list'),

    # Test Drive
    path('test-drives/', TestDriveCreateView.as_view(), name='test-drive-create'),
    path('test-drives/list/', TestDriveListView.as_view(), name='test-drive-list'),

    # Dashboard
    path('dashboard/stats/', DashboardSummaryView.as_view(), name='dashboard-stats'),
]
