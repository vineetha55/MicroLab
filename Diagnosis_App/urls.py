from django.urls import path
from . import views

urlpatterns=[
    path("",views.index,name="index"),
    path("Admin/",views.admin_login,name="admin_login"),
    path("admin_login_check/",views.admin_login_check,name="admin_login_check"),
    path("Admin_Dashboard/",views.Admin_Dashboard,name="Admin_Dashboard"),

    ##########################################################################
    path('change_password/', views.change_password_view, name='change_password'),
    path("LogoutAdmin/",views.LogoutAdmin,name="LogoutAdmin"),

    ##########################################################################

    path('tests/', views.test_list, name='test_list'),
    path('tests/add/', views.test_create, name='test_create'),
    path('tests/edit/<int:pk>/', views.test_edit, name='test_edit'),
    path('tests/delete/<int:pk>/', views.test_delete, name='test_delete'),

    ##########################################################################

    path('packages/', views.package_list, name='package_list'),
    path('package/add/', views.package_add, name='package_add'),
    path('package/edit/<int:id>/', views.package_edit, name='package_edit'),
    path('package/delete/<int:id>/', views.package_delete, name='package_delete'),


    ############################################################################

    path("branch/",views.branch,name="branch_list"),
    path('branches/add/', views.branch_add, name='branch_add'),
    path('branches/edit/<int:id>/', views.branch_edit, name='branch_edit'),
    path('branches/delete/<int:id>/', views.branch_delete, name='branch_delete'),


    ###############################################################################

    path("user/tests/",views.user_tests,name="user_tests"),
    path('test/<int:test_id>/', views.test_detail, name='test_detail'),
    path('add-to-cart/<int:test_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),

    #################################################################################


    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),


    #################################################################################

    path('Checkups/', views.checkup_list, name='checkup_list'),
    path('checkup/add/', views.checkup_add, name='checkup_add'),
    path('checkup/edit/<int:pk>/', views.checkup_edit, name='checkup_edit'),
    path('checkup/delete/<int:pk>/', views.checkup_delete, name='checkup_delete'),



    #######################################################################################

    path("user/checkups/",views.user_checkups,name="user_checkups"),
    path("checkup/<slug:slug>/", views.checkup_detail, name="checkup_detail"),
    path("cart/add-checkup/", views.add_checkup_to_cart, name="add_checkup_to_cart"),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('thank-you/', views.thank_you, name='thank_you'),


    ########################################################################################

    path('new_lab_orders/', views.new_lab_orders, name='new_lab_orders'),
    path('cancelled_orders/', views.cancelled_orders, name='cancelled_orders'),
    path('completed_orders/', views.completed_orders, name='completed_orders'),
    path('update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('invoice/<int:order_id>/', views.print_invoice, name='print_invoice'),

    #################################################################################

    path("customers/",views.customers,name="customers"),
    path("Logout/",views.Logout,name="Logout"),
    path("My_orders/",views.My_orders,name="My_orders"),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/', views.reset_password, name='reset_password'),
    path("remove-from-cart/", views.remove_from_cart, name="remove_from_cart"),




]
