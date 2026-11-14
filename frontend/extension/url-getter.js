document.addEventListener('DOMContentLoaded', function () {

	// Find the button and attach the click event listener
	const button = document.getElementById("myButton");
	button.addEventListener('click', control_function);
});

async function control_function() {
	let tab_url = await getUrl();
	urlDisplayChange(tab_url);
	let name = await getNameFromUrl(tab_url);
	console.error(name);
	getTitle(tab_url);
}

async function getUrl() {

	const tabs = await chrome.tabs.query({
        	active: true,
        	currentWindow: true
    	});

    	if (tabs && tabs.length > 0) {
		return tabs[0].url;
	}

	return -1;
}

function urlDisplayChange(url) {

	if (url != -1) {
        	document.getElementById("scanned-url").textContent = url;
    	} else {
    		document.getElementById("scanned-url").textContent = "No valid active tab";
	}
}

async function getNameFromUrl(url) {
	const regex = /https:\/\/www\.([a-zA-Z0-9]+)\.(.*)/;
	const matches = url.match(regex);
	if (matches && matches.length() > 1) {
		return matches[1];
	}
	return -1;
}

async function getTitle(url) {
	try {
		const response = await fetch(url);
		if (!response.ok) {
			throw new Error(`Status: ${response.status}`);
		}

		const htmlString = await response.text();
		const parser = new DOMParser();
		const doc = parser.parseFromString(htmlString, 'text/html');
		const title = doc.querySelector('title').innerText;

		document.getElementById("scanned-title").innerHTML = title;

	} catch (error) {
		console.error("Original error:", error);
		console.error("Error cause:", error.cause);
	}
}
