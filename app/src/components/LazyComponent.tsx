import { Button } from "@canonical/react-ds-core";

export default function LazyComponent() {
  return (
    <Button appearance={"positive"} onClick={() => alert("clicked!")}>
      Click me
    </Button>
  );
}

