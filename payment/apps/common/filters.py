import django_filters
from django.db import models
from django_filters import rest_framework as filters


class BaseFilterSet(filters.FilterSet):
    """
    Base filter set with common filtering options.
    """
    created_at_gte = filters.DateTimeFilter(field_name="created_at", lookup_expr='gte', label="Created after")
    created_at_lte = filters.DateTimeFilter(field_name="created_at", lookup_expr='lte', label="Created before")
    updated_at_gte = filters.DateTimeFilter(field_name="updated_at", lookup_expr='gte', label="Updated after")
    updated_at_lte = filters.DateTimeFilter(field_name="updated_at", lookup_expr='lte', label="Updated before")
    
    # Search functionality
    search = filters.CharFilter(method='filter_search', label="Search")
    
    class Meta:
        abstract = True
    
    def filter_search(self, queryset, name, value):
        """
        Override this method in child classes to implement custom search logic.
        """
        return queryset


class CommonSettingsFilterSet(BaseFilterSet):
    """
    Filter set for CommonSettings model.
    """
    key = filters.CharFilter(field_name="key", lookup_expr='icontains', label="Key contains")
    value = filters.CharFilter(field_name="value", lookup_expr='icontains', label="Value contains")
    is_public = filters.BooleanFilter(field_name="is_public", label="Is public")
    is_deleted = filters.BooleanFilter(field_name="is_deleted", label="Is deleted")
    
    class Meta:
        model = None  # Will be set when imported
        fields = ['key', 'value', 'is_public', 'is_deleted']
    
    def filter_search(self, queryset, name, value):
        """
        Search in key, value, and description fields.
        """
        return queryset.filter(
            models.Q(key__icontains=value) |
            models.Q(value__icontains=value) |
            models.Q(description__icontains=value)
        )


class DateRangeFilter(filters.FilterSet):
    """
    Generic date range filter that can be used with any model.
    """
    date_from = filters.DateFilter(method='filter_date_from', label="Date from")
    date_to = filters.DateFilter(method='filter_date_to', label="Date to")
    
    def filter_date_from(self, queryset, name, value):
        """Filter records from the specified date."""
        return queryset.filter(created_at__date__gte=value)
    
    def filter_date_to(self, queryset, name, value):
        """Filter records up to the specified date."""
        return queryset.filter(created_at__date__lte=value)


class StatusFilter(filters.FilterSet):
    """
    Generic status filter for models with status fields.
    """
    status = filters.CharFilter(field_name="status", lookup_expr='exact', label="Status")
    status_in = filters.CharFilter(method='filter_status_in', label="Status in (comma separated)")
    
    def filter_status_in(self, queryset, name, value):
        """Filter by multiple status values."""
        if value:
            status_list = [status.strip() for status in value.split(',')]
            return queryset.filter(status__in=status_list)
        return queryset


# Utility functions for common filtering patterns
def get_boolean_filter_choices():
    """Get choices for boolean filters."""
    return [
        ('true', 'Yes'),
        ('false', 'No'),
    ]


def get_ordering_filter_fields():
    """Get common ordering fields."""
    return ['created_at', '-created_at', 'updated_at', '-updated_at', 'id', '-id']
