import django_filters as filters

from .models import Card


class CardFilter(filters.FilterSet):
    grade = filters.BaseInFilter(field_name="grade")
    grade_min = filters.NumberFilter(field_name="grade", lookup_expr="gte")
    grade_max = filters.NumberFilter(field_name="grade", lookup_expr="lte")
    nation = filters.CharFilter(field_name="nation")
    clan = filters.CharFilter(field_name="clan", lookup_expr="icontains")
    card_type = filters.CharFilter(field_name="card_type")
    trigger = filters.CharFilter(field_name="trigger")
    is_trigger = filters.BooleanFilter(method="filter_is_trigger")
    format_code = filters.CharFilter(method="filter_format")
    set_code = filters.CharFilter(field_name="printings__card_set__code", distinct=True)
    rarity = filters.CharFilter(field_name="printings__rarity", lookup_expr="iexact", distinct=True)
    ability_contains = filters.CharFilter(field_name="ability_text", lookup_expr="icontains")

    class Meta:
        model = Card
        fields = ["grade", "nation", "clan", "card_type", "trigger"]

    def filter_is_trigger(self, queryset, name, value):
        if value:
            return queryset.exclude(trigger="")
        return queryset.filter(trigger="")

    def filter_format(self, queryset, name, value):
        return queryset.filter(
            format_legalities__format_code=value,
            format_legalities__legality__in=["legal", "restricted"],
        ).distinct()
