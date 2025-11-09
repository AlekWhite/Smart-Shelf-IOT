
// load item.html
async function loadItemTemplate() {
    const response = await fetch('/static/item.html');
    const text = await response.text();
    const template = document.createElement('template');
    template.innerHTML = text.trim();
    return template.content.firstElementChild;
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
                if (i.allowed){
                    const item = temp.cloneNode(true);

                    // display item info
                    item.querySelector(".name").innerText = i.name;
                    item.querySelector(".image").src = i.image_link;

                    // display & setup manager options
                    item.querySelector(".manager_html").style.display = "block";
                    item.querySelector(".textInpR").innerText = i.restock_count;
                    item.querySelector(".textInpC").innerText = i.count;
                    item.querySelectorAll(".shelfCaller").forEach(el => { el.value = s.name; });
                    item.querySelectorAll(".itemCaller").forEach(el => { el.value = i.name; });

                    document.getElementById("items_" + s.name).appendChild(item);
                }
            })
        });
    } catch (err) {
        console.error("Error loading items:", err);
    }
}

async function onLoad(){

    // load items from the db for each shelf
    await setAllItems();

    // get items from, put them in the dropdown menu 
    try {
        const response = await fetch("/api/items");
        if (!response.ok) throw new Error("Failed to fetch items");
        const items = await response.json();
        const dropdown1 = document.getElementById("newItemsS1");
        const dropdown2 = document.getElementById("newItemsS2");
        const dropdown3 = document.getElementById("newItemsS3");
        items.forEach(item => {
            const option = document.createElement("option");
            option.value = item.name;
            option.textContent = item.name;
            dropdown1.appendChild(option.cloneNode(true));
            dropdown2.appendChild(option.cloneNode(true));
            dropdown3.appendChild(option.cloneNode(true));
        });
    } catch (err) {
        console.error("Error loading items:", err);
    }
}


onLoad();