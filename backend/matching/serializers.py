from rest_framework import serializers

from .models import ChatInvite


class MatchResponseSerializer(serializers.Serializer):
    is_solo = serializers.BooleanField()
    matched_user_id = serializers.IntegerField(allow_null=True)
    username = serializers.CharField(allow_null=True)
    interests = serializers.ListField(child=serializers.CharField())
    detail = serializers.CharField(required=False)


class MatchCandidateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    shared_interests = serializers.IntegerField()
    interests = serializers.ListField(child=serializers.CharField())


class InviteCreateSerializer(serializers.Serializer):
    to_user_id = serializers.IntegerField(min_value=1)


class InviteSerializer(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField(read_only=True)
    to_user_id = serializers.IntegerField(read_only=True)
    from_username = serializers.CharField(source="from_user.username", read_only=True)
    to_username = serializers.CharField(source="to_user.username", read_only=True)

    class Meta:
        model = ChatInvite
        fields = [
            "id",
            "from_user_id",
            "from_username",
            "to_user_id",
            "to_username",
            "status",
            "created_at",
        ]
