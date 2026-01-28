from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from .models import Mensagem, Reuniao, Tarefa, Perfil
from .forms import ReuniaoForm, TarefaForm
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserUpdateForm, PerfilUpdateForm
from django.http import HttpResponseForbidden
from django.db.models import Count 
from .forms import PostForm, ComentarioForm
from .models import Post, Comentario 

# --- Página de Entrada (Pública) ---
def home(request):
    # Se o usuário já estiver logado, manda direto pro painel
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

# --- Painel Principal (Protegido) ---
@login_required
def dashboard(request):
    hoje = timezone.now().date()
    
    # Busca reuniões onde sou solicitante OU estou na lista de convidados
    reunioes = Reuniao.objects.filter(
        Q(solicitante=request.user) | Q(convidados=request.user)
    ).filter(data_inicio__date=hoje).distinct().order_by('data_inicio')
    
    # Mostra se: Eu sou o dono da tarefa (usuario) OU Eu fui quem criou (criador)
    tarefas = Tarefa.objects.filter(
        Q(usuario=request.user) | Q(criador=request.user),
        data_prazo=hoje
    ).distinct()
    
    # Conta mensagens não lidas
    notificacoes = Mensagem.objects.filter(destinatario=request.user, lido=False).count()
    
    context = {
        'reunioes': reunioes,
        'tarefas': tarefas,
        'notificacoes': notificacoes,
        'hoje': hoje
    }
    return render(request, 'dashboard.html', context)

# --- CRIAR REUNIÃO (Renomeado para bater com o HTML) ---
@login_required
def nova_reuniao(request):
    if request.method == 'POST':
        form = ReuniaoForm(request.POST, user=request.user)
        if form.is_valid():
            reuniao = form.save(commit=False)
            reuniao.solicitante = request.user
            reuniao.save() # Salva os dados básicos (título, data)
            
            form.save_m2m() # <--- OBRIGATÓRIO: Salva os convidados (Many-to-Many)
            
            messages.success(request, 'Reunião agendada com sucesso!')
            # MUDANÇA AQUI: Agora vai para o calendário
            return redirect('calendario')
    else:
        form = ReuniaoForm(user=request.user)
    
    return render(request, 'criar_reuniao.html', {'form': form})

@login_required
def lista_usuarios(request):
    # Busca usuários que trocaram mensagens comigo
    usuarios = User.objects.filter(
        Q(mensagens_enviadas__destinatario=request.user) | 
        Q(mensagens_recebidas__remetente=request.user)
    ).distinct().exclude(id=request.user.id)

    return render(request, 'lista_usuarios.html', {'usuarios': usuarios})

@login_required
def sala_chat(request, username):
    outro_usuario = get_object_or_404(User, username=username)

    if request.method == 'POST':
        conteudo = request.POST.get('conteudo')
        if conteudo:
            Mensagem.objects.create(
                remetente=request.user,
                destinatario=outro_usuario,
                conteudo=conteudo
            )
            return redirect('sala_chat', username=username)

    mensagens = Mensagem.objects.filter(
        Q(remetente=request.user, destinatario=outro_usuario) | 
        Q(remetente=outro_usuario, destinatario=request.user)
    ).order_by('data_envio')

    Mensagem.objects.filter(remetente=outro_usuario, destinatario=request.user, lido=False).update(lido=True)

    return render(request, 'chat.html', {
        'outro_usuario': outro_usuario,
        'mensagens': mensagens
    })

# --- CRIAR TAREFA (Renomeado para bater com o HTML) ---
@login_required
def nova_tarefa(request):
    if request.method == 'POST':
        form = TarefaForm(request.POST, user=request.user)
        
        if form.is_valid():
            tarefa = form.save(commit=False)
            
            # Define o criador para evitar erro de integridade
            tarefa.criador = request.user 
            
            # Lógica para definir para QUEM é a tarefa
            usuario_escolhido = form.cleaned_data.get('usuario')
            if usuario_escolhido:
                tarefa.usuario = usuario_escolhido
                messages.success(request, f'Tarefa atribuída para {usuario_escolhido.username}!')
            else:
                tarefa.usuario = request.user
                messages.success(request, 'Tarefa criada com sucesso!')
            
            tarefa.save()
            return redirect('calendario')
            
    else:
        form = TarefaForm(user=request.user)
    
    # Usamos o 'form_generico.html' pois você disse que funcionou melhor
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Nova Tarefa'})

@login_required
def calendario(request):
    agora = timezone.now()
    hoje = agora.date()

    # 1. Reuniões (Com filtro de segurança)
    reunioes = Reuniao.objects.filter(
        Q(solicitante=request.user) | Q(convidados=request.user),
        data_inicio__gte=agora
    ).distinct().order_by('data_inicio')

    # 2. Tarefas (Com filtro de segurança)
    todas_minhas_tarefas = Tarefa.objects.filter(
        Q(usuario=request.user) | Q(criador=request.user)
    ).distinct()

    # Separa em Futuras e Antigas
    tarefas = todas_minhas_tarefas.filter(data_prazo__gte=hoje).order_by('data_prazo')
    tarefas_antigas = todas_minhas_tarefas.filter(data_prazo__lt=hoje).order_by('-data_prazo')

    context = {
        'reunioes': reunioes,
        'tarefas': tarefas,
        'tarefas_antigas': tarefas_antigas,
    }
    return render(request, 'calendario.html', context)

def quem_somos(request):
    return render(request, 'quem_somos.html')

@login_required
def usuarios_online(request):
    mentores = User.objects.filter(perfil__tipo='Mentor', is_active=True)
    estudantes = User.objects.filter(perfil__tipo='Estudante', is_active=True)

    return render(request, 'usuarios_online.html', {
        'mentores': mentores,
        'estudantes': estudantes
    })

@login_required
def meu_perfil(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = PerfilUpdateForm(request.POST, request.FILES, instance=request.user.perfil)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('meu_perfil') 
            
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = PerfilUpdateForm(instance=request.user.perfil)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'perfil.html', context)

def perfil_publico(request, username):
    perfil_user = get_object_or_404(User, username=username)
    
    # Busca os posts desse usuário (do mais novo para o mais velho)
    posts = Post.objects.filter(autor=perfil_user).order_by('-data_criacao')
    
    context = {
        'perfil_user': perfil_user,
        'posts': posts
    }
    return render(request, 'perfil_publico.html', context)

@login_required
def editar_tarefa(request, id):
    tarefa = get_object_or_404(Tarefa, id=id)
    
    # Segurança
    if tarefa.criador != request.user:
        return HttpResponseForbidden("Você não tem permissão.")

    if request.method == 'POST':
        tarefa.titulo = request.POST.get('titulo')
        tarefa.data_prazo = request.POST.get('data')
        tarefa.informacoes = request.POST.get('descricao')
        tarefa.save()
        return redirect('calendario') # Redireciona para o calendário
    
    return render(request, 'editar_tarefa.html', {'tarefa': tarefa})

@login_required
def excluir_tarefa(request, id):
    tarefa = get_object_or_404(Tarefa, id=id)
    if tarefa.criador == request.user:
        tarefa.delete()
    return redirect('calendario')

@login_required
def editar_reuniao(request, id):
    reuniao = get_object_or_404(Reuniao, id=id)
    
    # Segurança
    if reuniao.solicitante != request.user:
        return HttpResponseForbidden("Você não tem permissão.")

    if request.method == 'POST':
        reuniao.titulo = request.POST.get('titulo')
        
        data_str = request.POST.get('data')
        hora_str = request.POST.get('hora')
        
        if data_str and hora_str:
            reuniao.data_inicio = f"{data_str} {hora_str}"
            
        reuniao.link_externo = request.POST.get('link')
        reuniao.save()
        return redirect('calendario') # Redireciona para o calendário
    
    return render(request, 'editar_reuniao.html', {'reuniao': reuniao})

@login_required
def excluir_reuniao(request, id):
    reuniao = get_object_or_404(Reuniao, id=id)
    if reuniao.solicitante == request.user:
        reuniao.delete()
    return redirect('calendario')


# --- VIEW DO FÓRUM (FEED) ---
@login_required
def forum(request):
    form = PostForm()
    
    # 1. Se o usuário enviou um novo post
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.autor = request.user
            post.save()
            return redirect('forum')

    # 2. Configuração dos Filtros e Busca
    posts = Post.objects.all()
    
    # Busca (Search)
    query = request.GET.get('q')
    if query:
        # Busca no conteúdo do post OU no username do autor
        posts = posts.filter(
            Q(conteudo__icontains=query) | 
            Q(autor__username__icontains=query)
        )

    # Filtro de Tipo de Usuário (Alunos ou Mentores)
    filtro_autor = request.GET.get('filtro_autor')
    if filtro_autor == 'mentores':
        posts = posts.filter(autor__perfil__tipo='Mentor')
    elif filtro_autor == 'alunos':
        posts = posts.filter(autor__perfil__tipo='Estudante')

    # Ordenação (Mais Recentes ou Mais Curtidos)
    ordem = request.GET.get('ordem')
    if ordem == 'curtidos':
        # Anota a contagem de likes e ordena por ela (desc), e depois por data (desc)
        posts = posts.annotate(num_likes=Count('likes')).order_by('-num_likes', '-data_criacao')
    else:
        # Padrão: Mais recentes primeiro
        posts = posts.order_by('-data_criacao')

    context = {
        'posts': posts,
        'form': form,
    }
    return render(request, 'forum.html', context)

# --- DETALHES DO POST (COMENTÁRIOS) ---
@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Lista apenas os comentários principais (que não são respostas)
    comentarios_principais = post.comentarios.filter(parent=None).order_by('-data_criacao')
    
    form = ComentarioForm()

    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.autor = request.user
            comentario.post = post
            
            # Lógica da Resposta: Verifica se veio um ID de pai
            parent_id = request.POST.get('parent_id')
            if parent_id:
                parent_obj = Comentario.objects.get(id=parent_id)
                comentario.parent = parent_obj
            
            comentario.save()
            return redirect('post_detail', pk=pk)

    context = {
        'post': post,
        'comentarios': comentarios_principais, # Passamos a lista filtrada
        'form': form
    }
    return render(request, 'post_detail.html', context)

# --- FUNÇÃO DE DAR LIKE (AJAX/Simples) ---
@login_required
def dar_like(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    
    # Redireciona de volta para a mesma página que estava (feed ou detalhe)
    return redirect(request.META.get('HTTP_REFERER', 'forum'))