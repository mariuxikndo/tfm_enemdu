"""
tests/analisis_sus.py
────────────────────────────────────────────────────────────────────
Script de análisis de resultados de la evaluación de usabilidad SUS.

Uso:
  python tests/analisis_sus.py

Instrucciones:
  1. Completa el diccionario RESULTADOS con las respuestas de cada participante
  2. Cada participante tiene 10 respuestas (ítems 1-10, escala 1-5)
  3. Ejecuta el script para obtener el análisis completo
  4. El reporte se guarda en data/outputs/reporte_sus.txt
"""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ══════════════════════════════════════════════════════════════════
#  RESULTADOS DE LOS PARTICIPANTES
#  Completa con los valores reales de cada cuestionario
#  Formato: {"P-01": [R1, R2, R3, R4, R5, R6, R7, R8, R9, R10], ...}
#  Escala: 1=Totalmente en desacuerdo ... 5=Totalmente de acuerdo
# ══════════════════════════════════════════════════════════════════

RESULTADOS = {
    # Ejemplo de datos (reemplazar con resultados reales)
    "P-01": [4, 2, 4, 2, 4, 2, 4, 2, 4, 2],   # ← reemplazar
    "P-02": [5, 1, 5, 1, 5, 1, 5, 1, 5, 1],   # ← reemplazar
    "P-03": [4, 2, 4, 2, 4, 2, 4, 1, 4, 2],   # ← reemplazar
    "P-04": [3, 3, 3, 2, 4, 2, 4, 2, 4, 2],   # ← reemplazar
    "P-05": [4, 2, 5, 1, 4, 2, 5, 1, 5, 1],   # ← reemplazar
    # Añadir P-06, P-07, P-08 si hay más participantes
}

# Ítems del cuestionario (referencia)
ITEMS = {
    1:  "Usaría la plataforma frecuentemente para consultar indicadores",
    2:  "La plataforma es innecesariamente compleja",
    3:  "La plataforma es fácil de usar",
    4:  "Necesitaría ayuda de un técnico para usarla",
    5:  "Las funciones están bien integradas",
    6:  "Hay demasiada inconsistencia en los datos",
    7:  "La mayoría aprendería a usarla rápidamente",
    8:  "La plataforma es muy incómoda de usar",
    9:  "Me sentí seguro interpretando los indicadores",
    10: "Necesité aprender muchas cosas antes de usarla",
}

# Escala de interpretación SUS
ESCALA_SUS = [
    (85, 100, "Excelente",    "A",  "2D8C3F"),
    (70,  85, "Aceptable",    "B",  "1A6F9C"),
    (50,  70, "Marginal",     "C",  "D97706"),
    ( 0,  50, "Inaceptable",  "F",  "C0392B"),
]

CRITERIO_TFM = 70.0


def calcular_sus(respuestas: list[int]) -> float:
    """
    Calcula la puntuación SUS de una lista de 10 respuestas.

    Fórmula:
      - Ítems impares (1,3,5,7,9): puntuación = respuesta - 1
      - Ítems pares  (2,4,6,8,10): puntuación = 5 - respuesta
      - Total = suma × 2.5 (rango 0-100)
    """
    if len(respuestas) != 10:
        raise ValueError(f"Se requieren 10 respuestas, se recibieron {len(respuestas)}")

    puntuaciones = []
    for i, r in enumerate(respuestas, start=1):
        if not 1 <= r <= 5:
            raise ValueError(f"Ítem {i}: la respuesta debe ser 1-5, obtenido {r}")
        if i % 2 != 0:   # ítem impar
            puntuaciones.append(r - 1)
        else:             # ítem par
            puntuaciones.append(5 - r)

    return sum(puntuaciones) * 2.5


def interpretar_sus(puntuacion: float) -> tuple[str, str]:
    """Retorna (nivel, grado) según la puntuación SUS."""
    for min_val, max_val, nivel, grado, _ in ESCALA_SUS:
        if min_val <= puntuacion <= max_val:
            return nivel, grado
    return "Indeterminado", "?"


def analizar_item(item_num: int) -> dict:
    """Calcula estadísticas por ítem."""
    respuestas = [RESULTADOS[p][item_num - 1] for p in RESULTADOS]
    return {
        "item":   item_num,
        "texto":  ITEMS[item_num],
        "media":  round(np.mean(respuestas), 2),
        "std":    round(np.std(respuestas), 2),
        "min":    min(respuestas),
        "max":    max(respuestas),
    }


def main():
    print()
    print("═" * 65)
    print("  ANÁLISIS DE USABILIDAD — Sistema SUS")
    print("  Plataforma MIAH-ENEMDU 2025")
    print("═" * 65)

    if not RESULTADOS:
        print("\n  ⚠ No hay resultados. Completa el diccionario RESULTADOS.")
        return

    # ── Puntuaciones individuales ─────────────────────────────────
    print(f"\n  {'Participante':<12} {'Puntuación SUS':>16} {'Nivel':>14} {'Criterio (≥70)':>16}")
    print("  " + "─" * 62)

    puntuaciones = {}
    for pid, respuestas in RESULTADOS.items():
        try:
            sus = calcular_sus(respuestas)
            nivel, grado = interpretar_sus(sus)
            cumple = "✓  Cumple" if sus >= CRITERIO_TFM else "✗  No cumple"
            print(f"  {pid:<12} {sus:>14.1f}  {nivel:>14}  {cumple:>16}")
            puntuaciones[pid] = sus
        except ValueError as e:
            print(f"  {pid:<12} ERROR: {e}")

    # ── Estadísticas globales ─────────────────────────────────────
    vals = list(puntuaciones.values())
    media_sus = np.mean(vals)
    std_sus   = np.std(vals)
    min_sus   = min(vals)
    max_sus   = max(vals)

    print()
    print("═" * 65)
    print("  RESULTADO GLOBAL")
    print("═" * 65)
    print(f"  Participantes evaluados: {len(vals)}")
    print(f"  Puntuación SUS media:    {media_sus:.1f} puntos")
    print(f"  Desviación estándar:     ±{std_sus:.1f}")
    print(f"  Rango:                   {min_sus:.1f} – {max_sus:.1f}")

    nivel_global, _ = interpretar_sus(media_sus)
    cumple_global = "✓  CUMPLE el criterio de aceptación" if media_sus >= CRITERIO_TFM \
                    else "✗  NO CUMPLE el criterio de aceptación"
    print(f"  Nivel de usabilidad:     {nivel_global}")
    print(f"  Criterio TFM (SUS ≥ 70): {cumple_global}")

    # ── Análisis por ítem ─────────────────────────────────────────
    print()
    print("═" * 65)
    print("  ANÁLISIS POR ÍTEM")
    print("═" * 65)
    print(f"  {'Ítem':<6} {'Media':>6} {'±':>5}  {'Texto (resumido)'}")
    print("  " + "─" * 62)

    for i in range(1, 11):
        stats = analizar_item(i)
        tipo = "(inverso)" if i % 2 == 0 else ""
        texto_corto = stats["texto"][:45] + "..." if len(stats["texto"]) > 45 else stats["texto"]
        print(f"  {i:<6} {stats['media']:>6.2f} {stats['std']:>5.2f}  {texto_corto} {tipo}")

    # ── Ítems problemáticos (media baja en positivos, alta en negativos) ─
    print()
    print("  Ítems que requieren atención (positivos con media < 3.5):")
    items_positivos = [1, 3, 5, 7, 9]
    items_negativos = [2, 4, 6, 8, 10]
    items_problema = []

    for i in items_positivos:
        stats = analizar_item(i)
        if stats["media"] < 3.5:
            items_problema.append((i, stats["media"], stats["texto"]))
            print(f"  ⚠  Ítem {i} (media={stats['media']:.2f}): {stats['texto'][:50]}")

    for i in items_negativos:
        stats = analizar_item(i)
        if stats["media"] > 2.5:
            items_problema.append((i, stats["media"], stats["texto"]))
            print(f"  ⚠  Ítem {i} (media={stats['media']:.2f}): {stats['texto'][:50]}")

    if not items_problema:
        print("  ✓  Ningún ítem presenta puntuación problemática.")

    # ── Guardar reporte ───────────────────────────────────────────
    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    reporte_path = "data/outputs/reporte_sus.txt"

    with open(reporte_path, "w", encoding="utf-8") as f:
        f.write("REPORTE DE EVALUACIÓN DE USABILIDAD — SUS\n")
        f.write("Plataforma MIAH-ENEMDU 2025\n")
        f.write("=" * 65 + "\n\n")
        f.write(f"Participantes: {len(vals)}\n")
        f.write(f"Puntuación SUS media: {media_sus:.1f}\n")
        f.write(f"Desviación estándar:  ±{std_sus:.1f}\n")
        f.write(f"Nivel: {nivel_global}\n")
        f.write(f"Cumple criterio TFM (≥70): {'Sí' if media_sus >= CRITERIO_TFM else 'No'}\n\n")
        f.write("Resultados individuales:\n")
        for pid, sus in puntuaciones.items():
            nivel, _ = interpretar_sus(sus)
            f.write(f"  {pid}: {sus:.1f} pts — {nivel}\n")
        f.write("\nAnálisis por ítem:\n")
        for i in range(1, 11):
            stats = analizar_item(i)
            f.write(f"  Ítem {i}: media={stats['media']:.2f}, std={stats['std']:.2f} — {stats['texto'][:60]}\n")

    print()
    print(f"  Reporte guardado en {reporte_path}")
    print("═" * 65 + "\n")


if __name__ == "__main__":
    main()
