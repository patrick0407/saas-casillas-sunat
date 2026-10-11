from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from clientes.models import PerfilEstudio
from .models import NotificacionCasilla

@login_required
def bandeja_casilla_view(request):
    estudio, _ = PerfilEstudio.objects.get_or_create(
        usuario=request.user,
        defaults={'nombre_estudio': f'Estudio de {request.user.username}'}
    )
    
    # Base Queryset: Notificaciones aisladas por estudio
    notificaciones = NotificacionCasilla.objects.filter(
        cliente_ruc__estudio=estudio
    ).select_related('cliente_ruc').order_by('-fecha_emision')

    # --- 1. Filtro por Búsqueda (Texto) ---
    query = request.GET.get('q', '').strip()
    if query:
        notificaciones = notificaciones.filter(
            Q(asunto__icontains=query) |
            Q(codigo_documento__icontains=query) |
            Q(cliente_ruc__ruc__icontains=query) |
            Q(cliente_ruc__razon_social__icontains=query)
        )

    # --- 2. Filtro por Estado (Leído / No Leído) ---
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro == 'nuevo':
        notificaciones = notificaciones.filter(leido=False)
    elif estado_filtro == 'leido':
        notificaciones = notificaciones.filter(leido=True)

    # --- 3. Filtro por Origen (SUNAT / SUNAFIL) ---
    origen_filtro = request.GET.get('origen', '')
    if origen_filtro:
        notificaciones = notificaciones.filter(origen=origen_filtro)

    # Conteos para tarjetas
    total_count = notificaciones.count()
    sin_leer_count = NotificacionCasilla.objects.filter(cliente_ruc__estudio=estudio, leido=False).count()

    # --- 4. Paginación (10 items por página) ---
    paginator = Paginator(notificaciones, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'sin_leer_count': sin_leer_count,
        'total_count': total_count,
        'query': query,
        'estado_filtro': estado_filtro,
        'origen_filtro': origen_filtro,
    }
    return render(request, 'bandeja_casilla.html', context)


@login_required
def marcar_leido_view(request, notificacion_id):
    estudio = get_object_or_404(PerfilEstudio, usuario=request.user)
    notificacion = get_object_or_404(
        NotificacionCasilla, 
        id=notificacion_id, 
        cliente_ruc__estudio=estudio
    )
    
    notificacion.leido = True
    notificacion.save()
    
    return redirect('bandeja_casilla')