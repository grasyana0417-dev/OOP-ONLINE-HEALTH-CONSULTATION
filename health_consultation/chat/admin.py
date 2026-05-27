from django.contrib import admin
from .models import ChatMessage, ChatRoom, ChatAttachment


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'content_preview', 'message_type', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read', 'created_at']
    search_fields = ['sender__email', 'receiver__email', 'content']
    raw_id_fields = ['sender', 'receiver', 'appointment']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def content_preview(self, obj):
        """Show a preview of the message content."""
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    content_preview.short_description = 'Content'


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'resident', 'health_worker', 'room_type', 'is_active', 'last_message_at']
    list_filter = ['room_type', 'is_active', 'created_at']
    search_fields = ['name', 'resident__email', 'health_worker__email']
    raw_id_fields = ['resident', 'health_worker', 'appointment']


@admin.register(ChatAttachment)
class ChatAttachmentAdmin(admin.ModelAdmin):
    list_display = ['message', 'file_name', 'file_size_display', 'file_type', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['file_name', 'message__content']
