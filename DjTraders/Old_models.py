# # This is an auto-generated Django model module.
# # You'll have to do the following manually to clean this up:
# #   * Rearrange models' order
# #   * Make sure each model has one field with primary_key=True
# #   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
# #   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# # Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.db.models import F, Sum, Count, Max, ExpressionWrapper, DecimalField
from decimal import Decimal
#from django.utils import timezone
from datetime import timedelta
import datetime
#from datetime import datetime
from django.db.models.functions import ExtractYear, ExtractMonth, Cast
import plotly.express as px
from plotly.offline import plot

import pandas as pd

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    #    category_name = models.CharField(max_length=255, blank=True, null=True)
    #blank = False, null=False => Field is required.
    category_name = models.CharField(max_length=255, blank=False, null=False)
    #Can assign a default value for fields using default.
    description = models.CharField(max_length=255, blank=True, null=True, default="")

    class Meta:
        managed = False
        db_table = 'categories'
    
    def __str__(self):
        return (
    		self.category_name
        )
    
    @property
    def category(self):
        return self.category_name

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    customer_name = models.CharField(max_length=255, blank=False, null=False) #required
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    
    is_active = models.BooleanField(default=True, null=True)
    
    class Meta:
        managed = True
        db_table = 'customers'
     
    def CustomerOrders(self):
        orders = Order.objects.all().filter(customer = self.customer_id)
        return orders
    
    def NumberOfOrders(self):
        orders = Order.objects.all().filter(customer = self.customer_id)
        return orders.count()
    
    def get_customer_latest_order_date(self):
        customer_latest_order = Order.objects.filter(customer=self).aggregate(latest_order_date=Max('order_date'))
        return customer_latest_order['latest_order_date']
 
    def get_activeStatus(self):
        one_year_ago = datetime.datetime.now().date() - timedelta(days=365)
        customer_latest_order_date = self.get_customer_latest_order_date()
 
        if customer_latest_order_date:
            if customer_latest_order_date > one_year_ago:
                self.is_active = True
                self.save()
                return "Active"
            else:
                self.is_active = False
                self.save()
                return "Inactive"
        else:
            return "Active"

    def __str__(self):
        return (
    		self.customer_name 
      		+ " [Contact: "+ self.contact_name +  "]"
        )
        
    def OrdersPlacedPlot(self):
        customerOrders = self.CustomerOrders()
        
        print(list(customerOrders.values_list()))

        ordersdFrame = pd.DataFrame(
            list(customerOrders.values())
        )
        
        print(ordersdFrame)

        # Create arrays to hold data 
        number_Of_Orders = customerOrders.count()
        order_dates = [0 for _ in range(number_Of_Orders)]
        order_totals = [0 for _ in range(number_Of_Orders)]
        order_ids = [0 for _ in range(number_Of_Orders)]
        index = 0
        
        # for each order in customerOrders, extract, dates, totals and id in each order.
        for order in customerOrders:
            order_ids[index] = order.order_id
            order_dates[index] = order.order_date
            order_totals[index] = order.OrderTotal()
            index = index+1
        
        # Create the bar chart - x and y are required, 
        # others are optional formatting.
        fig = px.bar(
            x=order_dates,
            y= order_totals,
            
            color=order_ids,
            labels={'color':'Order'},
            text_auto=True,
        )
        
        figure_title = 'Total Order by Date for '  + self.customer_name
        
        # Format Chart and Axes titles 
        fig.update_layout(
            title = figure_title,
            xaxis_title="Order Date",
            yaxis_title="Order Total",
        )
        
        # Colors and formats - remove legend.
        fig.update_layout(
            coloraxis_showscale=False,
            yaxis_tickprefix = '$', 
            yaxis_tickformat = ',.2f'
        )
        
        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')
        #return the html to place in the context and display
        return plot_html
  
    # v3.1 Added - Member function in Customers class uses query techniques 
    # to generate the data for the Orders Plot 
    # Shows extraction of individual elements in order and order details.
    def AnotherOrdersPlot(self):
        customerOrders = self.CustomerOrders().annotate(
        Year = ExtractYear("order_date"),
        Month = ExtractMonth("order_date"),
        CustomerName = F('customer__customer_name'),
        NumberOfProducts = Count('orderdetail'),
        #   ProductName = F('orderdetail__product__product_name'),
        #   CategoryName = F('orderdetail__product__category__category_name'),
        #   TotalQuantity = Sum('orderdetail__quantity'),
        #   ProductPrice = Sum('orderdetail__product__price'),
            OrderTotal = Sum(F('orderdetail__product__price')*F('orderdetail__quantity')),
        )
        
        print(list(customerOrders.values_list()))
        
        ordersdFrame = pd.DataFrame(
            list(customerOrders.values())
        )
        print(ordersdFrame)
        
        fig = px.bar(ordersdFrame,
            x='order_date',
            y= 'OrderTotal',
            
            color='order_id',
            labels={'color':'Order'},
            text_auto=True,
        )
        
        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')
        
        #return the html to place in the context and display
        return plot_html

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255, blank=True, null=True)
    
    # category_id = models.IntegerField(blank=True, null=True)
    # I am not using on_delete=models.Cascade because I dont want to delete categories when a product is deleted.
    # Also note the name change, since category_id is in the DB, this should just be category.
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING)
    
    unit = models.CharField(max_length=255, blank=True, null=True)
    
    # Must define a price.
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    
    is_available = models.BooleanField(default=True, null=True)
    
    # Method to return the customers who purchased this product
    def PurchasedBy(self):
        CustomersWhoBoughtProduct = Customer.objects.filter(
            order__orderdetail__product_id=self.product_id
        ).distinct()
        return CustomersWhoBoughtProduct
    
    def customer_purchase_summary(self):
        purchase_summary = OrderDetail.objects.filter(product=self).values('order__customer__customer_name').annotate(
            total_quantity=Sum('quantity'),
            total_orders=Count('order')
        )
        return purchase_summary
    
    def get_product_latest_order_date(self):
        product_latest_order = OrderDetail.objects.filter(product=self).aggregate(latest_order_date=Max('order__order_date'))
        print(product_latest_order['latest_order_date'])
        return product_latest_order['latest_order_date']
 
    def get_availabilityStatus(self):
        one_year_ago = datetime.datetime.now().date() - timedelta(days=365)
        product_latest_order_date = self.get_product_latest_order_date()
 
        if product_latest_order_date:
            if product_latest_order_date > one_year_ago:
                self.is_available = True
                self.save()
                return "Available"
            else:
                self.is_available = False
                self.save()
                return "Unavailable"
        else:
            return "Available"

    class Meta:
        managed = True
        db_table = 'products'


class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    #customer_id = models.IntegerField(blank=True, null=True)
    # I am not using on_delete=models.Cascade because I dont want to delete customers when an order is deleted.
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    # The order date will be added for the current date when the order is saved.
    order_date = models.DateField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'orders'
    
    def AllOrderDetails(self):
        orderdetails = OrderDetail.objects.filter(order = self.order_id)
        return orderdetails
    
    def OrderTotal(self):
        orderDetails = OrderDetail.objects.filter(order = self.order_id)
        
        total = Decimal("0.0")
        
        for line in orderDetails:
            total += line.Total #(quantity*product.price)
        
        return total
        # return orderDetails.aggregate(
        #     total=Sum('LineTotal')
        # )['total']
    
    def AllOrderYears():
        '''
            Returns a queryset of each distinct year an order was placed, 
            in chronological order
        '''
        allYears = Order.objects.all().annotate(
            Year = ExtractYear("order_date")
        ).order_by('Year').distinct()
        
        return allYears.values('Year')
   

class OrderDetail(models.Model):
    order_detail_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_details'
    
    @property
    def Total(self):
        return self.quantity*self.product.price
    
    @property
    def product_name(self):
        if (self.product):
            return self.product.product_name
        else:
            return ''