from django.db import models


class OrderReport(models.Model):
    order_id = models.IntegerField()
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OrderReport #{self.id} - Order {self.order_id}"

    def save(self, *args, **kwargs):
        # Auto calculate profit
        self.total_profit = self.total_revenue - self.total_cost
        super().save(*args, **kwargs)


class ProductReport(models.Model):
    order_report = models.ForeignKey(OrderReport, related_name='product_reports', on_delete=models.CASCADE)
    product_id = models.IntegerField()
    total_sold = models.IntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ProductReport #{self.id} - Product {self.product_id}"

    def save(self, *args, **kwargs):
        # Auto calculate profit
        self.profit = self.revenue - self.cost
        super().save(*args, **kwargs)

