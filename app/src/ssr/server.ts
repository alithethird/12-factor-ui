import * as process from "node:process";
import { serveStream } from "@canonical/react-ssr/server";
import express from "express";
import render from "./renderer.js";

const PORT = process.env.PORT || 5173;

const app = express();

app.use(/^\/(assets|public)/, express.static("dist/client/assets"));

// Health check endpoint
app.get("/_status/check", (req, res) => {
  res.status(200).json({ status: "OK" });
});

app.use(serveStream(render));

app.listen(PORT, () => {
  console.log(`Server started on http://localhost:${PORT}/`);
});

export default app;
