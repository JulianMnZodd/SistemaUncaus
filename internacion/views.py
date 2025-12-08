from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import uuid
from habitaciones.models import Cama, Habitacion
from .forms import DiagnosticoForm, AsignarCamaForm
from .models import Paciente, Medico, Enfermero, Internacion
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from personal.decoradores_permisos import (
    medico_or_enfermero_or_staff_required,
    medico_or_staff_required,
    recepcionista_or_staff_required,
    enfermero_or_staff_required,
    staff_required
)


from django.db import transaction

@login_required
@recepcionista_or_staff_required(redirect_url="lista_habitaciones")
def asignar_cama(request, idcama):
    pacientes_list = Paciente.objects.all()
    paginator = Paginator(pacientes_list, 10)
    page_number = request.GET.get("page")
    try:
        pacientes = paginator.page(page_number)
    except PageNotAnInteger:
        pacientes = paginator.page(1)
    except EmptyPage:
        pacientes = paginator.page(paginator.num_pages)

    if request.method == "POST":
        form = AsignarCamaForm(request.POST)
        if form.is_valid():
            paciente_id = form.cleaned_data["paciente_id"]
            paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
            nota_ingreso = form.cleaned_data["nota_ingreso"]
            action = request.POST.get("action")

            with transaction.atomic():
                # Bloquea la cama hasta que termine la transacción
                cama = Cama.objects.select_for_update().get(idcama=idcama)
                if cama.estado == "O":
                    messages.error(request, "La cama ya no está disponible.")
                    return redirect("lista_habitaciones")

                if action == "asignar":
                    Internacion.objects.create(
                        idpaciente=paciente,
                        fecha_admision=timezone.now(),
                        cama=cama,
                        nota_ingreso=nota_ingreso,
                    )
                    cama.estado = "O"
                    cama.save()
                    messages.success(request, "Cama asignada correctamente.")
                    return redirect("lista_habitaciones")
                elif action == "generar_pdf":
                    return generar_consentimiento_pdf(request, paciente.idpaciente)
    else:
        form = AsignarCamaForm()

    cama = get_object_or_404(Cama, idcama=idcama)  # Para GET, sin lock
    return render(
        request,
        "asignar_cama.html",
        {
            "form": form,
            "cama": cama,
            "pacientes": pacientes,
        },
    )

@login_required
def generar_consentimiento(request):
    if request.method == "POST":
        form = AsignarCamaForm(request.POST)
        if form.is_valid():
            paciente = form.cleaned_data["idpaciente"]
            return generar_consentimiento_pdf(request, paciente.id)
    else:
        return redirect("asignar_cama")


@login_required
def seleccionar_cama(request, paciente_id):
    paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
    habitaciones = Habitacion.objects.prefetch_related(
        "camas"
    ).all()  # Obtener todas las habitaciones con sus camas
    return render(
        request,
        "seleccionar_cama.html",
        {"habitaciones": habitaciones, "paciente": paciente},
    )


@login_required
@medico_or_enfermero_or_staff_required(redirect_url="lista_habitaciones")
def listar_internaciones(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    # Obtener parámetro de búsqueda
    search_query = request.GET.get('search', '').strip()
    
    # Filtro base: solo internaciones activas
    internaciones_list = Internacion.objects.filter(fecha_alta__isnull=True)
    
    # Aplicar búsqueda si hay query
    if search_query:
        internaciones_list = internaciones_list.filter(
            Q(idpaciente__nombre__icontains=search_query) |
            Q(idpaciente__apellido__icontains=search_query) |
            Q(idpaciente__dni__icontains=search_query)
        )
    
    internaciones_list = internaciones_list.order_by('-fecha_admision')
    
    # Paginación: 10 internaciones por página
    paginator = Paginator(internaciones_list, 10)
    page_number = request.GET.get('page')
    internaciones = paginator.get_page(page_number)
    
    es_medico = hasattr(request.user, "medico")
    es_enfermero = hasattr(request.user, "enfermero")
    return render(
        request,
        "listar_internaciones.html",
        {
            "internaciones": internaciones,
            "es_medico": es_medico,
            "es_enfermero": es_enfermero,
            "search_query": search_query,
        },
    )


@login_required
@medico_or_staff_required(redirect_url="lista_habitaciones")
def crear_diagnostico(request, internacion_id):
    internacion = get_object_or_404(Internacion, idinternacion=internacion_id)
    paciente = internacion.idpaciente
    medico = get_object_or_404(
        Medico, persona=request.user
    )  # Usar el campo correcto para obtener el médico logeado

    # Verificar si ya existe un diagnóstico para esta internación
    if Diagnostico.objects.filter(idinternacion=internacion).exists():
        return redirect(
            "detalle_diagnostico", internacion_id=internacion.idinternacion
        )  # Redirigir al detalle del diagnóstico si ya existe

    if request.method == "POST":
        form = DiagnosticoForm(request.POST)
        if form.is_valid():
            diagnostico = form.save(commit=False)
            diagnostico.idpaciente = paciente
            diagnostico.idmedico = medico
            diagnostico.idinternacion = (
                internacion  # Asociar el diagnóstico con la internación actual
            )
            idmedico_derivado = form.cleaned_data.get("idmedico_derivado")
            if idmedico_derivado:
                diagnostico.idmedico_derivado = idmedico_derivado
            diagnostico.save()
            return redirect(
                "detalle_diagnostico", internacion_id=internacion.idinternacion
            )  # Redirigir al detalle del diagnóstico
    else:
        form = DiagnosticoForm()

    return render(
        request, "crear_diagnostico.html", {"form": form, "paciente": paciente}
    )


@login_required
@medico_or_staff_required(redirect_url="lista_habitaciones")
def editar_diagnostico(request, diagnostico_id):
    # Obtener el diagnóstico a editar
    diagnostico = get_object_or_404(Diagnostico, pk=diagnostico_id)

    if request.method == "POST":
        # Procesar el formulario enviado
        form = DiagnosticoForm(request.POST, instance=diagnostico)
        if form.is_valid():
            print("Formulario válido:", form.cleaned_data)
            form.save()  # Guardar los cambios directamente
            return redirect(
                "detalle_diagnostico",
                internacion_id=diagnostico.idinternacion.idinternacion,
            )
    else:
        # Mostrar el formulario con los datos actuales del diagnóstico
        form = DiagnosticoForm(instance=diagnostico)

    context = {
        "form": form,
        "paciente": diagnostico.idpaciente,
        "diagnostico": diagnostico,
    }
    return render(request, "editar_diagnostico.html", context)


from .models import Diagnostico


@login_required
@medico_or_enfermero_or_staff_required(redirect_url="lista_habitaciones")
def detalle_diagnostico(request, internacion_id):
    internacion = get_object_or_404(Internacion, idinternacion=internacion_id)
    diagnostico = get_object_or_404(Diagnostico, idinternacion=internacion)
    return render(
        request,
        "detalle_diagnostico.html",
        {"internacion": internacion, "diagnostico": diagnostico},
    )


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from .forms import SeguimientoForm, MedicacionForm, SignosVitalesForm
from .models import Paciente, Enfermero, Seguimiento, Medicacion, SignosVitales


@login_required
@enfermero_or_staff_required(redirect_url="listar_internaciones")
def seguimiento(request, internacion_id):
    internacion = get_object_or_404(Internacion, idinternacion=internacion_id)
    enfermero = Enfermero.objects.filter(persona=request.user).first()
    if not enfermero:
        raise Http404("No se encontró un enfermero asociado al usuario.")
    # Usar el campo correcto para obtener el enfermero logeado

    MedicacionFormSet = inlineformset_factory(
        Seguimiento, Medicacion, form=MedicacionForm, extra=1, can_delete=False
    )
    SignosVitalesFormSet = inlineformset_factory(
        Seguimiento, SignosVitales, form=SignosVitalesForm, extra=1, can_delete=False
    )

    if request.method == "POST":
        form = SeguimientoForm(request.POST)
        medicacion_formset = MedicacionFormSet(request.POST, instance=Seguimiento())
        signos_vitales_formset = SignosVitalesFormSet(
            request.POST, instance=Seguimiento()
        )

        if (
            form.is_valid()
            and medicacion_formset.is_valid()
            and signos_vitales_formset.is_valid()
        ):
            seguimiento = form.save(commit=False)
            seguimiento.idinternacion = internacion
            seguimiento.idenfermero = enfermero
            seguimiento.save()
            medicacion_formset.instance = seguimiento
            signos_vitales_formset.instance = seguimiento
            medicacion_formset.save()
            signos_vitales_formset.save()
            messages.success(request, "Seguimiento creado exitosamente.")
            return redirect('listar_seguimientos', internacion_id=internacion.idinternacion)
    else:
        form = SeguimientoForm()
        medicacion_formset = MedicacionFormSet(instance=Seguimiento())
        signos_vitales_formset = SignosVitalesFormSet(instance=Seguimiento())

    return render(
        request,
        "seguimiento.html",
        {
            "form": form,
            "medicacion_formset": medicacion_formset,
            "signos_vitales_formset": signos_vitales_formset,
            "internacion": internacion,
            "enfermero": enfermero,
        },
    )

@login_required
@enfermero_or_staff_required(redirect_url="listar_internaciones")
def editar_seguimiento(request, seguimiento_id):
    seguimiento = get_object_or_404(Seguimiento, pk=seguimiento_id)

    MedicacionFormSet = inlineformset_factory(
        Seguimiento, Medicacion, form=MedicacionForm, extra=0, can_delete=False
    )
    SignosVitalesFormSet = inlineformset_factory(
        Seguimiento, SignosVitales, form=SignosVitalesForm, extra=0, can_delete=False
    )

    if request.method == "POST":
        form = SeguimientoForm(request.POST, instance=seguimiento)
        medicacion_formset = MedicacionFormSet(request.POST, instance=seguimiento)
        signos_vitales_formset = SignosVitalesFormSet(request.POST, instance=seguimiento)

        if form.is_valid() and medicacion_formset.is_valid() and signos_vitales_formset.is_valid():
            form.save()
            medicacion_formset.save()
            signos_vitales_formset.save()
            messages.success(request, "Seguimiento actualizado exitosamente.")
            return redirect('listar_seguimientos', internacion_id=seguimiento.idinternacion.idinternacion)
    else:
        form = SeguimientoForm(instance=seguimiento)
        medicacion_formset = MedicacionFormSet(instance=seguimiento)
        signos_vitales_formset = SignosVitalesFormSet(instance=seguimiento)

    return render(request, 'editar_seguimiento.html', {
        'form': form,
        'medicacion_formset': medicacion_formset,
        'signos_vitales_formset': signos_vitales_formset,
        'seguimiento': seguimiento,
    })

@login_required
@staff_required(redirect_url="listar_internaciones")
def eliminar_seguimiento(request, seguimiento_id):
    seguimiento = get_object_or_404(Seguimiento, idseguimiento=seguimiento_id)
    seguimiento.delete()
    messages.success(request, "Seguimiento eliminado exitosamente.")
    return redirect("listar_internaciones")
    
    
    
@login_required
@medico_or_enfermero_or_staff_required(redirect_url="listar_internaciones")
def listar_seguimientos(request, internacion_id):
    internacion = get_object_or_404(Internacion, idinternacion=internacion_id)
    seguimientos = Seguimiento.objects.filter(idinternacion=internacion)
    return render(
        request,
        "listar_seguimientos.html",
        {
            "internacion": internacion,
            "seguimientos": seguimientos,
        },
    )


@login_required
@medico_or_enfermero_or_staff_required(redirect_url="listar_internaciones")
def seguimiento_detalles(request, seguimiento_id):
    seguimiento = get_object_or_404(Seguimiento, idseguimiento=seguimiento_id)
    return render(
        request,
        "seguimiento_detalles.html",
        {
            "seguimiento": seguimiento,
        },
    )


from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from .utils_reportes import agregar_encabezado_bedwise, agregar_pie_pagina


@login_required
def generar_consentimiento_pdf(request, paciente_id):
    paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
    
    # Generar un ID único para este documento
    doc_id = f"CON{paciente_id}-{uuid.uuid4()}"

    # Crear el objeto HttpResponse con el encabezado PDF adecuado.
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="consentimiento_{paciente.idpaciente}.pdf"'
    )

    # Crear el objeto PDF usando el HttpResponse como "archivo".
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Usar la función de utilidad para agregar el encabezado
    agregar_encabezado_bedwise(
        p, "ACTA DE CONSENTIMIENTO PARA INTERNACIÓN", width, height
    )

    margin = 50
    bottom_margin = 120
    y_position = height - 140
    spacing = 20
    
    # Datos del paciente o representante
    p.setFont("Helvetica", 11)
    patient_info = [
        f"Nombre del Paciente: {paciente.nombre} {paciente.apellido}",
        f"Fecha de Nacimiento: {paciente.fecha_nacimiento}",
        f"Dirección: {paciente.domicilio}",
        f"Teléfono: {paciente.telefono}",
        f"Email: {paciente.email}",
        f"Documento de Identidad: {paciente.dni}",
        "Relación (si es representante): _________________"
    ]
    
    for line in patient_info:
        p.drawString(margin, y_position, line)
        y_position -= spacing
    
    y_position -= spacing

    # Datos del establecimiento y personal médico
    p.drawString(margin, y_position, "Médico Responsable: _________")
    y_position -= spacing
    p.drawString(margin, y_position, "Registro Profesional: _________")
    y_position -= spacing * 2

    # Exposición de la información
    text = p.beginText(margin, y_position)
    text.setFont("Helvetica", 11)
    exposicion = [
        "Yo, el suscrito, declaro haber sido informado de manera clara y comprensible",
        "sobre la situación médica que requiere la internación, incluyendo:",
        "  - Diagnóstico y necesidad del tratamiento hospitalario.",
        "  - Procedimientos, exámenes y terapias previstos.",
        "  - Riesgos, complicaciones y beneficios asociados.",
        "  - Alternativas de tratamiento y posibilidad de realizar consultas adicionales.",
        "He tenido la oportunidad de formular preguntas, las cuales han sido contestadas",
        "a mi entera satisfacción.",
    ]
    for line in exposicion:
        text.textLine(line)
    p.drawText(text)
    
    y_position -= (len(exposicion) * 14) + spacing

    # Consentimiento
    text = p.beginText(margin, y_position)
    text.setFont("Helvetica", 11)
    # consentimiento = [
    #     "Doy mi consentimiento libre y voluntario para la internación y la realización",
    #     "de los procedimientos y tratamientos que el personal médico estime necesarios,",
    #     "exonerando de responsabilidad al personal del establecimiento, siempre que",
    #     "se actúe conforme a la normatividad vigente y al debido proceder profesional.",
    # ]
    # for line in consentimiento:
    #     text.textLine(line)
    # p.drawText(text)
    
    # y_position -= (len(consentimiento) * 14) + spacing * 2

    # Firmas y fechas
    if y_position < bottom_margin + 100:
        agregar_pie_pagina(p, width, 1, 2, doc_id)
        p.showPage()
        agregar_encabezado_bedwise(p, "ACTA DE CONSENTIMIENTO PARA INTERNACIÓN", width, height)
        y_position = height - 140
    
    p.setFont("Helvetica", 11)
    p.drawString(margin, y_position, "Firma del Paciente o Representante: ______")
    y_position -= spacing
    p.drawString(margin, y_position, "Fecha: __________________________")
    y_position -= spacing * 2
    p.drawString(margin, y_position, "Firma del Médico: ___________________")
    y_position -= spacing
    p.drawString(margin, y_position, "Fecha: ____________________")

    # Agregar pie de página con código QR para validación
    agregar_pie_pagina(p, width, 1, 1, doc_id)

    # Finalizar el PDF
    p.showPage()
    p.save()

    return response


from django import forms


class InformeInternacionesForm(forms.Form):
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Fecha de Inicio",
        required=True,
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Fecha de Fin",
        required=True,
    )


@login_required
@medico_or_enfermero_or_staff_required(redirect_url="listar_internaciones")
def generar_informe_internaciones(request):
    if request.method == "POST":
        form = InformeInternacionesForm(request.POST)
        if form.is_valid():
            fecha_inicio = form.cleaned_data["fecha_inicio"]
            fecha_fin = form.cleaned_data["fecha_fin"]
            
            # Generar un ID único para este documento
            doc_id = f"LISTI{fecha_inicio.strftime('%Y%m%d')}-{uuid.uuid4()}"

            # Validar que fecha_inicio no sea posterior a fecha_fin
            if fecha_inicio > fecha_fin:
                messages.error(
                    request,
                    "La fecha de inicio no puede ser posterior a la fecha de fin.",
                )
                return redirect("listar_internaciones")

            # Obtener todas las internaciones en el rango de fechas
            internaciones = Internacion.objects.filter(
                fecha_admision__gte=fecha_inicio, fecha_admision__lte=fecha_fin
            ).order_by("-fecha_admision")

            if not internaciones:
                messages.warning(
                    request,
                    "No se encontraron internaciones en el rango de fechas seleccionado.",
                )
                return redirect("listar_internaciones")

            # Crear el objeto HttpResponse con el encabezado PDF adecuado
            response = HttpResponse(content_type="application/pdf")
            filename = f"informe_internaciones_{fecha_inicio.strftime('%Y-%m-%d')}_a_{fecha_fin.strftime('%Y-%m-%d')}.pdf"
            response["Content-Disposition"] = (
                f'attachment; filename="{filename}"'
            )

            # Crear el objeto PDF usando el HttpResponse como "archivo"
            p = canvas.Canvas(response, pagesize=letter)
            width, height = letter

            # Usar la función de utilidad para agregar el encabezado
            agregar_encabezado_bedwise(
                p, 
                f"Informe de Internaciones ({fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')})",
                width,
                height
            )

            margin = 50
            bottom_margin = 120
            
            # Encabezados de la tabla
            p.setFont("Helvetica-Bold", 10)
            p.drawString(margin, height - 140, "Paciente")
            p.drawString(margin + 130, height - 140, "F. Ingreso")
            p.drawString(margin + 220, height - 140, "F. Alta")
            p.drawString(margin + 310, height - 140, "Motivo")

            # Datos de la tabla
            y = height - 160
            p.setFont("Helvetica", 9)
            for internacion in internaciones:
                # Truncar motivo si es muy largo (ajustado para el espacio disponible)
                motivo = internacion.nota_ingreso[:50] + "..." if len(internacion.nota_ingreso) > 50 else internacion.nota_ingreso
                
                # Nombre del paciente (truncado si es necesario)
                nombre_completo = f"{internacion.idpaciente.nombre} {internacion.idpaciente.apellido}"
                nombre = nombre_completo[:18] + "..." if len(nombre_completo) > 18 else nombre_completo
                
                p.drawString(margin, y, nombre)
                p.drawString(
                    margin + 130, y, str(internacion.fecha_admision.strftime("%d/%m/%Y"))
                )
                p.drawString(
                    margin + 220,
                    y,
                    (
                        internacion.fecha_alta.strftime("%d/%m/%Y")
                        if internacion.fecha_alta
                        else "En curso"
                    ),
                )
                p.drawString(margin + 310, y, motivo)
                y -= 18

                if y < bottom_margin + 100:  # Salto de página si no hay espacio
                    agregar_pie_pagina(p, width, p.getPageNumber(), 0)
                    p.showPage()
                    agregar_encabezado_bedwise(
                        p, 
                        f"Informe de Internaciones ({fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')})",
                        width,
                        height
                    )
                    # Repetir encabezados en la nueva página
                    p.setFont("Helvetica-Bold", 10)
                    p.drawString(margin, height - 140, "Paciente")
                    p.drawString(margin + 130, height - 140, "F. Ingreso")
                    p.drawString(margin + 220, height - 140, "F. Alta")
                    p.drawString(margin + 310, height - 140, "Motivo")
                    y = height - 160
                    p.setFont("Helvetica", 9)

            # Agregar estadísticas
            total_internaciones = internaciones.count()
            altas = internaciones.filter(fecha_alta__isnull=False).count()
            en_curso = internaciones.filter(fecha_alta__isnull=True).count()
            
            if y < bottom_margin + 80:
                agregar_pie_pagina(p, width, p.getPageNumber(), 0)
                p.showPage()
                agregar_encabezado_bedwise(
                    p, 
                    f"Informe de Internaciones ({fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')})",
                    width,
                    height
                )
                y = height - 140
            
            y -= 20
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y, "Resumen:")
            y -= 20
            p.setFont("Helvetica", 10)
            p.drawString(margin + 20, y, f"Total internaciones: {total_internaciones}")
            y -= 18
            p.drawString(margin + 20, y, f"Internaciones finalizadas: {altas}")
            y -= 18
            p.drawString(margin + 20, y, f"Internaciones en curso: {en_curso}")
            
            # Agregar pie de página final
            agregar_pie_pagina(p, width, 1, 1, doc_id)

            # Finalizar el PDF
            p.save()
            return response

    # Si no es POST, redirigir a listar_internaciones
    return redirect("listar_internaciones")


@login_required
def generar_informe_internacion(request, internacion_id):
    # Obtener la internación y sus seguimientos
    internacion = get_object_or_404(Internacion, idinternacion=internacion_id)
    seguimientos = Seguimiento.objects.filter(idinternacion=internacion).order_by(
        "fecha"
    )
    
    # Obtener diagnóstico si existe
    diagnostico = internacion.diagnostico_set.first()
    
    # Generar un ID único para este documento
    doc_id = f"INT{internacion_id}-{uuid.uuid4()}"

    # Crear el objeto HttpResponse con el encabezado PDF adecuado
    response = HttpResponse(content_type="application/pdf")
    paciente_nombre = f"{internacion.idpaciente.apellido}_{internacion.idpaciente.nombre}".replace(" ", "_")
    filename = f"informe_internacion_{internacion.idinternacion}_{paciente_nombre}.pdf"
    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    # Crear el objeto PDF usando el HttpResponse como "archivo"
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Usar la función de utilidad para agregar el encabezado
    titulo = f"Informe de Internación - {internacion.idpaciente.apellido}, {internacion.idpaciente.nombre}"
    agregar_encabezado_bedwise(p, titulo, width, height)

    margin = 50
    bottom_margin = 120
    spacing = 18
    
    # Información general de la internación
    p.setFont("Helvetica", 11)
    y = height - 140
    p.drawString(
        margin,
        y,
        f"Fecha de Ingreso: {internacion.fecha_admision.strftime('%d/%m/%Y %H:%M')}",
    )
    y -= spacing
    p.drawString(
        margin,
        y,
        f"Fecha de Alta: {internacion.fecha_alta.strftime('%d/%m/%Y %H:%M') if internacion.fecha_alta else 'N/A'}",
    )
    y -= spacing
    p.drawString(margin, y, f"Motivo de Internación: {internacion.nota_ingreso}")
    y -= spacing * 2

    # Agregar diagnóstico si existe
    if diagnostico:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(margin, y, "Diagnóstico:")
        y -= spacing
        
        p.setFont("Helvetica", 10)
        p.drawString(margin + 20, y, f"Fecha: {diagnostico.fecha.strftime('%d/%m/%Y %H:%M')}")
        y -= 15
        p.drawString(margin + 20, y, f"Detalles: {diagnostico.detalles}")
        y -= 15
        p.drawString(margin + 20, y, f"Gravedad: {diagnostico.gravedad}")
        y -= 15
        p.drawString(margin + 20, y, f"Tratamiento: {diagnostico.tratamiento}")
        y -= 15
        
        if diagnostico.idmedico:
            p.drawString(margin + 20, y, f"Médico: Dr. {diagnostico.idmedico.persona.first_name} {diagnostico.idmedico.persona.last_name}")
            y -= 15
        
        if diagnostico.idmedico_derivado:
            p.drawString(margin + 20, y, f"Médico Derivado: Dr. {diagnostico.idmedico_derivado.persona.first_name} {diagnostico.idmedico_derivado.persona.last_name}")
            y -= 15
        
        y -= spacing * 2

    # Detalles del seguimiento
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y, "Seguimientos:")
    y -= spacing

    p.setFont("Helvetica", 10)
    for seguimiento in seguimientos:
        if y < bottom_margin + 120:  # Salto de página si no hay espacio
            agregar_pie_pagina(p, width, p.getPageNumber(), 0)
            p.showPage()
            agregar_encabezado_bedwise(p, titulo, width, height)
            y = height - 140
            p.setFont("Helvetica", 10)

        p.drawString(margin, y, f"- Fecha: {seguimiento.fecha.strftime('%d/%m/%Y %H:%M')}")
        y -= 15
        p.drawString(margin + 20, y, f"  Observación: {seguimiento.observacion}")
        y -= 15

        # Medicación
        if seguimiento.medicaciones.exists():
            p.drawString(margin + 20, y, "  Medicación:")
            y -= 15
            for medicacion in seguimiento.medicaciones.all():
                if y < bottom_margin:
                    agregar_pie_pagina(p, width, p.getPageNumber(), 0)
                    p.showPage()
                    agregar_encabezado_bedwise(p, titulo, width, height)
                    y = height - 140
                    p.setFont("Helvetica", 10)
                
                p.drawString(
                    margin + 40,
                    y,
                    f"- {medicacion.tipo}: {medicacion.nombre} a las {medicacion.hora_medicacion.strftime('%H:%M')}",
                )
                y -= 15

        # Signos vitales
        if seguimiento.signos_vitales.exists():
            if y < bottom_margin:
                agregar_pie_pagina(p, width, p.getPageNumber(), 0)
                p.showPage()
                agregar_encabezado_bedwise(p, titulo, width, height)
                y = height - 140
                p.setFont("Helvetica", 10)
            
            p.drawString(margin + 20, y, "  Signos Vitales:")
            y -= 15
            for signo in seguimiento.signos_vitales.all():
                if y < bottom_margin:
                    agregar_pie_pagina(p, width, p.getPageNumber(), 0)
                    p.showPage()
                    agregar_encabezado_bedwise(p, titulo, width, height)
                    y = height - 140
                    p.setFont("Helvetica", 10)
                
                p.drawString(
                    margin + 40,
                    y,
                    f"- Temp: {signo.temperatura_corporal}°C, Pulso: {signo.pulso}, FR: {signo.frecuencia_respiratoria}",
                )
                y -= 15

        y -= 10  # Espacio entre seguimientos
    
    # Calcular duración de la internación
    duracion = ""
    if internacion.fecha_alta:
        dias = (internacion.fecha_alta.date() - internacion.fecha_admision.date()).days
        duracion = f"{dias} días"
    else:
        dias = (timezone.now().date() - internacion.fecha_admision.date()).days
        duracion = f"{dias} días (en curso)"
    
    if y < bottom_margin + 20:
        agregar_pie_pagina(p, width, p.getPageNumber(), 0)
        p.showPage()
        agregar_encabezado_bedwise(p, titulo, width, height)
        y = height - 140
    
    p.setFont("Helvetica", 10)
    p.drawString(margin, y, f"Duración de la internación: {duracion}")
    
    # Agregar pie de página final
    agregar_pie_pagina(p, width, 1, 1, doc_id)
    
    # Finalizar el PDF
    p.save()
    return response


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Cama, Internacion

from .models import Seguimiento


@login_required
@enfermero_or_staff_required(redirect_url="lista_habitaciones")
def derivar_paciente(request):
    if request.method == "POST":
        idcama_origen = request.POST.get("idcama_origen")
        idcama_destino = request.POST.get("idcama_destino")

        # Verificar que ambos parámetros estén presentes
        if not idcama_origen or not idcama_destino:
            messages.error(request, "Debe seleccionar ambas camas (origen y destino)")
            return redirect("lista_habitaciones")

        # Obtener las camas
        try:
            cama_origen = get_object_or_404(Cama, idcama=idcama_origen)
            cama_destino = get_object_or_404(Cama, idcama=idcama_destino)
        except:
            messages.error(request, "No se encontraron las camas especificadas")
            return redirect("lista_habitaciones")

        # Verificar que la cama de destino esté libre
        if cama_destino.estado != "L":
            messages.error(request, "La cama de destino no está disponible")
            return redirect("lista_habitaciones")

        # Obtener la internación activa del paciente en la cama de origen
        internacion = Internacion.objects.filter(
            cama=cama_origen, fecha_alta__isnull=True
        ).first()
        if not internacion:
            messages.error(request, "No se encontró paciente en la cama de origen")
            return redirect("lista_habitaciones")

        try:
            # Registrar la derivación como un seguimiento
            enfermero = Enfermero.objects.filter(persona=request.user).first()

            # Registrar la derivación como un seguimiento
            Seguimiento.objects.create(
                idinternacion=internacion,
                idenfermero=enfermero,
                observacion=f"Derivación de sector: {cama_origen.habitacion.idsector}, habitacion: {cama_origen.habitacion}, cama: {cama_origen} a sector: {cama_destino.habitacion.idsector}, habitacion: {cama_destino.habitacion}, cama: {cama_destino}",
                cama_origen=cama_origen,
                cama_destino=cama_destino,
            )

            # Actualizar la internación para mover al paciente a la cama de destino
            internacion.cama = cama_destino
            internacion.save()

            # Actualizar los estados de las camas
            cama_origen.estado = "L"  # Liberar la cama de origen
            cama_origen.save()

            cama_destino.estado = "O"  # Ocupada la cama de destino
            cama_destino.save()

            messages.success(request, "Derivación realizada exitosamente")
            return redirect("lista_habitaciones")

        except Exception as e:
            messages.error(
                request, f"Ocurrió un error al procesar la derivación: {str(e)}"
            )
            return redirect("lista_habitaciones")

    return redirect("lista_habitaciones")


from datetime import datetime


@login_required
def generar_informe_alta(request, internacion_id):
    internacion = get_object_or_404(Internacion, idinternacion=internacion_id)
    
    # Generar un ID único para este documento
    doc_id = f"ALTA{internacion_id}-{uuid.uuid4()}"

    response = HttpResponse(content_type="application/pdf")
    paciente_nombre = f"{internacion.idpaciente.apellido}_{internacion.idpaciente.nombre}".replace(" ", "_")
    fecha_alta_str = internacion.fecha_alta.strftime('%Y-%m-%d') if internacion.fecha_alta else "sin_fecha"
    filename = f"informe_alta_{internacion.idinternacion}_{paciente_nombre}_{fecha_alta_str}.pdf"
    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Configuración inicial
    p.setTitle(f"Informe de Alta Médica - {internacion.idpaciente.apellido}")
    margin = 50
    bottom_margin = 120  # Espacio reservado para pie de página
    
    # Usar la función de utilidad para agregar el encabezado
    agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
    
    y_position = height - 140
    spacing = 18

    # Información del paciente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y_position, "DATOS DEL PACIENTE:")
    y_position -= spacing + 5

    p.setFont("Helvetica", 11)
    patient_data = [
        f"Nombre: {internacion.idpaciente.nombre} {internacion.idpaciente.apellido}",
        f"DNI: {internacion.idpaciente.dni}",
        f"Fecha de Nacimiento: {internacion.idpaciente.fecha_nacimiento.strftime('%d/%m/%Y')}",
        f"Fecha de Admisión: {internacion.fecha_admision.strftime('%d/%m/%Y %H:%M')}",
        (
            f"Fecha de Alta: {internacion.fecha_alta.strftime('%d/%m/%Y %H:%M')}"
            if internacion.fecha_alta
            else "Fecha de Alta: Pendiente"
        ),
    ]

    for line in patient_data:
        if y_position < bottom_margin:
            agregar_pie_pagina(p, width, 1, 2, doc_id)
            p.showPage()
            agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
            y_position = height - 140
        
        p.drawString(margin + 10, y_position, line)
        y_position -= spacing

    y_position -= spacing

    # Motivo de internación
    if y_position < bottom_margin:
        agregar_pie_pagina(p, width, 1, 2, doc_id)
        p.showPage()
        agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
        y_position = height - 140
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y_position, "MOTIVO DE INTERNACIÓN:")
    y_position -= spacing + 5
    p.setFont("Helvetica", 11)
    
    # Dividir el motivo en líneas si es muy largo
    motivo = internacion.nota_ingreso
    max_width = width - (margin * 2 + 20)
    motivo_lines = []
    
    if p.stringWidth(motivo, "Helvetica", 11) > max_width:
        words = motivo.split()
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if p.stringWidth(test_line, "Helvetica", 11) <= max_width:
                current_line = test_line
            else:
                motivo_lines.append(current_line)
                current_line = word
        if current_line:
            motivo_lines.append(current_line)
    else:
        motivo_lines = [motivo]
    
    for line in motivo_lines:
        if y_position < bottom_margin:
            agregar_pie_pagina(p, width, 1, 2, doc_id)
            p.showPage()
            agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
            y_position = height - 140
        p.drawString(margin + 10, y_position, line)
        y_position -= spacing
    
    y_position -= spacing

    # Diagnóstico y tratamiento
    diagnostico = internacion.diagnostico_set.order_by("-fecha").first()
    if diagnostico:
        if y_position < bottom_margin + 100:
            agregar_pie_pagina(p, width, 1, 2, doc_id)
            p.showPage()
            agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
            y_position = height - 140
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(margin, y_position, "DIAGNÓSTICO PRINCIPAL:")
        y_position -= spacing + 5
        p.setFont("Helvetica", 11)
        
        diagnostic_data = [
            f"Fecha: {diagnostico.fecha.strftime('%d/%m/%Y %H:%M')}",
            f"Detalles: {diagnostico.detalles}",
            f"Gravedad: {diagnostico.gravedad}",
            f"Tratamiento: {diagnostico.tratamiento}",
        ]

        for line in diagnostic_data:
            if y_position < bottom_margin:
                agregar_pie_pagina(p, width, 1, 2, doc_id)
                p.showPage()
                agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
                y_position = height - 140
            p.drawString(margin + 10, y_position, line)
            y_position -= spacing

        y_position -= spacing
        
        # Datos del médico
        if y_position < bottom_margin + 60:
            agregar_pie_pagina(p, width, 1, 2, doc_id)
            p.showPage()
            agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
            y_position = height - 140
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(margin, y_position, "MÉDICO RESPONSABLE:")
        y_position -= spacing + 5
        p.setFont("Helvetica", 11)
        p.drawString(
            margin + 10,
            y_position,
            f"Dr. {diagnostico.idmedico.persona.last_name}, {diagnostico.idmedico.persona.first_name}",
        )
        p.drawString(
            width - 200, y_position, f"Matrícula: {diagnostico.idmedico.matricula}"
        )
        y_position -= spacing * 2

    # Solo agregar seguimiento si hay espacio suficiente o si hay contenido previo
    # Calcular espacio necesario para el resto del contenido (aproximadamente 220 puntos)
    espacio_necesario = spacing * 12  # Aproximadamente para seguimiento + recomendaciones
    
    # Agregar información de seguimiento médico recomendado
    if y_position < bottom_margin + espacio_necesario:
        # Solo crear nueva página si ya hay contenido significativo
        if diagnostico:  # Solo si ya se escribió algo antes
            agregar_pie_pagina(p, width, 1, 2, doc_id)
            p.showPage()
            agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
            y_position = height - 140
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y_position, "SEGUIMIENTO MÉDICO RECOMENDADO:")
    y_position -= spacing + 5
    p.setFont("Helvetica", 10)
    p.drawString(margin + 10, y_position, "□ Control en consulta externa en 7 días")
    y_position -= spacing
    p.drawString(margin + 10, y_position, "□ Control en consulta externa en 14 días")
    y_position -= spacing
    p.drawString(margin + 10, y_position, "□ Control en consulta externa en 30 días")
    y_position -= spacing
    p.drawString(margin + 10, y_position, "□ Otro: _______________________________")
    
    # Agregar recomendaciones generales
    y_position -= spacing * 2
    
    if y_position < bottom_margin + 100:
        agregar_pie_pagina(p, width, 1, 2, doc_id)
        p.showPage()
        agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
        y_position = height - 140
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y_position, "RECOMENDACIONES:")
    y_position -= spacing + 5
    p.setFont("Helvetica", 10)
    recomendaciones = [
        "Acudir a emergencias ante cualquier síntoma de alarma.",
        "Cumplir con el tratamiento médico indicado.",
        "Mantener reposo según las indicaciones médicas.",
        "Asistir a las citas de control programadas."
    ]
    
    for rec in recomendaciones:
        if y_position < bottom_margin:
            agregar_pie_pagina(p, width, 1, 2, doc_id)
            p.showPage()
            agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
            y_position = height - 140
        p.drawString(margin + 10, y_position, "• " + rec)
        y_position -= spacing
    
    # Sección de firmas
    y_position -= spacing * 2
    
    if y_position < bottom_margin + 100:
        agregar_pie_pagina(p, width, 1, 2, doc_id)
        p.showPage()
        agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
        y_position = height - 140
    
    p.line(margin, y_position, width - margin, y_position)
    y_position -= spacing * 2

    # Firma Médico y Paciente
    if diagnostico:
        p.setFont("Helvetica", 10)
        p.drawString(
            margin + 50, y_position, "_________________________________________"
        )
        y_position -= 20
        p.drawString(
            margin + 50,
            y_position,
            f"Dr. {diagnostico.idmedico.persona.last_name}, {diagnostico.idmedico.persona.first_name}",
        )
        y_position -= 20
        p.drawString(
            margin + 50, y_position, f"Matrícula: {diagnostico.idmedico.matricula}"
        )

        # Volver a la posición para firma del paciente (misma altura que médico)
        y_position += 40
        
        # Firma Paciente
        p.drawString(
            width - 250, y_position, "_________________________________________"
        )
        y_position -= 20
        p.drawString(
            width - 250,
            y_position,
            f"{internacion.idpaciente.nombre} {internacion.idpaciente.apellido}",
        )
        y_position -= 20
        p.drawString(
            width - 250, y_position, "DNI: " + str(internacion.idpaciente.dni)
        )
    
    # Usar la función de utilidad para agregar el pie de página
    agregar_pie_pagina(p, width, 1, 1, doc_id)

    p.save()
    return response
