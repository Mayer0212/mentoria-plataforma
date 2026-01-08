from django import forms
from .models import Reuniao, Tarefa
from django.contrib.auth.models import User
from .models import Perfil, Reuniao, Tarefa # Adicione Perfil aqui

# Formulário para criar Reunião
class ReuniaoForm(forms.ModelForm):
    class Meta:
        model = Reuniao
        # MUDANÇA AQUI: 'convidados' no plural
        fields = ['titulo', 'convidados', 'data_inicio', 'link_externo']
        widgets = {
            'data_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            # Isso transforma a lista em caixinhas de marcar (Checkboxes)
            'convidados': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ReuniaoForm, self).__init__(*args, **kwargs)
        # Removemos o próprio usuário da lista para ele não se auto-convidar
        if user:
            self.fields['convidados'].queryset = User.objects.exclude(id=user.id)
# (Bônus) Já vamos deixar pronto o de Tarefa também
class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        # Adicione 'informacoes' na lista abaixo
        fields = ['titulo', 'informacoes', 'data_prazo']
        
        widgets = {
            'data_prazo': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            # Isso deixa a caixa de texto maior (3 linhas) para digitar bastante coisa
            'informacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': 'Nome de Usuário (Login)',
            'first_name': 'Primeiro Nome',
            'last_name': 'Sobrenome',
        }

class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto', 'profissao', 'empresa', 'formacao', 'idade', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }