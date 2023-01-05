from fastapi import FastAPI


app = FastAPI()


@app.get('/ocreniisan')
async def read_root():
    return {'Hello': 'World'}
