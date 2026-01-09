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
        # Adicionei 'usuario' aqui para o Django saber que esse campo pode ser salvo
        fields = ['titulo', 'informacoes', 'data_prazo', 'usuario']
        
        widgets = {
            'data_prazo': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'informacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            # Estilo para o campo de seleção (caso apareça)
            'usuario': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # 1. Pega o usuário que passamos lá na View
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 2. Configuração Padrão: O campo 'usuario' não é obrigatório no form
        # (porque se estiver vazio, a View vai preencher com o próprio usuário logado)
        self.fields['usuario'].required = False

        # 3. LÓGICA DE PERMISSÃO
        # Se for MENTOR, configuramos o campo para mostrar os Estudantes
        if user and hasattr(user, 'perfil') and user.perfil.tipo == 'Mentor':
            self.fields['usuario'].label = "Designar para (Opcional)"
            self.fields['usuario'].queryset = User.objects.filter(perfil__tipo='Estudante')
            self.fields['usuario'].empty_label = "Para mim mesmo"
        
        # Se for ESTUDANTE, escondemos o campo (ele nem vai saber que existe)
        else:
            self.fields['usuario'].widget = forms.HiddenInput()

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