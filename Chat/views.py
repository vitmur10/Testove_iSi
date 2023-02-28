from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, F, Count, Max
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Thread, Message
from .serializers import ThreadSerializer, MessageSerializer


class ThreadViewSet(viewsets.ModelViewSet):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer

    def perform_create(self, serializer):
        """
        If a thread already exists with the given participants, return it.
        Otherwise, create a new thread.
        """
        participants = self.request.data.get('participants', [])
        if len(participants) != 2:
            return Response({'error': 'A thread can only have 2 participants.'}, status=400)

        queryset = Thread.objects.filter(participants__in=participants).distinct()

        if queryset.exists():
            thread = queryset.annotate(last_message_created=Max('messages__created')).order_by(
                '-last_message_created').first()
            return Response(self.serializer_class(thread).data)

        serializer.save()

    def perform_destroy(self, instance):
        """
        Remove all messages associated with the thread before deleting it.
        """
        instance.messages.all().delete()
        instance.delete()

    @action(detail=False, methods=['get'])
    def user_threads(self, request):
        """
        Return all threads for the current user.
        """
        threads = Thread.objects.filter(participants=request.user)
        serializer = self.get_serializer(threads, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        """
        Set the sender of the message to the current user.
        """
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """
        Mark a single message as read.
        """

        message = self.get_object()
        message.is_read = True
        message.save()
        serializer = self.get_serializer(message)
        return Response(serializer.data)


@action(detail=False, methods=['patch'])
def mark_all_read(self, request):
    """
    Mark all unread messages as read for the current user.
    """
    Message.objects.filter(thread__participants=request.user, is_read=False).update(is_read=True)
    return Response({'message': 'All unread messages marked as read.'})


@login_required
def get_unread_count(self, request):
    """
    Return the number of unread messages for the current user.
    """

    count = Message.objects.filter(thread__participants=request.user, is_read=False).count()
    return Response({'unread_count': count})
