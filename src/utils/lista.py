def primer_repetido(lista):
    vistos = set()
    for numero in lista:
        if numero in vistos:
            return numero
        vistos.add(numero)
    return None  # si no hay repetidos

# Lista desordenada con al menos un número repetido
numeros = [7, 3, 8, 2, 5, 3, 1, 9, 8]

resultado = primer_repetido(numeros)

if resultado:
    print("El primer número repetido es:", resultado)
else:
    print("No se encontró ningún número repetido.")
