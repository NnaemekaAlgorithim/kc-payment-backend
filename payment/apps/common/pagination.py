from rest_framework.pagination import PageNumberPagination
from django.http import JsonResponse


class GenericPagination(PageNumberPagination):
    page_size = 10  # Default number of items per page
    page_size_query_param = 'page_size'  # Query parameter to control page size
    max_page_size = 100  # Maximum allowed page size to prevent large responses

    def get_paginated_response(self, data):
        """
        Returns a paginated response in the format: {"message": str, "data": dict}.
        
        Args:
            data: The serialized data for the current page.
        
        Returns:
            JsonResponse: A response containing pagination metadata and results.
        """
        # Use a default or provided message for the paginated response
        message = getattr(self, 'custom_message', "Data retrieved successfully.")
        return JsonResponse({
            "message": message,
            "data": {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data
            }
        }, status=200)
