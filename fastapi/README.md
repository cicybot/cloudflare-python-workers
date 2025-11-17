# db commands
    
- https://developers.cloudflare.com/d1/wrangler-commands/


    npx wrangler d1 create quotes
    npx wrangler d1 execute quotes --local --file=./db_init.sql

    npx wrangler d1 execute quotes --remote --file=./db_init.sql

    npx wrangler d1 execute quotes --remote --command="select * from users"

