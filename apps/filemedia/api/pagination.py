from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """
    Custom pagination dengan format:
    {
        "totalCount": int,
        "offset": int,
        "limit": int,
        "items": []
    }
    """
    page_size = 50  # Default limit
    page_size_query_param = 'limit'
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response({
            'totalCount': self.page.paginator.count,
            'offset': (self.page.number - 1) * self.page_size,
            'limit': self.page_size,
            'items': data
        })