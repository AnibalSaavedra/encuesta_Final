# Encuesta Satisfacción CRB – Fix .env sin espacios en clave

## Credenciales
`.env` incluido ya corregido:
```env
SMTP_USER="estudios.preventivos@gmail.com"
SMTP_PASS="utkiwdegorrlinmq"
REPORTE_TO="estudios.preventivos@gmail.com"
```

⚠️ IMPORTANTE: la contraseña de aplicación de Gmail son 16 caracteres sin espacios.  
Si copias con espacios, el envío fallará.

## Streamlit Cloud → Settings → Secrets
```toml
SMTP_USER = "estudios.preventivos@gmail.com"
SMTP_PASS = "utkiwdegorrlinmq"
REPORTE_TO = "estudios.preventivos@gmail.com"
```
