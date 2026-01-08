from django.db import models
from django.contrib.auth.models import User  # <--- ESSA LINHA RESOLVE O ERRO
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- SEUS MODELOS ANTIGOS (Mantive eles aqui) ---
class Mensagem(models.Model):
    remetente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensagens_enviadas')
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensagens_recebidas')
    conteudo = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)
    lido = models.BooleanField(default=False)

    class Meta:
        ordering = ['data_envio'] # Mensagens antigas primeiro

    def __str__(self):
        return f"De {self.remetente} para {self.destinatario}"

class Reuniao(models.Model):
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reunioes_solicitadas')
    # AQUI MUDOU: De ForeignKey para ManyToManyField
    convidados = models.ManyToManyField(User, related_name='reunioes_convidadas')
    
    titulo = models.CharField(max_length=200)
    data_inicio = models.DateTimeField()
    link_externo = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.titulo

class Tarefa(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    informacoes = models.TextField(blank=True, null=True) 
    data_prazo = models.DateField()
    concluida = models.BooleanField(default=False)
    criador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tarefas')

    def __str__(self):
        return self.titulo

# --- NOVO MODELO: PERFIL ---
class Perfil(models.Model):
    # Aqui voltamos a usar User direto, pois importamos ele lá em cima
    TIPO_USUARIO_CHOICES = (
        ('Estudante', 'Estudante'),
        ('Mentor', 'Mentor'),
    )
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_USUARIO_CHOICES, 
        default='Estudante',
        verbose_name="Tipo de Usuário"
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    bio = models.TextField(blank=True, null=True, verbose_name="Sobre mim")
    idade = models.PositiveIntegerField(blank=True, null=True)
    profissao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Profissão")
    formacao = models.CharField(max_length=150, blank=True, null=True, verbose_name="Formação Acadêmica")
    empresa = models.CharField(max_length=100, blank=True, null=True)
    foto = models.ImageField(upload_to='perfil_fotos/', blank=True, null=True, default='default.jpg')

    def __str__(self):
        return f'{self.user.username} Perfil'

# --- SINAIS AUTOMÁTICOS ---
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.perfil.save()
    except:
        Perfil.objects.create(user=instance)