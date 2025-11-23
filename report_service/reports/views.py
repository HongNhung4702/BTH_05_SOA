from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import OrderReport, ProductReport
from .serializers import OrderReportSerializer, ProductReportSerializer
import requests
from django.conf import settings
from decimal import Decimal


class OrderReportViewSet(viewsets.ModelViewSet):
    queryset = OrderReport.objects.all()
    serializer_class = OrderReportSerializer

    def get_headers(self, request):
        headers = {}
        if 'Authorization' in request.headers:
            headers['Authorization'] = request.headers.get('Authorization')
        return headers

    def create(self, request, *args, **kwargs):
        """
        POST /reports/orders
        Tạo báo cáo đơn hàng từ order_service
        """
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'order_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        headers = self.get_headers(request)

        # Lấy thông tin đơn hàng từ order_service
        try:
            order_resp = requests.get(
                f"{settings.ORDER_SERVICE_BASE_URL}/orders/{order_id}/",
                headers=headers
            )
            if order_resp.status_code != 200:
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
            order_data = order_resp.json()
        except Exception as e:
            return Response({'error': f'Error connecting to order_service: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Tính toán total_revenue từ order.total_amount
        total_revenue = Decimal(str(order_data.get('total_amount', 0)))
        total_cost = Decimal('0')  # Giả sử cost = 0, có thể tính từ product cost sau

        # Lấy items từ order để tính cost và tạo product_reports
        items = order_data.get('items', [])
        product_reports_data = []

        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            unit_price = Decimal(str(item.get('unit_price', 0)))
            revenue = unit_price * quantity

            # Lấy thông tin sản phẩm để tính cost (giả sử cost = 70% của price)
            try:
                product_resp = requests.get(
                    f"{settings.PRODUCT_SERVICE_BASE_URL}/products/{product_id}/",
                    headers=headers
                )
                if product_resp.status_code == 200:
                    product_data = product_resp.json()
                    # Giả sử cost = 70% của price (có thể thay đổi logic)
                    product_price = Decimal(str(product_data.get('price', 0)))
                    cost_per_unit = product_price * Decimal('0.7')
                else:
                    cost_per_unit = unit_price * Decimal('0.7')
            except:
                cost_per_unit = unit_price * Decimal('0.7')

            cost = cost_per_unit * quantity
            total_cost += cost

            product_reports_data.append({
                'product_id': product_id,
                'total_sold': quantity,
                'revenue': revenue,
                'cost': cost,
            })

        # Tạo OrderReport
        order_report = OrderReport.objects.create(
            order_id=order_id,
            total_revenue=total_revenue,
            total_cost=total_cost,
        )

        # Tạo ProductReport cho từng item
        for pr_data in product_reports_data:
            ProductReport.objects.create(
                order_report=order_report,
                product_id=pr_data['product_id'],
                total_sold=pr_data['total_sold'],
                revenue=pr_data['revenue'],
                cost=pr_data['cost'],
            )

        serializer = self.get_serializer(order_report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductReportViewSet(viewsets.ModelViewSet):
    queryset = ProductReport.objects.all()
    serializer_class = ProductReportSerializer

    def get_headers(self, request):
        headers = {}
        if 'Authorization' in request.headers:
            headers['Authorization'] = request.headers.get('Authorization')
        return headers

    def create(self, request, *args, **kwargs):
        """
        POST /reports/products
        Tạo báo cáo sản phẩm từ product_service và order_service
        Tạo ProductReport cho sản phẩm trong tất cả các orders có chứa sản phẩm này
        """
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        headers = self.get_headers(request)

        # Lấy thông tin sản phẩm từ product_service
        try:
            product_resp = requests.get(
                f"{settings.PRODUCT_SERVICE_BASE_URL}/products/{product_id}/",
                headers=headers
            )
            if product_resp.status_code != 200:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            product_data = product_resp.json()
        except Exception as e:
            return Response({'error': f'Error connecting to product_service: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Lấy tất cả orders từ order_service
        try:
            orders_resp = requests.get(
                f"{settings.ORDER_SERVICE_BASE_URL}/orders/",
                headers=headers
            )
            if orders_resp.status_code != 200:
                return Response({'error': 'Error fetching orders'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            orders_data = orders_resp.json()
        except Exception as e:
            return Response({'error': f'Error connecting to order_service: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        product_price = Decimal(str(product_data.get('price', 0)))
        cost_per_unit = product_price * Decimal('0.7')  # Giả sử cost = 70% của price
        created_reports = []

        # Duyệt qua tất cả orders và tạo ProductReport cho mỗi order có chứa sản phẩm này
        for order in orders_data:
            items = order.get('items', [])
            for item in items:
                if item.get('product_id') == product_id:
                    order_id = order.get('id')
                    quantity = item.get('quantity', 0)
                    unit_price = Decimal(str(item.get('unit_price', 0)))
                    revenue = unit_price * quantity
                    cost = cost_per_unit * quantity

                    # Tìm hoặc tạo OrderReport cho order này
                    order_report, _ = OrderReport.objects.get_or_create(
                        order_id=order_id,
                        defaults={
                            'total_revenue': Decimal(str(order.get('total_amount', 0))),
                            'total_cost': Decimal('0'),
                        }
                    )

                    # Kiểm tra xem ProductReport đã tồn tại chưa (tránh duplicate)
                    product_report, created = ProductReport.objects.get_or_create(
                        order_report=order_report,
                        product_id=product_id,
                        defaults={
                            'total_sold': quantity,
                            'revenue': revenue,
                            'cost': cost,
                        }
                    )

                    if not created:
                        # Cập nhật nếu đã tồn tại
                        product_report.total_sold += quantity
                        product_report.revenue += revenue
                        product_report.cost += cost
                        product_report.save()

                    created_reports.append(product_report.id)
                    break  # Mỗi order chỉ có 1 item của product này

        if created_reports:
            # Trả về ProductReport đầu tiên hoặc danh sách
            product_report = ProductReport.objects.get(id=created_reports[0])
            serializer = self.get_serializer(product_report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'No orders found for this product'}, status=status.HTTP_404_NOT_FOUND)

