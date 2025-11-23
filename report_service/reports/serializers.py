from rest_framework import serializers
from .models import OrderReport, ProductReport


class ProductReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReport
        fields = ['id', 'order_report', 'product_id', 'total_sold', 'revenue', 'cost', 'profit', 'created_at', 'updated_at']
        read_only_fields = ['profit', 'created_at', 'updated_at']


class OrderReportSerializer(serializers.ModelSerializer):
    product_reports = ProductReportSerializer(many=True, read_only=True)

    class Meta:
        model = OrderReport
        fields = ['id', 'order_id', 'total_revenue', 'total_cost', 'total_profit', 'created_at', 'updated_at', 'product_reports']
        read_only_fields = ['total_profit', 'created_at', 'updated_at']

