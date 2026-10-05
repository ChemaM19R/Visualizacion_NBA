# Visualizacion_NBA
Este repositorio contiene un datset de datos nba extraído de Kaggle y un análisis y visualización de los mismos

## Acceso a los datos
Los datos se encuentran en el archivo Players.csv y el otro archivo hay que descargarlo desde kaggle, leer el datasets.txt para más información.

## Evolución de la NBA
La primera parte se encuentra en el archivo nba.ipynb, un notebook de jupyter, en el se preparan los datsets, primero se leen para luego unirlos y limpiarlos. Tras ello se hace una pequeña exploración de los datos y se muestran distintas gráficas para ver como ha sido la evolución de la NBA desde el año 1960 (la NBA tiene origen en 196 pero los datos están incompletos al principio)

## Dashboard interactivo
Con el dataframe limpiado obtenido en la parte de evolución (nos lo guardamos como csv, contiene para cada jugador los datos y las estadísticas de cada temporada jugada) se lleva a cabo una visualización dinámica e interactiva de los datos contenidos. Con el archivo dinamicos.py aparece un dashboard ejecutado en local y creado con dash.
El objetivo de este dashboard es hacer énfasis en una recopilación de todos los jugadores que han pasado por la NBA, poder ver sus estadísticas, su +/- y el lugar de formación que tuvieron (desde que estado o país dieron el salto a la NBA)
En el dashboard se puede filtrar por temporada, equipo, nombre de jugador, lugar de formación (pinchando en el mapa) y promedios de temporada.
