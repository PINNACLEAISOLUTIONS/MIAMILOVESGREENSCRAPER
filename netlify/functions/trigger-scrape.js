exports.handler = async function (event, context) {
    // Only allow POST
    if (event.httpMethod !== "POST") {
        return {
            statusCode: 405,
            body: JSON.stringify({ error: "Method not allowed" })
        };
    }

    const token = process.env.GH_ACTION_TOKEN;
    const owner = process.env.GH_OWNER || "PINNACLEAISOLUTIONS";
    const repo = process.env.GH_REPO || "MIAMILOVESGREENSCRAPER";
    const workflow = process.env.GH_WORKFLOW || "daily_scrape.yml";

    if (!token) {
        console.error("Missing GH_ACTION_TOKEN");
        return {
            statusCode: 500,
            body: JSON.stringify({ error: "Server configuration error: Token missing" })
        };
    }

    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(
            `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`,
            {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Netlify-Scraper-Trigger"
                },
                body: JSON.stringify({ ref: "master" })
            }
        );

        if (response.status === 204) {
            return {
                statusCode: 200,
                body: JSON.stringify({ success: true, message: "Scrape triggered" })
            };
        } else {
            const text = await response.text();
            return {
                statusCode: 502,
                body: JSON.stringify({ success: false, error: `GitHub API ${response.status}`, detail: text })
            };
        }
    } catch (error) {
        console.error(error);
        return {
            statusCode: 500,
            body: JSON.stringify({ success: false, error: error.message })
        };
    }
};
