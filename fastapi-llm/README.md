

    uv init --app
    uv add fastapi --extra standard

    docker build -t fastapi-app .
    docker run -p 8000:80 fastapi-app

    export PYTHONPATH=$PYTHONPATH:$(pwd)/app
    uv run fastapi dev app/app.py 
