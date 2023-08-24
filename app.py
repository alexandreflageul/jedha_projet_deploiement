from fastapi import FastAPI
from typing import List
from pydantic import BaseModel

app = FastAPI()


class PredictionInput(BaseModel):
    input_data: List[float]

        
@app.post("/predict", tags=["POST", "MachineLearning"])
async def whats_my_price(inputpath_to_model, json_data):
    # load the model
    model = tf.keras.load_model("model/get_my_price.model.sav")
    # transforme input
    transformed_input = model.transform(data)
    # realise prediction
    rental_price = model.predict(transformed_input)
    # return nice sentence with the rental daily price
    return f"It seams that your car could be rent for {rental_price} euros per day"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)
