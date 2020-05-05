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


class customer_data_request(BaseModel):
    company: str = None
    address: str = None
    city: str = None
    state: str = None
    country: str = None
    postalcode: str = None
    fax: str = None


class customer_data(BaseModel):
    CustomerId: int
    FirstName: str = None
    LastName: str = None
    Company: str = None
    Address: str = None
    City: str = None
    State: str = None
    Country: str = None
    PostalCode: str = None
    Phone: str = None
    Fax: str = None
    Email: str = None
    SupportRepId: int



'''Create /customers/{customer_id} page where customer data might be edited'''
@app.put("/customers/{customer_id}", response_model=customer_data)
async def update_customer(customer_id: int, request: customer_data_request):
    customer = app.db_connection.execute('SELECT CustomerId FROM customers WHERE CustomerId = ?', (customer_id,)).fetchone()
    data_for_change = dict(request)
    shrinked_data_for_change = {key: value for key, value in data_for_change.items() if value is not None}
    if customer:
        for key in shrinked_data_for_change:
            app.db_connection.execute('UPDATE customers SET ' + str(key)+ ' = ? WHERE CustomerId = ?', (shrinked_data_for_change[key], customer_id))
        app.db_connection.commit()
        app.db_connection.row_factory = sqlite3.Row
        cust_data = app.db_connection.execute('SELECT * FROM customers WHERE CustomerId = ?', (customer_id,)).fetchone()
        print(list(cust_data))
        response = customer_data(CustomerId = cust_data['CustomerId'],
                                FirstName = cust_data['FirstName'],
                                LastName = cust_data['LastName'],
                                Company = cust_data['Company'],
                                Address = cust_data['Address'],
                                City = cust_data['City'],
                                State = cust_data['State'],
                                Country = cust_data['Country'],
                                PostalCode = cust_data['PostalCode'],
                                Phone = cust_data['Phone'],
                                Fax = cust_data['Fax'],
                                Email = cust_data['Email'],
                                SupportRepId = cust_data['SupportRepId'])
        return response
    else:
        raise HTTPException(status_code=404, detail={'error': 'There is no such customer!'})


'''Create /sales page where customer statistics are presented'''
@app.get("/sales")
async def customers_statistics(category: str = None):
    if category == "customers":
        cust_data = app.db_connection.execute('''SELECT c.CustomerId, c.Email, c.Phone, ROUND(SUM(i.Total), 2) 
                                                 FROM customers AS c
                                                 INNER JOIN invoices AS i ON i.CustomerId = c.CustomerId
                                                 GROUP BY c.CustomerId 
                                                 ORDER BY SUM(i.Total) DESC, c.CustomerId ASC
                                                 ''').fetchall()
        for i in range(len(cust_data)):
            cust_data[i] = {
                            "CustomerId": cust_data[i][0],
                            "Email": cust_data[i][1],
                            "Phone": cust_data[i][2],
                            "Sum": cust_data[i][3]
                           }
        return cust_data
    else:
        raise HTTPException(status_code=404, detail={'error': 'There is no such category!'})