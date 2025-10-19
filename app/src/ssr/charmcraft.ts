// src/ssr/charmcraft.ts

import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';
import yaml from 'js-yaml'; // New dependency

// Define the structure of the data it expects
type ConfigOption = {
  key: string;
  type: string;
  value: string;
  isOptional: boolean;
};
type CharmData = {
  integrations: string[];
  configOptions: ConfigOption[];
  projectName: string;
};

// Helper to run shell commands
function runCommand(command: string, cwd: string): Promise<string> {
  return new Promise((resolve, reject) => {
    exec(command, { cwd }, (error, stdout, stderr) => {
      if (error) {
        console.error(`[Charmcraft] exec error: ${error}`);
        return reject(new Error(stderr || error.message));
      }
      resolve(stdout);
    });
  });
}

// A simple map to convert our integration IDs to charm relations
const INTEGRATION_MAP: Record<string, any> = {
  postgresql: {
    db: { interface: 'postgresql_client' },
  },
  prometheus: {
    'metrics-endpoint': { interface: 'prometheus_scrape' },
  },
  grafana: {
    'grafana-dashboard': { interface: 'grafana_dashboard' },
  },
  loki: {
    logging: { interface: 'loki_push_api' },
  },
  ingress: {
    ingress: { interface: 'ingress', limit: 1 },
  },
  // Add other integrations here
};

export class CharmcraftGenerator {
  constructor(private charmPath: string, private data: CharmData) {
    if (!charmPath || !data) {
      throw new Error('CharmcraftGenerator requires a path and data.');
    }
  }

  /**
   * Initializes a new charm project.
   */
  public async init() {
    console.log(`[Charmcraft] Initializing new charm at ${this.charmPath}...`);
    // Create the directory first
    fs.mkdirSync(this.charmPath, { recursive: true });
    // Init inside that directory
    await runCommand(`charmcraft init --name ${this.data.projectName}`, this.charmPath);
    console.log('[Charmcraft] Charm project created.');
  }

  /**
   * Reads charmcraft.yaml, updates it, and writes it back.
   */
  public async update() {
    console.log('[Charmcraft] Updating charmcraft.yaml...');
    const yamlPath = path.join(this.charmPath, this.data.projectName, 'charmcraft.yaml');
    
    // 1. Read and Parse
    let charmYaml: any;
    try {
      const fileContents = fs.readFileSync(yamlPath, 'utf8');
      charmYaml = yaml.load(fileContents);
    } catch (e: any) {
      throw new Error(`Failed to read or parse charmcraft.yaml: ${e.message}`);
    }

    // 2. Add Integrations (as 'requires' relations)
    const relations: Record<string, any> = {};
    for (const integrationId of this.data.integrations) {
      if (INTEGRATION_MAP[integrationId]) {
        Object.assign(relations, INTEGRATION_MAP[integrationId]);
      }
    }
    charmYaml.requires = relations;

    // 3. Add Config Options
    const options: Record<string, any> = {};
    for (const config of this.data.configOptions) {
      options[config.key] = {
        type: config.type,
        description: `A custom config option for ${config.key}.`,
      };
      
      // Per our rule: only optional configs have default values
      if (config.isOptional) {
        options[config.key].default = this.getTypedValue(config.value, config.type);
      }
    }
    charmYaml.options = options;

    // 4. Write back
    try {
      const newYamlContents = yaml.dump(charmYaml);
      fs.writeFileSync(yamlPath, newYamlContents, 'utf8');
    } catch (e: any) {
      throw new Error(`Failed to write charmcraft.yaml: ${e.message}`);
    }
    console.log('[Charmcraft] charmcraft.yaml updated successfully.');
  }
  
  /**
   * Packs the charm and returns the path to the .charm file.
   */
  public async pack(): Promise<string> {
    const charmProjectPath = path.join(this.charmPath, this.data.projectName);
    console.log(`[Charmcraft] Packing Charm in ${charmProjectPath}...`);
    await runCommand('charmcraft pack', charmProjectPath);

    // Find the generated .charm file
    const files = fs.readdirSync(charmProjectPath);
    const charmFile = files.find(f => f.endsWith('.charm'));

    if (!charmFile) {
      throw new Error('Charm packing failed, no .charm file found.');
    }

    console.log(`[Charmcraft] Found Charm: ${charmFile}`);
    return path.join(charmProjectPath, charmFile);
  }

  /** Helper to cast string default value to the correct type */
  private getTypedValue(value: string, type: string) {
    if (type === 'bool') return value.toLowerCase() === 'true';
    if (type === 'int') return parseInt(value, 10) || 0;
    if (type === 'float') return parseFloat(value) || 0.0;
    return value; // string or secret
  }
}