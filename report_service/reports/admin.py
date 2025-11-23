from django.contrib import admin
from .models import OrderReport, ProductReport


@admin.register(OrderReport)
class OrderReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_id', 'total_revenue', 'total_cost', 'total_profit', 'created_at']
    list_filter = ['created_at']
    search_fields = ['order_id']


@admin.register(ProductReport)
class ProductReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_report', 'product_id', 'total_sold', 'revenue', 'cost', 'profit', 'created_at']
    list_filter = ['created_at', 'product_id']
    search_fields = ['product_id']

