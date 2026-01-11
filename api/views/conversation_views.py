from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Max

from api.serializers import ConversationSerializer, MessageSerializer
from taskify_app.models import Conversation, Message


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def conversations(request):
    """Devuelve todas las conversaciones del usuario autenticado con el último mensaje incluido.
    Soporta query params:
      - offset: offset (int, por defecto 0)
      - limit: cantidad máxima de conversaciones a devolver (int, opcional)
    """
    user = request.user
    offset = request.GET.get("offset")
    limit = request.GET.get("limit")

    try:
        offset = int(offset) if offset is not None else 0
        if offset < 0:
            offset = 0
    except (ValueError, TypeError):
        offset = 0

    try:
        limit = int(limit) if limit is not None else None
        if limit is not None and limit < 1:
            limit = None
    except (ValueError, TypeError):
        limit = None

    # Ordenar por timestamp del último mensaje (si existe), sino por created_at
    qs = Conversation.objects.filter(participants=user).distinct().annotate(last_msg_ts=Max('messages__timestamp')).order_by("-last_msg_ts", "-created_at")

    # Aplicar offset/limit
    if limit is not None:
        qs = qs[offset: offset + limit]
    else:
        qs = qs[offset:]

    serializer = ConversationSerializer(qs, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def conversation_messages(request, pk):
    """Devuelve los mensajes de una conversación con soporte de offset y limit.
    Query params:
      - offset: entero >= 0 (por defecto 0)
      - limit: entero > 0 (opcional)

    POST: crear un nuevo mensaje en la conversación (body JSON: { "content": "..." }).
    """
    user = request.user
    try:
        conv = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversación no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    if not conv.participants.filter(id=user.id).exists():
        return Response({"error": "No tienes permisos para ver esta conversación."}, status=status.HTTP_403_FORBIDDEN)

    # POST -> crear mensaje
    if request.method == "POST":
        content = request.data.get("content")
        if not content or not str(content).strip():
            return Response({"error": "El campo 'content' es requerido."}, status=status.HTTP_400_BAD_REQUEST)
        # Asegurarse de que el sender sea participante (ya comprobado) y crear
        message = Message.objects.create(conversation=conv, sender=user, content=content)
        return Response(MessageSerializer(message, context={"request": request}).data, status=status.HTTP_201_CREATED)

    # GET -> listar mensajes con offset/limit
    offset = request.GET.get("offset")
    limit = request.GET.get("limit")

    try:
        offset = int(offset) if offset is not None else 0
        if offset < 0:
            offset = 0
    except (ValueError, TypeError):
        offset = 0

    try:
        limit = int(limit) if limit is not None else None
        if limit is not None and limit < 1:
            limit = None
    except (ValueError, TypeError):
        limit = None

    qs = conv.messages.filter(sender__in=conv.participants.all()).order_by("timestamp")
    total = qs.count()
    if limit is not None:
        qs = qs[offset: offset + limit]
    else:
        qs = qs[offset:]

    data = {
        "conversation": conv.id,
        "offset": offset,
        "limit": limit,
        "total": total,
        "messages": MessageSerializer(qs, many=True, context={"request": request}).data,
    }
    return Response(data)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def conversation_mark_read(request, pk):
    """Marca como leídos (is_read=True) todos los mensajes de la conversación `pk` cuyo sender != request.user.
    Devuelve la cantidad de mensajes actualizados.
    """
    user = request.user
    try:
        conv = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversación no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    if not conv.participants.filter(id=user.id).exists():
        return Response({"error": "No tienes permisos para modificar esta conversación."}, status=status.HTTP_403_FORBIDDEN)

    # Filtrar mensajes de la conversación donde sender != user y is_read == False
    msgs_to_update = conv.messages.exclude(sender=user).filter(is_read=False)
    updated_count = msgs_to_update.update(is_read=True)

    return Response({"updated": updated_count}, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def conversation_detail(request, pk):
    """Devuelve los datos de la conversación `pk` si el usuario autenticado es participante."""
    user = request.user
    try:
        conv = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversación no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    if not conv.participants.filter(id=user.id).exists():
        return Response({"error": "No tienes permisos para ver esta conversación."}, status=status.HTTP_403_FORBIDDEN)

    serializer = ConversationSerializer(conv, context={"request": request})
    return Response(serializer.data)
