const origin = window.location.origin;

function onLoad(){
    const inv = setInterval( getShelfData(), 250);
}

async function getShelfData() {
    try {
        const res = await fetch(`${origin}/pulldata`);
        if (!res.ok){
            throw new Error(`HTTP Error ${res.status}`);}
        const data = await res.json();
        document.getElementById("outText").innerText = data.s1;

    } catch (error) {
        console.error("Error fetching data", error);}

}