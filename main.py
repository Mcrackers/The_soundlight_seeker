import sqlite3
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

app = FastAPI()


'''Application startup'''
@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect('DB/chinook.db')


'''Application shutdown'''
@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()


'''Create root page'''
@app.get("/")
async def root():
    return {"message": "The soundlight seeker welcome You! On /tracks page You can find music suitable for Your today mood"}


'''Create /tracks page where the songs are listed in given order'''
@app.get("/tracks")
async def get_tracks(page: int = 0, per_page: int = 10):
    tracks_data = app.db_connection.execute('SELECT * FROM tracks LIMIT '+str(per_page)+' OFFSET '+str(per_page*page)).fetchall()
    for i in range(len(tracks_data)):
        tracks_data[i] = {"TrackId": tracks_data[i][0],
                          "Name": tracks_data[i][1],
                          "AlbumId": tracks_data[i][2],
                          "MediaTypeId": tracks_data[i][3],
                          "GenreId": tracks_data[i][4],
                          "Composer": tracks_data[i][5],
                          "Milliseconds": tracks_data[i][6],
                          "Bytes": tracks_data[i][7],
                          "UnitPrice": tracks_data[i][8]}
    return tracks_data

'''Create /tracks/composers page where the songs of the given composer are listed by Name'''
@app.get("/tracks/composers")
async def composer_songs(composer_name: str):
    track_list = []
    comp_data = app.db_connection.execute('SELECT Composer FROM tracks WHERE Composer = ?', (composer_name,)).fetchall()
    if comp_data == []:
        raise HTTPException(status_code=404, detail={'error': 'There is no such composer'})
    tracks_data = app.db_connection.execute('SELECT Name FROM tracks WHERE Composer = ? ORDER BY Name', (composer_name,)).fetchall()
    for song in tracks_data:
        track_list += song
    return track_list


class add_album_request(BaseModel):
    title: str
    artist_id: int


class album_response(BaseModel):
    AlbumId: int
    Title: str
    ArtistId: int


'''Create /albums page where new album of the given composer is added'''
@app.post("/albums", response_model=album_response)
async def add_album(request: add_album_request, response: Response):
    artist = app.db_connection.execute('SELECT ArtistId FROM albums WHERE ArtistId = ?', (request.artist_id,)).fetchone()
    if artist:
        new_title = app.db_connection.execute('INSERT INTO albums (Title, ArtistId) VALUES (?,?)', (request.title, request.artist_id))
        app.db_connection.commit()
        new_albumid = new_title.lastrowid
        response.status_code = 201
        return album_response(AlbumId = new_albumid, Title = request.title, ArtistId = request.artist_id)
    else:
        raise HTTPException(status_code=404, detail={'error': 'There is no such artistid!'})


'''Create /albums/{album_id page where album is shown when album_id is typed'''
@app.get("/albums/{album_id}")
async def check_album(album_id: int):
    app.db_connection.row_factory = sqlite3.Row
    album_data = app.db_connection.execute('SELECT AlbumId, Title, ArtistId FROM albums WHERE AlbumId = ?', (album_id,)).fetchone()
    return album_response(AlbumId = album_data['AlbumId'], Title = album_data['Title'], ArtistId = album_data['ArtistId'])
