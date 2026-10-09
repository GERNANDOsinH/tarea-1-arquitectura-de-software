#!/bin/bash
echo "Levantando los 5 suscriptores..."

NAME="Arica" LAT="-18.4746" LON="-70.29792" RABBITMQ_HOST="localhost" API_URL="http://localhost:8000" python subscriber/subscriber.py &
PID1=$!

NAME="Coquimbo" LAT="-29.95332" LON="-71.33947" RABBITMQ_HOST="localhost" API_URL="http://localhost:8000" python subscriber/subscriber.py &
PID2=$!

NAME="Valparaíso" LAT="-33.036" LON="-71.62963" RABBITMQ_HOST="localhost" API_URL="http://localhost:8000" python subscriber/subscriber.py &
PID3=$!

NAME="Concepción" LAT="-36.82699" LON="-73.04977" RABBITMQ_HOST="localhost" API_URL="http://localhost:8000" python subscriber/subscriber.py &
PID4=$!

NAME="Punta Arenas" LAT="-53.16282" LON="-70.90922" RABBITMQ_HOST="localhost" API_URL="http://localhost:8000" python subscriber/subscriber.py &
PID5=$!

# Cierra todos los procesos hijos al presionar Ctrl+C
trap "kill $PID1 $PID2 $PID3 $PID4 $PID5 2>/dev/null; echo 'Ciudades desconectadas.'" SIGINT
wait