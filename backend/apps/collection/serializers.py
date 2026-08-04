from rest_framework import serializers

from apps.cards.models import Card
from apps.cards.serializers import CardListSerializer, CardPrintingSerializer

from .models import CollectionPrinting, TradeItem, UserCollectionItem, WishlistItem


class CollectionPrintingSerializer(serializers.ModelSerializer):
    printing = CardPrintingSerializer(read_only=True)

    class Meta:
        model = CollectionPrinting
        fields = ["uuid", "printing", "quantity", "language", "condition", "finish",
                  "note", "price_paid"]


class CollectionItemSerializer(serializers.ModelSerializer):
    card = CardListSerializer(read_only=True)
    printings = CollectionPrintingSerializer(many=True, read_only=True)
    owned_quantity = serializers.SerializerMethodField()

    class Meta:
        model = UserCollectionItem
        fields = ["uuid", "card", "note", "owned_quantity", "printings"]

    def get_owned_quantity(self, obj) -> int:
        return sum(p.quantity for p in obj.printings.all())


class SetOwnedSerializer(serializers.Serializer):
    printing = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=0, max_value=999)
    condition = serializers.CharField(required=False, default="near_mint")
    language = serializers.CharField(required=False, default="en")
    finish = serializers.CharField(required=False, allow_blank=True, default="")
    price_paid = serializers.DecimalField(max_digits=10, decimal_places=2,
                                          required=False, allow_null=True)


class WishlistSerializer(serializers.ModelSerializer):
    card = CardListSerializer(read_only=True)
    card_uuid = serializers.UUIDField(write_only=True)

    class Meta:
        model = WishlistItem
        fields = ["uuid", "card", "card_uuid", "priority", "note", "created_at"]

    def create(self, validated_data):
        card = Card.objects.get(uuid=validated_data.pop("card_uuid"))
        user = self.context["request"].user
        obj, _ = WishlistItem.objects.update_or_create(
            user=user, card=card,
            defaults={"priority": validated_data.get("priority", 2),
                      "note": validated_data.get("note", "")},
        )
        return obj


class TradeSerializer(serializers.ModelSerializer):
    printing = CardPrintingSerializer(read_only=True)
    printing_uuid = serializers.UUIDField(write_only=True)

    class Meta:
        model = TradeItem
        fields = ["uuid", "printing", "printing_uuid", "quantity", "note", "created_at"]

    def create(self, validated_data):
        from apps.cards.models import CardPrinting

        printing = CardPrinting.objects.get(uuid=validated_data.pop("printing_uuid"))
        user = self.context["request"].user
        obj, _ = TradeItem.objects.update_or_create(
            user=user, printing=printing,
            defaults={"quantity": validated_data.get("quantity", 1),
                      "note": validated_data.get("note", "")},
        )
        return obj
