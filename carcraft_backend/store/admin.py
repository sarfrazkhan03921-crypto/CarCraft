from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, CarMake, CarModel, UserVehicle, Category, Brand, Product,
    ProductImage, ProductReview, CustomBuild, CustomBuildPart,
    WorkshopService, ServiceBooking, Cart, CartItem, Order, OrderItem,
    CustomQuoteRequest,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('CarCraft Profile', {
            'fields': ('role', 'phone', 'avatar', 'address', 'city', 'state', 'postal_code', 'bio'),
        }),
    )


@admin.register(CarMake)
class CarMakeAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'make', 'body_type', 'year_start', 'year_end')
    list_filter = ('body_type', 'make')
    search_fields = ('name', 'make__name')


@admin.register(UserVehicle)
class UserVehicleAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'user', 'license_plate', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('user__username', 'license_plate')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_featured')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'brand', 'price', 'discount_price', 'stock', 'in_stock', 'is_featured')
    list_filter = ('category', 'brand', 'in_stock', 'is_featured', 'is_bestseller')
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'verified_purchase', 'created_at')
    list_filter = ('rating', 'verified_purchase')


@admin.register(WorkshopService)
class WorkshopServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'estimated_duration_hours', 'is_active', 'is_popular')
    list_filter = ('is_active', 'is_popular')
    search_fields = ('name',)


@admin.register(ServiceBooking)
class ServiceBookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'user', 'service', 'booking_date', 'time_slot', 'status')
    list_filter = ('status', 'booking_date')
    search_fields = ('booking_reference', 'user__username')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'subtotal', 'updated_at')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'subtotal')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'product_sku', 'unit_price', 'quantity', 'total_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'total_amount', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method')
    search_fields = ('order_number', 'user__username', 'user__email')
    inlines = [OrderItemInline]


@admin.register(CustomBuild)
class CustomBuildAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'total_cost', 'is_public')
    list_filter = ('status', 'is_public')


@admin.register(CustomQuoteRequest)
class CustomQuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'vehicle_details', 'project_type', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'email', 'vehicle_details')
