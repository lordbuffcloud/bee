import uvicorn
from dotenv import find_dotenv, load_dotenv

from bee.app import create_app


load_dotenv(find_dotenv())

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host=app.state.settings.host, port=app.state.settings.port)
