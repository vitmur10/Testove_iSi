from rest_framework import serializers
from .models import Thread, Message


class ThreadSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = '__all__'

    def get_last_message(self, obj):
        """
        Return the last message in the thread.
        """
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()
    thread = ThreadSerializer(read_only=True)

    class Meta:
        model = Message
        fields = '__all__'

    def create(self, validated_data):
        print(validated_data)
        thread_data = validated_data.pop('sender')
        thread = Thread.objects.create(**thread_data)
        message = Message.objects.create(thread=thread, **validated_data)
        return message
