"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Starships, Planets, Films, Characters, Species, Favorite_Starships, Favorite_Planets, Favorite_Films, Favorite_Characters, Favorite_Species, Starships_Films, Starships_Characters, Planets_Films, Films_Characters, Films_Species
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


# endpoints de tablas únicas ########################################################################################################################################################################
# ENDPOINTS DE USER
# (post) agregar nuevos usuarios y (get) obtener todos los usuarios agregados ------------------------------------------------------------------------------------------------------------------------
@app.route('/user', methods=['POST', 'GET'])
def handle_allusers():
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'The request body is null'}), 400
        if 'name' not in body: 
            return jsonify({'msg': 'Specify name'}), 400
        if 'age' not in body: 
            return jsonify({'msg': 'Specify age'}), 400
        if 'email' not in body: 
            return jsonify({'msg': 'Specify email'}), 400
        user = User()
        user.name = body['name']
        user.age = body['age']
        user.email = body['email']
        db.session.add(user)
        db.session.commit()
        return jsonify({'msg': 'User successfully added'}), 200
    if request.method == 'GET':
        users = User.query.all()
        users_serialized = list(map(lambda x: x.serialize(), users))
        return jsonify(users_serialized)

# (get) obtener la información de un usuario en concreto y (put) modificar datos de un usuario en concreto ------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>', methods=['GET', 'PUT'])
def handle_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'msg': 'User do not exist'}), 400
    if request.method == 'GET':
        return jsonify(user.serialize())
    if request.method == 'PUT':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'name' in body:
            user.name = body['name']
        if 'age' in body:
            user.age = body['age']
        if 'email' in body: 
            user.email = body['email']
        db.session.commit()
        return jsonify({'msg': 'Updated user with ID {}'.format(user_id)}), 200

# (get) para obtener los favoritos de todas las secciones de un usuario en concreto -------------------------------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>/favorites', methods=['GET'])
def handle_user_all_favorites(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'msg': 'User do not exist'}), 400
    user_favorite_starships = Favorite_Starships.query.filter_by(user_id = user_id).all()
    user_favorite_starships_serialized = list(map(lambda x: x.serialize(), user_favorite_starships))
    user_favorite_planets = Favorite_Planets.query.filter_by(user_id = user_id).all()
    user_favorite_planets_serialized = list(map(lambda x: x.serialize(), user_favorite_planets))
    user_favorite_films = Favorite_Films.query.filter_by(user_id = user_id).all()
    user_favorite_films_serialized = list(map(lambda x: x.serialize(), user_favorite_films))
    user_favorite_characters = Favorite_Characters.query.filter_by(user_id = user_id).all()
    user_favorite_characters_serialized = list(map(lambda x: x.serialize(), user_favorite_characters))
    user_favorite_species = Favorite_Species.query.filter_by(user_id = user_id).all()
    user_favorite_species_serialized = list(map(lambda x: x.serialize(), user_favorite_species))

    favorites = {
        "favorite_starships": user_favorite_starships_serialized,
        "favorite_planets": user_favorite_planets_serialized,
        "favorite_films": user_favorite_films_serialized,
        "favorite_characters": user_favorite_characters_serialized,
        "favorite_species": user_favorite_species_serialized
    }

    return jsonify(favorites), 200

# ENDPOINTS DE STARSHIPS
# (post) agregar nuevos starships y (get) obtener todos los starships agregados ---------------------------------------------------------------------------------------------------------------------------------------
@app.route('/starships', methods=['POST', 'GET'])
def handle_allstarships():
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'name' not in body:
            return jsonify({'msg': 'Specify name'}), 400
        if 'model' not in body:
            return jsonify({'msg': 'Specify model'}), 400
        starships = Starships()
        starships.name = body['name']
        starships.model = body['model']
        db.session.add(starships)
        db.session.commit()
        return jsonify({'msg': 'Starship successfully added'}), 200
    if request.method == 'GET':
        starships = Starships.query.all()
        starships_with_related_films = []
        for starship in starships:
            related_films = [film.film_data.serialize() for film in starship.related_films]
            related_characters = [character.character_data.serialize() for character in starship.related_characters]
            starships_with_related_films.append({
                "starship_data": starship.serialize(),
                "related_films": related_films,
                "related_characters": related_characters
            })
        return jsonify(starships_with_related_films)

# (get) obtener la información de un starship en concreto y (put) modificar datos de un starship en concreto -----------------------------------------------------------------------------------------------------------------
@app.route('/starships/<int:starships_id>', methods=['GET', 'PUT'])
def handle_starship(starships_id):
    starship = Starships.query.get(starships_id)
    if starship is None:
        return jsonify({'msg': 'Starships do not exist'}), 400
    if request.method == 'GET':
        return jsonify(starship.serialize())
    if request.method == 'PUT':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'name' in body:
            starship.name = body['name']
        if 'model' in body: 
            starship.model = body['model']  
        db.session.commit()
        return jsonify({'msg': 'Updated starship with ID {}'.format(starships_id)})

# ENDPOINTS DE PLANETS
# (post) agregar nuevos planets y (get) obtener todos los planets agregados --------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/planets', methods=['POST', 'GET'])
def handle_allplanets():
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'name' not in body:
            return jsonify({'msg': 'Specify name'}), 400
        if 'rotation_period' not in body:
            return jsonify({'msg': 'Specify rotation_period'}), 400
        if 'climate' not in body:
            return jsonify({'msg': 'Specify climate'}), 400
        planets = Planets()
        planets.name = body['name']
        planets.rotation_period = body['rotation_period']
        planets.climate = body['climate']
        db.session.add(planets)
        db.session.commit()
        return jsonify({'msg': 'Planet successfully added'}), 200
    if request.method == 'GET':
        planets = Planets.query.all()
        planets_with_related_films = []
        for planet in planets:
            related_films = [film.film_data.serialize() for film in planet.related_films]
            planets_with_related_films.append({
                "planet_data": planet.serialize(),
                "related_films": related_films
            })
        return jsonify(planets_with_related_films)

# (get) obtener la información de un planeta en concreto y (put) modificar datos de un planeta en concreto ------------------------------------------------------------------------------------------------------------------------------------
@app.route('/planets/<int:planets_id>', methods=['GET', 'PUT'])
def handle_planet(planets_id):
    planets = Planets.query.get(planets_id)
    if planets is None:
        return jsonify({'msg': 'planets do not exist'}), 400
    if request.method == 'GET':
        return jsonify(planets.serialize())
    if request.method == 'PUT':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'name' in body:
            planets.name = body['name']
        if 'rotation_period' in body:
            planets.rotation_period = body['rotation_period']
        if 'climate' in body:
            planets.climate = body['climate'] 
        db.session.commit()
        return jsonify({'msg': 'Updated planet with ID {}'.format(planets_id)})

# ENDPOINTS DE FILMS
# (post) agregar nuevos films y (get) obtener todos los films agregados -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/films', methods=['POST', 'GET'])
def handle_newfilm():
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'title' not in body: 
            return jsonify({'msg': 'Specify title'}), 400
        if 'episode' not in body:
            return jsonify({'msg': 'Specify episode'}), 400
        if 'director' not in body:
            return jsonify({'msg': 'Specify director'}), 400
        film = Films()
        film.title = body['title']
        film.episode = body['episode']
        film.director = body['director']
        db.session.add(film)
        db.session.commit()
        return jsonify({'msg': 'Film successfully added'}), 200
    if request.method == 'GET':
        films = Films.query.all()
        films_with_related = []
        for film in films:
            related_starships = [starship.starship_data.serialize() for starship in film.related_starships]
            related_films = [planet.planet_data.serialize() for planet in film.related_planets]
            related_characters = [character.character_data.serialize() for character in film.related_characters]
            related_species = [species.species_data.serialize() for species in film.related_species]
            films_with_related.append({
                "film_data": film.serialize(),
                "related_starships": related_starships,
                "related_planets": related_films,
                "related_characters": related_characters, 
                "related_species": related_species
            })
        return jsonify(films_with_related)

# (get) obtener la información de un film en concreto y (put) modificar datos de un film en concreto ---------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/films/<int:films_id>', methods=['GET', 'PUT'])
def handle_film(films_id):
    film = Films.query.get(films_id)
    if request.method == 'GET':
        return jsonify(film.serialize())
    if request.method == 'PUT': 
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'title' in body:
            film.title = body['title']
        if 'episode' in body:
            film.episode = body['episode']
        if 'director' in body:
            film.director = body['director']
        db.session.commit()
        return jsonify({'msg': 'Updated film with ID {}'.format(films_id)}), 200

# ENDPOINTS DE CHARACTERS
# (post) agregar nuevos characters y (get) obtener todos los characters agregados -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/characters', methods=['POST', 'GET'])
def handle_allcharacters():
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if "name" not in body:
            return jsonify({'msg': 'Specify name'}), 400
        if "species_id" not in body:
            return jsonify({'msg': 'Specify species_id'}), 400
        if "planet_id" not in body:
            return jsonify({'msg': 'Specify planet_id'})
        character = Characters()
        character.name = body['name']
        character.species_id = body['species_id']
        character.planet_id = body['planet_id']
        db.session.add(character)
        db.session.commit()
        return jsonify({'msg': 'Character successfully added'}), 200
    
    if request.method == 'GET':
        characters = Characters.query.all()
        characters_with_related = []
        for character in characters:
            related_starships = [starship.starship_data.serialize() for starship in character.related_starships]
            related_films = [film.film_data.serialize() for film in character.related_films]
            characters_with_related.append({
                "character_data": character.serialize(),
                "related_starships": related_starships,
                "related films": related_films
            })
        return jsonify(characters_with_related)

# (get) obtener la información de un character en concreto y (put) modificar datos de un character en concreto ---------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/characters/<int:characters_id>', methods=['GET', 'PUT'])
def handle_character(characters_id):
    character = Characters.query.get(characters_id)
    if request.method == 'GET':
        return jsonify(character.serialize())
    if request.method == 'PUT':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'name' in body: 
            character.name = body['name']
            db.session.commit()
            return jsonify({'msg': 'Updated character with ID {}'.format(characters_id)}), 200

# ENPOINTS DE SPECIES
# (post) agregar nuevos species y (get) obtener todos los species agregados --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/species', methods=['POST', 'GET'])
def handle_allspecies():
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if "name" not in body:
            return jsonify({'msg': 'Specify name'}), 400
        if "classification" not in body:
            return jsonify({'msg': 'Specify classification'}), 400
        if "planet_id" not in body:
            return jsonify({'msg': 'Specify planet'}), 400
        species = Species()
        species.name = body['name']
        species.classification = body['classification']
        species.planet_id = body['planet_id']
        db.session.add(species)
        db.session.commit()
        return jsonify({'msg': 'Species successfully added'}), 200
    if request.method == 'GET':
        species = Species.query.all()
        species_with_related = []
        for species in species:
            related_films = [film.film_data.serialize() for film in species.related_films]
            species_with_related.append({
                "species_data": species.serialize(),
                "related films": related_films
            })
        return jsonify(species_with_related)

# (get) obtener la información de un species en concreto y (put) modificar datos de un species en concreto --------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/species/<int:species_id>', methods=['GET', 'PUT'])
def handle_species(species_id):
    species = Species.query.get(species_id)
    if request.method == 'GET':
        return jsonify(species.serialize()), 200
    if request.method == 'PUT':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'name' in body:
            species.name = body['name']
        if 'classification' in body:
            species.classification = body['classification']
        db.session.commit()
        return jsonify({'msg': 'Updated species with ID {}'.format(species_id)})

# endspoints de las tablas de favoritos ##########################################################################################################################################################################################
# ENDPOINTS DE FAVORITES STARSHIPS
# admin endpoint // (get) ver todas las starships favoritas con sus usuarios correspondientes
@app.route('/favorite_starships', methods=['GET'])
def handle_allfavoritestarships():    
    all_favorite_starships = Favorite_Starships.query.all()
    all_favorite_starships_serialized = list(map(lambda x: x.serialize(), all_favorite_starships))
    return jsonify(all_favorite_starships_serialized), 200

# admin endpoint // (get) para ver todas las veces que una starship en concreta fue agregada a favoritos y (delete) eliminar de favoritos todas las instancias que contengan una starship en concreta -------------------------------------------------------------------------------
@app.route('/favorite_starships/<int:starship_id>', methods=['GET', 'DELETE'])
def handle_favoritestarship(starship_id):
    favorite_starships = Favorite_Starships.query.filter_by(starship_id = starship_id)
    if favorite_starships is None: 
        return jsonify({'msg': 'The starship with ID {} does not exist'.format(starship_id)})
    if request.method == 'GET':
        favorite_starships_serialized = list(map(lambda x: x.serialize(), favorite_starships))
        return jsonify(favorite_starships_serialized), 200
    
    if request.method == 'DELETE':
        for fav in favorite_starships:
            db.session.delete(fav)
        db.session.commit()
        return jsonify({'msg': 'Favorite Starships with ID {} succefully deleted'.format(starship_id)})

# (post) agregar starship a un usuario en concreto y (get) ver las starships favoritas de un usuario en concreto ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>/favorite_starships', methods=['GET', 'POST'])
def handle_userfavoritestarships(user_id):
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'starship_id' not in body:
            return jsonify({'msg': 'Specify starship_id'}), 400
        if not (Starships.query.get(body['starship_id']) and User.query.get(user_id)):
            return jsonify({'msg': 'Invalid starship_id o user_id'}), 400
        if (Favorite_Starships.query.filter_by(user_id = user_id, starship_id = body['starship_id']).first()):
            return jsonify({'msg': 'Starship already in favorites of the user with ID {}'.format(user_id)})
        user_favorite_starship = Favorite_Starships()
        user_favorite_starship.starship_id = body['starship_id']
        user_favorite_starship.user_id = user_id
        db.session.add(user_favorite_starship)
        db.session.commit()
        return jsonify({'msg': 'Favorite starship successfully added'}), 200
    if request.method == 'GET':
        user_favorite_starship = Favorite_Starships.query.filter_by(user_id = user_id)
        user_favorite_starship_serialized = list(map(lambda x: x.serialize(), user_favorite_starship))
        return jsonify(user_favorite_starship_serialized), 200

# (get) para ver individualmente el starship concreto de un user concreto y (delete) para eliminar un starship concreto de los favoritos de un user concreto --------------------------------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>/favorite_starships/<int:starship_id>', methods=['GET', 'DELETE'])
def handle_userfavoritestarship(user_id, starship_id):
    user_favorite_starship = Favorite_Starships.query.filter_by(starship_id = starship_id, user_id = user_id).first()
    if not user_favorite_starship:
        return jsonify({'msg': 'Invalid user_id or starship_id'}), 400
    if request.method == 'GET':
        user_favorite_starship_serialized = user_favorite_starship.serialize()
        return jsonify(user_favorite_starship_serialized), 200
    if request.method == 'DELETE':
        db.session.delete(user_favorite_starship)
        db.session.commit()
        return jsonify({'msg': 'Favorite starship with ID {} deleted from favorites of user with ID {}'.format(starship_id, user_id)}), 200

#ENPOINTS DE FAVORITE_PLANETS
# admin endpoint // (get) ver todos los planets favoritos con sus usuarios correspondientes
@app.route('/favorite_planets', methods=['GET'])
def handle_allfavoriteplanets():
    all_favorite_planets = Favorite_Planets.query.all()
    all_favorite_planets_serialized = list(map(lambda x: x.serialize(), all_favorite_planets))
    return jsonify(all_favorite_planets_serialized), 200

# admin endpoint // (get) para ver todas las veces que un planet en concreto fue agregado a favoritos y (delete) eliminar de favoritos todas las instancias que contengan un planet en concreto --------------------------------------------------------------------------------------------------------------------------------
@app.route('/favorite_planets/<int:planet_id>', methods=['GET', 'DELETE'])
def handle_favoriteplanets(planet_id):
    favorite_planets = Favorite_Planets.query.filter_by(planet_id = planet_id)
    if favorite_planets is None:
        return jsonify({'msg': 'The planet with ID {} does not exist'.format(planet_id)}), 400
    if request.method == 'GET':
        favorite_planets_serialized = list(map(lambda x: x.serialize(), favorite_planets))
        return jsonify(favorite_planets_serialized), 200
    if request.method == 'DELETE':
        for fav in favorite_planets:
            db.session.delete(fav)
        db.session.commit()
        return jsonify({'msg': 'Favorite Planets with ID {} successfully delete'.format(planet_id)}), 200

# (post) agregar planets a un usuario en concreto y (get) ver los planets favoritos de un usuario en concreto --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>/favorite_planets', methods=['GET', 'POST'])
def handle_userfavoriteplanets(user_id):
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empy'}), 400
        if 'planet_id' not in body:
            return jsonify({'msg': 'Specify planet_id'}), 400
        if not (Planets.query.get(body['planet_id']) and User.query.get(user_id)):
            return jsonify({'msg': 'Invalid planet_id or user_id'}), 400
        if (Favorite_Planets.query.filter_by(user_id = user_id, planet_id = body['planet_id']).first()):
            return jsonify({'msg': 'Planet already in favorites of the user with ID {}'.format(user_id)})
        user_favorite_planet = Favorite_Planets()
        user_favorite_planet.planet_id = body['planet_id']
        user_favorite_planet.user_id = user_id
        db.session.add(user_favorite_planet)
        db.session.commit()
        return jsonify({'msg': 'Favorite planet successfully added'}), 200
    if request.method == 'GET':
        user_favorite_planet = Favorite_Planets.query.filter_by(user_id = user_id)
        user_favorite_planet_serialized = list(map(lambda x: x.serialize(), user_favorite_planet))
        return jsonify(user_favorite_planet_serialized), 200

# (get) para ver individualmente el planet concreto de un user concreto y (delete) para eliminar un planet concreto de los favoritos de un user concreto ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>/favorite_planets/<int:planet_id>', methods=['GET', 'DELETE'])
def handle_userfavoriteplanet(user_id, planet_id):
    user_favorite_planet = Favorite_Planets.query.filter_by(user_id = user_id, planet_id = planet_id).first()
    if not user_favorite_planet:
        return jsonify({'msg': 'Invalid user_id or planet_id'})
    if request.method == 'GET':
        user_favorite_planet_serialized = user_favorite_planet.serialize()
        return jsonify(user_favorite_planet_serialized), 200
    if request.method == 'DELETE':
        db.session.delete(user_favorite_planet)
        db.session.commit()
        return jsonify({'msg': 'Favorite planet with ID {} deleted from favorites of user with ID {}'.format(planet_id, user_id)}), 200 

# ENDPOINTS DE FAVORITE_FILMS
# admin endpoint // (get) ver todos los films favoritos con sus usuarios correspondientes
@app.route('/favorite_films', methods=['GET'])
def handle_allfavoritefilms():
    all_favorite_films = Favorite_Films.query.all()
    all_favorite_films_serialized = list(map(lambda x: x.serialize(), all_favorite_films))
    return jsonify(all_favorite_films_serialized), 200

# admin endpoint // (get) para ver todas las veces que un film en concreto fue agregado a favoritos y (delete) eliminar de favoritos todas las instancias que contengan un film en concreto --------------------------------------------------------------------------------------------------------------------------------
@app.route('/favorite_films/<int:film_id>', methods=['GET', 'DELETE'])
def handle_favoritefilm(film_id):
    favorite_film = Favorite_Films.query.filter_by(film_id = film_id)
    if favorite_film is None:
        return jsonify({'msg': 'The film with ID {} does not exist'.format(film_id)}), 400
    if request.method == 'GET':
        favorite_film_serialized = list(map(lambda x: x.serialize(), favorite_film))
        return jsonify(favorite_film_serialized), 200
    if request.method == 'DELETE':
        for fav in favorite_film:
            db.session.delete(fav)
        db.session.commit()
        return jsonify({'msg': 'Favorite Films with ID {} successfully deleted'.format(film_id)})
    
# (post) agregar films a un usuario en concreto y (get) ver los films favoritos de un usuario en concreto ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>/favorite_films', methods=['POST', 'GET'])
def handle_userfavoritefilms(user_id):
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'film_id' not in body:
            return jsonify({'msg': 'Specify film_id'}), 400
        if not (Films.query.get(body['film_id']) and User.query.get(user_id)):
            return jsonify({'msg': 'Invalid film_id or user_id'}), 400
        if (Favorite_Films.query.filter_by(user_id = user_id, film_id = body['film_id']).first()):
            return jsonify({'msg': 'Film already in favorites of the user with ID {}'.format(user_id)})
        user_favorite_film = Favorite_Films()
        user_favorite_film.film_id = body['film_id']
        user_favorite_film.user_id = user_id
        db.session.add(user_favorite_film)
        db.session.commit()
        return jsonify({'msg': 'Favorite film successfully added'}), 200
    if request.method == 'GET':
        user_favorite_film = Favorite_Films.query.filter_by(user_id = user_id) 
        user_favorite_film_serialized = list(map(lambda x: x.serialize(), user_favorite_film))
        return jsonify(user_favorite_film_serialized), 200
    
# (get) para ver individualmente el film concreto de un user concreto y (delete) para eliminar un film concreto de los favoritos de un user concreto -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>/favorite_films/<int:film_id>', methods=['GET', 'DELETE'])
def handle_userfavoritefilm(user_id, film_id): 
    user_favorite_film = Favorite_Films.query.filter_by(user_id = user_id, film_id = film_id).first()
    user_favorite_film_serialized = user_favorite_film.serialize()
    if request.method == 'GET':
        return jsonify(user_favorite_film_serialized), 200
    if request.method == 'DELETE':
        db.session.delete(user_favorite_film)
        db.session.commit()
        return ({'msg': 'Favorite film with ID {} deleted from favorites of user with ID {}'.format(film_id, user_id)})

# ENDPOINTS DE FAVORITE_CHARACTERS
# admin endpoint // (get) ver todos los characters favoritos con sus usuarios correspondientes
@app.route('/favorite_characters', methods=['GET'])
def handle_allfavoritecharacters():
    all_favorite_characters = Favorite_Characters.query.all()
    all_favorite_characters_serialized = list(map(lambda x: x.serialize(), all_favorite_characters))
    return jsonify(all_favorite_characters_serialized), 200

# admin endpoint // (get) para ver todas las veces que un character en concreto fue agregado a favoritos y (delete) eliminar de favoritos todas las instancias que contengan un character en concreto --------------------------------------------------------------------------------------------------------------------------------
@app.route('/favorite_characters/<int:character_id>', methods=['GET', 'DELETE'])
def handle_favoritecharacter(character_id):
    favorite_characters = Favorite_Characters.query.filter_by(character_id = character_id)
    if request.method == 'GET':
        favorite_characters_serialized = list(map(lambda x: x.serialize(), favorite_characters))
        return jsonify(favorite_characters_serialized), 200
    if request.method == 'DELETE':
        for fav in favorite_characters:
            db.session.delete(fav)
        db.session.commit()
        return jsonify({'msg': 'Favorite character with ID {} successfully deleted'.format(character_id)}), 200
    
# (post) agregar characters a un usuario en concreto y (get) ver los characters favoritos de un usuario en concreto -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>/favorite_characters', methods=['POST', 'GET'])
def handle_userfavoritecharacters(user_id):
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'character_id' not in body:
            return jsonify({'msg': 'Specify character_id'}), 400
        if not (Characters.query.get(body['character_id']) and User.query.get(user_id)):
            return ({'msg': 'Invalid character_id or user_id'}), 400
        if (Favorite_Characters.query.filter_by(user_id = user_id, character_id = body['character_id']).first()):
            return jsonify({'msg': 'Character already in favorites of the user with ID {}'.format(user_id)})
        user_favorite_character = Favorite_Characters()
        user_favorite_character.character_id = body['character_id']
        user_favorite_character.user_id = user_id
        db.session.add(user_favorite_character)
        db.session.commit()
        return ({'msg': 'Favorite character successfully added'}), 200
    if request.method == 'GET':
        user_favorite_characters = Favorite_Characters.query.filter_by(user_id = user_id)
        user_favorite_characters_serialized = list(map(lambda x: x.serialize(), user_favorite_characters))
        return jsonify(user_favorite_characters_serialized)

# (get) para ver individualmente el character concreto de un user concreto y (delete) para eliminar un character concreto de los favoritos de un user concreto --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>/favorite_characters/<int:character_id>', methods=['GET', 'DELETE'])
def handle_userfavoritecharacter(user_id, character_id):
    user_favorite_character = Favorite_Characters.query.filter_by(user_id = user_id, character_id = character_id).first()
    if not user_favorite_character:
        return ({'msg': 'Invalid user_id or character_id'}), 400
    if request.method == 'GET':
        return jsonify(user_favorite_character.serialize()), 200
    if request.method == 'DELETE':
        db.session.delete(user_favorite_character)
        db.session.commit()
        return ({'msg': 'Favorite character with ID {} deleted from favorites of user with ID {}'.format(character_id, user_id)})

# ENDPOINTS DE FAVORITE_SPECIES
# admin endpoint // (get) ver todos las species favoritas con sus usuarios correspondientes ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/favorite_species', methods=['GET'])
def handle_all_favorite_species():
    all_favorite_species = Favorite_Species.query.all()
    all_favorite_species_serialized = list(map(lambda x: x.serialize(), all_favorite_species))
    return jsonify(all_favorite_species_serialized), 200

# admin endpoint // (get) para ver todas las veces que una species en concreto fue agregada a favoritos y (delete) eliminar de favoritos todas las instancias que contengan una species en concreto --------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/favorite_species/<int:species_id>', methods=['GET', 'DELETE'])
def handle_favorite_species_group(species_id):
    favorite_species = Favorite_Species.query.filter_by(species_id = species_id)
    if favorite_species is None:
        return jsonify({'msg': 'Favorite species with ID {} does not exist'.format(species_id)}), 400
    if request.method == 'GET':
        favorite_species_serialized = list(map(lambda x: x.serialize(), favorite_species))
        return jsonify(favorite_species_serialized), 200
    if request.method == 'DELETE':
        for fav in favorite_species:
            db.session.delete(fav)
        db.session.commit()
        return jsonify({'msg': 'Favorite species with ID {} successfully deleted'.format(species_id)}), 200

# (post) agregar species a un usuario en concreto y (get) ver las species favoritos de un usuario en concreto -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>/favorite_species', methods=['POST', 'GET'])
def handle_user_all_favorite_species(user_id):
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'species_id' not in body:
            return jsonify({'msg': 'Specify species_id'}), 400
        if (Favorite_Species.query.filter_by(user_id = user_id, species_id = body['species_id']).first()):
            return jsonify({'msg': 'Species already in favorites of the user with ID {}'.format(user_id)})
        user_favorite_species = Favorite_Species()
        user_favorite_species.species_id = body['species_id']
        user_favorite_species.user_id = user_id
        db.session.add(user_favorite_species)
        db.session.commit()
        return jsonify({'msg': 'Favorite species successfully added'}), 200
    if request.method == 'GET':
        user_favorite_species = Favorite_Species.query.filter_by(user_id = user_id)
        user_favorite_species_serialized = list(map(lambda x: x.serialize(), user_favorite_species))
        return jsonify(user_favorite_species_serialized), 200

# (get) para ver individualmente las species concretas de un user concreto y (delete) para eliminar una species concreta de los favoritos de un user concreto -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/user/<int:user_id>/favorite_species/<int:species_id>', methods=['GET', 'DELETE'])
def handle_user_one_favorite_species(user_id, species_id):
    user_one_favorite_species = Favorite_Species.query.filter_by(user_id = user_id, species_id = species_id).first()
    if request.method == 'GET':
        return jsonify(user_one_favorite_species.serialize()), 200
    if request.method == 'DELETE':
        db.session.delete(user_one_favorite_species)
        db.session.commit()
        return jsonify({'msg': 'Favorite species with ID {} deleted from favorites of user with ID {}'.format(species_id, user_id)})


# endpoints de associated tables (many to many) #####################################################################################################################################################################
# ENPOINTS DE STARSHIPS_FILMS
# (get) para obtener todas las relaciones entre starships y films y (post) para agregar una nueva relación entre starships y films -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/starships_films', methods=['GET', 'POST'])
def handle_all_starships_films():
    if request.method == 'GET':
        all_starships_films = Starships_Films.query.all()
        all_starships_films_serialized = list(map(lambda x: x.serialize(), all_starships_films))
        return jsonify(all_starships_films_serialized), 200
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'starship_id' not in body:
            return jsonify({'msg': 'Specify starship_id'}), 400
        if 'film_id' not in body:
            return jsonify({'msg': 'Specify film_id'})
        if (Starships_Films.query.filter_by(starship_id = body['starship_id'], film_id = body['film_id']).first()):
            return jsonify({'msg': 'Relationship already exists'}), 400
        if not (Starships.query.filter_by(id = body['starship_id']).first() and Films.query.filter_by(id = body['film_id']).first()):
            return jsonify({'msg': 'Invalid starship_id or film_id'})
        new_starship_film = Starships_Films()
        new_starship_film.starship_id = body['starship_id']
        new_starship_film.film_id = body['film_id']
        db.session.add(new_starship_film)
        db.session.commit()
        return jsonify({'msg': 'Relationship successfully added'}), 200

# (get) para obtener una relación starship/film específica y (delete) para eliminar una relación starship/film específica
@app.route('/starships_films/<int:relationship_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_one_starship_film(relationship_id):
    one_starship_film = Starships_Films.query.filter_by(id = relationship_id).first()
    if one_starship_film is None:
        return jsonify({'msg': 'Invalid relationship id'})
    if request.method == 'GET':
        return jsonify(one_starship_film.serialize()), 200
    if request.method == 'PUT':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'starship_id' in body:
            if not (Starships.query.filter_by(id = body['starship_id']).first()):
                return jsonify({'msg': 'Invalid starship_id'})
            one_starship_film.starship_id = body['starship_id']
        if 'film_id' in body: 
            if not (Films.query.filter_by(id = body['film_id']).first()):
                return jsonify({'msg': 'Invalid film_id'})
            one_starship_film.film_id = body['film_id']
        db.session.commit()
        return jsonify({'msg':'Updated relationship starship/film with ID {}'.format(relationship_id)}), 200
    if request.method == 'DELETE':
        db.session.delete(one_starship_film)
        db.session.commit()
        return jsonify({'msg': 'Deleted relationship starship/film with ID {}'.format(relationship_id)})
    
# ENPOINTS DE STARSHIPS_CHARACTERS
# (get) para obtener todas las relaciones entre starships y characters y (post) para agregar una nueva relación entre starships y characters -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/starships_characters', methods=['GET', 'POST'])
def handle_all_starships_characters():
    if request.method == 'GET':
        all_starships_characters = Starships_Characters.query.all()
        all_starships_characters_serialized = list(map(lambda x: x.serialize(), all_starships_characters))
        return jsonify(all_starships_characters_serialized), 200
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'starship_id' not in body:
            return jsonify({'msg': 'Specify starship_id'}), 400
        if 'character_id' not in body:
            return jsonify({'msg': 'Specify character_id'})
        if (Starships_Characters.query.filter_by(starship_id = body['starship_id'], character_id = body['character_id']).first()):
            return jsonify({'msg': 'Relationship already exists'}), 400
        if not (Starships.query.filter_by(id = body['starship_id']).first() and Characters.query.filter_by(id = body['character_id']).first()):
            return jsonify({'msg': 'Invalid starship_id or character_id'})
        new_starship_character = Starships_Characters()
        new_starship_character.starship_id = body['starship_id']
        new_starship_character.character_id = body['character_id']
        db.session.add(new_starship_character)
        db.session.commit()
        return jsonify({'msg': 'Relationship successfully added'}), 200

# (get) para obtener una relación starship/character específica y (delete) para eliminar una relación starship/character específica
@app.route('/starships_characters/<int:relationship_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_one_starship_character(relationship_id):
    one_starship_character = Starships_Characters.query.filter_by(id = relationship_id).first()
    if one_starship_character is None:
        return jsonify({'msg': 'Invalid relationship id'})
    if request.method == 'GET':
        return jsonify(one_starship_character.serialize()), 200
    if request.method == 'PUT':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'starship_id' in body:
            if not (Starships.query.filter_by(id = body['starship_id']).first()):
                return jsonify({'msg': 'Invalid starship_id'})
            one_starship_character.starship_id = body['starship_id']
        if 'character_id' in body:
            if not (Characters.query.filter_by(id = body['character_id']).first()):
                return jsonify({'msg': 'Invalid character_id'}) 
            one_starship_character.character_id = body['character_id']
        db.session.commit()
        return jsonify({'msg':'Updated relationship starship/character with ID {}'.format(relationship_id)}), 200
    if request.method == 'DELETE':
        db.session.delete(one_starship_character)
        db.session.commit()
        return jsonify({'msg': 'Deleted relationship starship/character with ID {}'.format(relationship_id)})

# ENPOINTS DE PLANETS_FILMS
# (get) para obtener todas las relaciones entre planets y films y (post) para agregar una nueva relación entre planets y films -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/planets_films', methods=['GET', 'POST'])
def handle_all_planets_films():
    if request.method == 'GET':
        all_planets_films = Planets_Films.query.all()
        all_planets_films_serialized = list(map(lambda x: x.serialize(), all_planets_films))
        return jsonify(all_planets_films_serialized), 200
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'planet_id' not in body:
            return jsonify({'msg': 'Specify planet_id'}), 400
        if 'film_id' not in body:
            return jsonify({'msg': 'Specify film_id'})
        if (Planets_Films.query.filter_by(planet_id = body['planet_id'], film_id = body['film_id']).first()):
            return jsonify({'msg': 'Relationship already exists'}), 400
        if not (Planets.query.filter_by(id = body['planet_id']).first() and Films.query.filter_by(id = body['film_id']).first()):
            return jsonify({'msg': 'Invalid planet_id or film_id'})
        new_planet_film = Planets_Films()
        new_planet_film.planet_id = body['planet_id']
        new_planet_film.film_id = body['film_id']
        db.session.add(new_planet_film)
        db.session.commit()
        return jsonify({'msg': 'Relationship successfully added'}), 200

# (get) para obtener una relación planet/film específica y (delete) para eliminar una relación planet/film específica
@app.route('/planets_films/<int:relationship_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_one_planet_film(relationship_id):
    one_planet_film = Planets_Films.query.filter_by(id = relationship_id).first()
    if one_planet_film is None:
        return jsonify({'msg': 'Invalid relationship id'})
    if request.method == 'GET':
        return jsonify(one_planet_film.serialize()), 200
    if request.method == 'PUT':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'planet_id' in body:
            if not (Planets.query.filter_by(id = body['planet_id']).first()):
                return jsonify({'msg': 'Invalid planet_id'})
            one_planet_film.planet_id = body['planet_id']
        if 'film_id' in body:
            if not (Films.query.filter_by(id = body['film_id']).first()):
                return jsonify({'msg': 'Invalid film_id'})
            one_planet_film.film_id = body['film_id']
        db.session.commit()
        return jsonify({'msg':'Updated relationship planet/film with ID {}'.format(relationship_id)}), 200
    if request.method == 'DELETE':
        db.session.delete(one_planet_film)
        db.session.commit()
        return jsonify({'msg': 'Deleted relationship planet/film with ID {}'.format(relationship_id)})
    
# ENPOINTS DE FILMS_CHARACTERS
# (get) para obtener todas las relaciones entre films y characters y (post) para agregar una nueva relación entre films y characters -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/films_characters', methods=['GET', 'POST'])
def handle_all_films_characters():
    if request.method == 'GET':
        all_films_characters = Films_Characters.query.all()
        all_films_characters_serialized = list(map(lambda x: x.serialize(), all_films_characters))
        return jsonify(all_films_characters_serialized), 200
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'film_id' not in body:
            return jsonify({'msg': 'Specify film_id'}), 400
        if 'character_id' not in body:
            return jsonify({'msg': 'Specify character_id'})
        if (Films_Characters.query.filter_by(film_id = body['film_id'], character_id = body['character_id']).first()):
            return jsonify({'msg': 'Relationship already exists'}), 400
        if not (Films.query.filter_by(id = body['film_id']).first() and Characters.query.filter_by(id = body['character_id']).first()):
            return jsonify({'msg': 'Invalid film_id or character_id'})
        new_film_character = Films_Characters()
        new_film_character.film_id = body['film_id']
        new_film_character.character_id = body['character_id']
        db.session.add(new_film_character)
        db.session.commit()
        return jsonify({'msg': 'Relationship successfully added'}), 200

# (get) para obtener una relación film/character específica y (delete) para eliminar una relación film/character específica
@app.route('/films_characters/<int:relationship_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_one_film_character(relationship_id):
    one_film_character = Films_Characters.query.filter_by(id = relationship_id).first()
    if one_film_character is None:
        return jsonify({'msg': 'Invalid relationship id'}), 400
    if request.method == 'GET':
        return jsonify(one_film_character.serialize()), 200
    if request.method == 'PUT':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'film_id' in body:
            if not (Films.query.filter_by(id = body['film_id']).first()):
                return jsonify({'msg': 'Invalid film_id'}), 400
            one_film_character.film_id = body['film_id']
        if 'character_id' in body:
            if not (Characters.query.filter_by(id = body['character_id']).first()):
                return jsonify({'msg': 'Invalid character_id'}), 400
            one_film_character.character_id = body['character_id']
        db.session.commit()
        return jsonify({'msg':'Updated relationship film/character with ID {}'.format(relationship_id)}), 200
    if request.method == 'DELETE':
        db.session.delete(one_film_character)
        db.session.commit()
        return jsonify({'msg': 'Deleted relationship film/character with ID {}'.format(relationship_id)}), 200

# ENPOINTS DE FILMS_SPECIES
# (get) para obtener todas las relaciones entre films y species y (post) para agregar una nueva relación entre films y species -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/films_species', methods=['GET', 'POST'])
def handle_all_films_species():
    if request.method == 'GET':
        all_films_species = Films_Species.query.all()
        all_films_species_serialized = list(map(lambda x: x.serialize(), all_films_species))
        return jsonify(all_films_species_serialized), 200
    if request.method == 'POST':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'film_id' not in body:
            return jsonify({'msg': 'Specify film_id'}), 400
        if 'species_id' not in body:
            return jsonify({'msg': 'Specify species_id'}), 400
        if (Films_Species.query.filter_by(film_id = body['film_id'], species_id = body['species_id']).first()):
            return jsonify({'msg': 'Relationship already exists'}), 400
        if not (Films.query.filter_by(id = body['film_id']).first() and Species.query.filter_by(id = body['species_id']).first()):
            return jsonify({'msg': 'Invalid film_id or species_id'}), 400
        new_film_species = Films_Species()
        new_film_species.film_id = body['film_id']
        new_film_species.species_id = body['species_id']
        db.session.add(new_film_species)
        db.session.commit()
        return jsonify({'msg': 'Relationship successfully added'}), 200

# (get) para obtener una relación film/species específica y (delete) para eliminar una relación film/species específica
@app.route('/films_species/<int:relationship_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_one_film_species(relationship_id):
    one_film_species = Films_Species.query.filter_by(id = relationship_id).first()
    if one_film_species is None:
        return jsonify({'msg': 'Invalid relationship id'}), 400
    if request.method == 'GET':
        return jsonify(one_film_species.serialize()), 200
    if request.method == 'PUT':
        body = request.get_json(silent=True)
        if body is None: 
            return jsonify({'msg': 'Body cannot be empty'}), 400
        if 'film_id' in body:
            if not (Films.query.filter_by(id = body['film_id']).first()):
                return jsonify({'msg': 'Invalid film_id'}), 400
            one_film_species.film_id = body['film_id']
        if 'species_id' in body:
            if not (Species.query.filter_by(id = body['species_id']).first()):
                return jsonify({'msg': 'Invalid species_id'}), 400
            one_film_species.species_id = body['species_id']
        db.session.commit()
        return jsonify({'msg':'Updated relationship film/species with ID {}'.format(relationship_id)}), 200
    if request.method == 'DELETE':
        db.session.delete(one_film_species)
        db.session.commit()
        return jsonify({'msg': 'Deleted relationship film/species with ID {}'.format(relationship_id)}), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)

