import random
import matplotlib.pyplot as plt

def simular_evaluacion_peor_escenario(num_simulaciones=1000000):
    """
    Simula la distribución de puntajes en el peor escenario para un examen.

    Args:
        num_simulaciones (int): Número de simulaciones a realizar.

    Returns:
        dict: Un diccionario con los puntajes posibles como claves y sus probabilidades como valores.
    """
    if not isinstance(num_simulaciones, int) or num_simulaciones <= 0:
        raise ValueError("El número de simulaciones debe ser un entero positivo.")

    posibles_puntajes = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
    resultados = {puntaje: 0 for puntaje in posibles_puntajes}

    for _ in range(num_simulaciones):
        # Simular un evaluador muy estricto o estricto con alta probabilidad
        evaluador = random.choices(["Muy Estricto", "Estricto", "Moderado"], [0.35, 0.55, 0.10])[0]

        if evaluador == "Muy Estricto":
            puntaje = random.uniform(0, 1.0)
        elif evaluador == "Estricto":
            puntaje = random.uniform(0.5, 2.0)
        else:  # Moderado
            puntaje = random.uniform(1.5, 2.5)

        # Redondear al puntaje posible más cercano
        puntaje_asignado = min(posibles_puntajes, key=lambda x: abs(x - puntaje))
        resultados[puntaje_asignado] += 1

    probabilidades = {puntaje: count / num_simulaciones for puntaje, count in resultados.items()}
    return probabilidades

def graficar_histograma(probabilidades, guardar=False):
    """
    Genera un histograma de las probabilidades de puntajes.

    Args:
        probabilidades (dict): Diccionario con los puntajes como claves y las probabilidades como valores.
        guardar (bool): Si es True, guarda el gráfico como un archivo PNG.
    """
    plt.bar(probabilidades.keys(), probabilidades.values(), color='salmon')
    plt.xlabel("Puntaje")
    plt.ylabel("Probabilidad")
    plt.title("Distribución de Probabilidades (Peor Escenario)")
    plt.xticks(list(probabilidades.keys()))
    plt.grid(axis='y', alpha=0.75)
    if guardar:
        plt.savefig("distribucion_peor_escenario.png")  # Guardar el gráfico
        print("El gráfico ha sido guardado como 'distribucion_peor_escenario.png'.")
    plt.show()

def graficar_linea(probabilidades, guardar=False):
    """
    Genera un gráfico de líneas de las probabilidades de puntajes.

    Args:
        probabilidades (dict): Diccionario con los puntajes como claves y las probabilidades como valores.
        guardar (bool): Si es True, guarda el gráfico como un archivo PNG.
    """
    plt.plot(probabilidades.keys(), probabilidades.values(), marker='o', color='blue')
    plt.xlabel("Puntaje")
    plt.ylabel("Probabilidad")
    plt.title("Distribución de Probabilidades (Peor Escenario - Línea)")
    plt.grid(axis='y', alpha=0.75)
    if guardar:
        plt.savefig("distribucion_peor_escenario_linea.png")  # Guardar el gráfico
        print("El gráfico ha sido guardado como 'distribucion_peor_escenario_linea.png'.")
    plt.show()

# Ejecutar la simulación del peor escenario
probabilidades_puntajes_peor = simular_evaluacion_peor_escenario()

# Imprimir resultados
print("\nProbabilidades del peor escenario para el punto 14 del examen:")
for puntaje, probabilidad in sorted(probabilidades_puntajes_peor.items()):
    print(f"Puntaje: {puntaje:.1f}, Probabilidad: {probabilidad:.2%}")
