import io
from PIL import Image
import math

def calculate_entropy(data):
    if not data:
        return 0
    entropy = 0
    for x in range(256):
        p_x = float(data.count(x))/len(data)
        if p_x > 0:
            entropy += - p_x*math.log(p_x, 2)
    return entropy

def analyze_image_lsb(image_bytes: bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Asegurar un formato procesable (RGB o RGBA para conservar el canal Alpha si existe)
        if image.mode not in ("RGB", "RGBA", "L"):
            image = image.convert("RGB")
        
        width, height = image.size
        total_pixels = width * height
        
        # Tamaño de muestra dinámico
        sample_size = min(500000, total_pixels)
        
        import itertools
        def get_entropy_for_sample(pixel_iter):
            lsb1_list = [] # Bit 0
            lsb2_list = [] # Bit 1
            
            for pixel in pixel_iter:
                # Manejar píxeles que pueden ser enteros (L) o tuplas (RGB, RGBA)
                channels = [pixel] if isinstance(pixel, int) else pixel
                for val in channels:
                    lsb1_list.append(val & 1)
                    lsb2_list.append((val >> 1) & 1)
            
            if not lsb1_list: return {"e1": 0, "r1": 0, "e2": 0, "r2": 0}

            def bits_to_entropy(bits):
                b_list = []
                # Solo procesamos si tenemos suficientes bits para formar bytes
                for i in range(0, len(bits) - 8, 8):
                    byte_val = 0
                    for j in range(8):
                        byte_val = (byte_val << 1) | bits[i + j]
                    b_list.append(byte_val)
                return calculate_entropy(b_list), (sum(bits)/len(bits))

            e1, r1 = bits_to_entropy(lsb1_list)
            e2, r2 = bits_to_entropy(lsb2_list)
            return {"e1": e1, "r1": r1, "e2": e2, "r2": r2}

        # Tomar muestras de 3 puntos: Inicio, Mitad y Final
        start_sample = list(itertools.islice(image.getdata(), sample_size))
        
        mid_offset = max(0, (total_pixels // 2) - (sample_size // 2))
        mid_sample = list(itertools.islice(image.getdata(), mid_offset, mid_offset + sample_size))
        
        end_offset = max(0, total_pixels - sample_size)
        end_sample = list(itertools.islice(image.getdata(), end_offset, total_pixels))
        
        res_start = get_entropy_for_sample(start_sample)
        res_mid = get_entropy_for_sample(mid_sample)
        res_end = get_entropy_for_sample(end_sample)
        
        # Marcamos como sospechoso si cualquier zona tiene entropía crítica en LSB1 o LSB2
        is_suspicious = any(r["e1"] > 7.9 or r["e2"] > 7.9 for r in [res_start, res_mid, res_end])
        
        return {
            "status": "success",
            "format": image.format if image.format else "Imagen",
            "mode": image.mode,
            "dimensions": f"{width}x{height}",
            "analysis_details": {
                "start_zone": res_start,
                "middle_zone": res_mid,
                "end_zone": res_end
            },
            "is_suspicious": is_suspicious,
            "diagnosis": "ALTA PROBABILIDAD DE ESTEGANOGRAFÍA (2-LSB)" if is_suspicious else "No se detectaron anomalías evidentes"
        }



        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
