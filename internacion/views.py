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
    internaciones = Internacion.objects.filter(fecha_alta__isnull=True)
    es_medico = hasattr(request.user, "medico")
    es_enfermero = hasattr(request.user, "enfermero")
    return render(
        request,
        "listar_internaciones.html",
        {
            "internaciones": internaciones,
            "es_medico": es_medico,
            "es_enfermero": es_enfermero,
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
            return redirect(
                "listar_internaciones"
            )  # Asegúrate de tener esta vista y URL configurada
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
            return redirect('listar_internaciones')
    else:
        form = SeguimientoForm(instance=seguimiento)
        medicacion_formset = MedicacionFormSet(instance=seguimiento)
        signos_vitales_formset = SignosVitalesFormSet(instance=seguimiento)

    return render(request, 'editar_seguimiento.html', {
        'form': form,
        'medicacion_formset': medicacion_formset,
        'signos_vitales_formset': signos_vitales_formset,
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

    # Datos del paciente o representante
    p.setFont("Helvetica", 12)
    p.drawString(
        50, height - 140, f"Nombre del Paciente: {paciente.nombre} {paciente.apellido}"  # Aumentado de -80 a -140 para dar más espacio
    )
    p.drawString(50, height - 160, f"Fecha de Nacimiento: {paciente.fecha_nacimiento}")  # Ajustado de -100 a -160
    p.drawString(50, height - 180, f"Dirección: {paciente.domicilio}")  # Ajustado de -120 a -180
    p.drawString(50, height - 200, f"Teléfono: {paciente.telefono}")  # Ajustado de -140 a -200
    p.drawString(50, height - 220, f"Email: {paciente.email}")  # Ajustado de -160 a -220
    # Campos adicionales que se pueden complementar desde la BD o dejar en blanco
    p.drawString(50, height - 240, f"Documento de Identidad: {paciente.dni}")  # Ajustado de -180 a -240
    p.drawString(50, height - 260, "Relación (si es representante): _________________")  # Ajustado de -200 a -260

    # Datos del establecimiento y personal médico
    p.drawString(50, height - 290, "Médico Responsable: _________")  # Ajustado de -250 a -290
    p.drawString(50, height - 310, "Registro Profesional: _________")  # Ajustado de -270 a -310

    # Exposición de la información
    text = p.beginText(50, height - 340)  # Ajustado de -300 a -340
    text.setFont("Helvetica", 12)
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

    # Consentimiento
    text = p.beginText(50, height - 460)  # Ajustado de -420 a -460
    text.setFont("Helvetica", 12)
    consentimiento = [
        "Doy mi consentimiento libre y voluntario para la internación y la realización",
        "de los procedimientos y tratamientos que el personal médico estime necesarios,",
        "exonerando de responsabilidad al personal del establecimiento, siempre que",
        "se actúe conforme a la normatividad vigente y al debido proceder profesional.",
    ]
    for line in consentimiento:
        text.textLine(line)
    p.drawText(text)

    # Firmas y fechas
    p.drawString(50, height - 540, "Firma del Paciente o Representante: ______")  # Ajustado de -500 a -540
    p.drawString(50, height - 560, "Fecha: __________________________")  # Ajustado de -520 a -560
    p.drawString(50, height - 590, "Firma del Médico: ___________________")  # Ajustado de -550 a -590
    p.drawString(50, height - 610, "Fecha: ____________________")  # Ajustado de -570 a -610

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
            response["Content-Disposition"] = (
                'attachment; filename="informe_internaciones.pdf"'
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

            # Encabezados de la tabla
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, height - 120, "Paciente")  # Aumentado el margen superior de 100 a 120
            p.drawString(200, height - 120, "Fecha de Ingreso")  # Ajustado a -120
            p.drawString(350, height - 120, "Fecha de Alta")  # Ajustado a -120
            p.drawString(500, height - 120, "Motivo")  # Ajustado a -120

            # Datos de la tabla
            y = height - 140  # Ajustado de -120 a -140 para dar más espacio
            p.setFont("Helvetica", 10)
            for internacion in internaciones:
                p.drawString(
                    50,
                    y,
                    f"{internacion.idpaciente.nombre} {internacion.idpaciente.apellido}",
                )
                p.drawString(
                    200, y, str(internacion.fecha_admision.strftime("%d/%m/%Y %H:%M"))
                )
                p.drawString(
                    350,
                    y,
                    (
                        internacion.fecha_alta.strftime("%d/%m/%Y %H:%M")
                        if internacion.fecha_alta
                        else "En curso"
                    ),
                )
                p.drawString(500, y, internacion.nota_ingreso)
                y -= 20

                if y < 50:  # Salto de página si no hay espacio
                    p.showPage()
                    # Repetir encabezados en la nueva página
                    p.setFont("Helvetica-Bold", 12)
                    p.drawString(50, height - 120, "Paciente")  # Ajustado a -120
                    p.drawString(200, height - 120, "Fecha de Ingreso")  # Ajustado a -120
                    p.drawString(350, height - 120, "Fecha de Alta")  # Ajustado a -120
                    p.drawString(500, height - 120, "Motivo")  # Ajustado a -120
                    y = height - 140  # Ajustado a -140 para dar más espacio

            # Agregar estadísticas
            total_internaciones = internaciones.count()
            altas = internaciones.filter(fecha_alta__isnull=False).count()
            en_curso = internaciones.filter(fecha_alta__isnull=True).count()
            
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, 100, "Resumen:")
            p.setFont("Helvetica", 10)
            p.drawString(70, 80, f"Total internaciones: {total_internaciones}")
            p.drawString(70, 65, f"Internaciones finalizadas: {altas}")
            p.drawString(70, 50, f"Internaciones en curso: {en_curso}")
            
            # Obtener el número total de páginas
            total_paginas = p.getPageNumber()
            
            # Agregar encabezado y pie de página en cada página
            for i in range(1, total_paginas + 1):
                if i < total_paginas:
                    p.showPage()
                    # Repetir encabezados en la nueva página
                    agregar_encabezado_bedwise(
                        p, 
                        f"Informe de Internaciones ({fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')})",
                        width,
                        height
                    )
                    p.setFont("Helvetica-Bold", 12)
                    p.drawString(50, height - 120, "Paciente")
                    p.drawString(200, height - 120, "Fecha de Ingreso")
                    p.drawString(350, height - 120, "Fecha de Alta")
                    p.drawString(500, height - 120, "Motivo")
                
                # Agregar pie de página con número de página y código QR en la última página
                if i == total_paginas:
                    agregar_pie_pagina(p, width, i, total_paginas, doc_id)
                else:
                    agregar_pie_pagina(p, width, i, total_paginas)

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
    response["Content-Disposition"] = (
        f'attachment; filename="informe_internacion_{internacion.idinternacion}.pdf"'
    )

    # Crear el objeto PDF usando el HttpResponse como "archivo"
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Usar la función de utilidad para agregar el encabezado
    titulo = f"Informe de Internación - {internacion.idpaciente.apellido}, {internacion.idpaciente.nombre}"
    agregar_encabezado_bedwise(p, titulo, width, height)

    # Información general de la internación
    p.setFont("Helvetica", 12)
    y = height - 120  # Aumentado el margen superior de 100 a 120
    p.drawString(
        50,
        y,
        f"Fecha de Ingreso: {internacion.fecha_admision.strftime('%d/%m/%Y %H:%M')}",
    )
    y -= 20
    p.drawString(
        50,
        y,
        f"Fecha de Alta: {internacion.fecha_alta.strftime('%d/%m/%Y %H:%M') if internacion.fecha_alta else 'N/A'}",
    )
    y -= 20
    p.drawString(50, y, f"Motivo de Internación: {internacion.nota_ingreso}")
    y -= 40

    # Detalles del seguimiento
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Seguimientos:")
    y -= 20

    p.setFont("Helvetica", 10)
    for seguimiento in seguimientos:
        if y < 100:  # Salto de página si no hay espacio
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 10)

        p.drawString(50, y, f"- Fecha: {seguimiento.fecha.strftime('%d/%m/%Y %H:%M')}")
        y -= 15
        p.drawString(70, y, f"  Observación: {seguimiento.observacion}")
        y -= 15

        # Medicación
        p.drawString(70, y, "  Medicación:")
        y -= 15
        for medicacion in seguimiento.medicaciones.all():
            p.drawString(
                90,
                y,
                f"- {medicacion.tipo}: {medicacion.nombre} a las {medicacion.hora_medicacion.strftime('%H:%M')}",
            )
            y -= 15

        # Signos vitales
        p.drawString(70, y, "  Signos Vitales:")
        y -= 15
        for signo in seguimiento.signos_vitales.all():
            p.drawString(
                90,
                y,
                f"- Temperatura: {signo.temperatura_corporal}°C, Pulso: {signo.pulso}, Frecuencia Respiratoria: {signo.frecuencia_respiratoria}",
            )
            y -= 15

        y -= 10  # Espacio entre seguimientos

    # Agregar diagnóstico si existe
    if diagnostico:
        if y < 100:  # Salto de página si no hay espacio
            p.showPage()
            y = height - 50
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Diagnóstico:")
        y -= 15
        
        p.setFont("Helvetica", 10)
        p.drawString(70, y, f"Fecha: {diagnostico.fecha.strftime('%d/%m/%Y %H:%M')}")
        y -= 15
        p.drawString(70, y, f"Detalles: {diagnostico.detalles}")
        y -= 15
        p.drawString(70, y, f"Gravedad: {diagnostico.gravedad}")
        y -= 15
        p.drawString(70, y, f"Tratamiento: {diagnostico.tratamiento}")
        y -= 15
        
        if diagnostico.idmedico:
            p.drawString(70, y, f"Médico: Dr. {diagnostico.idmedico.persona.last_name}, {diagnostico.idmedico.persona.first_name}")
            y -= 15
    
    # Calcular duración de la internación
    duracion = ""
    if internacion.fecha_alta:
        dias = (internacion.fecha_alta.date() - internacion.fecha_admision.date()).days
        duracion = f"{dias} días"
    else:
        dias = (timezone.now().date() - internacion.fecha_admision.date()).days
        duracion = f"{dias} días (en curso)"
    
    p.setFont("Helvetica", 10)
    p.drawString(50, 60, f"Duración de la internación: {duracion}")
    
    # Manejo de páginas múltiples
    total_paginas = p.getPageNumber()
    
    # Volver a la primera página y agregar números de página
    for i in range(1, total_paginas + 1):
        if i < total_paginas:
            p.showPage()
            # Agregar encabezado en páginas adicionales
            agregar_encabezado_bedwise(p, titulo, width, height)
        
        # Agregar pie de página con número de página y código QR en la última página
        if i == total_paginas:
            agregar_pie_pagina(p, width, i, total_paginas, doc_id)
        else:
            agregar_pie_pagina(p, width, i, total_paginas)
    
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
    response["Content-Disposition"] = (
        f'attachment; filename="informe_alta_{internacion.idinternacion}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Configuración inicial
    p.setTitle(f"Informe de Alta Médica - {internacion.idpaciente.apellido}")
    margin = 50
    
    # Usar la función de utilidad para agregar el encabezado
    agregar_encabezado_bedwise(p, "INFORME DE ALTA MÉDICA", width, height)
    
    y_position = height - 140  # Aumentado de -120 a -140 para dar más espacio
    spacing = 20

    # Información del paciente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y_position, "DATOS DEL PACIENTE:")
    y_position -= spacing

    p.setFont("Helvetica", 12)
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
        p.drawString(margin + 10, y_position, line)
        y_position -= spacing

    y_position -= spacing

    # Motivo de internación
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y_position, "MOTIVO DE INTERNACIÓN:")
    y_position -= spacing
    p.setFont("Helvetica", 12)
    p.drawString(margin + 10, y_position, internacion.nota_ingreso)
    y_position -= spacing * 2

    # Diagnóstico y tratamiento
    diagnostico = internacion.diagnostico_set.order_by("-fecha").first()
    if diagnostico:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(margin, y_position, "DIAGNÓSTICO PRINCIPAL:")
        y_position -= spacing
        p.setFont("Helvetica", 12)
        diagnostic_data = [
            f"Fecha: {diagnostico.fecha.strftime('%d/%m/%Y %H:%M')}",
            f"Detalles: {diagnostico.detalles}",
            f"Gravedad: {diagnostico.gravedad}",
            f"Tratamiento: {diagnostico.tratamiento}",
        ]

        for line in diagnostic_data:
            p.drawString(margin + 10, y_position, line)
            y_position -= spacing

        # Datos del médico
        p.setFont("Helvetica-Bold", 12)
        p.drawString(margin, y_position, "MÉDICO RESPONSABLE:")
        y_position -= spacing
        p.setFont("Helvetica", 12)
        p.drawString(
            margin + 10,
            y_position,
            f"Dr. {diagnostico.idmedico.persona.last_name}, {diagnostico.idmedico.persona.first_name}",
        )
        p.drawString(
            width - 200, y_position, f"Matrícula: {diagnostico.idmedico.matricula}"
        )
        y_position -= spacing * 2

    # Sección de firmas
    p.line(margin, y_position, width - margin, y_position)
    y_position -= spacing * 2

    # Firma Médico
    if diagnostico:
        p.drawString(
            margin + 50, y_position, "_________________________________________"
        )
        p.drawString(
            margin + 50,
            y_position - 20,
            f"Dr. {diagnostico.idmedico.persona.last_name}, {diagnostico.idmedico.persona.first_name}",
        )
        p.drawString(
            margin + 50, y_position - 40, f"Matrícula: {diagnostico.idmedico.matricula}"
        )

        # Firma Paciente
        p.drawString(
            width - 250, y_position, "_________________________________________"
        )
        p.drawString(
            width - 250,
            y_position - 20,
            f"{internacion.idpaciente.nombre} {internacion.idpaciente.apellido}",
        )
        p.drawString(
            width - 250, y_position - 40, "DNI: " + str(internacion.idpaciente.dni)
        )

    # Agregar información de seguimiento médico recomendado
    y_position -= spacing * 2
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y_position, "SEGUIMIENTO MÉDICO RECOMENDADO:")
    y_position -= spacing
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
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y_position, "RECOMENDACIONES:")
    y_position -= spacing
    p.setFont("Helvetica", 10)
    recomendaciones = [
        "Acudir a emergencias ante cualquier síntoma de alarma.",
        "Cumplir con el tratamiento médico indicado.",
        "Mantener reposo según las indicaciones médicas.",
        "Asistir a las citas de control programadas."
    ]
    
    for rec in recomendaciones:
        p.drawString(margin + 10, y_position, "• " + rec)
        y_position -= spacing
    
    # Usar la función de utilidad para agregar el pie de página
    agregar_pie_pagina(p, width, 1, 1, doc_id)

    p.save()
    return response
