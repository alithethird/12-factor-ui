# Developer's Guide

This guide details the various ways to set up and run the Charmed Node.js Boilerplate for local development.

## Develop with Taskfile

This section explains how to set up and run the Node.js boilerplate using Taskfile and Docker.

### Prerequisites
* [Taskfile](https://taskfile.dev/installation/)
* [Docker](https://docs.docker.com/engine/install/)

### Running the Project

To start the development server, run:

```bash
task
```

*Note: You might have to restart the terminal and run the command again if you didn't have `docker` installed before running this command.*

Once the server has started, you can visit:
* [http://localhost:5173](http://localhost:5173) to see the frontend running with Hot Module Replacement using Vite.
* [http://localhost:8000](http://localhost:8000) to see the Express server running with reloading enabled.

## Develop with Bun

This section explains how to set up and run the Node.js boilerplate manually using Bun.

### Prerequisites
* [Bun](https://bun.sh/docs/installation)
* [Nodemon](https://nodemon.io/) (Optional: If you want automatic server restart during development)

### Running the Project

Run `bun run serve` to run a server-side rendered version of the app using the [React SSR](https://github.com/canonical/pragma/tree/main/packages/react/ssr) package. You can also run `bun run dev` to run a client-side rendered version of the app using Vite.

### Watch Commands

*These commands should not be used alongside `bun run serve`*

You can run `bun run watch:server` and `bun run watch:client` to automatically build client and server code whenever there is a change in the source files.

This should be used alongside [Nodemon](https://nodemon.io/) to automatically restart the server when the source files change. After running the watch commands, simply run:

```bash
nodemon --watch dist --ext js --exec "node dist/server/server.js"
```

Your server will start on [http://localhost:8000](http://localhost:8000).

### Troubleshooting Bin Script Issues

You may run into an issue where `serve-express` is not linked in `node_modules/.bin` after running `bun i`. This will result in an error when running `bun run serve:cli`.

To fix this, run `bun i` again. For more information, see [this documentation](https://github.com/jmuzina/bun-repro/tree/7c9f9efae2843bc904eabc10825e36502251d13f/bun-wont-link-modules/express-example).

## Next Steps

With your development environment configured, you're ready to:

* [Build the Application](./build-app.md) for testing or deployment.