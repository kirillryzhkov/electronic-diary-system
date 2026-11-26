from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications_app.services import send_telegram_message
from users.models import User


class TelegramProfileSerializer(serializers.ModelSerializer):
    telegram_chat_id = serializers.RegexField(r'\A-?[1-9][0-9]{0,18}\Z', allow_blank=True)
    bot_configured = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['telegram_chat_id', 'telegram_notifications_enabled', 'bot_configured']

    def get_bot_configured(self, user) -> bool:
        return bool(settings.TELEGRAM_BOT_TOKEN)


class TelegramProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=TelegramProfileSerializer)
    def get(self, request):
        return Response(TelegramProfileSerializer(request.user).data)

    @extend_schema(request=TelegramProfileSerializer, responses=TelegramProfileSerializer)
    def patch(self, request):
        serializer = TelegramProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        # Restrict writes to fields present in PATCH, including under concurrent requests.
        changes = serializer.validated_data
        if changes:
            for field, value in changes.items():
                setattr(request.user, field, value)
            request.user.save(update_fields=list(changes))
            request.user.refresh_from_db(fields=[
                'telegram_chat_id', 'telegram_notifications_enabled',
            ])
        return Response(serializer.data)


class TelegramTestView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        chat_id = request.user.telegram_chat_id
        if not chat_id or not settings.TELEGRAM_BOT_TOKEN:
            return Response(
                {'detail': 'Укажи Telegram Chat ID и проверь настройку бота.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not send_telegram_message(chat_id, 'Тестовое уведомление из электронного дневника.'):
            return Response(
                {'detail': 'Telegram не принял тестовое уведомление.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({'ok': True, 'detail': 'Тестовое уведомление отправлено'})
