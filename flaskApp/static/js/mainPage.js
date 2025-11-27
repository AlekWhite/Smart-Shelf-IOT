
// load item.html
async function loadItemTemplate() {
    const response = await fetch('/static/item.html');
    const text = await response.text();
    const template = document.createElement('template');
    template.innerHTML = text.trim();
    return template.content.firstElementChild;
}

async function onLoad(){

    // get data every 1sec
    async function loop() {
        try { await setAllItems();
        } catch (err) {
            console.error("Error updating data:", err); }
        setTimeout(loop, 1000); // run again in 1 second
    }

    // load stock
    await setAllItems();
    loop();

}

const status_map = {"HEALTHY": {"text": "Healthy", "color": "#6fa86bff"},
                            "UNSTABLE": {"text": "Unstable", "color": "#b29d4aff"},
                            "OFFLINE": {"text": "Offline", "color": "#6591aeff"},
                            "ANOMALY": {"text": "Anomaly", "color": "#8b7196ff"}} 

// pull item data, display items on each shelf 
async function setAllItems() {
    const temp = await loadItemTemplate();
    try {

        // fetch all display data
        const response = await fetch("/api/shelves");
        if (!response.ok) throw new Error("Failed to fetch items");
        const data = await response.json();
        const shelves = data.shelves;

        // clear any existing display data
        shelves.forEach(s => {
            const shelfContainer = document.getElementById("items_" + s.name);
            if (shelfContainer) { shelfContainer.innerHTML = ""; }
        });

        // for each item on each shelf 
        shelves.forEach(s => {
            s.items.forEach( i => {
                if (i.count > 0){
                    const item = temp.cloneNode(true);

                    // display item info
                    item.querySelector(".name").innerText = i.name;
                    item.querySelector(".count").innerText = "Count: " + i.count;
                    item.querySelector(".image").src = i.image_link;

                    // display low stock
                    var stockLevel = {"text": "Low Stock", "color": "#a3a86bff"};
                    if (i.count == 0){stockLevel = {"text": "Out of Stock", "color":"#a8796bff"};}
                    if (i.count >= i.restock_count){stockLevel = {"text": "In Stock", "color": "#5d8f59ff"};}
                    item.querySelector(".restock").innerText = stockLevel["text"];
                    item.querySelector(".restock").style.backgroundColor = stockLevel["color"];

                    // display un-allowed item alert 
                    if (!i.allowed) {
                        item.querySelector(".restock").innerText = "item not allowed on this shelf";
                        item.style.backgroundColor = "#9b8888";
                    }

                    document.getElementById("items_" + s.name).appendChild(item);
                }
            })

            // update shelf status
            const stat = status_map[s.status];
            if (stat){
                document.getElementById("status_text_" + s.name).style.backgroundColor = stat.color;
                document.getElementById("status_text_" + s.name).innerText = "Status: " + stat.text;
            }

        });
    } catch (err) {
        console.error("Error loading items:", err);
    }
}

onLoad();