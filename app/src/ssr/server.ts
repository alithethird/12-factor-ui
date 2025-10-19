// src/ssr/server.ts

import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { exec } from 'child_process';
import tmp from 'tmp'; // For creating secure temporary directories

// --- 1. Setup Express & Middleware ---

const app = express();
const port = 8080; // The port your React app will call

// Enable CORS for your React app
app.use(cors({ origin: 'http://localhost:5173' })); // Adjust if your React port is different
app.use(express.json());

// Configure Multer for file uploads
// We'll save uploads to the OS's temporary directory
const upload = multer({ dest: tmp.tmpNameSync() });

// --- 2. Helper Functions ---

/**
 * Promisified version of child_process.exec
 */
function runCommand(command: string): Promise<string> {
  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error(`exec error: ${error}`);
        return reject(new Error(stderr || error.message));
      }
      resolve(stdout);
    });
  });
}

/**
 * Safely create a temporary directory.
 */
function createTempDir(): Promise<{ path: string; cleanup: () => void }> {
  return new Promise((resolve, reject) => {
    tmp.dir({ unsafeCleanup: true }, (err, path, cleanup) => {
      if (err) {
        return reject(err);
      }
      resolve({ path, cleanup });
    });
  });
}

// --- 3. Backend Service Classes ---

/**
 * Downloads a GitHub repository to a temporary folder.
 */
class GithubDownloader {
  constructor(private repoUrl: string) { }

  public async download(): Promise<{ folderPath: string; cleanup: () => void }> {
    const { path: tempDir, cleanup } = await createTempDir();
    console.log(`Cloning ${this.repoUrl} into ${tempDir}...`);

    // Use --depth 1 to only get the latest commit, which is much faster
    const command = `git clone --depth 1 ${this.repoUrl} ${tempDir}`;

    await runCommand(command);

    console.log(`Successfully cloned to ${tempDir}`);
    return { folderPath: tempDir, cleanup };
  }
}

/**
 * Extracts a .zip or .tar.gz file to a temporary folder.
 */
class ArchiveExtractor {
  constructor(private file: Express.Multer.File) { }

  public async extract(): Promise<{ folderPath: string; cleanup: () => void }> {
    const { path: tempDir, cleanup } = await createTempDir();
    const filePath = this.file.path;
    const fileType = this.file.mimetype;

    console.log(`Extracting ${this.file.originalname} to ${tempDir}...`);
    console.log(`File type: ${fileType}`);
    console.log(`File path: ${filePath}`);
    let command: string;

    if (fileType === 'application/zip' || filePath.endsWith('.zip')) {
      command = `unzip ${filePath} -d ${tempDir}`;
    } else if (fileType === 'application/gzip' || filePath.endsWith('.tar.gz')) {
      command = `tar -xzf ${filePath} -C ${tempDir}`;
    } else if (fileType === 'application/x-tar' || filePath.endsWith('.tar')) {
      command = `tar -xf ${filePath} -C ${tempDir}`;
    } else {
      cleanup();
      throw new Error(`Unsupported file type: ${fileType}`);
    }

    await runCommand(command);

    console.log(`Successfully extracted to ${tempDir}`);
    return { folderPath: tempDir, cleanup };
  }
}
type CheckResult = {
  valid: boolean;
  error?: string;
};

/**
 * Checks the project structure based on the selected framework.
 */
class ApplicationProcessor {
  constructor(private folderPath: string, private framework: string) { }


  public async checkProject(): Promise<CheckResult> {
    console.log(`Checking project at ${this.folderPath} for framework: ${this.framework}`);
    // --- ADD THIS DEBUG BLOCK ---
    try {
      console.log(`[DEBUG] File structure in ${this.folderPath}:`);
      // We use `ls -R` for a recursive file listing.
      // We pipe to `head -n 20` to avoid spamming the log if the repo is huge.
      const fileList = await runCommand(`ls -R ${this.folderPath} | head -n 20`);
      console.log('---------------------------------');
      console.log(fileList);
      console.log('---------------------------------');
    } catch (err: any) {
      // We warn instead of erroring, so debugging doesn't crash the server.
      console.warn(`[DEBUG] Could not list file structure: ${err.message}`);
    }
    // --- END DEBUG BLOCK ---
    // Helper function to check if a file exists
    const fileExists = (fileName: string) => {
      return fs.existsSync(path.join(this.folderPath, fileName));
    };

    const checkRequirements = (requirementsPath, packageName) => {
      if (!requirementsPath || !packageName) {
        return false;
      }

      // 1. Sanitize the package name for use in a RegExp
      const escapedPackageName = packageName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

      // 2. Create a Regular Expression to find the package.
      // This regex looks for:
      // ^\s* : Start of line, allowing for leading whitespace.
      // ${...}     : The escaped package name.
      // (?:\s* : Non-capturing group for what follows the name (optional).
      // (?:[<=>!~] : Looks for version specifiers (==, >=, <=, !=, ~)
      // |#.*)      : OR a comment (# and anything after it).
      // )?         : Makes the whole trailing part optional.
      // $          : End of the package entry (or line).
      // i          : Case-insensitive search.
      // m          : Multiline mode, so '^' and '$' match start/end of lines.

      // Key parts of the regex logic:
      // - \s* means 0 or more spaces.
      // - (?:...|...) ensures we stop matching when we hit a version specifier or a comment.
      // - If no specifier or comment is present, it looks for the end of the line.

      const packageRegex = new RegExp(
        `^\\s*${escapedPackageName}(?:\\s*(?:[<=>!~].*|#.*))?$`,
        'im'
      );

      // 3. Normalize content: Remove blank lines and lines starting with a comment, 
      //    and then check for a match.
      // Note: The regex with 'm' flag is powerful enough to handle most cases 
      // without heavy pre-processing, but trimming is useful.
      const requirementsContent = fs.readFileSync(requirementsPath, 'utf-8');
      const lines = requirementsContent.split('\n');

      console.log(lines);
      // Filter out blank lines and full-line comments before checking
      const relevantContent = lines
        .map(line => line.trim())
        .filter(line => line.length > 0 && !line.startsWith('#'))
        .join('\n');

      return packageRegex.test(relevantContent);
    };

    switch (this.framework) {
      case 'flask':
        // Check for 'requirements.txt' or 'app.py'
        if (!fileExists('requirements.txt') || !fileExists('app.py') || !checkRequirements(path.join(this.folderPath, "requirements.txt"), "flask")) {
          return { valid: false, error: "Project missing 'requirements.txt' or 'app.py'." };
        }
        return { valid: true };

      case 'django':
        // Check for 'manage.py'
        if (!fileExists('requirements.txt') || !checkRequirements(path.join(this.folderPath, "requirements.txt"), "django")) {
          return { valid: false, error: "Project missing 'manage.py' at root." };
        }
        return { valid: true };

      case 'fastapi':
        // Check for 'main.py'
        if (!fileExists('requirements.txt') || !fileExists('app.py') || !checkRequirements(path.join(this.folderPath, "requirements.txt"), "fastapi")) {
          return { valid: false, error: "Project missing 'app.py' at root." };
        }
        return { valid: true };

      case 'go':
        // Check for 'go.mod'
        if (!fileExists('go.mod') || !fileExists('go.sum')) {
          return { valid: false, error: "Project missing 'go.mod' file." };
        }
        return { valid: true };

      case 'expressjs':
        // Check for 'package.json'
        if (!fileExists('package.json')) {
          return { valid: false, error: "Project missing 'package.json'." };
        }
        const packageJsonPath = path.join(this.folderPath, 'package.json');
        const fileContent = fs.readFileSync(packageJsonPath, 'utf-8');
        const packageJson = JSON.parse(fileContent);
        const scripts = packageJson.scripts;

        console.log('[DEBUG] Found scripts in package.json:', scripts);

        if (scripts && scripts.start) {
          console.log("[DEBUG] Found 'start' script.");
          return { valid: true }; // Success!
        } else {
          return { valid: false, error: "The 'package.json' is missing a 'start' script." };
        }

      case 'springboot':
        // Check for 'pom.xml' or 'build.gradle'
        if (!fileExists('pom.xml') && !fileExists('build.gradle')) {
          return { valid: false, error: "Project missing 'pom.xml' or 'build.gradle'." };
        }
        return { valid: true };

      default:
        return { valid: false, error: `Unknown framework: ${this.framework}` };
    }
  }
}

// --- 4. API Endpoints ---

/**
 * Endpoint for validating a GitHub repository.
 */
app.post('/api/validate-github', async (req: Request, res: Response) => {
  const { repoUrl, framework } = req.body;

  if (!repoUrl || !framework) {
    return res.status(400).json({ success: false, error: 'Missing repoUrl or framework.' });
  }

  let cleanup: () => void = () => { }; // No-op cleanup function

  try {
    // 1. Download
    const downloader = new GithubDownloader(repoUrl);
    const { folderPath, cleanup: downloadCleanup } = await downloader.download();
    cleanup = downloadCleanup; // Assign the real cleanup function

    // 2. Validate
    const processor = new ApplicationProcessor(folderPath, framework);
    const result = await processor.checkProject();

    if (!result.valid) {
      throw new Error(result.error || 'Project validation failed.');
    }
    const projectName = repoUrl.split('/').pop()?.replace('.git', '') || 'GitHub Repo';
    // 3. Success
    res.json({
      success: true,
      sourceData: { type: 'github', url: repoUrl, projectName: projectName, },
    });
  } catch (error: any) {
    res.status(400).json({ success: false, error: error.message });
  } finally {
    cleanup(); // Clean up the temp directory
  }
});

/**
 * Endpoint for validating an uploaded file.
 */
app.post('/api/validate-upload', upload.single('file'), async (req: Request, res: Response) => {
  const { framework } = req.body;
  const file = req.file;

  if (!file || !framework) {
    return res.status(400).json({ success: false, error: 'Missing file or framework.' });
  }

  let extractCleanup: () => void = () => { };

  try {
    // 1. Extract
    const extractor = new ArchiveExtractor(file);
    const { folderPath, cleanup } = await extractor.extract();
    extractCleanup = cleanup;

    let projectPath = folderPath;
    let projectName = file.originalname.replace('.zip', '').replace('.tar.gz', '').replace('.tar', ''); // Default

    // Read the contents of the extracted directory
    const rootItems = fs.readdirSync(folderPath).filter(name =>
      !name.startsWith('.') && name !== '__MACOSX'
    );

    // If there is exactly one item, and it's a directory, use it as the project path
    if (rootItems.length === 1) {
      const singleItemPath = path.join(folderPath, rootItems[0]);
      if (fs.statSync(singleItemPath).isDirectory()) {
        projectPath = singleItemPath; // This is the real project path
        projectName = rootItems[0];   // This is the real project name
      }
    }
    // Else: we assume it's a "rootless" archive, so folderPath is correct.
    // 2. Validate
    const processor = new ApplicationProcessor(projectPath, framework);
    const result = await processor.checkProject();

    if (!result.valid) {
      throw new Error(result.error || 'Project validation failed.');
    }

    // 3. Success
    res.json({
      success: true,
      sourceData: { type: 'upload', fileName: file.originalname, projectName: projectName, },
    });
  } catch (error: any) {
    res.status(400).json({ success: false, error: error.message });
  } finally {
    // Clean up the extracted folder
    extractCleanup();
    // Clean up the original upload file
    if (file) {
      fs.unlink(file.path, (err) => {
        if (err) console.error(`Failed to delete uploaded file: ${file.path}`, err);
      });
    }
  }
});

// --- 5. Global Error Handler & Server Start ---

// Basic global error handler
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error(err.stack);
  res.status(500).send('Something broke!');
});

app.listen(port, () => {
  console.log(`🚀 Backend server listening at http://localhost:${port}`);
});