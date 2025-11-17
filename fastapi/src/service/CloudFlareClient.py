import httpx
import logging
from typing import List, Any, Optional
from service.Global import Global

logger = logging.getLogger(__name__)

class CloudFlareClient:
    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if CloudFlareClient._instance is not None:
            raise RuntimeError("请使用 CloudFlareClient.get_instance() 获取单例实例，不要直接构造。")

        account_id = Global.get_options("CLOUDFLARE_ACCOUNT_ID")
        db_id = Global.get_options("CLOUDFLARE_DATABASE_ID")
        kv_id = Global.get_options("CLOUDFLARE_KV_NAMESPACE_ID")
        self.headers = Global.get_options("cf_api_headers")

        if not all([account_id,db_id,self.headers]):
            raise ValueError(
                "Please set "
                "CLOUDFLARE_ACCOUNT_ID, "
                "CLOUDFLARE_DATABASE_ID, "
                "CLOUDFLARE_API_TOKEN environment variables"
            )

        cf_api_base_url = Global.get_options("cf_api_base_url")
        self.cf_d1_api_base_url = f"{cf_api_base_url}/{account_id}/d1/database/{db_id}"
        self.cf_kv_api_base_url = f"{cf_api_base_url}/{account_id}/storage/kv/namespaces/{kv_id}"

    async def _fetch(self,method:str,url:str, payload: dict[str, str | list] | list):
        logging.debug("[REQ] url: %s,payload: %s",url,payload)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
        response.raise_for_status()
        data = response.json()

        if Global.is_local():
            import pprint
            pprint.pprint(data)

        return data


    async def _kv_bulk(self,rows:list):
        """
         rows: Array<{
            key: string
            (maxLength: 512)
            A key's name. The name may be at most 512 bytes. All printable, non-whitespace characters are valid.

            value: string
            (maxLength: 26214400)
            A UTF-8 encoded string to be stored, up to 25 MiB in length.

            base64: booleanOptional
            Indicates whether or not the server should base64 decode the value before storing it. Useful for writing values that wouldn't otherwise be valid JSON strings, such as images.

            expiration: numberOptional
            Expires the key at a certain time, measured in number of seconds since the UNIX epoch.

            expiration_ttl: numberOptional
            (minimum: 60)
            Expires the key after a number of seconds. Must be at least 60.

            metadata: unknownOptional
            Arbitrary JSON that is associated with a key.

curl https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/storage/kv/namespaces/$NAMESPACE_ID/bulk \
    -X PUT \
    -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -d '[
          {
            "key": "My-Key",
            "value": "Some string",
            "base64": true,
            "expiration": 1578435000,
            "expiration_ttl": 300,
            "metadata": {}
          }
        ]'

        """
        url = f"{self.cf_kv_api_base_url}/bulk"
        return await self._fetch("put",url,rows)

    async def _kv_bulk_delete(self,keys: list):
        url = f"{self.cf_kv_api_base_url}/bulk/delete"
        return await self._fetch("post",url,keys)

    async def _kv_bulk_get(self,keys: list):
        payload = {
            "keys": keys
        }
        url = f"{self.cf_kv_api_base_url}/bulk/get"
        return await self._fetch("post",url,payload)

    async def kv_get(self, key: str):
        res = await self._kv_bulk_get([key])
        success = res.get("success",False)
        if success:
            value = res.get("result",{}).get("values",{}).get(key,None)
            return value
        return None

    async def kv_get_batch(self, keys: list):
        return await self._kv_bulk_get(keys)


    async def kv_put(self, key: str,value: str):
        # {
        #     "result": {
        #         "successful_key_count": 1,
        #         "unsuccessful_keys": []
        #     },
        #     "success": true,
        #     "errors": [],
        #     "messages": []
        # }
        res = await self._kv_bulk([
            {
                "key":key,
                "value":value
            }
        ])
        success = res.get("success",False)
        if success:
            result = res.get("result",{})
            successful_key_count = result.get("successful_key_count",{})
            return successful_key_count == 1
        return False

    async def kv_put_batch(self,rows:list):
        return await self._kv_bulk(rows)
    async def kv_delete(self, key: str):
        res = await self._kv_bulk_delete([key])
        success = res.get("success",False)
        if success:
            result = res.get("result",{})
            successful_key_count = result.get("successful_key_count",{})
            return successful_key_count == 1
        return False
    async def kv_delete_batch(self, keys: list):
        return await self._kv_bulk_delete(keys)

    async def d1_exec(self, sql: str, params: Optional[List[Any]] = None):
        payload = {"sql": sql}
        if params:
            payload["params"] = params
        url = f"{self.cf_d1_api_base_url}/raw"
        return self.handle_d1_result_data(await self._fetch("post",url,payload))

    async def d1_query(self, sql: str, params: Optional[List[Any]] = None):
        payload = {"sql": sql}
        if params:
            payload["params"] = params

        url = f"{self.cf_d1_api_base_url}/query"
        return self.handle_d1_result_data(await self._fetch("post",url,payload))
    @classmethod
    def handle_d1_result_data(cls,data):
        success = data['success']
        rows = []
        info = {}
        if success is True:
            meta = data.get('result', [{}])[0].get('meta', {})
            info["duration"] = meta.get("duration")
            info["last_row_id"] = meta.get("last_row_id")
            info["changes"] = meta.get("changes")
            results_data = data.get('result', [{}])[0].get('results', {})
            if isinstance(results_data, list):
                rows = results_data
            elif isinstance(results_data, dict):
                rows_data = results_data.get('rows', [])
                columns = results_data.get('columns', [])
                rows = [dict(zip(columns, row)) for row in rows_data]
            if 'result' in data and data['result']:
                del data['result'][0]['results']
        logging.debug("[RES] rows: %s", rows)
        return {
            "rows":rows,
            "execInfo":info,
        }