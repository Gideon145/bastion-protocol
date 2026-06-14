// API proxy for Railway healthcheck — avoids CORS issues in browser
export async function GET() {
  try {
    const res = await fetch("https://bastion-protocol-production.up.railway.app");
    const data = await res.json();
    return Response.json(data, {
      headers: { "Access-Control-Allow-Origin": "*" },
    });
  } catch {
    return Response.json({ error: "Agent unreachable" }, { status: 502 });
  }
}
