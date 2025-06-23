
# Activación de Joi en GymProject (versión final)

✅ Esta versión incluye:
- Toda la lógica original de Joi (motivación, logros, emociones, recuerdos).
- Todos los templates y archivos estáticos.
- Avatares reubicados correctamente en `static/joi/avatars/`.

---

## Pasos para activar Joi

1. **Activar la app Joi**
   - Abre `gymproject/settings.py`
   - Añade `'joi'` a `INSTALLED_APPS`

2. **Incluir las rutas Joi**
   - Abre `gymproject/urls.py`
   - Añade:
     from django.urls import include
     path('joi/', include('joi.urls')),

3. **Migrar los modelos**
   - Ejecuta en terminal:
     python manage.py makemigrations joi
     python manage.py migrate

4. **Ver las vistas de Joi**
   - Accede a:
     http://localhost:8000/joi/recuerdos/
     http://localhost:8000/joi/diario/

5. **Revisar los modelos integrados**
   - `RecuerdoEmocional`, `EstadoEmocional`, `Entrenamiento`, `MotivacionUsuario`, `Logro`, `EventoLogro`.

6. **Ajustes que se aplicaron**
   - Las imágenes de `core/avatars/` fueron movidas a `static/joi/avatars/`.
   - Templates como `diario_resumen.html` ya usan esta nueva ruta.
   - Se detectaron rutas limpias, sin necesidad de refactor en los `views`, `forms`, ni `urls`.

---

¡Todo listo para que Joi funcione dentro de tu GymProject!

