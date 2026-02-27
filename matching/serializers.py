from rest_framework import serializers


class MatchResponseSerializer(serializers.Serializer):
    is_solo = serializers.BooleanField()
    matched_user_id = serializers.IntegerField(allow_null=True)
    username = serializers.CharField(allow_null=True)
    interests = serializers.ListField(child=serializers.CharField())
    detail = serializers.CharField(required=False)
