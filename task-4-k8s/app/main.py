from fastapi import FastAPI
import math

app = FastAPI(
    title="CPU Intensive App for K8s HPA Demo"
)

@app.get("/")
def read_root():
    return {"message": "Hello! The app is running. Hit /load to generate CPU load."}


@app.get("/load")
def generate_cpu_load():
    """
    This endpoint performs a CPU-intensive calculation to simulate load.
    It calculates a large number of square roots.
    """
    start_time = math.factorial(100000) # This is a dummy CPU-intensive task
    # A loop is more reliable for sustained load
    for i in range(50000000):
        _ = math.sqrt(i)
    return {"message": "CPU load generated successfully!"}