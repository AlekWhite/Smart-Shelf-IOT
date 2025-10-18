# Smart-Shelf-IOT
The Smart Shelf System consists of a set of three small shelves, each with a weight sensor, used to identify the quantity of each item being stored. This data is then analyzed and compared against the expected weight for a single unit of product. The results are displayed to users through a mobile web interface, as the contents of the shelves change the mobile web interface is updated in real time. 

Start:

``docker-compose up --build``

Access database shell:

``docker compose exec db psql -U postgres -d mydb``