

# <script src="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.27.1/swagger-ui-bundle.js"></script>
# <link type="text/css" rel="stylesheet" href="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.27.1/swagger-ui.css">
SWAGGER_HTML = f"""<!DOCTYPE html>
<html>
<head>
<link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">

<link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
<title>FastAPI - Swagger UI</title>
</head>
<body>
<div id="swagger-ui">
</div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>


<script>
    const ui = SwaggerUIBundle({{
    url: '/openapi.json',
    "dom_id": "#swagger-ui",
"layout": "BaseLayout",
"deepLinking": true,
"showExtensions": true,
"showCommonExtensions": true,
oauth2RedirectUrl: window.location.origin + '/docs/oauth2-redirect',
    presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
    }})
</script>
</body>
</html>
"""

auth_strip_path_prefixes = [
    "/api/auth/login",
    "/api/auth/password",
    "/api/d1/admin",
]

CORS_OPTIONS = {
    "allow_origins":[
        "*",
    ],
    "allow_credentials":True,
    "allow_methods":["*"],
    "allow_headers":["*"],
}