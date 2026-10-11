from django.shortcuts import redirect
from django.urls import reverse

class SubscriptionCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Si no está autenticado o es superusuario, dejar pasar de inmediato
        if not request.user.is_authenticated or request.user.is_superuser:
            return self.get_response(request)

        # 2. Si intenta entrar al Admin, dejar pasar
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # 3. Rutas permitidas siempre
        allowed_urls = [
            reverse('logout'), 
            reverse('login'), 
            reverse('cuenta_suspendida')
        ]

        if request.path in allowed_urls:
            return self.get_response(request)

        # 4. Obtener el estudio asociado
        estudio = getattr(request.user, 'perfil_estudio', None)
        if not estudio and request.user.estudios_asociados.exists():
            estudio = request.user.estudios_asociados.first()

        # 5. Aaquí estaba el error: SIN paréntesis () en suscripcion_valida
        if estudio and not estudio.suscripcion_valida:
            return redirect('cuenta_suspendida')

        return self.get_response(request)