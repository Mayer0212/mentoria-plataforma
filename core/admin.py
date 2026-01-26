from django.contrib import admin
from .models import Mensagem, Reuniao, Tarefa, Perfil
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User




class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil do Usuário'

class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Registrando os modelos para aparecerem no painel /admin/
admin.site.register(Mensagem)
admin.site.register(Reuniao)
admin.site.register(Tarefa)