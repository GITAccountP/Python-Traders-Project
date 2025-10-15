
from django.urls import path
from . import views

urlpatterns = [
    path(
        'DjTraders', 
        views.DjTradersHome, 
        name='DjTraders.Home'),
    
    path(
        'DjTraders/Customers', 
         views.DjTradersCustomersView.as_view(), 
         name='DjTraders.Customers'),
    
    path(
        'DjTraders/CustomersJSON', 
         views.CustomersListJSON.as_view(), 
         name='DjTraders.CustomersJSON'),
    
    path(
        'DjTraders/TopTenCustomers', 
         views.CustomerOrders.as_view(), 
         name='DjTraders.TopCustomerOrders'),

    # v2.1 
    # Add path to Form for add and edit customers
    path(
        route = 'DjTraders/Customers/new', 
        view = views.DjTradersCustomerCreate.as_view(), 
        name='DjTraders.CustomerAdd'),

    path(
        route = 'DjTraders/Customers/<int:pk>/Edit', 
        view = views.DjTradersCustomerEdit.as_view(), 
        name='DjTraders.CustomerEdit'),

    path(
        route = 'DjTraders/Customers/<int:pk>/Delete', 
        view = views.DjTradersCustomerDelete.as_view(), 
        name='DjTraders.CustomerDelete'),
    
    path(
        'DjTraders/CustomerDetail/<int:pk>', 
         views.DjTradersCustomerDetailView.as_view(), 
         name='DjTraders.CustomerDetail'),

    path(
        'DjTraders/Products', 
         views.DjTradersProductsView.as_view(), 
         name='DjTraders.Products'),
    
    path(
        'DjTraders/ProductDetail/<int:pk>', 
        views.DjTradersProductDetailView.as_view(), 
        name='DjTraders.ProductDetail'),

    path(
        route = 'DjTraders/Products/new', 
        view = views.DjTradersProductCreate.as_view(), 
        name='DjTraders.ProductAdd'),

    path(
        route = 'DjTraders/Products/<int:pk>/Edit', 
        view = views.DjTradersProductEdit.as_view(), 
        name='DjTraders.ProductEdit'),

    path(
        route = 'DjTraders/Products/<int:pk>/Delete', 
        view = views.DjTradersProductDelete.as_view(), 
        name='DjTraders.ProductDelete'),
    
    path(
        route = 'DjTraders/ProductPurchase/<int:pk>', 
        view = views.DjTradersProductPurchaseView.as_view(), 
        name='DjTraders.ProductPurchase'),
    
    path(
        'DjTraders/OrdersPlaced',
        views.OrdersPlaced,
        name='DjTraders.OrdersPlaced'),

    path(
        'DjTraders/OrdersByDate',
        views.OrdersByDate,
        {'selOrderYear': ""},
        name='DjTraders.OrdersByDate'),

    path(
        'DjTraders/OrdersByCategory',
        views.OrdersByCategory,
        name='DjTraders.OrdersByCategory'),

    path(
        'DjTraders/OrdersByProduct',
        views.OrdersByProduct,
        name='DjTraders.OrdersByProduct'),
    
    path(
        'DjTraders/ProductAnnualSales',
        views.ProductAnnualSales,
        name='DjTraders.ProductAnnualSales'),
    
    path(
        'DjTraders/TopBottomTenProducts/',
        views.plot_top_bottom_product_analysis,
        {'selOrderYear': ""},
        name='DjTraders.TopBottomProductAnalysis'),
    
    path(
        route = 'DjTraders/ProductAnalysisPage/<int:pk>',
        view = views.ProductAnalysisPageView.as_view(),
        name='DjTraders.ProductAnalysisPage'),

    path(
        route = 'DjTraders/AnnualAndMonthlyProduct/<int:pk>',
        view = views.ProductAnnualMonthlySales,
        name='DjTraders.AnnualAndMonthlyProduct'),

    path('DjTraders/ProductSaleAnalysis/<int:pk>',
        views.product_sales_analysis,
        name='DjTraders.ProductSaleAnalysis'),

    path('DjTraders/CategorySaleAnalysis/<int:pk>',
        views.CategoryAnalysis,
        name='DjTraders.CategorySaleAnalysis'),

    path(
        'DjTraders/GetEachProductDetails',
        views.GetProductDetails,
        name='DjTraders.GetEachProductDetails'),
 ]