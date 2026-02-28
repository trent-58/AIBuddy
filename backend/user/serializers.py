import random
import uuid

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import EmailVerificationCode, Interest, InterestOption, User


class InterestOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterestOption
        fields = ["id", "name"]


class InterestSerializer(serializers.ModelSerializer):
    option_id = serializers.IntegerField(source="name_id", read_only=True)
    name = serializers.CharField(source="name.name", read_only=True)

    class Meta:
        model = Interest
        fields = ["option_id", "name"]


class RegistrationStartSerializer(serializers.Serializer):
    email = serializers.EmailField()


class RegistrationVerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.RegexField(regex=r"^\d{6}$")


class RegistrationSetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    session_token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)


class ForgotPasswordStartSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.RegexField(regex=r"^\d{6}$")


class ForgotPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    session_token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)


class ResetPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user is None or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "Authentication required"})

        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"old_password": ["Old password is incorrect"]})

        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": ["Passwords do not match"]})

        return attrs


class RegistrationCompleteSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    session_token = serializers.CharField(write_only=True)
    interests = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        write_only=True,
        required=False,
        default=list,
    )
    selected_interests = InterestSerializer(source="interest_set", many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "session_token",
            "username",
            "first_name",
            "last_name",
            "bio",
            "interests",
            "selected_interests",
        ]
        read_only_fields = ["id", "selected_interests"]

    def validate_interests(self, value):
        unique_interest_ids = list(dict.fromkeys(value))
        found_ids = set(
            InterestOption.objects.filter(id__in=unique_interest_ids).values_list("id", flat=True)
        )
        missing_ids = [item for item in unique_interest_ids if item not in found_ids]
        if missing_ids:
            raise serializers.ValidationError(f"Unknown interest option ids: {missing_ids}")
        return unique_interest_ids


class LoginSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    username = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(
            username=attrs["username"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid credentials")

        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self, **kwargs):
        refresh = self.validated_data["refresh"]
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except AttributeError as exc:
            raise serializers.ValidationError(
                {"refresh": "Token blacklist is not enabled in SIMPLE_JWT configuration"}
            ) from exc
        except TokenError as exc:
            raise serializers.ValidationError({"refresh": "Invalid or expired token"}) from exc


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class SessionTokenSerializer(serializers.Serializer):
    session_token = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    selected_interests = InterestSerializer(source="interest_set", many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "bio",
            "selected_interests",
        ]
        read_only_fields = fields


def generate_email_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def generate_pending_username() -> str:
    return f"pending_{uuid.uuid4().hex[:12]}"


def get_valid_verification(*, email: str, session_token: str | None = None, code: str | None = None):
    qs = EmailVerificationCode.objects.filter(email=email, expires_at__gt=timezone.now())
    if session_token is not None:
        qs = qs.filter(session_token=session_token, is_verified=True)
    if code is not None:
        qs = qs.filter(code=code)
    return qs.order_by("-created_at").first()
