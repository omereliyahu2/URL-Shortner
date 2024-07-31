async function shortenUrl() {
    const urlInput = document.getElementById('urlInput').value;
    console.log(`URL to shorten: ${urlInput}`); // Debugging line

    const response = await fetch('http://127.0.0.1:8080/shorten/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: urlInput })
    });

    if (!response.ok) {
        console.error(`Error: ${response.statusText}`);
        return;
    }

    const data = await response.json();
    console.log(`Shortened URL: ${data.shortUrl}`); // Debugging line

    document.getElementById('shortUrl').innerText = `Shortened URL: ${data.shortUrl}`;
}
