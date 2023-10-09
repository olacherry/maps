import folium
from geopy.geocoders import Nominatim
from folium import plugins
import pandas as pd
import branca.colormap as cm
import sys
pd.options.mode.chained_assignment = None


# функция поиска координат городов
def find_cords(cities):
    geolocator = Nominatim(user_agent="MyApp")
    cord_list = list()
    for city in cities:
        location = geolocator.geocode(city)
        cord_list.append([location.latitude, location.longitude])
    return cord_list


# функция удаления симметричных маршрутов из dataframe
def delete_repeat(df):
    delete = list()
    for i in range(df.shape[0] - 1):
        for j in range(i + 1, df.shape[0]):
            if df.iloc[i]['city1'] == df.iloc[j]['city2'] and df.iloc[j]['city1'] == df.iloc[i]['city2']:
                new_size = df.iloc[i]['size'] + df.iloc[j]['size']
                df.iat[i, 2] = new_size
                delete.append(j)
    return delete


# создание путей между городами
def ways(df, coords,
         colormap, map):
    ways = list()
    fg1 = folium.FeatureGroup(name='Ways')
    for i in range(df.shape[0]):
        way1 = df.iloc[i]['city1']
        way2 = df.iloc[i]['city2']
        repeat = df.iloc[i]['size']
        size = df['size'].tolist()
        color = colormap(repeat)
        ways.append(coords.get(way1))
        ways.append(coords.get(way2))
        fg1.add_child(folium.PolyLine(ways, color=color, weight=3, tooltip="из г. "+way1+' в г. '+way2))
        ways.clear()
    map.add_child(fg1)


# функция создания легенды
def legend(sizes):
    if min(sizes) == max(sizes):
        repeat = str(min(sizes))
        legend_html = '''
                            <div style="position: fixed; 
                                        bottom: 50px; right: 50px; width: 200px; height: 100px; 
                                        border:2px solid grey; z-index:9999; font-size:14px;
                                        ">&nbsp; Legend <br>
                                          &nbsp; <p> {repeat} повторений маршрута 
                                            <i class="fa-solid fa-minus fa-xl" style="color:red"></i></p><br>
                                          
                            </div>
                            '''.format(repeat=repeat)
    else:
        repeat = str(min(sizes))
        repeat1 = str(int(max(sizes)*0.25))
        repeat11 = str(int(max(sizes)*0.25)+1)
        repeat2 = str(int(max(sizes) * 0.5))
        repeat22 = str(int(max(sizes) * 0.5)+1)
        repeat3 = str(int(max(sizes) * 0.75))
        repeat33 = str(int(max(sizes) * 0.75)+1)
        repeat4 = str(int(max(sizes)))
        legend_html = '''
                                    <div style="position: fixed; 
                                                bottom: 50px; right: 50px; width: 250px; height: 170px; 
                                                border:2px solid grey; z-index:9999; font-size:14px;
                                                ">&nbsp; Legend <br>
                                                  &nbsp; <p> от {repeat} до {repeat1} повторений маршрута 
                                                  <i class="fa-solid fa-minus fa-xl" style="color:red"></i></p>
                                                   <p> от {repeat11} до {repeat2} повторений маршрута 
                                                  <i class="fa-solid fa-minus fa-xl" style="color:orange"></i></p>
                                                   <p> от {repeat22} до {repeat3} повторений маршрута 
                                                  <i class="fa-solid fa-minus fa-xl" style="color:yellow"></i></p>
                                                  <p> от {repeat33} до {repeat4} повторений маршрута 
                                                  <i class="fa-solid fa-minus fa-xl" style="color:green"></i></p>

                                    </div>
                                    '''.format(repeat=repeat, repeat1=repeat1, repeat2=repeat2, repeat3=repeat3, repeat4=repeat4,
                                               repeat11=repeat11, repeat22=repeat22, repeat33=repeat33)
    return legend_html


# функция создания colormap
def create_colormap(sizes):
    colormap = cm.StepColormap(['red', 'orange', 'yellow', 'green'],
                               vmin=min(sizes), vmax=max(sizes),
                               index=[min(sizes), max(sizes) * 0.25, max(sizes) * 0.5, max(sizes) * 0.75, max(sizes)],
                               caption='Частота повторения маршрутов')
    return colormap


# работа с df из марщрута между 2 городами
def df_ways(df):
    df.columns = ['city1', 'city2']
    df = df.groupby(df.columns.tolist (), as_index=False). size()
    df = df.replace(r'\s+', '', regex=True)
    df = df.reset_index(drop=True)
    delete = delete_repeat(df)
    df = df.drop(index=delete)
    df = df.reset_index(drop=True)
    return df


# работа с df из городов
def df_city(df):
    df.columns = ['city']
    df = df.groupby(df.columns.tolist(), as_index=False).size()
    df = df.replace(r'\s+', '', regex=True)
    df = df.reset_index(drop=True)
    return df


df = pd.read_csv('Маршруты.csv', sep=';')
df = df.dropna(axis=1, how='all')
df = df.dropna()
df = pd.concat([pd.DataFrame([df.columns.values], columns=df.columns), df], ignore_index=True)
m1 = folium.Map(location=[64.6863136, 97.7453061],
                zoom_start=4)
folium.plugins.Geocoder().add_to(m1)
folium.TileLayer('cartodbdark_matter', name="dark mode", control=True).add_to(m1)
folium.TileLayer('cartodbpositron', name="light mode", control=True).add_to(m1)
folium.TileLayer('stamenterrain').add_to(m1)
fg = folium.FeatureGroup(name='Markers')

if df.shape[1] == 2:
    df = df_ways(df)
    cities = df['city1']. tolist()+df['city2']. tolist()
    cities = list(set(cities))
    sizes = df['size'].tolist()
    cord_list = find_cords(cities)
    coords = dict(zip(cities, cord_list))
    colormap = create_colormap(sizes)
    for i in range(len(cord_list)):
        fg.add_child(folium.Marker(location=cord_list[i], popup=cities[i], icon=folium.Icon('green')))
    ways(df, coords, colormap, m1)


elif df.shape[1] == 1:
    df = df_city(df)
    cities = df['city'].tolist()
    cities = list(set(cities))
    cord_list = find_cords(cities)
    coords = dict(zip(cities, cord_list))
    sizes = df['size'].tolist()
    colormap = create_colormap(sizes)
    for i in range(len(cord_list)):
        idx = df[df['city'] == cities[i]].index
        color = colormap(df.at[idx[0], "size"])
        fg.add_child(folium.CircleMarker(location=cord_list[i], radius=10, fill=True,
                                         color=color,
                                         fill_color=color,
                                         popup=cities[i]))


else:
    print('Uncorrect input Data')
    sys.exit(1)

legend_html = legend(sizes)
m1.get_root().html.add_child(folium.Element(legend_html))
m1.add_child(colormap)
m1.add_child(fg)
folium.LayerControl().add_to(m1)
m1.save("index.html")
