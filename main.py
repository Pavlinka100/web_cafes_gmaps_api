from flask import Flask, jsonify, render_template, request,  redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, Float, and_, text, or_
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, URL, NumberRange
from werkzeug.security import check_password_hash
from flask_googlemaps import GoogleMaps, Map
import requests
import os



app = Flask(__name__)

GOOGLE_MAPS_KEY = os.environ.get("GOOGLE_MAPS_KEY")
SECRET_KEY = os.environ.get("FLASK_APP_SECRET_KEY")

GoogleMaps(app, key=GOOGLE_MAPS_KEY)

app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap5(app)

class Base(DeclarativeBase):
    pass
# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)
    lat: Mapped[str] = mapped_column(Float, nullable=False)
    lon: Mapped[str] = mapped_column(Float, nullable=False)


with app.app_context():
    db.create_all()


#FORMS
class SearchForm(FlaskForm):
    location = StringField('City or area')
    has_toilet = BooleanField('Toilets')
    has_wifi = BooleanField('Wifi')


    can_take_calls = BooleanField('Calling')
    has_sockets = BooleanField('Power supply')
    submit = SubmitField('Search')

class LocateNewCafeForm(FlaskForm):
    text_input = StringField('Name and location of your cafe:', validators=[DataRequired()])
    submit = SubmitField('Locate')

class PriceUpdateForm(FlaskForm):
    coffee_price=StringField('New coffee price', validators=[DataRequired()])
    submit = SubmitField('Submit')

class DeleteConfirmationForm(FlaskForm):
    delete_key=PasswordField('Enter secret key', validators=[DataRequired()])
    submit = SubmitField('Confirm deletion')
class CafeForm(FlaskForm):
    name=StringField('Name', validators=[DataRequired()])

    seats=StringField('Number of seats', validators=[DataRequired()])
    coffee_price=StringField('Coffee price', validators=[DataRequired()])
    has_wifi = BooleanField('Is there wifi?')
    has_toilet = BooleanField('Are there toilets?')
    has_sockets = BooleanField('Are there sockets?')
    can_take_calls = BooleanField('Is OK to take call?')

    location = StringField('Location/address', validators=[DataRequired()])
    map_url = StringField('Map URL', validators=[DataRequired(), URL()])
    img_url = StringField('Image URL', validators=[DataRequired(), URL()])
    lat = StringField('Latitude', validators=[DataRequired(),NumberRange(min=-90, max=90, message="Please stay on our planet and input valid values")])
    lng = StringField('Longitude', validators=[DataRequired(), NumberRange(min=-180, max=180, message="Please stay on our planet and input valid values")])

    submit = SubmitField('Submit Cafe')
def create_map(cafes):
    markers_list = []
    if cafes:
        #if there is something wrong with the keys, maximal and minimal valid values are used
        try:
            max_lat = cafes[0].lat
            max_lon = cafes[0].lon
            min_lat = cafes[0].lat
            min_lon = cafes[0].lon
        except:
            max_lat = 90
            max_lon = 180
            min_lat = float(-90)
            min_lon = float(-180)


        for cafe in cafes:
            cafe_icons = ""
            if cafe.has_toilet:
                cafe_icons += f"<img src=\"{url_for('static', filename='assets/img/wc.png')}\" width=\'30px\'/>"
            if cafe.has_wifi:
                cafe_icons += f"<img src=\"{url_for('static', filename='assets/img/wifi.png')}\" width=\'30px\'/>"
            if cafe.can_take_calls:
                cafe_icons += f"<img src=\"{url_for('static', filename='assets/img/phone.png')}\" width=\'30px\'/>"
            if cafe.has_sockets:
                cafe_icons += f"<img src=\"{url_for('static', filename='assets/img/pwr.png')}\" width=\'30px\'/>"

            #DB allows float, validating the data
            if cafe.lat > 90:
                cafe.lat = 90
            if cafe.lon > 180:
                cafe.lon = 180
            if cafe.lat < -90:
                cafe.lat = -90
            if cafe.lon < -180:
                cafe.lon = -180


            marker = {
                'icon': 'http://maps.google.com/mapfiles/ms/icons/red-dot.png',
                'lat': cafe.lat,
                'lng': cafe.lon,
                'infobox': f"<a href = {url_for('show_cafe', cafe_id=cafe.id)} ><h6> {cafe.name} </h6> {cafe_icons} <br /> <img src='{cafe.img_url}' width='200px'/></a>",
            }

            #get the lat and lon min and max to adjust map centering
            if max_lat < cafe.lat:
                max_lat = cafe.lat
            if max_lon < cafe.lon:
                max_lon = cafe.lon
            if min_lat > cafe.lat:
                min_lat = cafe.lat
            if min_lon > cafe.lon:
                min_lon = cafe.lon
            markers_list.append(marker)
        print(markers_list)

        # diameter of max and min lat (lon) to center the map
        lat_center = (max_lat + min_lat) / 2
        lon_center = (max_lon + min_lon) / 2




    cafes_map = Map(
        identifier="all_cafes_map",
        lat=lat_center,
        lng=lon_center,
        markers=markers_list,
        style="height:500px;width:100%;margin:0;",
        fit_markers_to_bounds=True,
        maptype_control=False

    )
    return cafes_map


def get_empty_map():
    empty_map = Map(
        identifier="empty_map",
        lat=50,
        lng=10,
        markers=[],
        style="height:500px;width:100%;margin:0;",
        zoom=3,
        maptype_control=False

    )
    return empty_map

# HTTP GET - Read Record - API
@app.route("/cafe/<cafe_id>", methods=["GET"])
def show_cafe(cafe_id):
    chosen_cafe = db.session.execute(db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
    if chosen_cafe:
        return render_template("show_cafe.html", cafe=chosen_cafe)
    else:
        flash('Your cafe does not exist')
        return redirect(url_for('search'))



@app.route("/", methods=["GET", "POST"])
@app.route("/search", methods=["GET","POST"])
def search():

    search_form = SearchForm()

    if request.method == "GET":
        cafes = db.session.execute(db.select(Cafe)).scalars().all()
        if cafes:
            map = create_map(cafes)
            return render_template("search.html", cafes=cafes, map=map, h1="All cafes", form=search_form)
        else:
            flash("There is no cafe in the DB, please insert a new one")
            return redirect(url_for('locate'))

    else:



        if search_form.validate_on_submit():

            place = search_form.location.data
            place.replace(" ", "%20")

            has_toilet = search_form.has_toilet.data
            has_wifi = search_form.has_wifi.data
            has_sockets = search_form.has_sockets.data
            can_take_calls = search_form.can_take_calls.data


            conditions_string = ""
            if has_toilet:
                conditions_string += 'Cafe.has_toilet == True'
            if has_wifi:
                    if conditions_string == "":
                        conditions_string += 'Cafe.has_wifi == True'
                    else:
                        conditions_string += ' AND Cafe.has_wifi == True'
            if has_sockets:
                    if conditions_string == "":
                        conditions_string += 'Cafe.has_sockets == True'
                    else:
                        conditions_string += ' AND Cafe.has_sockets == True'
            if can_take_calls:
                    if conditions_string == "":
                        conditions_string += 'Cafe.can_take_calls == True'
                    else:
                        conditions_string += ' AND Cafe.can_take_calls == True'


            # get the candidates from the information given calling API
            myurl = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=\'{place}\'&key={GOOGLE_MAPS_KEY}"
            response = requests.get(url=myurl)
            print(response.status_code)
            print(response.json())

            if response.status_code != 200:
                response.raise_for_status()
                cafes = db.session.execute(db.select(Cafe).where(
                    and_(text(conditions_string), Cafe.location.icontains(place.lower())))).scalars().all()
            else:


                try:

                    # lat = response.json()['results'][0]['geometry']['location']['lat']
                    # lon = response.json()['results'][0]['geometry']['location']['lng']

                    lat_max = response.json()['results'][0]['geometry']['viewport']['northeast']['lat']
                    lat_min = response.json()['results'][0]['geometry']['viewport']['southwest']['lat']
                    lon_max = response.json()['results'][0]['geometry']['viewport']['northeast']['lng']
                    lon_min = response.json()['results'][0]['geometry']['viewport']['southwest']['lng']
                    lat_lon_condition = f'(Cafe.lat < {lat_max}) AND (Cafe.lat > {lat_min}) AND (Cafe.lon < {lon_max}) AND (Cafe.lon > {lon_min})'

                    if conditions_string != "":
                        lat_lon_condition = lat_lon_condition + ' AND ' + conditions_string
                    print(lat_lon_condition)
                    cafes = db.session.execute(db.select(Cafe).where(
                        or_(text(lat_lon_condition), Cafe.location.icontains(place.lower())))).scalars().all()

                except:

                    cafes = db.session.execute(db.select(Cafe).where(
                    and_(text(conditions_string), Cafe.location.icontains(place.lower())))).scalars().all()

            if not cafes:

                return render_template("search.html", form=search_form, h1 = "Nothing found",map = get_empty_map() )
            else:
                #create the map showing the cafes
                map = create_map(cafes)
                return render_template("search.html", cafes=cafes, map = map, h1 = "Your cafes", form=search_form)
        else:
            return render_template("search.html", form = search_form, h1 = "Search cafes", map = get_empty_map())


@app.route("/locate", methods=["POST", "GET"])
def locate():
    locate_form = LocateNewCafeForm()

    if locate_form.validate_on_submit():

        markers_list=[] #to create map markers
        place = locate_form.text_input.data
        place.replace(" ", "%20")
        place += "restaurant"

        #get the candidates from the information given calling API
        myurl = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=\'{place}\'&key={GOOGLE_MAPS_KEY}"
        response = requests.get(url=myurl)

        if response.status_code != 200:
            response.raise_for_status()
            flash("There is some issue with getting your cafes, please insert your data manually. ")
            return redirect(url_for('add'))
        else:
            try:
                candidates = response.json()['results']
            except KeyError:
                flash("There is some issue with getting your cafes, please insert your data manually. ")
                return redirect(url_for('add'))

            #create markers on the map to confirm the candidate
            for candidate in candidates:
                #take name, url, lat, lon, picture and show point on a map
                try:

                    photo_ref = candidate['photos'][0]['photo_reference']
                    request_photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=1000&photo_reference={photo_ref}&key={GOOGLE_MAPS_KEY}"
                    response_photo_url = requests.get(url=request_photo_url).url
                except:
                    #if there is something wrong with getting place picture simply assign some defaul picture
                    response_photo_url = "https://storage.googleapis.com/support-forums-api/attachment/thread-229005770-10479669858494658829.jpg"

                try:

                    candidate_marker = {
                        'icon': 'http://maps.google.com/mapfiles/ms/icons/red-dot.png',
                        'lat': candidate['geometry']['location']['lat'],
                        'lng': candidate['geometry']['location']['lng'],
                        'infobox': f"<h5> {candidate['name']} </h5> <br /> <a href={url_for('add')}?&lat={candidate['geometry']['location']['lat']}&place_id={candidate['place_id']}&lng={candidate['geometry']['location']['lng']}&photo_url={response_photo_url}&name={candidate['name'].replace(' ','%20')}&address={candidate['formatted_address'].replace(' ','%20')}>"
                                   f"<h6>Choose this cafe</h6> <a/> <br/><img src='{response_photo_url}' width='200px'/>",
                    }

                    markers_list.append(candidate_marker)


                except KeyError:
                    flash("There is some issue with getting your suggestions, please insert your data manually. ")
                    return redirect(url_for('add'))

            try:
                lat = markers_list[0]['lat']
                lon = markers_list[0]['lng']
            except:
                lat = 51
                lon = 0



            map = Map(
                identifier="located_points_map",
                lat=lat,
                lng=lon,
                markers=markers_list,
                style="height:500px;width:100%;margin:0;",
                zoom=13
            )

            #return rendered map and submit button to submit new_cafe_form
            return render_template("search.html", h1="Confirm cafe", map = map, form=locate_form)


    else:
        map = get_empty_map()
        return render_template("search.html", form=locate_form, h1="Add a new cafe", map=map)

@app.route("/add", methods=["POST", "GET"])
def add():

    new_cafe_form = CafeForm()
    if request.method == 'GET':

        if request.args.get("name"):
            new_cafe_form.name.data = request.args.get("name")
            chosen_cafe = db.session.execute(db.select(Cafe).where(Cafe.name == new_cafe_form.name.data)).scalar()
            if chosen_cafe:
                flash("Your cafe already exists, wellcome at its page")
                return render_template("show_cafe.html", cafe=chosen_cafe)

        if request.args.get("place_id"):
            new_cafe_form.map_url.data = f"https://www.google.com/maps/place/?q=place_id:{request.args.get('place_id')}"
        if request.args.get("lat"):
            new_cafe_form.lat.data = float(request.args.get("lat"))
        if request.args.get("lng"):
            new_cafe_form.lng.data = float(request.args.get("lng"))
        if request.args.get("photo_url"):
            new_cafe_form.img_url.data= request.args.get("photo_url")
        if request.args.get("address"):
            new_cafe_form.location.data = request.args.get("address")

    if request.method == 'POST':
        try:
            new_cafe_form.lat.data = float(new_cafe_form.lat.data)
            new_cafe_form.lng.data = float(new_cafe_form.lng.data)
        except:
            flash("Please stay somewhere on the Earth, insert valid latitude and longtitude")
            return render_template("add_new_cafe.html", form=new_cafe_form)


    if new_cafe_form.validate_on_submit():

        try:
            lat = float(new_cafe_form.lat.data)
            lon = float(new_cafe_form.lng.data)
        except:
            flash("Please stay somewhere on the Earth, insert valid latitude and longtitude")
            return render_template("add_new_cafe.html", form=new_cafe_form)


        if not (lat >= -90 and lat <= 90 and lon >= -180 and lon <= 180):
            flash("Please stay somewhere on the Earth, insert valid latitude and longtitude")
            return render_template("add_new_cafe.html", form = new_cafe_form)
        else:
            try:
                new_cafe = Cafe(
                    name=new_cafe_form.name.data,
                    map_url=new_cafe_form.map_url.data,
                    img_url=new_cafe_form.img_url.data,
                    location=new_cafe_form.location.data,
                    seats=new_cafe_form.seats.data,
                    has_wifi=new_cafe_form.has_wifi.data,
                    has_toilet = new_cafe_form.has_toilet.data,
                    has_sockets = new_cafe_form.has_sockets.data,
                    can_take_calls =new_cafe_form.can_take_calls.data,
                    coffee_price = new_cafe_form.coffee_price.data,
                    lat = lat,
                    lon = lon

                )

            except KeyError:
                flash("Something went wrong during inserting into the DB, please try again.")
                return render_template("add_new_cafe.html", form = new_cafe_form)
            except:
                flash("Do not understand you, please start again and do not cheat.")
                return redirect(url_for("add"))
            else:

                with app.app_context():
                    db.session.add(new_cafe)
                    db.session.commit()
                    return render_template("show_cafe.html", cafe=new_cafe)

    return render_template("add_new_cafe.html", form=new_cafe_form, h1="Add a new cafe!")

# Web page update price
@app.route("/update-price/<cafe_id>", methods=["POST", "GET"])
def update_price(cafe_id):
    price_update_form = PriceUpdateForm()
    cafe = db.session.execute(db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
    if cafe:
        if price_update_form.validate_on_submit():
            new_coffee_price = price_update_form.coffee_price.data
            cafe.coffee_price = new_coffee_price
            db.session.commit()
            return render_template('show_cafe.html', cafe = cafe)

        else:
            price_update_form.coffee_price.data = cafe.coffee_price
            return render_template('show_cafe.html', cafe = cafe, price_update_form = price_update_form)
    else:
        flash('Cafe does not exists')
        return redirect(url_for('search'))



# HTTP DELETE - Delete Record

@app.route("/delete/<cafe_id>", methods=["POST", "GET"])
def delete(cafe_id):
    delete_form = DeleteConfirmationForm()

    cafe = db.session.execute(db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
    if cafe:
        if delete_form.validate_on_submit():
            api_key = delete_form.delete_key.data

            if check_password_hash(app.secret_key,api_key):

                db.session.delete(cafe)
                db.session.commit()
                flash("Successfully deleted.")
                return redirect(url_for('search'))
            else:
                flash("Your key is not correct.")
                return render_template('show_cafe.html', cafe=cafe, delete_form=delete_form)

        else:
            return render_template('show_cafe.html', cafe=cafe, delete_form=delete_form)
    else:
        return redirect(url_for('search'))


@app.route("/api-doc")
def apidoc():
    return render_template("api_doc.html")

@app.errorhandler(404)
# inbuilt function which takes error as parameter
def not_found(e):
    # defining function

    return redirect(url_for('search'))

#all the api methods were created on the lessons (they are not part of the task), not changing the logic or output style for now

# HTTP GET - Read Record - web
@app.route("/api/cafe/<cafe_id>", methods=["GET"])
def api_show_cafe(cafe_id):
    cafe = db.session.execute(db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
    chosen_cafe_json = jsonify(id=cafe.id, name = cafe.name, map_url = cafe.map_url, img_url = cafe.img_url,
                                 location=cafe.location, seats = cafe.seats, has_toilet = cafe.has_toilet,
                                 has_wifi = cafe.has_wifi, has_sockets = cafe.has_sockets,
                                 can_take_calls=cafe.can_take_calls, coffee_price=cafe.coffee_price, lat = cafe.lat, lng = cafe.lon)

    return chosen_cafe_json

@app.route("/api/all", methods=["GET"])
def api_all_cafes():
    cafes = db.session.execute(db.select(Cafe)).scalars().all()
    all_cafes_json = []
    for cafe in cafes:
        cafe_json = jsonify(id=cafe.id, name = cafe.name, map_url = cafe.map_url, img_url = cafe.img_url,
                                 location=cafe.location, seats = cafe.seats, has_toilet = cafe.has_toilet,
                                 has_wifi = cafe.has_wifi, has_sockets = cafe.has_sockets,
                                 can_take_calls=cafe.can_take_calls, coffee_price=cafe.coffee_price, lat = cafe.lat, lng = cafe.lon)
        all_cafes_json.append(cafe_json.json)
    return all_cafes_json

@app.route("/api/search", methods=["GET"])
def api_search():
    query_location = request.args.get("loc")
    cafes = db.session.execute(db.select(Cafe).where(Cafe.location == query_location)).scalars().all()
    all_cafes_json = []
    for cafe in cafes:
        cafe_json = jsonify(id=cafe.id, name = cafe.name, map_url = cafe.map_url, img_url = cafe.img_url,
                                 location=cafe.location, seats = cafe.seats, has_toilet = cafe.has_toilet,
                                 has_wifi = cafe.has_wifi, has_sockets = cafe.has_sockets,
                                 can_take_calls=cafe.can_take_calls, coffee_price=cafe.coffee_price, lat = cafe.lat, lng = cafe.lon)
        all_cafes_json.append(cafe_json.json)
    if all_cafes_json == []:
        all_cafes_json = {"error": {"Not Found":"Sorry, we do not have anything in your location"}}
    return all_cafes_json


# HTTP POST - Create Record
@app.route("/api/add", methods=["POST"])
def api_add():
    try:
        cafe = Cafe(name=request.args.get("name"),
                    map_url=request.args.get("map_url"),
                    img_url=request.args.get("img_url"),
                    location=request.args.get("location"),
                    seats=request.args.get("seats"),
                    has_wifi=bool(request.args.get("has_wifi")),
                    has_toilet = bool(request.args.get("has_toilet")),
                    has_sockets = bool(request.args.get("has_sockets")),
                    can_take_calls = bool(request.args.get("can_take_calls")),
                    coffee_price = request.args.get("coffee_price"),
                    lat=request.args.get("lat"),
                    lon=request.args.get("lon")
                    )


    except KeyError:
        return jsonify(error={"Bad Request": "Some or all fields were incorrect or missing."})
    else:
        with app.app_context():
            db.session.add(cafe)
            db.session.commit()
        return jsonify(response={"success": f"Successfully added the new cafe."})

# HTTP PUT/PATCH - Update price
@app.route("/api/update-price/<cafe_id>", methods=["PATCH"])
def api_update_price(cafe_id):
    coffee_price = request.args.get("coffee_price")
    cafe = db.session.execute(db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
    if cafe:
        cafe.coffee_price = coffee_price
        db.session.commit()
        return jsonify({"success": "Successfully update the price."}), 200
    else:
        return jsonify({"error": {"Not found": "Sorry, a cafe with that id is not in the database."}}), 404

# HTTP DELETE - Delete Record

@app.route("/api/delete/<cafe_id>", methods=["DELETE"])
def api_delete(cafe_id):
    api_key = request.args.get("api_key")
    with app.app_context():

        if check_password_hash(app.secret_key,api_key):
            cafe = db.session.execute(db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
            if cafe:
                db.session.delete(cafe)
                db.session.commit()
                return jsonify({"success": "Successfully deleted."}), 200
            else:
                return jsonify({"error": {"Not found": "Sorry, a cafe with that id is not in the database."}}), 403
        else:
            return jsonify({"error": {"Not authorized": "Sorry, you are not allowed to permit this operation."}}), 403



if __name__ == '__main__':
    app.run(debug=False)
