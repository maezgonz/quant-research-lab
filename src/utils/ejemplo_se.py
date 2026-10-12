def diagnostico_enfermedad():
    print("Responde con 'sí' o 'no' a las siguientes preguntas:")

    fiebre = input("¿Tienes fiebre? ").lower()
    dolor_garganta = input("¿Tienes dolor de garganta? ").lower()
    estornudos = input("¿Estás estornudando mucho? ").lower()
    secrecion_nasal = input("¿Tienes secreción nasal? ").lower()
    dolor_cabeza = input("¿Tienes dolor de cabeza? ").lower()
    cansancio = input("¿Te sientes muy cansado/a? ").lower()
    picazon_ojos = input("¿Tienes picazón en los ojos? ").lower()

    # Diagnóstico basado en reglas simples
    if fiebre == "sí" and dolor_garganta == "sí" and dolor_cabeza == "sí" and cansancio == "sí":
        print("🩺 Podrías tener una gripe. Se recomienda reposo e hidratarte bien.")
    elif estornudos == "sí" and secrecion_nasal == "sí" and picazon_ojos == "sí" and fiebre == "no":
        print("🌸 Podrías tener una alergia. Evita alérgenos y consulta a tu médico.")
    elif secrecion_nasal == "sí" and dolor_garganta == "sí" and fiebre == "no":
        print("🤧 Parece un resfriado común. Descansa y toma líquidos.")
    else:
        print("❓ No se puede determinar claramente. Te recomendamos consultar a un médico.")
		
# Ejecutar el sistema
diagnostico_enfermedad()