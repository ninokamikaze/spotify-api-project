import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from bs4 import BeautifulSoup
from io import StringIO  # Importar StringIO para manejar la cadena HTML

# Configuración inicial de Spotify API
client_id = '785e1007323d4db3908b4c93764e9475'
client_secret = '41a16fe64c6b418a8116bab69309e82f'
redirect_uri = 'http://localhost:8080/callback'

# Autenticación con OAuth 2.0 para Spotify
scope = "user-top-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))

# Función para obtener el top de un país específico desde Kworb.net, con un límite de canciones
def get_kworb_top(country_code='ec', limit=20):
    """
    Obtiene el Top 200 de Spotify de un país específico desde Kworb.net con un límite de canciones.
    
    Args:
    - country_code: El código del país (por ejemplo, 'us' para Estados Unidos, 'ec' para Ecuador).
    - limit: El número de canciones a obtener (ejemplo: 20).

    Returns:
    - Un DataFrame con las canciones del Top y sus datos relevantes.
    """
    url = f'https://kworb.net/spotify/country/{country_code}_daily.html'
    response = requests.get(url)
    
    # Forzar la codificación UTF-8 para evitar problemas con caracteres especiales
    response.encoding = 'utf-8'  # Asegurar que la respuesta sea leída como UTF-8

    # Verificar si la solicitud fue exitosa
    if response.status_code != 200:
        print(f"Error al acceder a los datos de Kworb para {country_code}. Status Code: {response.status_code}")
        return pd.DataFrame()

    # Usar BeautifulSoup para extraer la tabla
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')  # Buscar la tabla principal

    # Leer la tabla en un DataFrame y limitar el número de filas según el parámetro 'limit'
    df_kworb = pd.read_html(StringIO(str(table)))[0].head(limit)

    # Ver la estructura original de la tabla
    print("Estructura original de la tabla Kworb:\n", df_kworb.head())

    # Dividir la columna "Artist and Title" en dos columnas: 'Artista' y 'Nombre'
    df_kworb[['Artista', 'Nombre']] = df_kworb['Artist and Title'].str.split(' - ', expand=True)

    # Limpiar el nombre de la canción eliminando cualquier texto que venga después de "(w/"
    df_kworb['Nombre'] = df_kworb['Nombre'].str.split(r' \(w/').str[0].str.strip()

    # Seleccionamos únicamente las columnas relevantes para continuar el análisis
    df_kworb = df_kworb[['Artista', 'Nombre']]  # Ahora tenemos solo las columnas limpias

    return df_kworb

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

# Obtener el top del país (por ejemplo, Ecuador) desde Kworb.net con un límite de 20 artistas
df_kworb = get_kworb_top('ec', limit=20)

if df_kworb.empty:
    print("No se pudo obtener el Top 200 de Kworb.")
else:
    print("Cargando lista...")

# Obtener las características de audio de las canciones del top a través de la API de Spotify
audio_features = []
for index, row in df_kworb.iterrows():
    query = f"track:{row['Nombre']} artist:{row['Artista']}"
    search_result = sp.search(q=query, type='track', limit=1)
    
    if search_result['tracks']['items']:
        track = search_result['tracks']['items'][0]
        track_id = track['id']  # Obtener el ID del track
        
        # Obtener las características de audio usando el ID de la canción
        features = sp.audio_features(track_id)[0]
        if features:
            audio_features.append({
                'name': row['Nombre'],
                'artist': row['Artista'],
                'id': track_id,
                'energy': features['energy'],
                'tempo': features['tempo'],
                'danceability': features['danceability'],
                'loudness': features['loudness']
            })
        else:
            print(f"No se encontraron características de audio para {row['Nombre']} - {row['Artista']}")
    else:
        print(f"No se encontró la canción {row['Nombre']} de {row['Artista']} en Spotify.")

# Crear un DataFrame con las características de audio
df_audio_features = pd.DataFrame(audio_features)

# Agregar la columna 'country' con la ubicación de cada artista
df_audio_features['country'] = df_audio_features['artist'].apply(get_artist_country)

# Limpieza: Reemplazar 'Desconocido' por 'N/A'
df_audio_features['country'] = df_audio_features['country'].replace('Desconocido', 'N/A')

# Mostrar el DataFrame con todas las columnas
print("\nTop de canciones con características de audio y país:")
print(df_audio_features[['name', 'artist', 'energy', 'tempo', 'danceability', 'loudness', 'country']])

# Guardar los datos en un archivo CSV
df_audio_features.to_csv('kworb_top_tracks_with_audio_features.csv', index=False)
print("\nDatos guardados en 'kworb_top_tracks_with_audio_features.csv'")

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