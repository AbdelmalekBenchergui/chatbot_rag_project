from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Conversation, Message, DocumentUpload


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'document_info', 'message_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'user']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25

    fieldsets = (
        ('Informations générales', {
            'fields': ('user', 'title', 'document')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Annoter le nombre de messages dans chaque conversation
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(message_count=Count('messages'))

    def message_count(self, obj):
        return obj.message_count
    message_count.short_description = 'Messages'
    message_count.admin_order_field = 'message_count'

    # Afficher un résumé du document lié à la conversation
    def document_info(self, obj):
        if obj.document:
            name = obj.document.filename
            return format_html(
                '<span title="{}"><i class="fas fa-file"></i> {}</span>',
                name, name[:30] + '...' if len(name) > 30 else name
            )
        return format_html('<span class="text-muted">Aucun document</span>')
    document_info.short_description = 'Document associé'



@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation_title', 'content_preview', 'sender_display', 'timestamp']
    list_filter = ['timestamp', 'sender', 'conversation']
    search_fields = ['content', 'conversation__title', 'sender__username']
    readonly_fields = ['timestamp']
    list_per_page = 50

    fieldsets = (
        ('Message', {
            'fields': ('conversation', 'sender', 'content')
        }),
        ('Métadonnées', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def conversation_title(self, obj):
        return obj.conversation.title or f"Conversation {obj.conversation.id}"
    conversation_title.short_description = 'Conversation'

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Contenu'

    def sender_display(self, obj):
        if obj.sender:
            return format_html('<span style="color: blue;">{}</span>', obj.sender.username)
        return format_html('<span style="color: green;">Bot</span>')
    sender_display.short_description = 'Expéditeur'


@admin.register(DocumentUpload)
class DocumentUploadAdmin(admin.ModelAdmin):
    list_display = ['filename', 'user', 'file_size_formatted', 'upload_date', 'indexing_status']
    list_filter = ['is_indexed', 'upload_date', 'indexing_date', 'user']
    search_fields = ['filename', 'user__username']
    readonly_fields = ['upload_date', 'file_size']
    list_per_page = 25

    fieldsets = (
        ('Fichier', {
            'fields': ('filename', 'file_size', 'user')
        }),
        ('Indexation', {
            'fields': ('is_indexed', 'indexing_date'),
            'description': "Statut de l'indexation du document dans le système RAG"
        }),
        ('Métadonnées', {
            'fields': ('upload_date',),
            'classes': ('collapse',)
        }),
    )

    def file_size_formatted(self, obj):
        """Affiche la taille du fichier de manière lisible"""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    file_size_formatted.short_description = 'Taille'

    def indexing_status(self, obj):
        if obj.is_indexed:
            return format_html(
                '<span style="color: green;">Indexé</span>'
                '<br><span style="color: gray; font-size: 0.8em;">{}</span>',
                obj.indexing_date.strftime("%d/%m/%Y %H:%M") if obj.indexing_date else ''
            )
        return format_html('<span style="color: orange;">⏳ En attente</span>')
    indexing_status.short_description = "Statut d'indexation"


admin.site.site_header = "Administration CV Assistant"
admin.site.site_title = "CV Assistant Admin"
admin.site.index_title = "Gestion du système RAG"
