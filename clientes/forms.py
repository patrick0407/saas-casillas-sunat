from django import forms
from .models import PerfilEstudio

class PerfilEstudioForm(forms.ModelForm):
    class Meta:
        model = PerfilEstudio
        fields = ['nombre_estudio', 'email_smtp', 'password_smtp', 'use_custom_email']
        widgets = {
            'nombre_estudio': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none text-sm'
            }),
            'email_smtp': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none text-sm',
                'placeholder': 'ejemplo@miestudio.com'
            }),
            'password_smtp': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none text-sm',
                'placeholder': 'Contraseña de aplicación (16 caracteres)'
            }),
            'use_custom_email': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500'
            }),
        }