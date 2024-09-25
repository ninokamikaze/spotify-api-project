import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import matplotlib.pyplot as plt
import requests
import pdb

# Configuración inicial de Spotify API
client_id = '785e1007323d4db3908b4c93764e9475'
client_secret = '41a16fe64c6b418a8116bab69309e82f'
redirect_uri = 'http://localhost:8080/callback'

# Autenticación con OAuth 2.0
scope = "user-top-read"  # Permiso para acceder a las canciones más escuchadas del usuario
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))

# Obtener las 30 canciones más reproducidas del usuario
top_tracks = sp.current_user_top_tracks(limit=10)

# Extraer datos importantes de cada canción y crear un DataFrame
track_data = [{
    'name': track['name'],
    'artist': track['artists'][0]['name'],
    'album': track['album']['name'],
    'popularity': track['popularity'],
    'track_id': track['id']  # Guardamos el ID de la canción para obtener sus características de audio
} for track in top_tracks['items']]

df_tracks = pd.DataFrame(track_data)

# Obtener características de audio de cada canción
audio_features = [{
    'id': features['id'],
    'energy': features['energy'],
    'tempo': features['tempo'],
    'danceability': features['danceability'],
    'loudness': features['loudness']
} for features in sp.audio_features(df_tracks['track_id'])]

# Crear un DataFrame con las características de audio
df_audio_features = pd.DataFrame(audio_features)

# Combinar ambos DataFrames (canciones + características de audio)
df_combined = pd.merge(df_tracks, df_audio_features, left_on='track_id', right_on='id')

# Función para obtener la ubicación del artista desde la API de MusicBrainz
def get_artist_country(artist_name):
    url = "https://musicbrainz.org/ws/2/artist/"
    params = {
        'query': artist_name,
        'fmt': 'json'
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data['artists']:
            return data['artists'][0].get('area', {}).get('name', 'Desconocido')
        return 'Desconocido'
    else:
        print(f"Error: {response.status_code}")
        return 'Error'

# Agregar la columna 'country' con la ubicación de cada artista
df_combined['country'] = df_combined['artist'].apply(get_artist_country)

# Limpieza: Reemplazar 'Desconocido' por 'N/A'
df_combined['country'] = df_combined['country'].replace('Desconocido', 'N/A')

# Mostrar el DataFrame con todas las columnas
print("\nTus canciones más reproducidas:")
print(df_combined[['name', 'artist', 'energy', 'tempo', 'danceability', 'loudness', 'country']])

# Guardar los datos en un archivo CSV
df_combined.to_csv('top_tracks_with_audio_features.csv', index=False)
print("\nDatos guardados en 'top_tracks_with_audio_features.csv'")

# Crear el gráfico de distribución de energía
# plt.figure(figsize=(10, 6))  # Define el tamaño del gráfico
# plt.hist(df_combined['energy'], bins=10, color='green', alpha=0.7)  # Histograma de la energía
# plt.title('Distribución de la Energía en Tus Canciones Favoritas')  # Título del gráfico
# plt.xlabel('Energía')  # Etiqueta del eje X
# plt.ylabel('Número de Canciones')  # Etiqueta del eje Y
# plt.grid(True)  # Activar cuadrícula en el gráfico
# plt.show()  # Mostrar el gráfico

# Código para Analizar el Loudness
# plt.figure(figsize=(10, 6))
# plt.hist(df_combined['loudness'], bins=10, color='blue', alpha=0.7)
# plt.title('Distribución del Loudness en Tus Canciones Favoritas')
# plt.xlabel('Loudness')
# plt.ylabel('Número de Canciones')
# plt.grid(True)
# plt.show()