from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentification
    path('login/',  auth_views.LoginView.as_view(template_name='rag_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register_user, name='register_user'),

    # Accueil
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),  
    # Gestion des documents
    path('upload/',                            views.upload_cvs,        name='upload_cvs'),
    path('index/',                             views.index_cvs,         name='index_cvs'),
    path('indexing-status/',                   views.indexing_status,   name='indexing_status'),
    path('documents/<int:doc_id>/update/',     views.update_document,   name='update_document'),
    path('documents/<int:doc_id>/delete/',     views.delete_document,   name='delete_document'),

    # Chat et conversations
    path('chat/',                              views.chat_interface,    name='chat_interface'),
    path('chat/<int:conversation_id>/',        views.chat_interface,    name='chat_interface'),
    path('send-message/',                      views.send_message,      name='send_message'),
    path('conversations/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
]
