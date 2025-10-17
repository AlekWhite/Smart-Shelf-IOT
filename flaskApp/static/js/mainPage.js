const origin = window.location.origin;

function onLoad(){
    console.log("loaded mainPage.js");
    const inv = setInterval(getShelfData, 250);

    // update page when server has new data
    var socket = io();
    socket.on('update', function(msg){
        const data = msg.json();
        document.getElementById("s1Text").innerText = data.s1;
        document.getElementById("s2Text").innerText = data.s2;
        document.getElementById("s3Text").innerText = data.s3;
    });
}

// pull all data from the server on request
async function getShelfData() {
    try {
        const res = await fetch(`${origin}/pulldata`);
        if (!res.ok){
            throw new Error(`HTTP Error ${res.status}`);}
        const data = await res.json();
        document.getElementById("s1Text").innerText = data.s1;
        document.getElementById("s2Text").innerText = data.s2;
        document.getElementById("s3Text").innerText = data.s3;
    } catch (error) {
        console.error("Error fetching data", error);}
}

onLoad();