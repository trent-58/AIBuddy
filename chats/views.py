from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from user.parsers import PlainTextJSONParser

from .serializers import (
    ChatDetailSerializer,
    ChatMessageCreateSerializer,
    ChatSerializer,
    ChatSelectSerializer,
)
from .services import ChatsService, ChatsServiceError


class ChatSelectView(GenericAPIView):
    serializer_class = ChatSelectSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Select Or Create Chat",
        description="Get existing chat or create one. `mode=ai` for AI chat, `mode=person|direct` with `peer_id` for direct chat.",
        request=ChatSelectSerializer,
        responses={status.HTTP_200_OK: ChatSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        mode = serializer.validated_data["mode"]
        if mode == "ai":
            chat = ChatsService.get_or_create_ai_chat(user=request.user)
        else:
            chat = ChatsService.get_or_create_direct_chat(
                user=request.user,
                peer=serializer.validated_data["peer"],
            )

        return Response(ChatSerializer(chat, context={"request": request}).data, status=200)


class ChatListView(GenericAPIView):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Chats",
        description="List all chats where current user is a participant.",
        responses={status.HTTP_200_OK: ChatSerializer(many=True)},
    )
    def get(self, request):
        chats = (
            ChatsService.list_user_chats(user=request.user)
            .distinct()
            .order_by("-updated_at")
        )
        data = ChatSerializer(chats, many=True, context={"request": request}).data
        return Response(data, status=200)


class ChatDetailView(GenericAPIView):
    serializer_class = ChatDetailSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Chat Detail",
        description="Return chat state and message history for one chat.",
        responses={status.HTTP_200_OK: ChatDetailSerializer},
    )
    def get(self, request, chat_id):
        try:
            chat = ChatsService.get_chat_for_user(chat_id=chat_id, user=request.user)
        except ChatsServiceError as exc:
            return Response({"detail": str(exc)}, status=404)

        data = ChatDetailSerializer(chat).data
        return Response(data, status=200)


class ChatMessageView(GenericAPIView):
    serializer_class = ChatMessageCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser, PlainTextJSONParser]

    @extend_schema(
        summary="Send Message",
        description="Send a message to chat. Supports AI commands: #topic, #task, #hint, #answer, #evaluate.",
        request=ChatMessageCreateSerializer,
        responses={status.HTTP_200_OK: OpenApiTypes.OBJECT},
    )
    def post(self, request, chat_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            chat = ChatsService.get_chat_for_user(chat_id=chat_id, user=request.user)
            result = ChatsService.send_message(
                chat=chat,
                user=request.user,
                text=serializer.validated_data["text"],
            )
        except ChatsServiceError as exc:
            return Response({"detail": str(exc)}, status=400)

        return Response(result, status=200)
