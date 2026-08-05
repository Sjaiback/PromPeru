# Sistema de Atención · PROMPERÚ Macro Región Centro Este

Aplicación Django para registro público de visitas, atención por asesores, seguimiento, evaluación empresarial, auditoría, BI y archivo mensual.

## Accesos actuales

- Formulario público: `http://IP-SERVIDOR:8000/`
- Login de asesores: `http://IP-SERVIDOR:8000/cuentas/ingresar/`
- Usuario inicial: `jvillaverdemontes`
- Contraseña inicial: `Sebas0203@`

La cuenta inicial corresponde a Jaime Sebastian Villaverde Montes, documento 75371089, cargo Ingeniero Sistema. Tiene permisos de asesor, BI, archivo mensual y administración. El correo proporcionado no contiene dominio; por ese motivo la recuperación automática de contraseña queda pendiente hasta registrar una dirección válida.

## Flujo del visitante

1. Ingresa DNI o RUC sin iniciar sesión.
2. Si existe, el sistema recupera el registro y solo solicita tipo de atención y responsable.
3. La opción **Actualizar mis datos** abre el resto del formulario.
4. Si es nuevo, el formulario completo se abre automáticamente.
5. La atención se guarda en la base de datos y entra a la bandeja del responsable.

La consulta inicial no devuelve teléfono ni correo al navegador hasta que se solicita actualizar. Para una futura publicación en Internet se recomienda añadir verificación por código enviado al contacto antes de mostrar datos personales.

## Flujo del asesor

- Cada usuario se vincula con un Responsable mediante `PerfilAsesor`.
- Al registrar una atención, el responsable se asigna automáticamente al asesor conectado.
- Puede consultar y actualizar empresas, atenciones, seguimientos y evaluaciones.
- Las modificaciones registran usuario, fecha, IP, valores anteriores y nuevos.
- La eliminación operativa es por anulación o desactivación; el historial de auditoría se conserva.

## Evaluación empresarial

El comando siguiente interpreta las filas 5, 6 y 7 de `SISTEMATIZAR.xlsx` y crea preguntas configurables por categoría:

```powershell
python manage.py cargar_criterios_excel "E:\PromPeru\SISTEMATIZAR.xlsx"
```

Actualmente hay 89 preguntas de asesor generadas desde el archivo. Se administran sin crear una tabla plana de más de 140 columnas.

## PostgreSQL local

La instancia actual usa:

- Servidor: `127.0.0.1:5432`
- Base: `PromPeru`
- Usuario: `postgres`

La contraseña está en `config/local_settings.py`, archivo excluido de Git. Antes de publicar o migrar, reemplázala por una variable de entorno. El mismo ORM permitirá migrar posteriormente a Supabase PostgreSQL sin reescribir la lógica.

## Instalación sin permisos de administrador

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_iniciales
python manage.py cargar_criterios_excel "E:\PromPeru\SISTEMATIZAR.xlsx"
python manage.py runserver 0.0.0.0:8000
```

Después de la instalación también puede iniciarse con doble clic en `iniciar_lan.bat`.

## Archivo mensual y liberación de espacio

El administrador elige un rango de fechas y genera un ZIP con:

- `00_GLOBAL_atenciones.xlsx`
- Un Excel separado por cada asesor.

El ZIP incluye atención, empresa, contacto, estado, seguimientos y rating. Se registra un checksum SHA-256. La depuración solo se habilita después de descargar el ZIP y exige escribir `DEPURAR`.

La depuración elimina únicamente atenciones, gestiones y seguimientos del periodo. Conserva empresas, contactos, asesores, usuarios, ratings, archivos generados y auditoría.

## Pruebas

```powershell
python manage.py check
python manage.py test
```
# PromPeru
