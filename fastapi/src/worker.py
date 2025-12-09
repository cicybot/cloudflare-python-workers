from workers import WorkerEntrypoint
from app import app
from service.Global import Global

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        import asgi
        env = self.env
        
        Global.init_cloudflare({
            "CLOUDFLARE_API_TOKEN":env.CLOUDFLARE_API_TOKEN,
            "CLOUDFLARE_ACCOUNT_ID":env.CLOUDFLARE_ACCOUNT_ID,
            "CLOUDFLARE_DATABASE_ID":env.CLOUDFLARE_DATABASE_ID,
            "JWT_SECRET_KEY":env.JWT_SECRET_KEY,
            "CLOUDFLARE_KV_NAMESPACE_ID":env.CLOUDFLARE_KV_NAMESPACE_ID,
            "INFO_URL":env.INFO_URL,
            "OTP_g_cicybot":env.OTP_g_cicybot,
            "OTP_g_cic_bot":env.OTP_g_cic_bot,
            "PWD_PERSONAL":env.PWD_PERSONAL
        })
        return await asgi.fetch(app, request.js_object, self.env)