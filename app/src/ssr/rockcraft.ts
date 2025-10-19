// src/ssr/rockcraft.ts

import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

// Helper to run shell commands
function runCommand(command: string, cwd: string): Promise<string> {
  return new Promise((resolve, reject) => {

    // Wrap the command in a login shell (`bash -l -c "..."`)
    // This forces it to load /etc/profile, which sets up the snap env.
const env = {
      ...process.env, // Inherit the Node.js server's environment
      // Explicitly add /snap/bin to the PATH
      PATH: `${process.env.PATH}:/snap/bin`,
    };
    exec(command=command,  { cwd:cwd, env:env }, (error, stdout, stderr) => {
      if (error) {
        // Log the actual CLI output that we need for debugging
        console.error(`[Rockcraft] FAILED COMMAND: ${command}`);
        console.error(`[Rockcraft] STDOUT: ${stdout}`);
        console.error(`[Rockcraft] STDERR: ${stderr}`);
        console.error(`[Rockcraft] error cmd: ${error.cmd}`);
        console.error(`[Rockcraft] error cause: ${error.cause}`);
        return reject(new Error(stderr || error.message));
      }
      resolve(stdout);
    });
  });
}

export class RockcraftGenerator {
  constructor(private projectPath: string) {
    if (!projectPath) {
      throw new Error('RockcraftGenerator requires a project path.');
    }
  }

  /**
   * Initializes a rockcraft.yaml in the project directory.
   */
  public async init() {
    console.log(`[Rockcraft] Initializing in ${this.projectPath}...`);
    // --force to overwrite any existing file (if any)
    await runCommand('/snap/bin/rockcraft --version', this.projectPath);
    
    // Note: You would customize the rockcraft.yaml here
    // e.g., fs.writeFileSync(...)
    console.log('[Rockcraft] rockcraft.yaml created.');
  }

  /**
   * Packs the Rock and returns the path to the .rock file.
   */
  public async pack(): Promise<string> {
    console.log(`[Rockcraft] Packing Rock in ${this.projectPath}...`);
    await runCommand('rockcraft pack', this.projectPath);

    // Find the generated .rock file
    const files = fs.readdirSync(this.projectPath);
    const rockFile = files.find(f => f.endsWith('.rock'));

    if (!rockFile) {
      throw new Error('Rock packing failed, no .rock file found.');
    }

    console.log(`[Rockcraft] Found Rock: ${rockFile}`);
    return path.join(this.projectPath, rockFile);
  }
}