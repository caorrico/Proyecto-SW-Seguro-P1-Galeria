"""
steg_analyzer.py — Módulo de detección de esteganografía LSB
============================================================
Combina el análisis de entropía por zonas (del equipo) con análisis
estadístico numpy de LSB ratio y detección de EOF para mayor precisión.
"""
import io
import math
import itertools

import numpy as np
from PIL import Image


# ── Entropía (implementación original del equipo) ─────────────────────────
def calculate_entropy(data: list[int]) -> float:
    if not data:
        return 0.0
    entropy = 0.0
    total = len(data)
    for x in range(256):
        count = data.count(x)
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def _get_entropy_for_sample(pixel_iter) -> dict:
    lsb1: list[int] = []
    lsb2: list[int] = []
    for pixel in pixel_iter:
        channels = [pixel] if isinstance(pixel, int) else list(pixel)
        for val in channels:
            lsb1.append(int(val) & 1)
            lsb2.append((int(val) >> 1) & 1)

    if not lsb1:
        return {"e1": 0.0, "r1": 0.5, "e2": 0.0, "r2": 0.5}

    def bits_to_entropy(bits: list[int]) -> tuple[float, float]:
        b_list = []
        for i in range(0, len(bits) - 8, 8):
            byte_val = 0
            for j in range(8):
                byte_val = (byte_val << 1) | bits[i + j]
            b_list.append(byte_val)
        return calculate_entropy(b_list), sum(bits) / len(bits)

    e1, r1 = bits_to_entropy(lsb1)
    e2, r2 = bits_to_entropy(lsb2)
    return {"e1": round(e1, 4), "r1": round(r1, 4),
            "e2": round(e2, 4), "r2": round(r2, 4)}


# ── Análisis numpy LSB ────────────────────────────────────────────────────
def _analyze_lsb_numpy(pixels: np.ndarray) -> dict:
    """
    Análisis estadístico de los bits menos significativos usando numpy.
    Una imagen con esteganografía LSB tiene ratio DEMASIADO cercano a 0.5
    porque los datos ocultos uniformizan la distribución.
    """
    lsb_plane = (pixels & 1).astype(np.float32)
    ratio = float(lsb_plane.mean())

    # Umbral empírico: si |ratio - 0.5| < 0.015 → muy sospechoso
    # Imágenes naturales tienen ratio entre 0.45-0.55 pero rara vez tan exacto
    suspicious = abs(ratio - 0.5) < 0.015

    # Chi-square simplificado: comparar distribución de LSB entre canales
    if pixels.ndim == 3 and pixels.shape[2] >= 3:
        ch_ratios = [(pixels[:, :, c] & 1).mean() for c in range(3)]
        # Si todos los canales tienen ratio casi idéntico → sospechoso
        spread = max(ch_ratios) - min(ch_ratios)
        if spread < 0.005:
            suspicious = True

    return {"lsb_ratio": round(ratio, 6), "lsb_suspicious": suspicious}


# ── Análisis de histograma ────────────────────────────────────────────────
def _analyze_histogram(pixels: np.ndarray) -> dict:
    """
    Detecta anomalías en el histograma de valores de píxel.
    La esteganografía LSB tiende a igualar la frecuencia de pares (2k, 2k+1).
    """
    flat = pixels.flatten()
    hist, _ = np.histogram(flat, bins=256, range=(0, 256))

    # Comparar pares adyacentes: en imagen con LSB steg, hist[2k] ≈ hist[2k+1]
    pairs_diff = []
    for k in range(0, 128):
        a, b = int(hist[2 * k]), int(hist[2 * k + 1])
        if a + b > 0:
            pairs_diff.append(abs(a - b) / (a + b))

    avg_pair_diff = float(np.mean(pairs_diff)) if pairs_diff else 1.0
    # Si la diferencia promedio entre pares es < 5%, el histograma está "aplanado"
    hist_suspicious = avg_pair_diff < 0.05

    return {
        "histogram_pair_diff": round(avg_pair_diff, 4),
        "histogram_suspicious": hist_suspicious,
    }


# ── Función principal de análisis ─────────────────────────────────────────
def analyze_image(image_bytes: bytes, mime_type: str = "") -> dict:
    """
    Análisis completo de esteganografía sobre los bytes de la imagen
    (después del re-encoding — detecta técnicas más avanzadas).

    Retorna un dict compatible con el campo steg_result del modelo Image.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode not in ("RGB", "RGBA", "L"):
            image = image.convert("RGB")

        width, height = image.size
        total_pixels = width * height
        sample_size = min(500_000, total_pixels)

        # ── Análisis por zonas (entropía) ──────────────────────────────
        start_sample = list(itertools.islice(image.getdata(), sample_size))
        mid_off = max(0, (total_pixels // 2) - (sample_size // 2))
        mid_sample = list(itertools.islice(image.getdata(), mid_off, mid_off + sample_size))
        end_off = max(0, total_pixels - sample_size)
        end_sample = list(itertools.islice(image.getdata(), end_off, total_pixels))

        res_start = _get_entropy_for_sample(start_sample)
        res_mid   = _get_entropy_for_sample(mid_sample)
        res_end   = _get_entropy_for_sample(end_sample)

        entropy_suspicious = any(
            r["e1"] > 7.9 or r["e2"] > 7.9
            for r in [res_start, res_mid, res_end]
        )

        # ── Análisis numpy ─────────────────────────────────────────────
        pixels = np.array(image, dtype=np.uint8)
        lsb_data  = _analyze_lsb_numpy(pixels)
        hist_data = _analyze_histogram(pixels)

        # ── Veredicto final ────────────────────────────────────────────
        mime_normalized = (mime_type or "").strip().lower().split(";")[0]
        is_jpeg = mime_normalized in {"image/jpeg", "image/jpg"} or (image.format or "").upper() == "JPEG"
        flags = [
            entropy_suspicious,
            lsb_data["lsb_suspicious"],
            hist_data["histogram_suspicious"],
        ]
        if is_jpeg:
            is_suspicious = entropy_suspicious and hist_data["histogram_suspicious"]
            decision_policy = "jpeg_entropy_and_histogram"
        else:
            is_suspicious = sum(flags) >= 2
            decision_policy = "two_or_more_signals"

        result = "SUSPICIOUS" if is_suspicious else "CLEAN"

        return {
            "result": result,
            "is_suspicious": is_suspicious,
            "dimensions": f"{width}x{height}",
            "format": image.format or "UNKNOWN",
            "lsb_ratio": lsb_data["lsb_ratio"],
            "lsb_suspicious": lsb_data["lsb_suspicious"],
            "histogram_pair_diff": hist_data["histogram_pair_diff"],
            "histogram_suspicious": hist_data["histogram_suspicious"],
            "entropy_suspicious": entropy_suspicious,
            "suspicious_signal_count": sum(flags),
            "decision_policy": decision_policy,
            "zone_analysis": {
                "start": res_start,
                "middle": res_mid,
                "end": res_end,
            },
            "diagnosis": (
                "HIGH PROBABILITY OF STEGANOGRAPHY DETECTED"
                if is_suspicious
                else "No steganographic anomalies detected"
            ),
        }

    except Exception as exc:
        return {
            "result": "ERROR",
            "is_suspicious": False,
            "error": str(exc),
        }
