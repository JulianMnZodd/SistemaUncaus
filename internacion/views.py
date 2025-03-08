from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from habitaciones.models import Cama, Habitacion
from .forms import DiagnosticoForm, AsignarCamaForm
from .models import Paciente, Medico, Enfermero, Internacion


@login_required
def asignar_cama(request, idcama):
    cama = get_object_or_404(Cama, idcama=idcama)
    pacientes = Paciente.objects.all()

    if request.method == "POST":
        form = AsignarCamaForm(request.POST)
        if form.is_valid():
            paciente_id = form.cleaned_data["paciente_id"]
            paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
            nota_ingreso = form.cleaned_data["nota_ingreso"]
            action = request.POST.get('action')

            if action == 'asignar':
                internacion = Internacion.objects.create(
                    idpaciente=paciente,
                    fecha_admision=timezone.now(),
                    cama=cama,
                    nota_ingreso=nota_ingreso,
                )
                cama.estado = "O"
                cama.save()
                return redirect('lista_habitaciones')
            elif action == 'generar_pdf':
                return generar_consentimiento_pdf(request, paciente.idpaciente)
    else:
        form = AsignarCamaForm()

    return render(request, 'asignar_cama.html', {'form': form, 'cama': cama, 'pacientes': pacientes})


@login_required
def generar_consentimiento(request):
    if request.method == "POST":
        form = AsignarCamaForm(request.POST)
        if form.is_valid():
            paciente = form.cleaned_data["idpaciente"]
            return generar_consentimiento_pdf(request, paciente.id)
    else:
        return redirect('asignar_cama')

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
def crear_diagnostico(request, internacion_id):
    internacion = get_object_or_404(Internacion, idinternacion=internacion_id)
    paciente = internacion.idpaciente
    medico = get_object_or_404(Medico, persona=request.user)  # Usar el campo correcto para obtener el médico logeado

    # Verificar si ya existe un diagnóstico para esta internación
    if Diagnostico.objects.filter(idinternacion=internacion).exists():
        return redirect('detalle_diagnostico', internacion_id=internacion.idinternacion)  # Redirigir al detalle del diagnóstico si ya existe

    if request.method == "POST":
        form = DiagnosticoForm(request.POST)
        if form.is_valid():
            diagnostico = form.save(commit=False)
            diagnostico.idpaciente = paciente
            diagnostico.idmedico = medico
            diagnostico.idinternacion = internacion  # Asociar el diagnóstico con la internación actual
            diagnostico.save()
            return redirect('detalle_diagnostico', internacion_id=internacion.idinternacion)  # Redirigir al detalle del diagnóstico
    else:
        form = DiagnosticoForm()

    return render(request, 'crear_diagnostico.html', {'form': form, 'paciente': paciente})

from .models import Diagnostico
@login_required
def detalle_diagnostico(request, internacion_id):
    internacion = get_object_or_404(Internacion, idinternacion=internacion_id)
    diagnostico = get_object_or_404(Diagnostico, idinternacion=internacion)
    return render(request, 'detalle_diagnostico.html', {'internacion': internacion, 'diagnostico': diagnostico})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from .forms import SeguimientoForm, MedicacionForm, SignosVitalesForm
from .models import Paciente, Enfermero, Seguimiento, Medicacion, SignosVitales


@login_required
def seguimiento(request, internacion_id):
    internacion = get_object_or_404(Internacion, idinternacion=internacion_id)
    enfermero = get_object_or_404(
        Enfermero, persona=request.user
    )  # Usar el campo correcto para obtener el enfermero logeado

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


def listar_seguimientos(request, internacion_id):
    internacion = get_object_or_404(Internacion, idinternacion=internacion_id)
    seguimientos = Seguimiento.objects.filter(idinternacion=internacion)
    return render(request, 'listar_seguimientos.html', {
        'internacion': internacion,
        'seguimientos': seguimientos,
    })
    

def seguimiento_detalles(request, seguimiento_id):
    seguimiento = get_object_or_404(Seguimiento, idseguimiento=seguimiento_id)
    return render(request, 'seguimiento_detalles.html', {
        'seguimiento': seguimiento,
    })
    
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

@login_required
def generar_consentimiento_pdf(request, paciente_id):
    paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
    
    # Crear el objeto HttpResponse con el encabezado PDF adecuado.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="consentimiento_{paciente.idpaciente}.pdf"'

    # Crear el objeto PDF usando el HttpResponse como "archivo".
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Título del documento (centrado)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height - 50, "ACTA DE CONSENTIMIENTO INFORMADO PARA INTERNACIÓN")

    # Datos del paciente o representante
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Nombre del Paciente: {paciente.nombre} {paciente.apellido}")
    p.drawString(50, height - 100, f"Fecha de Nacimiento: {paciente.fecha_nacimiento}")
    p.drawString(50, height - 120, f"Dirección: {paciente.domicilio}")
    p.drawString(50, height - 140, f"Teléfono: {paciente.telefono}")
    p.drawString(50, height - 160, f"Email: {paciente.email}")
    # Campos adicionales que se pueden complementar desde la BD o dejar en blanco
    p.drawString(50, height - 180, f"Documento de Identidad: {paciente.dni}")
    p.drawString(50, height - 200, "Relación (si es representante): _________________")

    # Datos del establecimiento y personal médico
    p.drawString(50, height - 250, "Médico Responsable: _________")
    p.drawString(50, height - 270, "Registro Profesional: _________")

    # Exposición de la información
    text = p.beginText(50, height - 300)
    text.setFont("Helvetica", 12)
    exposicion = [
        "Yo, el suscrito, declaro haber sido informado de manera clara y comprensible",
        "sobre la situación médica que requiere la internación, incluyendo:",
        "  - Diagnóstico y necesidad del tratamiento hospitalario.",
        "  - Procedimientos, exámenes y terapias previstos.",
        "  - Riesgos, complicaciones y beneficios asociados.",
        "  - Alternativas de tratamiento y posibilidad de realizar consultas adicionales.",
        "He tenido la oportunidad de formular preguntas, las cuales han sido contestadas",
        "a mi entera satisfacción."
    ]
    for line in exposicion:
        text.textLine(line)
    p.drawText(text)

    # Consentimiento
    text = p.beginText(50, height - 420)
    text.setFont("Helvetica", 12)
    consentimiento = [
        "Doy mi consentimiento libre y voluntario para la internación y la realización",
        "de los procedimientos y tratamientos que el personal médico estime necesarios,",
        "exonerando de responsabilidad al personal del establecimiento, siempre que",
        "se actúe conforme a la normatividad vigente y al debido proceder profesional."
    ]
    for line in consentimiento:
        text.textLine(line)
    p.drawText(text)

    # Firmas y fechas
    p.drawString(50, height - 500, "Firma del Paciente o Representante: ______")
    p.drawString(50, height - 520, "Fecha: __________________________")
    p.drawString(50, height - 550, "Firma del Médico: ___________________")
    p.drawString(50, height - 570, "Fecha: ____________________")

    # Finalizar el PDF
    p.showPage()
    p.save()

    return response