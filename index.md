# hykr

The goal of this project was to implement a web-based pathfinding tool that uses Python in the back end. I chose to use the [Flask](https://flask.palletsprojects.com/) framework due to its simplicity.

The site is hosted on heroku [here](https://hykr-app.herokuapp.com/).

## Problem Statement

We seek to find the fastest route between a starting point and ending point, given by their latitudes and longitudes. A number of different factors control how quickly our hiker can travel between two points. We first assume that the steepness of the terrain impacts the speed of our hiker. We also assume that the hiker never learned to swim, so they can't travel across bodies of water.

Once the hiker's starting and ending points have been chosen, we form a bounding box around the midpoint of the start and end points. The bounding box is divided into a grid of tiles.

### Computing Travel Times

TODO

## Pathfinding Algorithms

There are a number of different methods that can be used to compute the optimal path between 

### Dijkstra

TODO

## Data Sources

TODO

### Hiding API Keys

TODO

## Visualizing Results

TODO
