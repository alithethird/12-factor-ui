import { Button, TooltipArea } from "@canonical/react-ds-core";
import { Suspense, useState, lazy } from "react";
import canonicalLogo from "./assets/canonical.svg";
import "./index.css";

const LazyButton = lazy(
  () =>
    new Promise((resolve) => {
      // @ts-ignore
      setTimeout(() => resolve(import("./components/LazyComponent")), 2000);
    }),
);

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="app">
      <div>
        <a
          href="https://canonical.com"
          target="_blank"
          referrerPolicy="no-referrer"
          rel="noreferrer"
          style={{ display: "block", width: "100px"}}
        >
          <img src={canonicalLogo} className="logo" alt="Canonical logo" />
        </a>
      </div>
      <h1>React SSR with Express</h1>
      <Suspense fallback={"Loading..."}>
        <LazyButton />
      </Suspense>
      <div className="card">
        <TooltipArea
          preferredDirections={["right", "bottom"]}
          Message={`Increment count to ${count + 1}`}
        >
          <Button onClick={() => setCount((count) => count + 1)}>
            Count: {count}
          </Button>
        </TooltipArea>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
    </div>
  );
}

export default App;
