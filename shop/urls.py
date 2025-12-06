from django.urls import path
from . import views as v
from django.contrib.auth import views as auth_views


app_name = 'shop'

urlpatterns = [
    # Shop Pages
    path('', v.index, name='ShopHome'),
    path('fashion/', v.fashion, name="fashion"),
    
    path('product/<int:product_id>/', v.product_detail, name='product_detail'),

    path('product/<int:product_id>/rate/', v.add_rating, name='add_rating'),

    path('register/', v.register_user, name='register'),
    path('login/', v.login_user, name='login'),
    path('logout/', v.logout_user, name='logout'), 
    path('about/', v.about, name='about'),   
    path('contact', v.contact, name='Contact'),
    path('search', v.search, name='Search'),
#     path('productview', v.productView, name='ProductView'),
    path('checkout', v.checkout, name='checkout'),
    path('payment/', v.payment, name='payment'),
    path('invoice/<int:order_id>/', v.invoice, name='invoice'),  # html invoice
    path('invoice/<int:order_id>/pdf/', v.invoice_pdf, name='invoice_pdf'),  # pdf
    path('update-size/<int:cart_id>/', v.update_cart_size, name='update_cart_size'),
    # Cart size update
     path('cart/update_size/<int:cart_id>/', v.update_cart_size, name='update_cart_size'),


    path('payment/process/', v.payment_process, name='payment_process'),
    path('order/confirmation/<int:order_id>/', v.order_confirmation, name='order_confirmation'),

    path('admin-dashboard/', v.admin_dashboard, name='admin_dashboard'),
     path('admin-products/add/', v.add_product, name='add_product'),
     path('admin-products/edit/<int:prod_id>/', v.edit_product, name='edit_product'),
     path('admin-products/delete/<int:prod_id>/', v.delete_product, name='delete_product'),
     path('admin-orders/update/<int:order_id>/', v.update_order_status, name='update_order_status'),
     path('admin-users/', v.manage_users, name='manage_users'),

     # User management
     path('edit-user/<int:user_id>/', v.edit_user, name='edit_user'),
     path('delete-user/<int:user_id>/', v.delete_user, name='delete_user'),

    path('order/<int:order_id>/', v.order_detail, name='order_detail'),
    path('backup', v.backupindex, name='backupindex'),
    path('copyindex', v.copyindex, name='copyindex'),

    path('bestseller',v.bestseller,name='bestseller'),
    path('newlyadded',v.newlyadded,name='newlyadded'),
    path('trending',v.trending,name='trending'),

    # Cart
    path('add_to_cart/<int:prod_id>/', v.add_to_cart, name='add_to_cart'),
    path('cart/', v.view_cart, name='view_cart'),
    path('cart/increase/<int:cart_id>/', v.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:cart_id>/', v.decrease_quantity, name='decrease_quantity'),

    path('product/<int:id>/', v.productView, name="productview"),
    path("buy/<int:product_id>/", v.buy_now, name="buy_now"),


    # User order history page
    path('orders/', v.order_history, name='order_history'),

    # Forgot Password / Reset
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(template_name="auth/password_reset.html"), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="auth/password_reset_confirm.html"), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"), 
         name='password_reset_complete'),


]
