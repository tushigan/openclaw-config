"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.handleConfigCommand = handleConfigCommand;exports.handlePackageCommand = handlePackageCommand;var _chalk = _interopRequireDefault(require("chalk"));
var _child_process = require("child_process");
var _configSelector = require("./cli/config-selector.js");
var _config = require("./config.js");
var _packageManager = require("./core/package-manager.js");
var _settingsManager = require("./core/settings-manager.js");
var _childProcess = require("./utils/child-process.js");
var _versionCheck = require("./utils/version-check.js");function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
function reportSettingsErrors(settingsManager, context) {
  const errors = settingsManager.drainErrors();
  for (const { scope, error } of errors) {
    console.error(_chalk.default.yellow(`Warning (${context}, ${scope} settings): ${error.message}`));
    if (error.stack) {
      console.error(_chalk.default.dim(error.stack));
    }
  }
}
function getPackageCommandUsage(command) {
  switch (command) {
    case "install":
      return `${_config.APP_NAME} install <source> [-l]`;
    case "remove":
      return `${_config.APP_NAME} remove <source> [-l]`;
    case "update":
      return `${_config.APP_NAME} update [source|self|pi] [--self] [--extensions] [--extension <source>] [--force]`;
    case "list":
      return `${_config.APP_NAME} list`;
  }
}
function printPackageCommandHelp(command) {
  switch (command) {
    case "install":
      console.log(`${_chalk.default.bold("Usage:")}
  ${getPackageCommandUsage("install")}

Install a package and add it to settings.

Options:
  -l, --local    Install project-locally (.pi/settings.json)

Examples:
  ${_config.APP_NAME} install npm:@foo/bar
  ${_config.APP_NAME} install git:github.com/user/repo
  ${_config.APP_NAME} install git:git@github.com:user/repo
  ${_config.APP_NAME} install https://github.com/user/repo
  ${_config.APP_NAME} install ssh://git@github.com/user/repo
  ${_config.APP_NAME} install ./local/path
`);
      return;
    case "remove":
      console.log(`${_chalk.default.bold("Usage:")}
  ${getPackageCommandUsage("remove")}

Remove a package and its source from settings.
Alias: ${_config.APP_NAME} uninstall <source> [-l]

Options:
  -l, --local    Remove from project settings (.pi/settings.json)

Examples:
  ${_config.APP_NAME} remove npm:@foo/bar
  ${_config.APP_NAME} uninstall npm:@foo/bar
`);
      return;
    case "update":
      console.log(`${_chalk.default.bold("Usage:")}
  ${getPackageCommandUsage("update")}

Update pi and installed packages.

Options:
  --self                  Update pi only
  --extensions            Update installed packages only
  --extension <source>    Update one package only
  --force                 Reinstall pi even if the current version is latest

Short forms:
  ${_config.APP_NAME} update                Update pi and all extensions
  ${_config.APP_NAME} update <source>       Update one package
  ${_config.APP_NAME} update pi             Update pi only (self works as alias to pi)
`);
      return;
    case "list":
      console.log(`${_chalk.default.bold("Usage:")}
  ${getPackageCommandUsage("list")}

List installed packages from user and project settings.
`);
      return;
  }
}
function parsePackageCommand(args) {
  const [rawCommand, ...rest] = args;
  let command;
  if (rawCommand === "uninstall") {
    command = "remove";
  } else
  if (rawCommand === "install" || rawCommand === "remove" || rawCommand === "update" || rawCommand === "list") {
    command = rawCommand;
  }
  if (!command) {
    return undefined;
  }
  let local = false;
  let force = false;
  let help = false;
  let invalidOption;
  let invalidArgument;
  let missingOptionValue;
  let conflictingOptions;
  let source;
  let selfFlag = false;
  let extensionsFlag = false;
  let extensionFlagSource;
  for (let index = 0; index < rest.length; index++) {
    const arg = rest[index];
    if (arg === "-h" || arg === "--help") {
      help = true;
      continue;
    }
    if (arg === "-l" || arg === "--local") {
      if (command === "install" || command === "remove") {
        local = true;
      } else
      {
        invalidOption = invalidOption ?? arg;
      }
      continue;
    }
    if (arg === "--self") {
      if (command === "update") {
        selfFlag = true;
      } else
      {
        invalidOption = invalidOption ?? arg;
      }
      continue;
    }
    if (arg === "--extensions") {
      if (command === "update") {
        extensionsFlag = true;
      } else
      {
        invalidOption = invalidOption ?? arg;
      }
      continue;
    }
    if (arg === "--force") {
      if (command === "update") {
        force = true;
      } else
      {
        invalidOption = invalidOption ?? arg;
      }
      continue;
    }
    if (arg === "--extension") {
      if (command !== "update") {
        invalidOption = invalidOption ?? arg;
        continue;
      }
      const value = rest[index + 1];
      if (!value || value.startsWith("-")) {
        missingOptionValue = missingOptionValue ?? arg;
      } else
      if (extensionFlagSource) {
        conflictingOptions = conflictingOptions ?? "--extension can only be provided once";
        index++;
      } else
      {
        extensionFlagSource = value;
        index++;
      }
      continue;
    }
    if (arg.startsWith("-")) {
      invalidOption = invalidOption ?? arg;
      continue;
    }
    if (!source) {
      source = arg;
    } else
    {
      invalidArgument = invalidArgument ?? arg;
    }
  }
  let updateTarget;
  if (command === "update") {
    if (extensionFlagSource) {
      if (selfFlag || extensionsFlag) {
        conflictingOptions = conflictingOptions ?? "--extension cannot be combined with --self or --extensions";
      }
      if (source) {
        conflictingOptions = conflictingOptions ?? "--extension cannot be combined with a positional source";
      }
      updateTarget = { type: "extensions", source: extensionFlagSource };
    } else
    if (source) {
      const sourceIsSelf = source === "self" || source === "pi";
      if (sourceIsSelf) {
        updateTarget = extensionsFlag ? { type: "all" } : { type: "self" };
      } else
      {
        if (extensionsFlag || selfFlag) {
          conflictingOptions =
          conflictingOptions ?? "positional update targets cannot be combined with --self or --extensions";
        }
        updateTarget = { type: "extensions", source };
      }
    } else
    if (selfFlag && extensionsFlag) {
      updateTarget = { type: "all" };
    } else
    if (selfFlag) {
      updateTarget = { type: "self" };
    } else
    if (extensionsFlag) {
      updateTarget = { type: "extensions" };
    } else
    {
      updateTarget = { type: "all" };
    }
  }
  return {
    command,
    source,
    updateTarget,
    local,
    force,
    help,
    invalidOption,
    invalidArgument,
    missingOptionValue,
    conflictingOptions
  };
}
function updateTargetIncludesSelf(target) {
  return target.type === "all" || target.type === "self";
}
function updateTargetIncludesExtensions(target) {
  return target.type === "all" || target.type === "extensions";
}
function printSelfUpdateUnavailable(npmCommand) {
  console.error(`error: ${_config.APP_NAME} cannot self-update this installation.`);
  console.error((0, _config.getSelfUpdateUnavailableInstruction)(_config.PACKAGE_NAME, npmCommand));
  const entrypoint = process.argv[1];
  if (entrypoint) {
    console.error("");
    console.error(`Location of pi executable: ${entrypoint}`);
  }
}
function printSelfUpdateFallback(command) {
  console.error(_chalk.default.dim(`If this keeps failing, run this command yourself: ${command.display}`));
}
async function shouldRunSelfUpdate(force) {
  if (force) {
    return true;
  }
  let latestVersion;
  try {
    latestVersion = await (0, _versionCheck.getLatestPiVersion)(_config.VERSION);
  }
  catch {
    return true;
  }
  if (!latestVersion || (0, _versionCheck.isNewerPackageVersion)(latestVersion, _config.VERSION)) {
    return true;
  }
  console.log(_chalk.default.green(`${_config.APP_NAME} is already up to date (v${_config.VERSION})`));
  return false;
}
async function runSelfUpdate(command) {
  console.log(_chalk.default.dim(`Updating ${_config.APP_NAME} with ${command.display}...`));
  await new Promise((resolve, reject) => {
    // Windows package managers are commonly .cmd shims. Use the shell so Node can execute them.
    const child = (0, _child_process.spawn)(command.command, command.args, {
      stdio: "inherit",
      shell: (0, _childProcess.shouldUseWindowsShell)(command.command)
    });
    child.on("error", (error) => {
      reject(error);
    });
    child.on("close", (code, signal) => {
      if (code === 0) {
        resolve();
      } else
      if (signal) {
        reject(new Error(`${command.display} terminated by signal ${signal}`));
      } else
      {
        reject(new Error(`${command.display} exited with code ${code ?? "unknown"}`));
      }
    });
  });
}
async function handleConfigCommand(args) {
  if (args[0] !== "config") {
    return false;
  }
  const cwd = process.cwd();
  const agentDir = (0, _config.getAgentDir)();
  const settingsManager = _settingsManager.SettingsManager.create(cwd, agentDir);
  reportSettingsErrors(settingsManager, "config command");
  const packageManager = new _packageManager.DefaultPackageManager({ cwd, agentDir, settingsManager });
  const resolvedPaths = await packageManager.resolve();
  await (0, _configSelector.selectConfig)({
    resolvedPaths,
    settingsManager,
    cwd,
    agentDir
  });
  process.exit(0);
}
async function handlePackageCommand(args) {
  const options = parsePackageCommand(args);
  if (!options) {
    return false;
  }
  if (options.help) {
    printPackageCommandHelp(options.command);
    return true;
  }
  if (options.invalidOption) {
    console.error(_chalk.default.red(`Unknown option ${options.invalidOption} for "${options.command}".`));
    console.error(_chalk.default.dim(`Use "${_config.APP_NAME} --help" or "${getPackageCommandUsage(options.command)}".`));
    process.exitCode = 1;
    return true;
  }
  if (options.missingOptionValue) {
    console.error(_chalk.default.red(`Missing value for ${options.missingOptionValue}.`));
    console.error(_chalk.default.dim(`Usage: ${getPackageCommandUsage(options.command)}`));
    process.exitCode = 1;
    return true;
  }
  if (options.invalidArgument) {
    console.error(_chalk.default.red(`Unexpected argument ${options.invalidArgument}.`));
    console.error(_chalk.default.dim(`Usage: ${getPackageCommandUsage(options.command)}`));
    process.exitCode = 1;
    return true;
  }
  if (options.conflictingOptions) {
    console.error(_chalk.default.red(options.conflictingOptions));
    console.error(_chalk.default.dim(`Usage: ${getPackageCommandUsage(options.command)}`));
    process.exitCode = 1;
    return true;
  }
  const source = options.source;
  if ((options.command === "install" || options.command === "remove") && !source) {
    console.error(_chalk.default.red(`Missing ${options.command} source.`));
    console.error(_chalk.default.dim(`Usage: ${getPackageCommandUsage(options.command)}`));
    process.exitCode = 1;
    return true;
  }
  const cwd = process.cwd();
  const agentDir = (0, _config.getAgentDir)();
  const settingsManager = _settingsManager.SettingsManager.create(cwd, agentDir);
  reportSettingsErrors(settingsManager, "package command");
  const selfUpdateNpmCommand = settingsManager.getGlobalSettings().npmCommand;
  const packageManager = new _packageManager.DefaultPackageManager({ cwd, agentDir, settingsManager });
  packageManager.setProgressCallback((event) => {
    if (event.type === "start") {
      process.stdout.write(_chalk.default.dim(`${event.message}\n`));
    }
  });
  try {
    switch (options.command) {
      case "install":
        await packageManager.installAndPersist(source, { local: options.local });
        console.log(_chalk.default.green(`Installed ${source}`));
        return true;
      case "remove":{
          const removed = await packageManager.removeAndPersist(source, { local: options.local });
          if (!removed) {
            console.error(_chalk.default.red(`No matching package found for ${source}`));
            process.exitCode = 1;
            return true;
          }
          console.log(_chalk.default.green(`Removed ${source}`));
          return true;
        }
      case "list":{
          const configuredPackages = packageManager.listConfiguredPackages();
          const userPackages = configuredPackages.filter((pkg) => pkg.scope === "user");
          const projectPackages = configuredPackages.filter((pkg) => pkg.scope === "project");
          if (configuredPackages.length === 0) {
            console.log(_chalk.default.dim("No packages installed."));
            return true;
          }
          const formatPackage = (pkg) => {
            const display = pkg.filtered ? `${pkg.source} (filtered)` : pkg.source;
            console.log(`  ${display}`);
            if (pkg.installedPath) {
              console.log(_chalk.default.dim(`    ${pkg.installedPath}`));
            }
          };
          if (userPackages.length > 0) {
            console.log(_chalk.default.bold("User packages:"));
            for (const pkg of userPackages) {
              formatPackage(pkg);
            }
          }
          if (projectPackages.length > 0) {
            if (userPackages.length > 0)
            console.log();
            console.log(_chalk.default.bold("Project packages:"));
            for (const pkg of projectPackages) {
              formatPackage(pkg);
            }
          }
          return true;
        }
      case "update":{
          const target = options.updateTarget ?? { type: "all" };
          if (updateTargetIncludesExtensions(target)) {
            const updateSource = target.type === "extensions" ? target.source : undefined;
            await packageManager.update(updateSource);
            if (updateSource) {
              console.log(_chalk.default.green(`Updated ${updateSource}`));
            } else
            {
              console.log(_chalk.default.green("Updated packages"));
            }
          }
          if (updateTargetIncludesSelf(target)) {
            const selfUpdateCommand = (0, _config.getSelfUpdateCommand)(_config.PACKAGE_NAME, selfUpdateNpmCommand);
            if (!selfUpdateCommand) {
              printSelfUpdateUnavailable(selfUpdateNpmCommand);
              process.exitCode = 1;
              return true;
            }
            if (!(await shouldRunSelfUpdate(options.force))) {
              return true;
            }
            try {
              await runSelfUpdate(selfUpdateCommand);
            }
            catch (error) {
              const message = error instanceof Error ? error.message : "Unknown package command error";
              console.error(_chalk.default.red(`Error: ${message}`));
              printSelfUpdateFallback(selfUpdateCommand);
              process.exitCode = 1;
              return true;
            }
            console.log(_chalk.default.green(`Updated ${_config.APP_NAME}`));
          }
          return true;
        }
    }
  }
  catch (error) {
    const message = error instanceof Error ? error.message : "Unknown package command error";
    console.error(_chalk.default.red(`Error: ${message}`));
    process.exitCode = 1;
    return true;
  }
} /* v9-a1681f66f3371269 */
