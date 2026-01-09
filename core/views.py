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
    
    tarefas = Tarefa.objects.filter(usuario=request.user, data_prazo=hoje)
    
    # Conta mensagens não lidas
    notificacoes = Mensagem.objects.filter(destinatario=request.user, lido=False).count()
    
    context = {
        'reunioes': reunioes,
        'tarefas': tarefas,
        'notificacoes': notificacoes,
        'hoje': hoje
    }
    return render(request, 'dashboard.html', context)

@login_required
def criar_reuniao(request):
    if request.method == 'POST':
        form = ReuniaoForm(request.POST, user=request.user)
        if form.is_valid():
            reuniao = form.save(commit=False)
            reuniao.solicitante = request.user
            reuniao.save() # Salva os dados básicos (título, data)
            
            form.save_m2m() # <--- OBRIGATÓRIO: Salva os convidados (Many-to-Many)
            
            messages.success(request, 'Reunião agendada com sucesso!')
            return redirect('dashboard')
    else:
        form = ReuniaoForm(user=request.user)
    
    return render(request, 'criar_reuniao.html', {'form': form})

@login_required
def lista_usuarios(request):
    # Busca usuários que:
    # 1. Enviaram mensagem para mim (mensagens_enviadas__destinatario=eu)
    # OU
    # 2. Receberam mensagem minha (mensagens_recebidas__remetente=eu)
    usuarios = User.objects.filter(
        Q(mensagens_enviadas__destinatario=request.user) | 
        Q(mensagens_recebidas__remetente=request.user)
    ).distinct().exclude(id=request.user.id) # O distinct evita repetição e exclude tira o próprio user

    return render(request, 'lista_usuarios.html', {'usuarios': usuarios})

@login_required
def sala_chat(request, username):
    # Pega o usuário com quem quero falar (ou dá erro 404 se não existir)
    outro_usuario = get_object_or_404(User, username=username)

    # 1. Se eu enviei mensagem no formulário abaixo:
    if request.method == 'POST':
        conteudo = request.POST.get('conteudo')
        if conteudo:
            Mensagem.objects.create(
                remetente=request.user,
                destinatario=outro_usuario,
                conteudo=conteudo
            )
            return redirect('sala_chat', username=username)

    # 2. Busca o histórico de mensagens (Minhas p/ ele OU dele p/ mim)
    mensagens = Mensagem.objects.filter(
        Q(remetente=request.user, destinatario=outro_usuario) | 
        Q(remetente=outro_usuario, destinatario=request.user)
    ).order_by('data_envio')

    # 3. Marca as mensagens DELE como lidas (já que estou vendo elas agora)
    Mensagem.objects.filter(remetente=outro_usuario, destinatario=request.user, lido=False).update(lido=True)

    return render(request, 'chat.html', {
        'outro_usuario': outro_usuario,
        'mensagens': mensagens
    })

@login_required
def criar_tarefa(request):
    if request.method == 'POST':
        form = TarefaForm(request.POST)
        if form.is_valid():
            tarefa = form.save(commit=False)
            tarefa.usuario = request.user
            tarefa.save()
            return redirect('dashboard')
    else:
        form = TarefaForm()
    
    # Reutilizamos o mesmo HTML do formulário da reunião!
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Nova Tarefa'})

@login_required
def calendario(request):
    # Pega TODAS as reuniões futuras (não só as de hoje)
    reunioes = Reuniao.objects.filter(
        Q(solicitante=request.user) | Q(convidados=request.user)
    ).distinct().order_by('data_inicio')

    # Pega TODAS as tarefas não concluídas
    tarefas = Tarefa.objects.filter(usuario=request.user, concluida=False).order_by('data_prazo')

    return render(request, 'calendario.html', {
        'reunioes': reunioes, 
        'tarefas': tarefas
    })

def quem_somos(request):
    return render(request, 'quem_somos.html')

@login_required
def usuarios_online(request):
    # Vamos pegar TODOS os usuários ativos
    # Se quiser filtrar só quem logou recentemente, a lógica seria outra,
    # mas para uma lista de "Membros da Plataforma", pegar todos é melhor.
    
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
        # request.FILES é obrigatório para imagens!
        p_form = PerfilUpdateForm(request.POST, request.FILES, instance=request.user.perfil)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('meu_perfil') # Recarrega a página para mostrar os dados novos
            
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
    return render(request, 'perfil_publico.html', {'perfil_user': perfil_user})

@login_required
def editar_tarefa(request, id):
    tarefa = get_object_or_404(Tarefa, id=id)
    
    # Segurança
    if tarefa.criador != request.user:
        return HttpResponseForbidden("Você não tem permissão.")

    # Se clicou em "Salvar"
    if request.method == 'POST':
        tarefa.titulo = request.POST.get('titulo')
        tarefa.data_prazo = request.POST.get('data')
        tarefa.informacoes = request.POST.get('descricao')
        tarefa.save()
        return redirect('calendario') # ou redirect('calendario') se preferir
    
    # Se clicou no botão "Editar" (GET) -> Abre a página
    return render(request, 'editar_tarefa.html', {'tarefa': tarefa})

@login_required
def excluir_tarefa(request, id):
    tarefa = get_object_or_404(Tarefa, id=id)
    if tarefa.criador == request.user:
        tarefa.delete()
    return redirect('calendario')

# --- NOVAS VIEWS PARA REUNIÕES ---
@login_required
def editar_reuniao(request, id):
    reuniao = get_object_or_404(Reuniao, id=id)
    
    # Segurança
    if reuniao.solicitante != request.user:
        return HttpResponseForbidden("Você não tem permissão.")

    # Se clicou em "Salvar"
    if request.method == 'POST':
        reuniao.titulo = request.POST.get('titulo')
        
        data_str = request.POST.get('data')
        hora_str = request.POST.get('hora') # Vamos pegar a hora separada para facilitar
        
        # Junta data e hora se necessário, ou salva direto dependendo do seu model.
        # Assumindo que seu model usa DateTimeField, o ideal é juntar:
        if data_str and hora_str:
            reuniao.data_inicio = f"{data_str} {hora_str}"
            
        reuniao.link_externo = request.POST.get('link')
        reuniao.save()
        return redirect('calendario')
    
    # Se clicou no botão "Editar" (GET) -> Abre a página
    return render(request, 'editar_reuniao.html', {'reuniao': reuniao})

@login_required
def excluir_reuniao(request, id):
    reuniao = get_object_or_404(Reuniao, id=id)
    if reuniao.solicitante == request.user:
        reuniao.delete()
    return redirect('calendario')