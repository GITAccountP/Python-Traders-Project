# # This is an auto-generated Django model module.
# # You'll have to do the following manually to clean this up:
# #   * Rearrange models' order
# #   * Make sure each model has one field with primary_key=True
# #   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
# #   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# # Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.db.models import F, Sum, Count, Max
from decimal import Decimal
#from django.utils import timezone
from datetime import timedelta
import datetime
#from datetime import datetime
from django.db.models.functions import ExtractYear, ExtractMonth, Cast, Coalesce
import plotly.express as px
from plotly.offline import plot
import calendar
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
        
    # v3.2 Added - Member function in Customers class to generate Orders Plot based on supplied year
    def OrdersPlacedPlot(self, year):
        customerOrders = self.CustomerOrders().order_by('order_date').annotate(
        Year = ExtractYear("order_date"),
        Month = ExtractMonth("order_date"),
        CustomerName = F('customer__customer_name'),
        OrderTotal = Sum(F('orderdetail__product__price')*F('orderdetail__quantity')),
        NumberOfProducts = Count('orderdetail'),
        #   ProductName = F('orderdetail__product__product_name'),
        #   CategoryName = F('orderdetail__product__category__category_name'),
        #   TotalQuantity = Sum('orderdetail__quantity'),
        #   ProductPrice = Sum('orderdetail__product__price'),
        )
        if year: 
            customerOrders = customerOrders.filter(Year__contains= year)

        if customerOrders.count()==0:
            return '<div> No Orders placed</div>'

        #print(list(customerOrders.values_list()))

        ordersdFrame = pd.DataFrame(
            list(customerOrders.values())
        )
        #print(ordersdFrame)

        # Create the bar chart - x and y are required, 
        # others are optional formatting.
        fig = px.bar(
            ordersdFrame,
            x='order_date',
            y= 'OrderTotal',
            color='order_id',
            labels={'color':'order_id'},
            text_auto=True,
        )

        figure_title = 'Orders by Date for '  + self.customer_name

        # Format Chart and Axes titles 
        fig.update_layout(
            title = figure_title,
            xaxis_title="",
            yaxis_title="Year Order Placed",
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

    # v3.2 Generate a list of objects for the total sales revenue from orders placed each year by the current customer - "self".
    def AnnualOrders(self):
        # Year is extracted from order_date using the "__" for year ()
        # This is another method to get components of a datetime object, in addition to the "ExtractYear" function
        annualOrders = self.CustomerOrders().annotate(
            Year = Cast(F("order_date__year"),output_field=models.CharField()),
            OrderTotal = Sum(F('orderdetail__product__price')*F('orderdetail__quantity'), 
                            distinct=True),
        ).values('Year', 'OrderTotal').order_by("Year")
        #print(annualOrders)

        #print(list(annualOrders))

        annuals =pd.DataFrame(list(annualOrders)) 
        print(annuals)
        annuals = annuals.groupby("Year").agg("sum").reset_index()
        print(annuals)

        fig = px.bar(annuals,x='Year', y='OrderTotal', 
                        color='Year', text_auto=True,
                    )

        # Format Chart and Axes titles 
        fig.update_layout(
            title = 'Annual Orders',
            xaxis_title="Order Year",
            yaxis_title="Order Total",
        )

        # Colors and formats - show/hide legend.
        fig.update_layout(
            coloraxis_showscale=False,
            yaxis_tickprefix = '$', 
            yaxis_tickformat = ',.2f'
        )
        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')

        #return the html to place in the context and display
        return plot_html

    # v3.2 Generate a plot of products and their total sales revenue from orders placed by the current customer - "self".
    def ProductReveues(self):
        # Year is extracted from order_date using the "__" for year ()
        # This is another method to get components of a datetime object, in addition to the "ExtractYear" function
        productOrders = self.CustomerOrders().order_by('order_date').annotate(
            ProductName = F('orderdetail__product__product_name'),
            CategoryName = F('orderdetail__product__category__category_name'),
            TotalQuantity = Sum('orderdetail__quantity'),
            ProductTotal = Sum(F('orderdetail__product__price')*F('orderdetail__quantity'),distinct=True),
            #Year = Cast(F("order_date__year"), output_field=models.CharField()),
        ).distinct()

        productOrders = productOrders.values('ProductName', 'ProductTotal', 'CategoryName').order_by('CategoryName')
        productsData =pd.DataFrame(list(productOrders)) 
        productsData = productsData.groupby('ProductName').agg("sum").reset_index()
        print(productsData)

        fig = px.bar(productsData,x='ProductName', y='ProductTotal', 
                        color='ProductName', text_auto=True,                    )
                # Format Chart and Axes titles 
        fig.update_layout(
            title = 'Revenues from Products',
            xaxis_title="Products",
            yaxis_title="Revenue",
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

    # v3.2 Generate a plot of products and their total sales revenue from orders placed by the current customer - "self".
    def ProductsSoldPlot(self):
        # Year is extracted from order_date using the "__" for year ()
        # This is another method to get components of a datetime object, in addition to the "ExtractYear" function
        productOrders = self.CustomerOrders().order_by('order_date').annotate(
            ProductName = F('orderdetail__product__product_name'),
            CategoryName = F('orderdetail__product__category__category_name'),
            TotalQuantity = Sum('orderdetail__quantity'),
            ProductTotal = Sum(F('orderdetail__product__price')*F('orderdetail__quantity'),distinct=True),
            #Year = Cast(F("order_date__year"), output_field=models.CharField()),
        ).distinct()
        productOrders = productOrders.values('ProductName', 'ProductTotal', 'TotalQuantity')

        productsData =pd.DataFrame(list(productOrders)) 
        productsData = productsData.groupby('ProductName').agg("sum").reset_index()
        print(productsData)

        fig = px.bar(productsData,x='ProductName', y='TotalQuantity', 
                        color='ProductName', text_auto=True)
                # Format Chart and Axes titles 
        fig.update_layout(
            title = 'Products Quantities',
            xaxis_title="Products",
            yaxis_title="Revenue",
        )

        # Colors and formats - remove legend.
        fig.update_layout(
            coloraxis_showscale=False,
        )
        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')

        #return the html to place in the context and display
        return plot_html

    # v3.2 Generate a plot of products and their total sales revenue from orders placed by the current customer - "self".
    def ProductCategoryRevenusPlot(self):
        # Year is extracted from order_date using the "__" for year ()
        # This is another method to get components of a datetime object, in addition to the "ExtractYear" function
        categoryOrders = self.CustomerOrders().order_by('order_date').annotate(
            #ProductName = F('orderdetail__product__product_name'),
            CategoryName = F('orderdetail__product__category__category_name'),
            CategoryTotalQuantity = Sum('orderdetail__quantity'),
            CategoryTotalRevenue = Sum(F('orderdetail__product__price')*F('orderdetail__quantity'),distinct=True),
            #Year = Cast(F("order_date__year"), output_field=models.CharField()),
        ).distinct()

        categoryOrders = categoryOrders.values('CategoryName', 'CategoryTotalRevenue')

        print(list(categoryOrders))

        categoryData =pd.DataFrame(list(categoryOrders)) 
        categoryData = categoryData.groupby("CategoryName").agg("sum").reset_index()

        print(categoryData)

        fig = px.bar(categoryData,x='CategoryName', y='CategoryTotalRevenue', 
                        color='CategoryName', text_auto=True,)
                # Format Chart and Axes titles 
        fig.update_layout(
            title = 'Category Sales Revenues',
            xaxis_title="Category",
            yaxis_title="Sales Revenue from Category",
        )

        # Colors and formats - remove legend.
        fig.update_layout(
            coloraxis_showscale=False,
        )
        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')

        #return the html to place in the context and display
        return plot_html

    # v3.2 Generate a plot of products and their total sales revenue from orders placed by the current customer - "self".
    def ProductCategorySalesPlot(self):
        # Year is extracted from order_date using the "__" for year ()
        # This is another method to get components of a datetime object, in addition to the "ExtractYear" function
        categoryOrders = self.CustomerOrders().order_by('order_date').annotate(
            #ProductName = F('orderdetail__product__product_name'),
            CategoryName = F('orderdetail__product__category__category_name'),
            CategoryTotalQuantity = Sum('orderdetail__quantity'),
            #ProductTotal = Sum(F('orderdetail__product__price')*F('orderdetail__quantity'),distinct=True),
            #Year = Cast(F("order_date__year"), output_field=models.CharField()),
        ).distinct()

        categoryOrders = categoryOrders.values('CategoryName', 'CategoryTotalQuantity').order_by("CategoryTotalQuantity")

        print(list(categoryOrders))

        categoryData =pd.DataFrame(list(categoryOrders)) 
        categoryData = categoryData.groupby("CategoryName").agg("sum").reset_index()

        print(categoryData)

        fig = px.bar(categoryData,x='CategoryName', y='CategoryTotalQuantity', 
                        color='CategoryName', text_auto=True,)
                # Format Chart and Axes titles 
        fig.update_layout(
            title = 'Category Sales',
            xaxis_title="Category",
            yaxis_title="# of Products Bought with Category",
        )

        # Colors and formats - remove legend.
        fig.update_layout(
            coloraxis_showscale=False,
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
    
    def __str__(self):
        return self.product_name
    
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
        
    def ProductSales(self, year=None):
        """
        Calculate sales metrics for this product: revenue and quantity sold.
        Optional year parameter to filter by year.
        """
        sales_data = OrderDetail.objects.filter(product=self).annotate(
            Year=ExtractYear('order__order_date'),
            Month=ExtractMonth('order__order_date'),
            Revenue=F('quantity') * F('product__price'),
            # Revenue=Sum(F('quantity') * F('product__price'), distinct=True)
        ).values('Year', 'Month').annotate(
            TotalRevenue=Sum('Revenue'),
            # TotalRevenue='Revenue',
            TotalQuantity=Sum('quantity')
        ).order_by('Year', 'Month')

        if year:
            sales_data = sales_data.filter(Year=year)

        return pd.DataFrame(list(sales_data))

    def GenerateProductSalesPlot(self, year=None):
        """
        Generate a bar chart for product sales.
        """
        sales_data = self.ProductSales(year=year)

        if sales_data.empty:
            return "<div>No sales data available for this product.</div>"

        if year:
            title = f"Monthly Sales for {self.product_name} ({year})"
            x_axis = 'Month'
        else:
            title = f"Annual Sales for {self.product_name}"
            x_axis = 'Year'

        fig = px.bar(
            sales_data,
            x=x_axis,
            y=['TotalRevenue', 'TotalQuantity'],
            text_auto=True,
            barmode='group',
            labels={'value': 'Metrics', 'variable': 'Metrics Type'},
            title=title
        )
        fig.update_layout(
            xaxis_title="Time Period",
            yaxis_title="Values",
            legend_title="Metrics",
            yaxis_tickprefix='$' if 'Revenue' in sales_data.columns else ''
        )

        return plot(fig, output_type='div')
 
    def AnnualProductOrders(self, year=None):
        allOrders = OrderDetail.objects.filter(product=self)
        if year:
            allOrders = allOrders.filter(order__order_date__year=year)
 
        allOrders = allOrders.annotate(
            Year=ExtractYear(F("order__order_date")),
            OrderTotal=Sum(F('product__price') * F('quantity'))
        ).values('Year', 'OrderTotal').order_by('Year')
 
        dataFrame = pd.DataFrame(list(allOrders))
        if dataFrame.empty:
            return '<div>No annual data available.</div>'
 
        fig = px.bar(
            dataFrame,
            x='Year',
            y='OrderTotal',
            text_auto=True,
            color='Year',
            labels={'OrderTotal': 'Total Revenue', 'Year': 'Year'}
        )
        fig.update_layout(
            title='Annual Sales',
            xaxis_title='Year',
            yaxis_title='Revenue',
            yaxis_tickprefix='$',
            coloraxis_showscale=False,
        )
        return plot(fig, output_type='div')

    def MonthlyProductOrders(self, year=None):
        allOrders = OrderDetail.objects.filter(product=self)
        if year:
            allOrders = allOrders.filter(order__order_date__year=year)
 
        allOrders = allOrders.annotate(
            Month=ExtractMonth(F("order__order_date")),
            OrderTotal=Sum(F('product__price') * F('quantity'))
        ).values('Month', 'OrderTotal').order_by('Month')
 
        dataFrame = pd.DataFrame(list(allOrders))
        if not dataFrame.empty:
            dataFrame['Month'] = dataFrame['Month'].apply(lambda x: calendar.month_name[x])
       
        if dataFrame.empty:
            return '<div>No monthly data available.</div>'
 
        fig = px.bar(
            dataFrame,
            x='Month',
            y='OrderTotal',
            text_auto=True,
            color='Month',
            labels={'OrderTotal': 'Total Revenue', 'Month': 'Month'}
        )
        fig.update_layout(
            title='Monthly Sales',
            xaxis_title='Month',
            yaxis_title='Revenue',
            yaxis_tickprefix='$',
            coloraxis_showscale=False,
        )
        return plot(fig, output_type='div')

    def total_sales(self, year=None):
        allOrders = Order.objects.all()
 
        if year:
            allOrders = allOrders.filter(order__order_date__year=year)
 
        total_quantity = allOrders.aggregate(
            total_quantity=Coalesce(Sum('quantity'), 0)
        )['total_quantity']
 
        total_revenue = allOrders.aggregate(
            total_revenue=Coalesce(Sum(F('quantity') * F('product__price')), 0)
        )['total_revenue']
 
        return total_quantity, total_revenue

    def ProductCategoryRevenuesAnalysisPlot(self):
        category_orders = (
            OrderDetail.objects
            .values('product__category__category_name')  
            .annotate(
                CategoryTotalRevenue=Sum(F('product__price') * F('quantity')),  
            )
            .order_by('product__category__category_name')  
        )

        category_data = pd.DataFrame(list(category_orders))
        if category_data.empty:
            return "<div>No data available for Product Category Revenues</div>"
       
        print(category_data)

        fig = px.bar(
            category_data,
            x='product__category__category_name',
            y='CategoryTotalRevenue',
            color='product__category__category_name',
            text_auto=True,
            title='Category Sales Revenues for Product',
            labels={
                'product__category__category_name': 'Category',
                'CategoryTotalRevenue': 'Sales Revenue',
            },
        )

        fig.update_layout(
            xaxis_title="Category",
            yaxis_title="Sales Revenue from Category",
            coloraxis_showscale=False,
            title_x=0.5,
        )

        return plot(fig, output_type='div')

    def ProductCategorySalesAnalysisPlot(self):
        category_orders = (
            OrderDetail.objects
            .values('product__category__category_name')
            .annotate(CategoryTotalQuantity=Sum('quantity'))
            .order_by('product__category__category_name')
        )
 
        category_data = pd.DataFrame(list(category_orders))
        if category_data.empty:
            return "<div>No data available for Product Category Sales</div>"
       
        print(category_data)
 
        fig = px.bar(
            category_data,
            x='product__category__category_name',
            y='CategoryTotalQuantity',
            color='product__category__category_name',
            text_auto=True,
            title='Category Sales for Product',
            labels={
                'product__category__category_name': 'Category',
                'CategoryTotalQuantity': '# of Products Sold',
            },
        )
 
        fig.update_layout(
            xaxis_title="Category",
            yaxis_title="# of Products Sold in Category",
            coloraxis_showscale=False,
            title_x=0.5,
        )
       
        return plot(fig, output_type='div')
        

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
        
    def __str__(self):
        return f"Order {self.order_id} by {self.customer.customer_name}"
    
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
    
    @staticmethod
    def AnnualSales(year=None):
        """
        Calculate annual sales metrics: revenue, products sold, and orders count.
        Optional year parameter to filter data.
        """
        # Annotate data with year, month, and computed values
        annual_data = Order.objects.annotate(
            Year=ExtractYear('order_date'),
            Month=ExtractMonth('order_date'),
            Revenue=Sum(F('orderdetail__product__price') * F('orderdetail__quantity')),
            ProductsSold=Sum('orderdetail__quantity'),
        ).values('Year', 'Month').annotate(
            TotalRevenue=Sum('Revenue'),
            TotalProductsSold=Sum('ProductsSold'),
            TotalOrders=Count('order_id')
        ).order_by('Year', 'Month')

        if year:
            annual_data = annual_data.filter(Year=year)

        return pd.DataFrame(list(annual_data))

    @staticmethod
    def GenerateAnnualSalesPlot(year=None):
        """
        Generate a bar chart showing total revenue, orders, and products sold per year.
        Optional year parameter to drill down into monthly data.
        """
        # Get sales data
        sales_data = Order.AnnualSales(year=year)

        if sales_data.empty:
            return "<div>No sales data available.</div>"

        # Plot revenue by year or month
        if year:
            title = f"Monthly Sales Data for {year}"
            x_axis = 'Month'
        else:
            title = "Annual Sales Data"
            x_axis = 'Year'

        # Create bar plot
        fig = px.bar(
            sales_data,
            x=x_axis,
            y=['TotalRevenue', 'TotalProductsSold', 'TotalOrders'],
            text_auto=True,
            barmode='group',
            labels={'value': 'Metrics', 'variable': 'Metrics Type'},
            title=title
        )
        fig.update_layout(
            xaxis_title="Time Period",
            yaxis_title="Values",
            legend_title="Metrics",
            yaxis_tickprefix='$' if 'Revenue' in sales_data.columns else ''
        )

        # Generate HTML plot
        return plot(fig, output_type='div')
   

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