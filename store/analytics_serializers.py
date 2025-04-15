from rest_framework import serializers

class DailySalesSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_orders = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class TopBooksSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    title = serializers.CharField()
    total_quantity = serializers.IntegerField()
    total_earned = serializers.DecimalField(max_digits=10, decimal_places=2)

