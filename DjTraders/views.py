from django.shortcuts import get_object_or_404, render, redirect
import re

from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Customer, Product, Category, Order, OrderDetail
from .forms import CustomerForm, ProductForm
import plotly.express as px
import pandas as pd
from plotly.offline import plot
from django.http import JsonResponse
from django.db.models import Count, F, Sum, ExpressionWrapper, DecimalField
from django.db.models.functions import ExtractYear, ExtractMonth, Cast, Coalesce

def DjTradersHome(request):
    return render(
        request,
        'DjTraders/index.html',
        {}
	)

# Paginator documentation and working example is at:
# https://docs.djangoproject.com/en/5.1/topics/pagination/

class DjTradersCustomersView(ListView):
    model = Customer
    template_name = 'DjTraders/customers.html'
    context_object_name = 'customers'
    paginate_by=15
    
    def all_countries(self):
        Countries = self.model.objects.all().order_by('country').distinct()
        return Countries.values('country')
    
    def all_cities(self):
        Cities = self.model.objects.all().order_by('city').distinct()
        return Cities.values('city')
    
    def get_queryset(self):
        '''
            A ListView class returns its data in the form of a query set object.
            The query set is a list of object of the model type.  
            In this case, the queryset is a list of customers.
        
            The get_queryset(self) function provides access to the query that generates the list of objects to return.add()
            The default is all the data mapped to the table.
            
            The function provides a way to customise the "query" so that you can change the data that goes to the template page.
            
            This technique is called "Overriding" and is used to customize functionality.
            Essentially, you are "overriding" or customizing the default get_queryset() method, 
            which gives you all the objects, so that you get a custom set of objects from the query.
            
            
            See: https://docs.djangoproject.com/en/5.1/topics/class-based-views/generic-display/ for more on 
            how to customize the data from shown in a ListView.
            
        '''
        
        customerQuery = self.request.GET.get('srchCustomerName', '')
        countryQuery = self.request.GET.get('srchCountry', '')
        contactQuery = self.request.GET.get('srchContactName', '')
        cityQuery = self.request.GET.get('srchCity','')
        active_filter = self.request.GET.get('active', None)
        
        customers = self.model.objects.all()
        
        if active_filter is not None:
            is_active = active_filter.lower() == 'true'
            customers = customers.filter(is_active=is_active)
            
        if customerQuery:
            customers = self.model.objects.filter(
                customer_name__icontains=customerQuery
            )
        elif countryQuery:
            customers = self.model.objects.filter(
                country__icontains=countryQuery
            )
        elif contactQuery:
            customers = self.model.objects.filter(
                contact_name__icontains=contactQuery
            )
        elif cityQuery:
            customers = self.model.objects.filter(
                city__icontains=cityQuery
            )
        else:
            customers = self.model.objects.all()
            
        return customers.order_by("customer_name")
    
    def get_context_data(self, **kwargs):
        '''
            The "get_context_data() method determines what data goes back to the template as the context object.
            
            By default, its bahvior is to return the "context_object" that you specify in the class 
            
            Like the get_query set method,you can override this method to give you specific information in the context.
            
            A context is dictionary of objects - <key, value> pairs.
            It has the context_object_name as the only item in the dictionary.
            But you can add variables to the context dictionary to send them back to the form.
            
            For example, here, we are using this method to override the default context
            by adding the add the key "CustomerName" with the value of what the user typed in as the search item.
            
            searchTermForCustomerName is the name we give to what the user types in to the CustomerName field.
            We can extract that from the request object.
            and then add it to the context [the default context_data] dictionary.
            
            After this, the context will have 2 things:
                an object called customers (the list of customers from the queryset()), and 
                a string object with key = "CustomerName", and 
                value = the searchTermForCustomerName
            
            Now, the context contains both of these and they are available to the template.
            
        '''
        
        #1. Get the default context (list of objects)
        context = super().get_context_data(**kwargs)
        
        #2. Get the value for the input field "CustomerName"
        searchTermForCustomerName = self.request.GET.get('srchCustomerName', '')
        searchTermForCountry = self.request.GET.get('srchCountry', '')
        searchTermForContact = self.request.GET.get('srchContactName', '')
        searchTermForCity = self.request.GET.get('srchCity', '')
        
        #3 Add variables back to the context with the same key as the field name
        context["srchCustomerName"] = searchTermForCustomerName
        context["srchCountry"] = searchTermForCountry
        context["srchContactName"] = searchTermForContact
        context["srchCity"] = searchTermForCity
        
        context['Countries'] = self.all_countries()
        context['Cities'] = self.all_cities
        context['active_filter'] = self.request.GET.get('active', None)
        #4. Give back the modified context dictionary.
        return context

class CustomerOrders(ListView):
    model = Customer
    template_name = 'DjTraders/customer_orders.html'
    context_object_name = 'customer_orders'
    
    def CustomerNumOrdersPlot(self):
        CustomersWithOrders = Customer.objects.all().annotate(
            nOrders = Count('order')
        ).order_by('nOrders').reverse()
        
        TopTenCustomersWithOrders = CustomersWithOrders[:10]
        nCustomers =  CustomersWithOrders[:10].count()
        
        customer_names = [0 for _ in range(nCustomers)]
        NumberOfOrdersPlaced = [0 for _ in range(nCustomers)]
        index = 0
        
        for cOrder in TopTenCustomersWithOrders:
            customer_names[index] = cOrder.customer_name
            NumberOfOrdersPlaced[index] = cOrder.nOrders
            index = index+1
        
       
        fig = px.bar(
          x= customer_names,
          y= NumberOfOrdersPlaced,
          color_continuous_scale=px.colors.sequential.Jet,
          color=NumberOfOrdersPlaced,
          labels={'color':'Number Of Orders'},
          height=600,
          width=1000,
          text_auto=True,
        )
        
        fig.update_layout(
          title = 'Top 10 Customers by Number of Orders Placed',
          xaxis_title="Customer",
          yaxis_title="Number Of Orders",
        )
        
        # More on Plotly colors is here: https://plotly.com/python/builtin-colorscales/
        
              
        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')
        
        #return the html to place in the context and display
        return plot_html

    def NCustomerOrders(self):
        CustomersWithOrders = Customer.objects.all().annotate(
            nOrders = Count('order')
        ).order_by('nOrders').reverse()
        
        TopTenCustomersWithOrders = CustomersWithOrders[:10].values('customer_name', 'nOrders')
        
        nCustomers =  CustomersWithOrders[:10].count()

        dFrame = pd.DataFrame(
            list(TopTenCustomersWithOrders),
            #columns=["Customer Name", "Number Of Orders"]
        )
        print(dFrame)
        
        fig = px.bar(
            dFrame,
            x= 'customer_name',
            y= 'nOrders',
            color_continuous_scale=px.colors.sequential.Jet,
            color="nOrders",
            labels={'color':'nOrders'},
            height=600,
            width=1000,
            text_auto=True,
        )
        
        fig.update_layout(
          title = 'Top 10 Customers by Number of Orders Placed',
          xaxis_title="Customer",
          yaxis_title="Number Of Orders",
        )
        
        # More on Plotly colors is here: https://plotly.com/python/builtin-colorscales/
        
              
        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')
        
        #return the html to place in the context and display
        return plot_html

    def get_queryset(self):
        return super().get_queryset()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CustomerOrderPlot"] = self.CustomerNumOrdersPlot()
        context["NCustomerOrdersPlot"] = self.NCustomerOrders()
        return context

class DjTradersProductsView(ListView):
    model = Product
    template_name = 'DjTraders/products.html'
    context_object_name = 'products'
    paginate_by=15

    def all_categories(self):
        Categories = Category.objects.filter(product__isnull=False).distinct()
        return Categories.values_list('category_name', flat=True)
    
    def get_queryset(self):
        productQuery = self.request.GET.get('ProductName', '')
        categoryQuery = self.request.GET.get('srchCategory', '')
        priceQuery = self.request.GET.get('ProductPrice', '')
        
        if productQuery:
            products = self.model.objects.filter(product_name__icontains = productQuery)
        elif categoryQuery:
            products = self.model.objects.filter(category__category_name__icontains = categoryQuery)
        # elif priceQuery:
        #     try:
        #         price = float(priceQuery)
        #         price_operator = self.request.GET.get('PriceOperator', '')
        #         if price_operator == 'gte':
        #             products = self.model.objects.filter(price__gte=price)
        #         elif price_operator == 'lte':
        #             products = self.model.objects.filter(price__lte=price)
        #         else:
        #             products = self.model.objects.filter(price=price)
        #     except ValueError:
        #         pass
        elif priceQuery:
            price_match = re.match(r'([<>]=?|=)?\s*(\d+(\.\d+)?)', priceQuery)
            if price_match:
                operator, price_value, _ = price_match.groups()
                try:
                    price = float(price_value)
                    # Apply the appropriate filter based on the operator
                    if operator == '>':
                        products = self.model.objects.filter(price__gt=price)
                    elif operator == '>=':
                        products = self.model.objects.filter(price__gte=price)
                    elif operator == '<':
                        products = self.model.objects.filter(price__lt=price)
                    elif operator == '<=':
                        products = self.model.objects.filter(price__lte=price)
                    elif operator == '=' or operator is None:
                        products = self.model.objects.filter(price=price)
                except ValueError:
                    pass  # Ignore if price_value is not a valid number

        else:
            products = self.model.objects.all()
        
        return products.order_by("product_name")

    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        
        srchProductName = self.request.GET.get('ProductName', '')
        context["ProductName"] = srchProductName
        searchTermForCategory = self.request.GET.get('srchCategory', '')
        context["srchCategory"] = searchTermForCategory
        srchProductPrice = self.request.GET.get('ProductPrice', '')
        context["ProductPrice"] = srchProductPrice
        context['Categories'] = self.all_categories()
        
        return context
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('DjTraders.Products')
        else:
            print(form.errors)
    else:
        form = ProductForm()
    return render(request, 'product_form2.html', {'form': form})

def GetProductDetails(request):
    string_id = request.GET.get('product_id')
    id=int(string_id)          
    eachProduct = Product.objects.get(product_id=id)
    return render(request, 'DjTraders/ProductHome.html',
                  {'product': eachProduct})

def ProductAnnualMonthlySales(request, pk=None):
    selYear = request.GET.get('selOrderYear', "")
    eachProduct = get_object_or_404(Product, pk=pk)
    OrdersYears = Order.AllOrderYears()
    yearly_plot = eachProduct.AnnualProductOrders()
    monthly_plot = eachProduct.MonthlyProductOrders(year=selYear if selYear else None)
    return render(
        request,
        'DjTraders/_ProductAnnualSales.html',
        {
            'product': eachProduct,
            'selOrderYear': selYear,
            'OrderYears': OrdersYears,
            'AnnualySalePlot': yearly_plot,
            'MonthlySalePlot': monthly_plot,
        }
    )

def plot_top_bottom_product_analysis(request, selOrderYear=None):
    OrdersYears = Order.AllOrderYears()
    selYear = request.GET.get('selOrderYear', selOrderYear)
    orders_with_revenue = OrderDetail.objects.annotate(
        revenue=F('product__price') * F('quantity'),
        year=ExtractYear('order__order_date')
    )
    if selYear:
        orders_with_revenue = orders_with_revenue.filter(year=selYear)
    revenue_per_year = orders_with_revenue.values(
        'product__product_id', 'product__product_name', 'year'
    ).annotate(
        total_revenue=Sum('revenue')
    ).order_by('-total_revenue')
    top_10 = list(revenue_per_year[:10])  # Top 10
    bottom_10 = list(revenue_per_year[::-1][:10])  # Bottom 10
    def generate_bar_charts(data, title, color_scale):
        df = pd.DataFrame({
            'Product': [item['product__product_name'] for item in data],
            'Total Revenue': [item['total_revenue'] for item in data]
        })
        fig = px.bar(
            df, x='Product', y='Total Revenue', title=title,
            labels={'Total Revenue': 'Revenue ($)', 'Product': 'Product Name'},
            color='Total Revenue', color_continuous_scale=color_scale
        )
        return plot(fig, output_type='div')
    top_10 = generate_bar_charts(top_10, f'Top 10 Products by Revenue in {selYear or "All Years"}', 'Blues')
    bottom_10 = generate_bar_charts(bottom_10, f'Bottom 10 Products by Revenue in {selYear or "All Years"}', 'Reds')
    context = {
        'top_10_plot': top_10,
        'bottom_10_plot': bottom_10,
        'selOrderYear': selYear,
        'OrderYears': OrdersYears,
    }
    return render(request, 'DjTraders/_ProductTopBottomAnalysis.html', context)

def product_sales_analysis(request, pk):
    eachProduct = Product.objects.get(pk=pk)
   
    OrdersYears = Order.AllOrderYears()  
    selYear = request.GET.get('selOrderYear')
 
    total_sales_data = []
    if selYear:
        orders = Order.objects.filter(orderdetail__product=eachProduct, order_date__year=selYear)
    else:
        orders = Order.objects.filter(orderdetail__product=eachProduct)
 
    yearly_data = orders.annotate(
        year=ExtractYear('order_date')
        ).values('year').annotate(
        total_orders=Count('order_id'),
        total_products_sold=Sum('orderdetail__quantity'),
        total_revenue=Sum(
            ExpressionWrapper(
                F('orderdetail__quantity') * F('orderdetail__product__price'),
                output_field=DecimalField()
            )
        )
    ).order_by('year')
 
    for year_data in yearly_data:
        year = year_data['year']
        total_orders = year_data['total_orders']
        total_products_sold = year_data['total_products_sold']
        total_revenue = year_data['total_revenue']
 
        monthly_sales_data = []
       
    # Monthly sales data
        monthly_data = orders.filter(order_date__year=year).annotate(
        month=ExtractMonth('order_date')
        ).values('month').annotate(
        total_orders_month=Count('order_id'),
        total_products_sold_month=Sum('orderdetail__quantity'),
        total_revenue_month=Sum(
            ExpressionWrapper(
                F('orderdetail__quantity') * F('orderdetail__product__price'),
                output_field=DecimalField()
            )
        )
        ).order_by('month')
 
        avg_sales_data = {
            'avg_orders': total_orders / 12,
            'avg_products_sold': total_products_sold / 12,
            'avg_revenue': total_revenue / 12,
        }
 
        for month_data in monthly_data:
            month = month_data['month']
            total_orders_month = month_data['total_orders_month']
            total_products_sold_month = month_data['total_products_sold_month']
            total_revenue_month = month_data['total_revenue_month']
 
            # Compare monthly sales with average
            comparison = {
                'orders_vs_avg': total_orders_month - avg_sales_data['avg_orders'],
                'products_sold_vs_avg': total_products_sold_month - avg_sales_data['avg_products_sold'],
                'revenue_vs_avg': total_revenue_month - avg_sales_data['avg_revenue'],
            }
 
            monthly_sales_data.append({
                'month': month,
                'total_orders_month': total_orders_month,
                'total_products_sold_month': total_products_sold_month,
                'total_revenue_month': total_revenue_month,
                'comparison': comparison,
            })
 
        total_sales_data.append({
            'year': year,
            'total_orders': total_orders,
            'total_products_sold': total_products_sold,
            'total_revenue': total_revenue,
            'monthly_sales': monthly_sales_data,
            'avg_sales': avg_sales_data
        })
 
    # Prepare data for Plotly charts
    df_annual = pd.DataFrame(total_sales_data)
    df_annual['year'] = df_annual['year'].astype(int)
    df_annual['total_orders'] = pd.to_numeric(df_annual['total_orders'], errors='coerce')
    df_annual['total_revenue'] = pd.to_numeric(df_annual['total_revenue'], errors='coerce')
    df_annual['total_products_sold'] = pd.to_numeric(df_annual['total_products_sold'], errors='coerce')
   
    fig_annual = px.bar(df_annual, x='year', y=['total_orders', 'total_revenue', 'total_products_sold'],
                    title=f"Annual Sales for {eachProduct.product_name}")
    annual_chart_html = fig_annual.to_html(full_html=False)
 
 
    # Prepare monthly sales comparison chart
    df_monthly = pd.DataFrame([{
        'Month': month_data['month'],
        'Orders': month_data['total_orders_month'],
        'Revenue': month_data['total_revenue_month'],
        'Comparison with Avg': month_data['comparison']['revenue_vs_avg']
    } for year_data in total_sales_data for month_data in year_data['monthly_sales']])
   
    df_monthly['Month'] = df_monthly['Month'].astype(int)
    df_monthly['Orders'] = pd.to_numeric(df_monthly['Orders'], errors='coerce')
    df_monthly['Revenue'] = pd.to_numeric(df_monthly['Revenue'], errors='coerce')
    df_monthly['Comparison with Avg'] = pd.to_numeric(df_monthly['Comparison with Avg'], errors='coerce')
 
    fig_monthly = px.line(df_monthly, x='Month', y='Revenue', title=f"Monthly Sales Comparison for {eachProduct.product_name}")
    monthly_chart_html = fig_monthly.to_html(full_html=False)
 
 
    context = {
        'product': eachProduct,
        'ProductAnnualySalesPlot': annual_chart_html,
        'ProductMonthlySalesPlot': monthly_chart_html,
        'OrderYears': Order.objects.all().values('order_date').distinct(),
        'selOrderYear': selYear,
        'OrdersYears': OrdersYears,
    }
 
    return render(request, 'DjTraders/_ProductSalesAnalysis.html', context)

def CategoryAnalysis(request, pk):
    eachProduct = get_object_or_404(Product, pk=pk)
 
    category_sales = eachProduct.ProductCategorySalesAnalysisPlot()
    category_revenue = eachProduct.ProductCategoryRevenuesAnalysisPlot()
 
    return render(
        request,
        'DjTraders/_CategorySalesAnalysis.html',
        {
            'product': eachProduct,
            'CategoryRevenuesPlot': category_revenue,
            'CategoryPlot': category_sales,
        }
    )

class DjTradersProductDetailView(DetailView):
    model=Product
    template_name=  'DjTraders/productDetail.html'
    context_object_name='product'
    
def ProductAnnualSales(request):
    year = request.GET.get('year')  # Optional year filter
    plot_html = Order.GenerateAnnualSalesPlot(year=year)
    return render(request, 'DjTraders/Product_Annual_Sales.html', {'plot_html': plot_html})
        
    
# v2.1 
# Add the view class with the model, the form class and route for a successful submission.  
class DjTradersCustomerCreate(CreateView):
    model = Customer
    form_class= CustomerForm
    template_name='DjTraders/customer_form2.html'
    success_url='/DjTraders/Customers'

class DjTradersCustomerEdit(UpdateView):
    model=Customer
    form_class = CustomerForm
    success_url = '/DjTraders/Customers'

#Note - you do not need this - unless you are doing extra credit.
class DjTradersCustomerDelete(DeleteView):
    model=Customer
    success_url = '/DjTraders/Customers'
    template_name='DjTraders/customer_delete.html'

class DjTradersProductCreate(CreateView):
    model = Product
    form_class= ProductForm
    template_name='DjTraders/product_form2.html'
    success_url='/DjTraders/Products'

class DjTradersProductEdit(UpdateView):
    model=Product
    form_class = ProductForm
    success_url = '/DjTraders/Products'

#Note - you do not need this - unless you are doing extra credit.
class DjTradersProductDelete(DeleteView):
    model=Product
    success_url = '/DjTraders/Products'
    template_name='DjTraders/product_delete.html'
    
class DjTradersProductPurchaseView(DetailView):
    model = Product
    template_name = 'DjTraders/productPurchaseDetail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        purchase_summary = product.customer_purchase_summary()
        context['purchase_summary'] = purchase_summary
        return context
 
class ProductAnalysisPageView(DetailView):
    model=Product
    template_name='DjTraders/_ProductAnnualSales.html'
    context_object_name='product'
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        eachProduct = self.get_object()
        context['ProductsSalePlot'] = eachProduct.AnnualProductOrders()
        return context

class CustomersListJSON(View):
    
    def get(self, request):
        
        allCustomerData = Customer.objects.all().annotate(
            nOrders = Count('order')
        ).order_by('nOrders').reverse()
            

        x = allCustomerData.values('customer_name', 'country', 'nOrders')[:10]
        
        
        CustomerData = list(x)#serialize("json", allCustomerData)
        
        # print(CustomerData)        
        return JsonResponse(CustomerData, safe=False)


# region Customer Detail View with a OrdersPlaced plot
# v3.0 Added
class DjTradersCustomerDetailView(DetailView):
    model=Customer
    template_name=  'DjTraders/customerDetail.html'
    context_object_name='customer'

    # v3.0 Added
    def OrdersPlacedPlot(self):
        '''
        
        The OrdersPlacedPlot function uses the "current" customer object using the get_object() function
        
        The customer is queried for the customer's orders and extracting the number of orders, 
        as well as order id, order_date and the total for each order.        
        These are added to individual arrays, for each order.
        
        plotly express is used to create a bar chart of order totals arranged by order date.
        The plotly offline library is plot the chart in a "div" and make it available to the DetailView for the customer
        
        '''

        # for more on the "get_object()" function, see: https://docs.djangoproject.com/en/5.1/ref/class-based-views/mixins-single-object/
        
        #get the specific customer object 
        theCustomer = self.get_object()
        
        #CustomerOrders() member function returns a queryset of all orders placed by theCustomer.
        customerOrders = theCustomer.CustomerOrders()

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
            height=500,
            text_auto=True,
        )
        
        figure_title = 'Order Totals by Date <br><sup> for '  + theCustomer.customer_name + '</sup>'
        
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
  
    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        
        # Add the plot to the context to make it available to the template.
        context['OrdersPlot'] = self.OrdersPlacedPlot()
        return context
    
def OrdersPlaced(request):
    str_id = request.GET.get('customer_id')
    id=int(str_id)
    customer = Customer.objects.get(customer_id=id)
    return render(request, 'DjTraders/_OrdersPlaced.html', 
                {'customer': customer})
    
# v3.2 Orders By Date Plot 
def OrdersByDate(request, selOrderYear=""):
    # extract the customer_id and selected Order Year from the request.
    # the customer ID is converted to integer from the default string for I/O
    str_customer_id = request.GET.get('customer_id')
    customer_id=int(str_customer_id)
    selOrderYear = request.GET.get('selOrderYear')

    #use the customer_id to get the right customer.
    customer = Customer.objects.get(customer_id=customer_id)

    # To fill the dropdown, ask the Order Model for all distinct Years an Order was placed BY ANY customer.
    OrderYears = Order.AllOrderYears()

    TheAnnualOrders = customer.AnnualOrders()
    ordersByDatePlot = customer.OrdersPlacedPlot(selOrderYear)

    return render(
        request, 
        'DjTraders/_OrdersByDate.html', 
        {
            'customer': customer,
            'selOrderYear': selOrderYear,
            'OrderYears': OrderYears,
            'OrdersByDatePlot': ordersByDatePlot,
            'AnnualOrdersPlot': TheAnnualOrders,
        }
    )
    
# v3.2 Orders By Product Plot 
def OrdersByProduct(request):
    # extract the customer_id and selected Order Year from the request.
    # the customer ID is converted to integer from the default string for I/O
    str_customer_id = request.GET.get('customer_id')
    customer_id=int(str_customer_id)

    #use the customer_id to get the right customer.
    customer = Customer.objects.get(customer_id=customer_id)

    TheProductsRevenuePlot = customer.ProductReveues()
    TheProductsPlot = customer.ProductsSoldPlot()

    return render(
        request, 
        'DjTraders/_OrdersByProduct.html', 
        {
            'customer': customer,
            'ProductsPlot': TheProductsPlot,
            'ProductsRevenuePlot': TheProductsRevenuePlot,
        }
    )

# v3.2 Orders By Category Plot 
def OrdersByCategory(request):
    # extract the customer_id and selected Order Year from the request.
    # the customer ID is converted to integer from the default string for I/O
    str_customer_id = request.GET.get('customer_id')
    customer_id=int(str_customer_id)

    #use the customer_id to get the right customer.
    customer = Customer.objects.get(customer_id=customer_id)

    TheCategoryPlot = customer.ProductCategorySalesPlot()
    TheCategoryRevenusPlot = customer.ProductCategoryRevenusPlot()

    return render(
        request, 
        'DjTraders/_OrdersByCategory.html', 
        {
            'customer': customer,
            'CategoryRevenuesPlot': TheCategoryRevenusPlot,
            'CategoryPlot': TheCategoryPlot,
        }
    )
