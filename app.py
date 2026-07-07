from flask import Flask, redirect, url_for, render_template, request, abort
import requests

app = Flask(__name__)

api_key = "spxZenhUmF6c3Z4lbpq7ymb5KantH2cHl78cbKUf"
nasa_api = "https://api.nasa.gov/planetary/apod"
mars_api = "https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos"

manifest_api = "https://api.nasa.gov/mars-photos/api/v1/manifests/curiosity"

BACKUP_MANIFEST = {
    "photo_manifest": {
        "name": "Curiosity",
        "launch_date": "2011-11-26",
        "landing_date": "2012-08-06",
        "total_photos": 683512,
        "max_sol": 4100
    }
}

BACKUP_PHOTOS = {
    "photos": [
        {
            "img_src": "https://mars.nasa.gov/msl-raw-images/proj/msl/redops/ods/surface/sol/01000/opgs/edr/fcam/FLB_486265257EDR_F0481570FHAZ00323M_.JPG", 
            "camera": {"full_name": "Front Hazard Avoidance Camera"}
        },
        {
            "img_src": "https://mars.nasa.gov/msl-raw-images/proj/msl/redops/ods/surface/sol/01000/opgs/edr/fcam/FRB_486265257EDR_F0481570FHAZ00323M_.JPG", 
            "camera": {"full_name": "Front Hazard Avoidance Camera"}
        },
        {
            "img_src": "https://mars.nasa.gov/msl-raw-images/proj/msl/redops/ods/surface/sol/01000/opgs/edr/rcam/RLB_486265291EDR_F0481570RHAZ00323M_.JPG", 
            "camera": {"full_name": "Rear Hazard Avoidance Camera"}
        }
    ]
}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/apod")
@app.route("/apod/")
@app.route("/apod/<date>")
def apod(date="today"):
    data = get_apod(date)
    return render_template("apod.html", apod=data)


@app.route("/mars", methods=["GET", "POST"])
def mars():
    manifest = get_rover_manifest()

    if request.method == "POST":
        sol = request.form.get("sol", 1000)
        camera = request.form.get("camera", "fhaz")
    else:
        sol = 1000
        camera = "fhaz"

    data = get_rover_photos(sol, camera)

    if "error_code" in data or "error_code" in manifest:
        print("NASA API down. Filtering local fallback photos matrix.")
        
        filtered_photos = [
            p for p in BACKUP_PHOTOS["photos"] 
            if camera == "fhaz" and "fcam" in p["img_src"] or
               camera == "rhaz" and "rcam" in p["img_src"]
        ]
        
        if not filtered_photos:
            filtered_photos = BACKUP_PHOTOS["photos"]

        return render_template(
            "mars.html", 
            photos=filtered_photos, 
            mission=BACKUP_MANIFEST.get("photo_manifest", {}), 
            error=None
        )

    return render_template(
        "mars.html", 
        photos=data.get("photos", []), 
        mission=manifest.get("photo_manifest", {}), 
        error=None
    )


def get_apod(date):
    params = {"api_key": api_key}
    if date != "today":
        params["date"] = date

    res = requests.get(nasa_api, params)

    if res.status_code != 200:
        error_apod = {
            "title": f"API Error - {res.status_code}",
            "explanation": "Something went wrong...",
            "url": url_for("static", filename="fail.jpg"),
        }
        return error_apod
    return res.json()


def get_rover_photos(sol, camera):
    params = {"api_key": api_key, "sol": sol, "camera": camera, "page": 1}
    try:
        res = requests.get(mars_api, params, timeout=10)
        if res.status_code != 200:
            return {"error_code": res.status_code}
        return res.json()
    except Exception:
        return {"error_code": "exception_raised"}


def get_rover_manifest():
    params = {"api_key": api_key}
    try:
        res = requests.get(manifest_api, params, timeout=10)
        if res.status_code != 200:
            return {"error_code": res.status_code}
        return res.json()
    except Exception:
        return {"error_code": "exception_raised"}


@app.errorhandler(404)
def page_not_found(err):
    return render_template("404.html"), 404