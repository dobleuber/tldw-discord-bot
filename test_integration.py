"""
Script de prueba para verificar la integración completa del bot.
"""
import asyncio
import os
from dotenv import load_dotenv
from tldw.services.content_service import extract_youtube_transcript
from tldw.services.gemini_service import generate_summary_with_gemini
from tldw.utils.redis_cache import add_to_cache, get_from_cache, clear_cache

async def test_full_workflow():
    """Prueba el flujo completo del bot: extracción, resumen y caché."""
    # Cargar variables de entorno
    load_dotenv()
    
    # URL de prueba
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"Probando el flujo completo con la URL: {test_url}")
    
    # Comprobar si el resumen ya está en caché
    cached_summary = get_from_cache(test_url)
    if cached_summary:
        print("✅ Resumen encontrado en caché:")
        print(cached_summary)
        print("\nLimpiando caché para probar la generación...")
        clear_cache()
    
    # Paso 1: Extraer la transcripción
    print("\n--- EXTRAYENDO TRANSCRIPCIÓN ---")
    try:
        transcript = await extract_youtube_transcript(test_url)
        if transcript:
            print(f"✅ Transcripción extraída correctamente ({len(transcript)} caracteres)")
            print(f"Primeros 200 caracteres: {transcript[:200]}...")
        else:
            print("❌ No se pudo extraer la transcripción")
            return
    except Exception as e:
        print(f"❌ Error al extraer la transcripción: {e}")
        return
    
    # Paso 2: Generar resumen
    print("\n--- GENERANDO RESUMEN ---")
    try:
        summary = await generate_summary_with_gemini(transcript)
        if summary:
            print("✅ Resumen generado correctamente:")
            print(summary)
        else:
            print("❌ No se pudo generar el resumen")
            return
    except Exception as e:
        print(f"❌ Error al generar el resumen: {e}")
        return
    
    # Paso 3: Guardar en caché
    print("\n--- GUARDANDO EN CACHÉ ---")
    try:
        add_to_cache(test_url, summary)
        print("✅ Resumen guardado en caché")
        
        # Verificar que se guardó correctamente
        cached_summary = get_from_cache(test_url)
        if cached_summary == summary:
            print("✅ Verificación exitosa: El resumen se recuperó correctamente de la caché")
        else:
            print("❌ Verificación fallida: El resumen recuperado no coincide con el original")
    except Exception as e:
        print(f"❌ Error al guardar en caché: {e}")
    
    print("\nPrueba de integración completa.")

if __name__ == "__main__":
    asyncio.run(test_full_workflow())
