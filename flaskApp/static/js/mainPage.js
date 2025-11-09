
// load item.html
async function loadItemTemplate() {
    const response = await fetch('/static/item.html');
    const text = await response.text();
    const template = document.createElement('template');
    template.innerHTML = text.trim();
    return template.content.firstElementChild;
}

async function onLoad(){

    // setup socket
    const socket = io.connect(window.location.origin, {
        secure: true,
        rejectUnauthorized: false
    });
    socket.on('connect', () => {
        console.log('socket connected to server');
    });

    // display new stock info when the server has an update
    socket.on('update', setAllItems);

    // load stock
    await setAllItems();
 
}

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
                    var stockLevel = "Low Stock"
                    if (i.count == 0){stockLevel = "Out of Stock";}
                    if (i.count >= i.restock_count){stockLevel = "In Stock";}
                    item.querySelector(".restock").innerText = stockLevel;

                    // display un-allowed item alert 
                    if (!i.allowed) {
                        item.querySelector(".restock").innerText = "item not allowed on this shelf";
                        item.style.backgroundColor = "#9b8888";
                    }

                    document.getElementById("items_" + s.name).appendChild(item);
                }
            })
        });
    } catch (err) {
        console.error("Error loading items:", err);
    }
}

onLoad();