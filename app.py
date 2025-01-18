from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def example():
    return {'message':'welcome to first app using fastapi'}
