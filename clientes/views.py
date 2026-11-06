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
    # 1. Traer absolutamente TODOS los comprobantes de la base de datos sin filtros
    comprobantes = Comprobante.objects.all().order_by('-id')
    
    # 2. Imprimir en los logs de Render cuántos registros existen realmente
    print(f"--- TOTAL DE COMPROBANTES EN BD: {comprobantes.count()} ---")
    for c in comprobantes:
        print(f"Comprobante ID: {c.id}, Ruc Propietario: {c.ruc_propietario}, Serie: {c.serie}, Monto: {c.monto_total}")

    context = {
        'comprobantes': comprobantes,
    }
    return render(request, 'comprobantes.html', context)

@login_required
def sincronizar_manual_sunat(request):
    # Obtener el estudio del usuario o filtrar todos sus RUCs
    estudio = getattr(request.user, 'perfil_estudio', None)
    
    if estudio:
        rucs_a_sincronizar = ClienteRuc.objects.filter(estudio=estudio)
    else:
        rucs_a_sincronizar = ClienteRuc.objects.filter(usuario=request.user)

    # Si por alguna razón no se encuentran vinculados al usuario directo, tomar todos los RUCs disponibles
    if not rucs_a_sincronizar.exists():
        rucs_a_sincronizar = ClienteRuc.objects.all()

    if rucs_a_sincronizar.exists():
        rucs_exitosos = []
        rucs_fallidos = []

        for cliente in rucs_a_sincronizar:
            try:
                # Ejecuta la extracción del bot SIRE para cada RUC registrado
                extraer_historial_sire(cliente.id)
                rucs_exitosos.append(cliente.ruc)
            except Exception as e:
                rucs_fallidos.append(f"{cliente.ruc} ({str(e)})")

        # Generar mensajes informativos según los resultados
        if rucs_exitosos:
            messages.success(
                request, 
                f"¡Sincronización completada exitosamente para {len(rucs_exitosos)} RUC(s): {', '.join(rucs_exitosos)}!"
            )
        if rucs_fallidos:
            messages.error(
                request, 
                f"Ocurrió un inconveniente al sincronizar los siguientes RUCs: {', '.join(rucs_fallidos)}"
            )
    else:
        messages.error(request, "No se encontró ningún RUC registrado para ejecutar la sincronización.")

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

import pandas as pd
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Comprobante

@login_required
def cargar_excel_comprobantes(request):
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        file = request.FILES['archivo_excel']
        
        try:
            # Leer las columnas del Excel cargado
            df = pd.read_excel(file)
            
            creados = 0
            for _, row in df.iterrows():
                # Leemos los campos (si los nombres de tus columnas cambian, solo ajusta los textos entre comillas)
                ruc_prop = str(row.get('RUC_Propietario', row.get('RUC', '10442302516'))).strip()
                tipo_cp = str(row.get('Tipo_Doc', row.get('Tipo', '01'))).zfill(2)
                serie = str(row.get('Serie', 'F001')).strip()
                numero = str(row.get('Numero', '1')).strip()
                
                # Manejo de la fecha
                fecha_raw = row.get('Fecha_Emision', row.get('Fecha', datetime.now().date()))
                try:
                    fecha_val = pd.to_datetime(fecha_raw).date()
                except Exception:
                    fecha_val = datetime.now().date()

                ruc_contra = str(row.get('RUC_Contraparte', row.get('RUC_Proveedor', '20000000000'))).strip()
                razon_social = str(row.get('Razon_Social', 'CLIENTE FICTICIO S.A.C.')).strip()
                
                try:
                    monto_val = float(str(row.get('Monto_Total', row.get('Monto', 0))).replace(',', ''))
                except ValueError:
                    monto_val = 0.0

                # Insertar o actualizar en Neon
                Comprobante.objects.update_or_create(
                    ruc_propietario=ruc_prop,
                    serie=serie,
                    numero=numero,
                    defaults={
                        'tipo_comprobante': tipo_cp,
                        'fecha_emision': fecha_val,
                        'ruc_contraparte': ruc_contra,
                        'razon_social_contraparte': razon_social,
                        'monto_total': monto_val,
                        'origen': 'EXCEL'
                    }
                )
                creados += 1

            messages.success(request, f"¡Se cargaron {creados} comprobantes exitosamente!")
            return redirect('comprobantes')

        except Exception as e:
            messages.error(request, f"Error al procesar el archivo Excel: {str(e)}")

    return render(request, 'clientes/cargar_excel.html')