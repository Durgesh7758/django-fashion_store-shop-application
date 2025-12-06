from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from shop.api_views import ProductViewSet, CartViewSet, OrderViewSet
from shop import views as shop_views

# DRF Router (API ke liye)
router = DefaultRouter()
router.register('products', ProductViewSet, basename='products')
router.register('cart', CartViewSet, basename='cart')
router.register('orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Root -> shop home
    path('', shop_views.index, name='home'),

    # Shop normal pages
    path('shop/', include(('shop.urls', 'shop'), namespace='shop')),

    # Password reset ke liye default URL mapping bina namespace ke
    path('', include('django.contrib.auth.urls')),

    # API routes
    path('api/', include(router.urls)),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

