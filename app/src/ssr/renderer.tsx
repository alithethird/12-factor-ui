import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { JSXRenderer } from "@canonical/react-ssr/renderer";
import EntryServer from "./entry-server.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const htmlString = readFileSync(
  path.resolve(__dirname, "../client/index.html"),
  "utf8"
);

const Renderer = new JSXRenderer(EntryServer, {
  htmlString,
});

export default Renderer.render;
