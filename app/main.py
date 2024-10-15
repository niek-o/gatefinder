from fastapi import FastAPI

from app.routers import flights

app = FastAPI()


app.include_router(flights.router)


@app.get("/")
async def root():
    return {"message": "Hello World!"}
