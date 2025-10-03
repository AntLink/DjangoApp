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


class CustomResultsSetPagination(PageNumberPagination):
    """
    Kelas pagination kustom untuk mencocokan format respons API CKBox.
    """
    # Nilai default, bisa dioverride dengan query parameter 'limit'
    page_size = 50
    page_size_query_param = 'limit'
    max_page_size = 500

    def get_paginated_response(self, data):
        """
        Menimpa metode ini untuk mengubah nama kunci dalam respons.
        """
        return Response({
            'totalCount': self.page.paginator.count,
            'offset': (self.page.start_index() - 1) if self.page.start_index() else 0,
            'limit': self.get_page_size(self.request),
            'items': data
        })