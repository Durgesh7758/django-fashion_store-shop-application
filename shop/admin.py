from django.contrib import admin
from .models import Product, ProductImage, ProductVariant, Cart, Order, OrderItem, UserAddress, Rating

# Inline for multiple images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'subcategory', 'price', 'is_trending', 'pub_date')
    list_filter = ('category', 'is_trending')
    search_fields = ('product_name', 'category', 'subcategory')
    inlines = [ProductImageInline, ProductVariantInline]

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'added_on')
    search_fields = ('user__username', 'product__product_name')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'paid', 'payment_method', 'txn_id', 'ordered_on')
    list_filter = ('status', 'paid')
    search_fields = ('user__username', 'txn_id')
    list_editable = ('status',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'product', 'quantity')
    search_fields = ('order__id', 'product__product_name', 'user__username')

@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'email', 'phone', 'city', 'state', 'pincode')
    search_fields = ('user__username', 'name', 'city', 'state')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__product_name', 'user__username')
