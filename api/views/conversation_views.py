from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Max, Count
from django.contrib.auth import get_user_model

from api.serializers import ConversationSerializer, MessageSerializer
from taskify_app.models import Conversation, Message


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def conversations(request):
    """Devuelve todas las conversaciones del usuario autenticado con el último mensaje incluido.
    Soporta query params:
      - offset: offset (int, por defecto 0)
      - limit: cantidad máxima de conversaciones a devolver (int, opcional)

    POST: crear una nueva conversación.
      - body esperado (JSON): { "participants": [<user_id>, ...] } o { "participant": <user_id> }
      - El usuario autenticado será añadido automáticamente a participants si no está.
      - Para conversaciones 1:1 (dos participantes) se intenta devolver la conversación existente si ya existe.
    """
    User = get_user_model()
    user = request.user

    # POST -> crear conversación
    if request.method == "POST":
        data = request.data or {}
        # aceptar 'participant' (single) o 'participants' (list)
        participants = data.get("participants")
        single = data.get("participant")
        ids = []
        if participants is not None:
            if not isinstance(participants, (list, tuple)):
                return Response({"error": "'participants' debe ser una lista de ids."}, status=status.HTTP_400_BAD_REQUEST)
            ids = [int(i) for i in participants if i is not None]
        elif single is not None:
            try:
                ids = [int(single)]
            except (ValueError, TypeError):
                return Response({"error": "'participant' debe ser un id válido."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Debes indicar 'participants' o 'participant'."}, status=status.HTTP_400_BAD_REQUEST)

        # Eliminar duplicados y convertir a enteros
        try:
            ids = list({int(i) for i in ids})
        except (ValueError, TypeError):
            return Response({"error": "Ids de participantes inválidos."}, status=status.HTTP_400_BAD_REQUEST)

        # Asegurar que el usuario autenticado esté incluido
        if user.id not in ids:
            ids.append(user.id)

        # No permitir solo el propio usuario
        other_ids = [i for i in ids if i != user.id]
        if len(other_ids) == 0:
            return Response({"error": "Debes incluir al menos a otro participante."}, status=status.HTTP_400_BAD_REQUEST)

        # Validar que existan los usuarios
        users_qs = User.objects.filter(id__in=ids)
        if users_qs.count() != len(ids):
            return Response({"error": "Uno o más ids de participantes no existen."}, status=status.HTTP_400_BAD_REQUEST)

        # Intentar evitar duplicados para conversaciones 1:1
        if len(ids) == 2:
            a, b = ids
            existing = Conversation.objects.annotate(num=Count('participants')).filter(num=2, participants__id=a).filter(participants__id=b).first()
            if existing:
                serializer = ConversationSerializer(existing, context={"request": request})
                return Response(serializer.data, status=status.HTTP_200_OK)

        # Crear la conversación y asignar participantes
        conv = Conversation.objects.create()
        conv.participants.set(users_qs)
        conv.save()
        serializer = ConversationSerializer(conv, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # GET -> listar conversaciones con offset/limit
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
