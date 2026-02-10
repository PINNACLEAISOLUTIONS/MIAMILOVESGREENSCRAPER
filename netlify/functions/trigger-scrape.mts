import type { Config } from "@netlify/functions";



export default async (req: Request) => {
    // Only allow POST requests
    if (req.method !== "POST") {
        return new Response(JSON.stringify({ error: "Method not allowed" }), {
            status: 405,
            headers: { "Content-Type": "application/json" },
        });
    }

    // Get token from process.env (standard Node.js patterns work best in Netlify Functions)
    const token = process.env.GH_ACTION_TOKEN;
    const owner = process.env.GH_OWNER || "PINNACLEAISOLUTIONS";
    const repo = process.env.GH_REPO || "MIAMILOVESGREENSCRAPER";
    const workflow = process.env.GH_WORKFLOW || "daily_scrape.yml";

    if (!token) {
        console.error("Missing GH_ACTION_TOKEN in environment variables");
        return new Response(
            JSON.stringify({ error: "Server configuration error: Token missing" }),
            { status: 500, headers: { "Content-Type": "application/json" } }
        );
    }

    // Trigger the GitHub Actions workflow
    try {
        const ghResponse = await fetch(
            `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    Accept: "application/vnd.github.v3+json",
                    "User-Agent": "Netlify-Scraper-Trigger",
                },
                body: JSON.stringify({ ref: "master" }),
            }
        );

        if (ghResponse.status === 204) {
            return new Response(
                JSON.stringify({
                    success: true,
                    message: "Scrape triggered! Results in ~2 minutes.",
                }),
                { status: 200, headers: { "Content-Type": "application/json" } }
            );
        } else {
            const errorText = await ghResponse.text();
            return new Response(
                JSON.stringify({
                    success: false,
                    error: `GitHub API returned ${ghResponse.status}`,
                    detail: errorText,
                }),
                { status: 502, headers: { "Content-Type": "application/json" } }
            );
        }
    } catch (err) {
        return new Response(
            JSON.stringify({
                success: false,
                error: "Failed to reach GitHub API",
            }),
            { status: 500, headers: { "Content-Type": "application/json" } }
        );
    }
};

export const config: Config = {
    path: "/api/trigger-scrape",
};
