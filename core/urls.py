# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    # O Django já tem uma View de Login pronta, só indicamos o template
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    
    # Rota de Logout
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('painel/', views.dashboard, name='dashboard'),

    path('nova-reuniao/', views.nova_reuniao, name='nova_reuniao'),

    path('chat/', views.lista_usuarios, name='lista_usuarios'),

    path('chat/<str:username>/', views.sala_chat, name='sala_chat'),

    path('nova-tarefa/', views.nova_tarefa, name='nova_tarefa'),

    path('calendario/', views.calendario, name='calendario'),

    path('quem-somos/', views.quem_somos, name='quem_somos'),

    path('comunidade/', views.usuarios_online, name='usuarios_online'),

    path('perfil/', views.meu_perfil, name='meu_perfil'),

    path('usuario/<str:username>/', views.perfil_publico, name='perfil_publico'),

    path('tarefa/editar/<int:id>/', views.editar_tarefa, name='editar_tarefa'),

    path('tarefa/excluir/<int:id>/', views.excluir_tarefa, name='excluir_tarefa'),

    path('reuniao/editar/<int:id>/', views.editar_reuniao, name='editar_reuniao'),
    
    path('reuniao/excluir/<int:id>/', views.excluir_reuniao, name='excluir_reuniao'),

    path('forum/', views.forum, name='forum'),

    path('forum/post/<int:pk>/', views.post_detail, name='post_detail'),
    
    path('forum/like/<int:pk>/', views.dar_like, name='dar_like'),

    path('post/<int:pk>/deletar/', views.deletar_post, name='deletar_post'),

    path('comentario/<int:pk>/deletar/', views.deletar_comentario, name='deletar_comentario'),

    path('notificacao/<int:id>/lida/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),
]