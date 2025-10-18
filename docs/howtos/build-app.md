# Build the Application

This guide explains how to build your Charmed Node.js Boilerplate application for production or deployment.

The application has separate build processes for its client-side (frontend) and server-side (backend, including Server-Side Rendering). The primary build commands are defined in the `app/package.json` file.

## Prerequisites
* Ensure you have [Bun](https://bun.sh/docs/installation) installed, as the build scripts use `bun run`.

## Build Commands

### Full Build (Client and Server)

To build both the client-side and server-side components of the application, use the main `build` script:

```bash
bun run build
```

This command executes: `bun run build:client` followed by `bun run build:server`.

### Client-Side Build

To build only the client-side assets (for the frontend):

```bash
bun run build:client
```

This command uses `vite build --ssrManifest --outDir dist/client`. The output will be in the `dist/client` directory.

### Server-Side Build

The server-side build process can be configured for different Server-Side Rendering (SSR) approaches. The default `build:server` command uses the `middleware` approach.

* **Default Server Build (Middleware-based SSR):**
    ```bash
    bun run build:server
    ```
    This command executes: `bun run build:server:middleware`, which is `vite build --ssr src/ssr/server.ts --outDir dist/server`. The output will be in the `dist/server` directory.

* **CLI-based Server Build (Alternative SSR approach):**
    If you intend to use the CLI-based SSR approach, you can build the server using:
    ```bash
    bun run build:server:cli
    ```
    This command executes: `vite build --ssr src/ssr/renderer.tsx --outDir dist/server`.

After running the build commands, your compiled application assets will be available in the `dist/` directory.

## Next Steps

Once your application is built, the next logical step is to:

* [Pack and Deploy the Charm](./pack-and-deploy.md) into your Juju environment.
