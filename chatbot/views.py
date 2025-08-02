# Imports organisés
import os, shutil, json, time, uuid, logging

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Conversation, Message, DocumentUpload
from .rag_system.indexing import IndexingService
from .rag_system.llm_processing import llm_service

logger = logging.getLogger(__name__)

# Utilisateurs authentifiés ou anonymes
def get_user_or_session_id(request):
    if request.user.is_authenticated:
        return request.user
    if 'anon_id' not in request.session:
        request.session['anon_id'] = str(uuid.uuid4())
    return request.session['anon_id']

def get_user_if_authenticated(user_or_session):
    return user_or_session if isinstance(user_or_session, User) else None

# Inscription
def register_user(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('home')
    return render(request, 'rag_app/register.html', {'form': form})

# Accueil
@login_required
def home(request):
    user_docs = DocumentUpload.objects.filter(user=request.user).order_by('-upload_date')
    user_convs = Conversation.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'rag_app/home.html', {
        'documents': user_docs,
        'conversations': user_convs
    })

# Upload CVs
@csrf_exempt
def upload_cvs(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        if not files:
            messages.error(request, "Aucun fichier sélectionné")
            return redirect('home')

        user = get_user_or_session_id(request)
        data_folder = settings.DATA_FOLDER
        os.makedirs(data_folder, exist_ok=True)

        for f in os.listdir(data_folder):
            file_path = os.path.join(data_folder, f)
            if os.path.isfile(file_path):
                os.remove(file_path)

        for f in files:
            file_path = os.path.join(data_folder, f.name)
            with open(file_path, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)

            DocumentUpload.objects.create(
                user=get_user_if_authenticated(user),
                filename=f.name,
                file_size=f.size
            )
        messages.success(request, f"{len(files)} fichiers sauvegardés avec succès")
    return redirect('home')

# Indexation
def index_cvs(request):
    success, msg = IndexingService.build_vector_store()
    if success:
        llm_service.build_graph()
        DocumentUpload.objects.filter(is_indexed=False).update(
            is_indexed=True, indexing_date=timezone.now()
        )
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect('home')

# Interface de chat
def chat_interface(request, conversation_id=None):
    user = get_user_or_session_id(request)
    user_filter = get_user_if_authenticated(user)

    conversation = None
    if conversation_id:
        conversation = get_object_or_404(Conversation, pk=conversation_id, user=user_filter)

    recent = Conversation.objects.filter(user=user_filter).order_by('-updated_at')[:10]
    documents = DocumentUpload.objects.filter(user=user_filter).order_by('-upload_date')

    return render(request, 'rag_app/chat.html', {
        'conversation': conversation,
        'recent_conversations': recent,
        'uploaded_documents': documents,
        'total_documents': documents.count(),
        'indexed_documents': documents.filter(is_indexed=True).count(),
    })

# Envoi message
@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    try:
        data = json.loads(request.body)
        content = data.get('message', '').strip()
        if not content:
            return JsonResponse({'error': 'Le message ne peut pas être vide'}, status=400)

        user = get_user_or_session_id(request)
        user_filter = get_user_if_authenticated(user)
        conv_id = data.get('conversation_id')

        if conv_id:
            conversation = get_object_or_404(Conversation, pk=conv_id, user=user_filter)
        else:
            conversation = Conversation.objects.create(
                user=user_filter,
                title=(content[:50] + '...') if len(content) > 50 else content,
                created_at=timezone.now()
            )

        user_msg = Message.objects.create(
            conversation=conversation,
            sender=user_filter,
            content=content,
            timestamp=timezone.now()
        )

        history = Message.objects.filter(conversation=conversation).order_by('timestamp')
        context = [{"role": "user" if m.sender == user_msg.sender else "assistant", "content": m.content} for m in history]

        start = time.time()
        results, error = llm_service.ask_question(content, conversation_context=context[:-1])
        duration = time.time() - start

        if error:
            return JsonResponse({'error': error}, status=400)

        response_text = "Aucun CV pertinent trouvé. Reformulez votre question."
        if results:
            response_text = "Voici les CV les plus pertinents :\n\n" + "\n\n".join(
                f"{i + 1}. **{r['filename']}** — Score LLM: {r['score_llm']}/10, FAISS: {r['score_faiss']}\nJustification: {r['justification']}"
                for i, r in enumerate(results)
            )

        bot_msg = Message.objects.create(
            conversation=conversation,
            sender=None,
            content=response_text,
            timestamp=timezone.now()
        )

        conversation.updated_at = timezone.now()
        conversation.save()

        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'user_message': {
                'id': user_msg.id,
                'content': user_msg.content,
                'timestamp': user_msg.timestamp.isoformat()
            },
            'bot_message': {
                'id': bot_msg.id,
                'content': bot_msg.content,
                'timestamp': bot_msg.timestamp.isoformat(),
                'response_time': duration
            },
            'results': results
        })

    except Exception as e:
        logger.exception("Erreur dans send_message")
        return JsonResponse({'error': str(e)}, status=500)

# Suppression conversation
@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def delete_conversation(request, conversation_id):
    user = get_user_or_session_id(request)
    conversation = get_object_or_404(Conversation, pk=conversation_id, user=get_user_if_authenticated(user))
    conversation.delete()
    return JsonResponse({'success': True, 'message': 'Conversation supprimée', 'conversation_id': conversation_id})

# Mise à jour document
@login_required
@require_http_methods(["POST"])
def update_document(request, doc_id):
    document = get_object_or_404(DocumentUpload, pk=doc_id, user=request.user)
    new_name = request.POST.get('filename')
    if new_name:
        document.filename = new_name
        document.save()
        return JsonResponse({'success': True, 'filename': document.filename})
    return JsonResponse({'success': False, 'error': 'Nom de fichier requis'})

# Statut d’indexation
def indexing_status(request):
    user = get_user_or_session_id(request)
    docs = DocumentUpload.objects.filter(user=get_user_if_authenticated(user))
    total = docs.count()
    indexed = docs.filter(is_indexed=True).count()
    return JsonResponse({
        'is_indexing': False,
        'progress': int((indexed / total * 100) if total > 0 else 0),
        'total_documents': total,
        'indexed_documents': indexed,
        'last_indexed': indexed
    })

# Suppression document
@login_required
@require_http_methods(["POST", "DELETE"])
def delete_document(request, doc_id):
    try:
        document = get_object_or_404(DocumentUpload, pk=doc_id, user=request.user)
        filename = document.filename
        document.delete()
        messages.success(request, f'Le document "{filename}" a été supprimé avec succès.')
        return JsonResponse({'success': True, 'message': f'Document "{filename}" supprimé', 'document_id': doc_id})
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du document {doc_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Erreur lors de la suppression du document'}, status=500)

# Déconnexion
def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('login')

