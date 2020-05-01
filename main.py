import sqlite3
from fastapi import FastAPI, HTTPException


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

@app.get("/tracks/composers")
async def composer_songs(composer_name: str):
    comp_data = app.db_connection.execute('SELECT Composer FROM tracks WHERE Composer = ?', (composer_name,)).fetchall()
    if comp_data == []:
        raise HTTPException(status_code=404, detail={'error': 'There is no such composer'})
    tracks_data = app.db_connection.execute('SELECT Name FROM tracks WHERE Composer = ? ORDER BY Name', (composer_name,)).fetchall()
    return tracks_data

