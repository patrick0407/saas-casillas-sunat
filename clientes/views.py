import threading
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import ClienteRuc, PerfilEstudio, Comprobante
from .forms import PerfilEstudioForm
from automatizacion.bot_sunat import extraer_historial_sire

# --- CREAR Y GESTIONAR RUCS ---

@login_required
def crear_ruc_view(request):
    if request.method == 'POST':
        try:
            ruc_ingresado = request.POST.get('ruc', '').strip()
            razon_social = request.POST.get('razon_social', '').strip()
            usuario_sol = request.POST.get('usuario_sol', '').strip()
            clave_sol = request.POST.get('clave_sol', '').strip()

            if not ruc_ingresado or not usuario_sol or not clave_sol:
                messages.error(request, "Por favor completa todos los campos requeridos.")
                return render(request, 'crear_ruc.html')

            # 1. Obtener o crear el perfil del estudio del usuario logueado
            estudio, _ = PerfilEstudio.objects.get_or_create(usuario=request.user)

            # 2. Guardar o actualizar en Neon vinculando el estudio
            cliente, creado = ClienteRuc.objects.get_or_create(
                ruc=ruc_ingresado,
                defaults={
                    'estudio': estudio,
                    'razon_social': razon_social,
                    'usuario_sol': usuario_sol,
                    'clave_sol': clave_sol,
                }
            )

            if not creado:
                cliente.estudio = estudio
                cliente.razon_social = razon_social
                cliente.usuario_sol = usuario_sol
                cliente.clave_sol = clave_sol
                cliente.save()
                messages.info(request, f"El RUC {ruc_ingresado} ya existía. Se actualizaron sus datos.")
            else:
                messages.success(request, f"¡RUC {ruc_ingresado} registrado con éxito!")

            # 3. Disparar el bot de SUNAT automáticamente en segundo plano
            try:
                hilo_bot = threading.Thread(target=extraer_historial_sire, args=(cliente.id,))
                hilo_bot.daemon = True
                hilo_bot.start()
            except Exception as e_bot:
                print(f"Aviso al iniciar bot: {str(e_bot)}")

            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f"Error al procesar el formulario: {str(e)}")
            return render(request, 'crear_ruc.html')

    return render(request, 'crear_ruc.html')


# --- VISTAS DE AUTENTICACIÓN ---

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"¡Bienvenido de nuevo, {username}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('login')


# --- VISTAS DEL DASHBOARD Y RUCS ---

def dashboard_casillas(request):
    if not request.user.is_superuser:
        estudio = getattr(request.user, 'perfil_estudio', None)
        if not estudio and hasattr(request.user, 'estudios_asociados') and request.user.estudios_asociados.exists():
            estudio = request.user.estudios_asociados.first()

        if not estudio or not getattr(estudio, 'suscripcion_valida', True):
            return redirect('cuenta_suspendida')

    return render(request, 'bandeja_casilla.html')

@login_required
def dashboard_view(request):
    estudio, _ = PerfilEstudio.objects.get_or_create(usuario=request.user)
    rucs = ClienteRuc.objects.filter(estudio=estudio)
    return render(request, 'dashboard.html', {'estudio': estudio, 'rucs': rucs})

@login_required
def lista_rucs_view(request):
    estudio, _ = PerfilEstudio.objects.get_or_create(usuario=request.user)
    rucs = ClienteRuc.objects.filter(estudio=estudio)
    return render(request, 'lista_rucs.html', {'rucs': rucs})


# --- VISTA DE COMPROBANTES Y FACTURAS (SIRE / RCE) ---

@login_required
def lista_comprobantes(request):
    # Traer todos los comprobantes ordenados por fecha
    comprobantes = Comprobante.objects.all().order_by('-fecha_emision')

    origen_filter = request.GET.get('origen', '').strip()
    anio_filter = request.GET.get('anio', '').strip()
    mes_filter = request.GET.get('mes', '').strip()
    ruc_filter = request.GET.get('ruc', '').strip()

    # Filtrar por Origen solo si el usuario seleccionó uno específico
    if origen_filter:
        comprobantes = comprobantes.filter(origen=origen_filter)

    # Filtrar por Año si viene en los parámetros
    if anio_filter:
        comprobantes = comprobantes.filter(fecha_emision__year=anio_filter)

    # Filtrar por Mes solo si especifica un mes
    if mes_filter:
        comprobantes = comprobantes.filter(fecha_emision__month=mes_filter)

    # Solo filtrar por RUC si el usuario escribió algo en el campo RUC
    if ruc_filter:
        comprobantes = comprobantes.filter(
            Q(ruc_propietario__icontains=ruc_filter) | Q(ruc_contraparte__icontains=ruc_filter)
        )

    context = {
        'comprobantes': comprobantes,
    }
    return render(request, 'comprobantes.html', context)

@login_required
def sincronizar_manual_sunat(request):
    # Intentar obtener el RUC desde la URL, de lo contrario buscar el primer RUC del usuario o del sistema
    ruc_numero = request.GET.get('ruc', '').strip()
    
    if ruc_numero:
        cliente = ClienteRuc.objects.filter(ruc=ruc_numero).first()
    else:
        estudio = getattr(request.user, 'perfil_estudio', None)
        if estudio:
            cliente = ClienteRuc.objects.filter(estudio=estudio).first()
        else:
            cliente = ClienteRuc.objects.first()

    if cliente:
        try:
            extraer_historial_sire(cliente.id)
            messages.success(request, f"¡Sincronización de SUNAT iniciada con éxito para el RUC {cliente.ruc}!")
        except Exception as e:
            messages.error(request, f"Error durante la sincronización: {str(e)}")
    else:
        messages.error(request, "No se encontró ningún RUC registrado para sincronizar.")

    return redirect('lista_comprobantes')


# --- CONFIGURACIÓN DE ESTUDIO Y CUENTA ---

@login_required
def configuracion_estudio_view(request):
    estudio, _ = PerfilEstudio.objects.get_or_create(
        usuario=request.user,
        defaults={'nombre_estudio': f'Estudio de {request.user.username}'}
    )

    if request.method == 'POST':
        form = PerfilEstudioForm(request.POST, instance=estudio)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Configuración del estudio actualizada con éxito!')
            return redirect('configuracion_estudio')
    else:
        form = PerfilEstudioForm(instance=estudio)

    return render(request, 'configuracion_estudio.html', {'form': form, 'estudio': estudio})

def cuenta_suspendida_view(request):
    return render(request, 'cuenta_suspendida.html')