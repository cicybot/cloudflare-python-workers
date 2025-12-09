import os

class Global:
    _options = {}
    @classmethod
    def is_local(cls):
        return os.getenv("IS_LOCAL",None) is not None

    @classmethod
    def init_cloudflare(cls, options=None):
        cls._options = options
        cls._options['is_cf'] = True

    @classmethod
    def get_options(cls,k =None):
        if k is not None:
            return cls._options.get(k,None)
        return cls._options

    @classmethod
    def init(cls):
        if cls._options.get("PWD_PERSONAL") is None:
            cls._options['PWD_PERSONAL'] = os.getenv("PWD_PERSONAL")
        if cls._options.get("INFO_URL") is None:
            cls._options['INFO_URL'] = os.getenv("INFO_URL")
        if cls._options.get("OTP_g_cic_bot") is None:
            cls._options['OTP_g_cic_bot'] = os.getenv("OTP_g_cic_bot")
        if cls._options.get("OTP_g_cicybot") is None:
            cls._options['OTP_g_cicybot'] = os.getenv("OTP_g_cicybot")
        if cls._options.get("CLOUDFLARE_API_TOKEN") is None:
            cls._options['CLOUDFLARE_API_TOKEN'] = os.getenv("CLOUDFLARE_API_TOKEN")
        if cls._options.get("CLOUDFLARE_ACCOUNT_ID") is None:
            cls._options['CLOUDFLARE_ACCOUNT_ID'] = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        if cls._options.get("CLOUDFLARE_DATABASE_ID") is None:
            cls._options['CLOUDFLARE_DATABASE_ID'] = os.getenv("CLOUDFLARE_DATABASE_ID")
        if cls._options.get("CLOUDFLARE_KV_NAMESPACE_ID") is None:
            cls._options['CLOUDFLARE_KV_NAMESPACE_ID'] = os.getenv("CLOUDFLARE_KV_NAMESPACE_ID")


        if cls._options.get("SWAGGER_USERNAME") is None:
            cls._options['SWAGGER_USERNAME'] = os.getenv("SWAGGER_USERNAME","admin")

        if cls._options.get("SWAGGER_PASSWORD") is None:
            cls._options['SWAGGER_PASSWORD'] = os.getenv("SWAGGER_PASSWORD","admin888")

        if cls._options.get("JWT_SECRET_KEY") is None:
            #  openssl rand -hex 32
            cls._options['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY","fa41173515a08b3060d6527544156c1f4a1079174f56e94a2ee3721a27fe99fa")

        if cls._options.get("JWT_ALGORITHM") is None:
            cls._options['JWT_ALGORITHM'] = os.getenv("JWT_ALGORITHM","HS256")

        if cls._options.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES") is None:
            cls._options['JWT_ACCESS_TOKEN_EXPIRE_MINUTES'] = os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES","30")

        cls._options['JWT_ACCESS_TOKEN_EXPIRE_MINUTES'] = int(cls._options['JWT_ACCESS_TOKEN_EXPIRE_MINUTES'])

        if not all([
            cls._options.get("CLOUDFLARE_API_TOKEN"),
            cls._options.get("CLOUDFLARE_ACCOUNT_ID"),
            cls._options.get("CLOUDFLARE_DATABASE_ID"),
            cls._options.get("CLOUDFLARE_KV_NAMESPACE_ID")
        ]
        ):
            raise ValueError(
                "Please set "
                "CLOUDFLARE_ACCOUNT_ID, "
                "CLOUDFLARE_DATABASE_ID, "
                "CLOUDFLARE_KV_NAMESPACE_ID, "
                "CLOUDFLARE_API_TOKEN "
                "environment variables"
            )
        cls._options['cf_api_base_url'] = f"https://api.cloudflare.com/client/v4/accounts"
        cls._options['cf_api_headers'] = {
            "Authorization": f"Bearer {cls._options['CLOUDFLARE_API_TOKEN']}",
            "Content-Type": "application/json"
        }

