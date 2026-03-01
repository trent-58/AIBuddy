from datetime import timedelta
import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerificationCode, Interest, InterestOption, User
from .parsers import PlainTextJSONParser
from .serializers import (
    ForgotPasswordResetSerializer,
    ForgotPasswordStartSerializer,
    ForgotPasswordVerifySerializer,
    InterestOptionSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegistrationCompleteSerializer,
    RegistrationSetPasswordSerializer,
    RegistrationStartSerializer,
    RegistrationVerifyCodeSerializer,
    SessionTokenSerializer,
    TokenPairSerializer,
    UserProfileUpdateSerializer,
    UserProfileSerializer,
    ResetPasswordSerializer,
    generate_email_code,
    generate_pending_username,
    get_valid_verification,
)


class RegisterEmailView(GenericAPIView):
    serializer_class = RegistrationStartSerializer
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Start Registration",
        description="Step 1: Send email and receive a 6-digit verification code.",
        request=RegistrationStartSerializer,
        responses={200: None},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email, is_active=True).exists():
            return Response({"detail": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        pending_user = User.objects.filter(email__iexact=email, is_active=False).order_by("id").first()
        if pending_user is None:
            while True:
                username = generate_pending_username()
                if not User.objects.filter(username=username).exists():
                    break
            pending_user = User.objects.create(username=username, email=email, is_active=False)
            pending_user.set_unusable_password()
            pending_user.save(update_fields=["password"])

        code = generate_email_code()
        EmailVerificationCode.objects.create(
            user=pending_user,
            email=email,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        send_mail(
            subject="Your verification code",
            message=f"Your verification code is: {code}. It expires in 10 minutes.",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"detail": "Verification code sent"}, status=status.HTTP_200_OK)


class RegisterVerifyCodeView(GenericAPIView):
    serializer_class = RegistrationVerifyCodeSerializer
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Verify Email Code",
        description="Step 2: Verify email+code and receive a registration session token.",
        request=RegistrationVerifyCodeSerializer,
        responses={200: SessionTokenSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        code = serializer.validated_data["code"]

        verification = get_valid_verification(email=email, code=code)
        if verification is None:
            return Response({"detail": "Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)

        verification.is_verified = True
        verification.session_token = uuid.uuid4().hex
        verification.save(update_fields=["is_verified", "session_token"])

        return Response(SessionTokenSerializer({"session_token": verification.session_token}).data, status=status.HTTP_200_OK)


class RegisterSetPasswordView(GenericAPIView):
    serializer_class = RegistrationSetPasswordSerializer
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Set Registration Password",
        description="Step 3: Set password using email + session_token.",
        request=RegistrationSetPasswordSerializer,
        responses={200: None},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        session_token = serializer.validated_data["session_token"]
        password = serializer.validated_data["password"]

        verification = get_valid_verification(email=email, session_token=session_token)
        if verification is None:
            return Response({"detail": "Invalid session token"}, status=status.HTTP_400_BAD_REQUEST)

        user = verification.user
        user.set_password(password)
        user.save(update_fields=["password"])

        return Response({"detail": "Password updated"}, status=status.HTTP_200_OK)


class RegisterCompleteView(GenericAPIView):
    serializer_class = RegistrationCompleteSerializer
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Complete Registration",
        description="Step 4: Set profile data and interests, then activate user.",
        request=RegistrationCompleteSerializer,
        responses={200: RegistrationCompleteSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        session_token = serializer.validated_data["session_token"]

        verification = get_valid_verification(email=email, session_token=session_token)
        if verification is None:
            return Response({"detail": "Invalid session token"}, status=status.HTTP_400_BAD_REQUEST)

        user = verification.user
        username = serializer.validated_data["username"]

        if User.objects.exclude(id=user.id).filter(username=username).exists():
            return Response({"username": ["A user with that username already exists."]}, status=status.HTTP_400_BAD_REQUEST)

        user.email = email
        user.username = username
        user.first_name = serializer.validated_data.get("first_name", "")
        user.last_name = serializer.validated_data.get("last_name", "")
        user.bio = serializer.validated_data.get("bio", "")
        user.is_active = True

        try:
            user.save(update_fields=["email", "username", "first_name", "last_name", "bio", "is_active"])
        except IntegrityError:
            return Response({"username": ["A user with that username already exists."]}, status=status.HTTP_400_BAD_REQUEST)

        interest_ids = serializer.validated_data.get("interests", [])
        options_by_id = InterestOption.objects.in_bulk(interest_ids)

        Interest.objects.filter(user=user).delete()
        Interest.objects.bulk_create(
            [Interest(user=user, name=options_by_id[option_id]) for option_id in interest_ids]
        )

        EmailVerificationCode.objects.filter(user=user).delete()

        payload = RegistrationCompleteSerializer(user).data
        return Response(payload, status=status.HTTP_200_OK)


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Login",
        description="Authenticate with username and password. Returns access+refresh JWT tokens.",
        request=LoginSerializer,
        responses={200: TokenPairSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        payload = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        return Response(TokenPairSerializer(payload).data, status=status.HTTP_200_OK)


class LogoutView(GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Logout",
        description="Blacklist refresh token (SimpleJWT token_blacklist must be migrated).",
        request=LogoutSerializer,
        responses={204: None},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InterestOptionListView(GenericAPIView):
    serializer_class = InterestOptionSerializer
    queryset = InterestOption.objects.none()
    permission_classes = [AllowAny]

    def get_queryset(self):
        return InterestOption.objects.all().order_by("name")

    @extend_schema(
        summary="List Interest Options",
        description="Returns available interest options used in registration profile completion.",
        responses={200: InterestOptionSerializer(many=True)},
    )
    def get(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileView(GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Current User Profile",
        description="Returns authenticated user's profile information and selected interests.",
        responses={200: UserProfileSerializer},
    )
    def get(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update Current User Profile",
        description="Update authenticated user's profile fields and selected interests.",
        request=UserProfileUpdateSerializer,
        responses={200: UserProfileSerializer},
    )
    def put(self, request):
        serializer = UserProfileUpdateSerializer(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(request.user).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Partial Update Current User Profile",
        description="Partially update authenticated user's profile fields and selected interests.",
        request=UserProfileUpdateSerializer,
        responses={200: UserProfileSerializer},
    )
    def patch(self, request):
        serializer = UserProfileUpdateSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(request.user).data, status=status.HTTP_200_OK)


class ResetPasswordView(GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Reset Password (Authenticated)",
        description="Reset current user's password using access token.",
        request=ResetPasswordSerializer,
        responses={200: None},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return Response({"detail": "Password updated"}, status=status.HTTP_200_OK)


class ForgotPasswordEmailView(GenericAPIView):
    serializer_class = ForgotPasswordStartSerializer
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Forgot Password: Send Code",
        description="Send a 6-digit verification code to the user's email.",
        request=ForgotPasswordStartSerializer,
        responses={200: None},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is not None:
            code = generate_email_code()
            EmailVerificationCode.objects.create(
                user=user,
                email=email,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=10),
            )

            send_mail(
                subject="Your password reset code",
                message=f"Your password reset code is: {code}. It expires in 10 minutes.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[email],
                fail_silently=False,
            )

        return Response(
            {"detail": "If this email exists, a verification code has been sent"},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordVerifyCodeView(GenericAPIView):
    serializer_class = ForgotPasswordVerifySerializer
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Forgot Password: Verify Code",
        description="Verify email+code and receive password-reset session token.",
        request=ForgotPasswordVerifySerializer,
        responses={200: SessionTokenSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        code = serializer.validated_data["code"]

        verification = get_valid_verification(email=email, code=code)
        if verification is None or not verification.user.is_active:
            return Response({"detail": "Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)

        verification.is_verified = True
        verification.session_token = uuid.uuid4().hex
        verification.save(update_fields=["is_verified", "session_token"])

        return Response(SessionTokenSerializer({"session_token": verification.session_token}).data, status=status.HTTP_200_OK)


class ForgotPasswordResetView(GenericAPIView):
    serializer_class = ForgotPasswordResetSerializer
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Forgot Password: Reset",
        description="Reset password using email + verified session token.",
        request=ForgotPasswordResetSerializer,
        responses={200: None},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        session_token = serializer.validated_data["session_token"]
        password = serializer.validated_data["password"]

        verification = get_valid_verification(email=email, session_token=session_token)
        if verification is None or not verification.user.is_active:
            return Response({"detail": "Invalid session token"}, status=status.HTTP_400_BAD_REQUEST)

        user = verification.user
        user.set_password(password)
        user.save(update_fields=["password"])
        EmailVerificationCode.objects.filter(user=user).delete()

        return Response({"detail": "Password updated"}, status=status.HTTP_200_OK)
