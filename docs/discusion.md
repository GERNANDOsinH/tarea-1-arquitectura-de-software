# Discusión: trade-offs y Back of the Envelope (BORRADOR)

> Borrador escrito por el publisher; el equipo debe revisarlo y ajustarlo a lo que finalmente implementen.

## 1. Trade-offs de la arquitectura

**Publish-subscribe con broker (RabbitMQ).**
- (+) Desacople: el publisher no conoce ni espera a los 5 subscribers; agregar una ciudad no cambia el publisher.
- (+) Con colas durables y mensajes persistentes, un subscriber caído recibe los sismos pendientes al volver.
- (−) El broker es un punto único de falla y un componente más que operar. En este dominio es relevante (alertas), por lo que en producción se justificaría un clúster/quorum queues.
- (−) Fanout entrega todo a todos: cada subscriber procesa también sismos que no le interesan. Aceptable aquí (mensajes de ~100 bytes y 5 consumidores). Alternativa: un topic exchange por zona geográfica; se descartó porque el enunciado pide que el filtro lo haga cada subscriber y complicaría el publisher.

**Mensaje mínimo + pull del detalle (en vez de push del sismo completo).**
- (+) Mensajes pequeños y rápidos; el detalle se baja solo cuando interesa (hoy solo una parte de los 5 lo pedirá).
- (+) El detalle puede actualizarse (los sismos se revisan: la magnitud preliminar cambia) sin republicar.
- (−) Latencia extra: un round trip http después de la notificación. En un sismo importante se suma al retraso total.
- (−) Acoplamiento temporal con el servicio http: si cae, el subscriber sabe que hay un sismo pero no su detalle (necesita reintentos). Además, varios subscribers interesados golpean el servicio casi a la vez (ráfaga).
- (−) Con el push, cada subscriber es autónomo; con el pull depende de un servicio adicional.

**Entrega.** El publisher usa confirms y mensajes persistentes: garantiza *at-least-once* hacia el broker; por eso los subscribers deben tolerar duplicados (usar `id` para idempotencia). Con `mandatory` se detecta que no había colas enlazadas.

**¿Importa en el dominio?** Sí en latencia y disponibilidad (alertas tempranas): el costo del round trip y la caída del http son lo más sensible. El volumen no es un problema (ver sección 2).

## 2. Back of the Envelope (cómo se calcularía, sin calcular)

Datos del fenómeno para estimar:
- **Frecuencia de sismos:** nº de eventos por día/año que reporta el servicio de sismología (incluye muchos sismos pequeños); considerar los picos por réplicas tras un terremoto (órdenes de magnitud más que el promedio).
- **Tamaño del mensaje:** ~100 bytes (id, datetime, latitude, longitude en JSON). Tráfico del publisher = frecuencia × tamaño.
- **Fan-out:** mensajes entregados = sismos × 5 subscribers.
- **Fracción de interés:** proporción de sismos a < 500 km de cada ciudad (depende de la distribución espacial de la sismicidad: Chile es una franja larga, por lo que cada ciudad cubre ~1000 km de costa). Consultas http = sismos × (suma de las fracciones de interés), con un pico de hasta 5 consultas casi simultáneas por sismo grande.
- **Tamaño de la respuesta http:** del orden de 1 KB por detalle; ancho de banda = consultas × tamaño.
- **Latencia:** publicación + entrega del broker + cálculo de distancia (haversine, trivial) + round trip http.

Con estas cifras se vería si el uso de un solo broker y un servicio http simple alcanza (probablemente sí por varios órdenes de magnitud) y cuánto margen hay en un pico por réplicas, lo que justifica la arquitectura propuesta.
