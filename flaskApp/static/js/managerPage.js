function onLoad(){
    getShelfData();

    // setup socket
    const socket = io.connect(window.location.origin, {
    secure: true,
    rejectUnauthorized: false
    });

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    // update page when server has new data
    socket.on('update', function(data){
        console.log(data);
        document.getElementById("s1Data").innerText = data.s1;
        document.getElementById("s2Data").innerText = data.s2;
        document.getElementById("s3Data").innerText = data.s3;
    });

}

// pull all data from the server on request
async function getShelfData() {
    try {
        const res = await fetch(`${window.location.origin}/pulldata`);
        if (!res.ok){
            throw new Error(`HTTP Error ${res.status}`);}
        const data = await res.json();
        document.getElementById("s1Data").innerText = data.s1;
        document.getElementById("s2Data").innerText = data.s2;
        document.getElementById("s3Data").innerText = data.s3;
    } catch (error) {
        console.error("Error fetching data", error);}
}

onLoad();