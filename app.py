from astroagent import astro_agent
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# ====== MODELS ======
class InputData(BaseModel):
    name: str
    birth_date: str  # YYYY-MM-DD
    birth_time: str  # HH:MM
    city_name: str

class PredictionResult(BaseModel):
    name: str
    ascendant: str
    moon_sign: str
    prediction: str


@app.post("/predict", response_model=PredictionResult)
def predict(data: InputData):
    state = {
        "name": data.name,
        "birth_date": data.birth_date,
        "birth_time": data.birth_time,
        "city_name":data.city_name
    }
    result = astro_agent.invoke(state)

    return PredictionResult(
        name=data.name,
        ascendant=result["ascendant"],
        moon_sign=result["moon_sign"],
        prediction=result["prediction"]
    )