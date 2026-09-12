from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow the React dev server to make requests to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "SmartFlow backend is running"}


@app.get("/traffic")
def get_dummy_traffic():
    dummy_data = [
        {
            "road": "North",
            "cars": 24,
            "bikes": 10,
            "bus": 2,
            "truck": 1,
            "ambulance": False,
            "congestion": "Medium",
            "priority_score": 68,
            "green_time": 50
        },
        {
            "road": "East",
            "cars": 15,
            "bikes": 6,
            "bus": 1,
            "truck": 2,
            "ambulance": False,
            "congestion": "Low",
            "priority_score": 42,
            "green_time": 30
        },
        {
            "road": "South",
            "cars": 30,
            "bikes": 8,
            "bus": 3,
            "truck": 0,
            "ambulance": True,
            "congestion": "High",
            "priority_score": 100,
            "green_time": 60
        },
        {
            "road": "West",
            "cars": 10,
            "bikes": 4,
            "bus": 0,
            "truck": 1,
            "ambulance": False,
            "congestion": "Low",
            "priority_score": 25,
            "green_time": 20
        }
    ]
    return dummy_data