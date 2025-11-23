from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderReportViewSet, ProductReportViewSet

router = DefaultRouter()
router.register(r'reports/orders', OrderReportViewSet, basename='order-report')
router.register(r'reports/products', ProductReportViewSet, basename='product-report')

urlpatterns = [
    path('', include(router.urls)),
]

