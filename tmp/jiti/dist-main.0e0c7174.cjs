"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.main = main;





var _nodePath = require("node:path");
var _nodeReadline = require("node:readline");
var _piAi = require("@mariozechner/pi-ai");
var _piTui = require("@mariozechner/pi-tui");
var _chalk = _interopRequireDefault(require("chalk"));
var _args = require("./cli/args.js");
var _fileProcessor = require("./cli/file-processor.js");
var _initialMessage = require("./cli/initial-message.js");
var _listModels = require("./cli/list-models.js");
var _sessionPicker = require("./cli/session-picker.js");
var _config = require("./config.js");
var _agentSessionRuntime = require("./core/agent-session-runtime.js");
var _agentSessionServices = require("./core/agent-session-services.js");
var _authGuidance = require("./core/auth-guidance.js");
var _authStorage = require("./core/auth-storage.js");
var _index = require("./core/export-html/index.js");
var _keybindings = require("./core/keybindings.js");
var _modelResolver = require("./core/model-resolver.js");
var _outputGuard = require("./core/output-guard.js");
var _sessionCwd = require("./core/session-cwd.js");
var _sessionManager = require("./core/session-manager.js");
var _settingsManager = require("./core/settings-manager.js");
var _timings = require("./core/timings.js");
var _migrations = require("./migrations.js");
var _index2 = require("./modes/index.js");
var _extensionSelector = require("./modes/interactive/components/extension-selector.js");
var _theme = require("./modes/interactive/theme/theme.js");
var _packageManagerCli = require("./package-manager-cli.js");
var _paths = require("./utils/paths.js");function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };} /**
 * Main entry point for the coding agent CLI.
 *
 * This file handles CLI argument parsing and translates them into
 * createAgentSession() options. The SDK does the heavy lifting.
 */ /**
 * Read all content from piped stdin.
 * Returns undefined if stdin is a TTY (interactive terminal).
 */async function readPipedStdin() {// If stdin is a TTY, we're running interactively - don't read stdin
  if (process.stdin.isTTY) {return undefined;}
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", () => {
      resolve(data.trim() || undefined);
    });
    process.stdin.resume();
  });
}
function collectSettingsDiagnostics(settingsManager, context) {
  return settingsManager.drainErrors().map(({ scope, error }) => ({
    type: "warning",
    message: `(${context}, ${scope} settings) ${error.message}`
  }));
}
function reportDiagnostics(diagnostics) {
  for (const diagnostic of diagnostics) {
    const color = diagnostic.type === "error" ? _chalk.default.red : diagnostic.type === "warning" ? _chalk.default.yellow : _chalk.default.dim;
    const prefix = diagnostic.type === "error" ? "Error: " : diagnostic.type === "warning" ? "Warning: " : "";
    console.error(color(`${prefix}${diagnostic.message}`));
  }
}
function isTruthyEnvFlag(value) {
  if (!value)
  return false;
  return value === "1" || value.toLowerCase() === "true" || value.toLowerCase() === "yes";
}
function resolveAppMode(parsed, stdinIsTTY) {
  if (parsed.mode === "rpc") {
    return "rpc";
  }
  if (parsed.mode === "json") {
    return "json";
  }
  if (parsed.print || !stdinIsTTY) {
    return "print";
  }
  return "interactive";
}
function toPrintOutputMode(appMode) {
  return appMode === "json" ? "json" : "text";
}
async function prepareInitialMessage(parsed, autoResizeImages, stdinContent) {
  if (parsed.fileArgs.length === 0) {
    return (0, _initialMessage.buildInitialMessage)({ parsed, stdinContent });
  }
  const { text, images } = await (0, _fileProcessor.processFileArguments)(parsed.fileArgs, { autoResizeImages });
  return (0, _initialMessage.buildInitialMessage)({
    parsed,
    fileText: text,
    fileImages: images,
    stdinContent
  });
}
/**
 * Resolve a session argument to a file path.
 * If it looks like a path, use as-is. Otherwise try to match as session ID prefix.
 */
async function resolveSessionPath(sessionArg, cwd, sessionDir) {
  // If it looks like a file path, use as-is
  if (sessionArg.includes("/") || sessionArg.includes("\\") || sessionArg.endsWith(".jsonl")) {
    return { type: "path", path: sessionArg };
  }
  // Try to match as session ID in current project first
  const localSessions = await _sessionManager.SessionManager.list(cwd, sessionDir);
  const localMatches = localSessions.filter((s) => s.id.startsWith(sessionArg));
  if (localMatches.length >= 1) {
    return { type: "local", path: localMatches[0].path };
  }
  // Try global search across all projects
  const allSessions = await _sessionManager.SessionManager.listAll();
  const globalMatches = allSessions.filter((s) => s.id.startsWith(sessionArg));
  if (globalMatches.length >= 1) {
    const match = globalMatches[0];
    return { type: "global", path: match.path, cwd: match.cwd };
  }
  // Not found anywhere
  return { type: "not_found", arg: sessionArg };
}
/** Prompt user for yes/no confirmation */
async function promptConfirm(message) {
  return new Promise((resolve) => {
    const rl = (0, _nodeReadline.createInterface)({
      input: process.stdin,
      output: process.stdout
    });
    rl.question(`${message} [y/N] `, (answer) => {
      rl.close();
      resolve(answer.toLowerCase() === "y" || answer.toLowerCase() === "yes");
    });
  });
}
function validateForkFlags(parsed) {
  if (!parsed.fork)
  return;
  const conflictingFlags = [
  parsed.session ? "--session" : undefined,
  parsed.continue ? "--continue" : undefined,
  parsed.resume ? "--resume" : undefined,
  parsed.noSession ? "--no-session" : undefined].
  filter((flag) => flag !== undefined);
  if (conflictingFlags.length > 0) {
    console.error(_chalk.default.red(`Error: --fork cannot be combined with ${conflictingFlags.join(", ")}`));
    process.exit(1);
  }
}
function forkSessionOrExit(sourcePath, cwd, sessionDir) {
  try {
    return _sessionManager.SessionManager.forkFrom(sourcePath, cwd, sessionDir);
  }
  catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(_chalk.default.red(`Error: ${message}`));
    process.exit(1);
  }
}
async function createSessionManager(parsed, cwd, sessionDir, settingsManager) {
  if (parsed.noSession) {
    return _sessionManager.SessionManager.inMemory();
  }
  if (parsed.fork) {
    const resolved = await resolveSessionPath(parsed.fork, cwd, sessionDir);
    switch (resolved.type) {
      case "path":
      case "local":
      case "global":
        return forkSessionOrExit(resolved.path, cwd, sessionDir);
      case "not_found":
        console.error(_chalk.default.red(`No session found matching '${resolved.arg}'`));
        process.exit(1);
    }
  }
  if (parsed.session) {
    const resolved = await resolveSessionPath(parsed.session, cwd, sessionDir);
    switch (resolved.type) {
      case "path":
      case "local":
        return _sessionManager.SessionManager.open(resolved.path, sessionDir);
      case "global":{
          console.log(_chalk.default.yellow(`Session found in different project: ${resolved.cwd}`));
          const shouldFork = await promptConfirm("Fork this session into current directory?");
          if (!shouldFork) {
            console.log(_chalk.default.dim("Aborted."));
            process.exit(0);
          }
          return forkSessionOrExit(resolved.path, cwd, sessionDir);
        }
      case "not_found":
        console.error(_chalk.default.red(`No session found matching '${resolved.arg}'`));
        process.exit(1);
    }
  }
  if (parsed.resume) {
    (0, _theme.initTheme)(settingsManager.getTheme(), true);
    try {
      const selectedPath = await (0, _sessionPicker.selectSession)((onProgress) => _sessionManager.SessionManager.list(cwd, sessionDir, onProgress), _sessionManager.SessionManager.listAll);
      if (!selectedPath) {
        console.log(_chalk.default.dim("No session selected"));
        process.exit(0);
      }
      return _sessionManager.SessionManager.open(selectedPath, sessionDir);
    } finally
    {
      (0, _theme.stopThemeWatcher)();
    }
  }
  if (parsed.continue) {
    return _sessionManager.SessionManager.continueRecent(cwd, sessionDir);
  }
  return _sessionManager.SessionManager.create(cwd, sessionDir);
}
function buildSessionOptions(parsed, scopedModels, hasExistingSession, modelRegistry, settingsManager) {
  const options = {};
  const diagnostics = [];
  let cliThinkingFromModel = false;
  // Model from CLI
  // - supports --provider <name> --model <pattern>
  // - supports --model <provider>/<pattern>
  if (parsed.model) {
    const resolved = (0, _modelResolver.resolveCliModel)({
      cliProvider: parsed.provider,
      cliModel: parsed.model,
      modelRegistry
    });
    if (resolved.warning) {
      diagnostics.push({ type: "warning", message: resolved.warning });
    }
    if (resolved.error) {
      diagnostics.push({ type: "error", message: resolved.error });
    }
    if (resolved.model) {
      options.model = resolved.model;
      // Allow "--model <pattern>:<thinking>" as a shorthand.
      // Explicit --thinking still takes precedence (applied later).
      if (!parsed.thinking && resolved.thinkingLevel) {
        options.thinkingLevel = resolved.thinkingLevel;
        cliThinkingFromModel = true;
      }
    }
  }
  if (!options.model && scopedModels.length > 0 && !hasExistingSession) {
    // Check if saved default is in scoped models - use it if so, otherwise first scoped model
    const savedProvider = settingsManager.getDefaultProvider();
    const savedModelId = settingsManager.getDefaultModel();
    const savedModel = savedProvider && savedModelId ? modelRegistry.find(savedProvider, savedModelId) : undefined;
    const savedInScope = savedModel ? scopedModels.find((sm) => (0, _piAi.modelsAreEqual)(sm.model, savedModel)) : undefined;
    if (savedInScope) {
      options.model = savedInScope.model;
      // Use thinking level from scoped model config if explicitly set
      if (!parsed.thinking && savedInScope.thinkingLevel) {
        options.thinkingLevel = savedInScope.thinkingLevel;
      }
    } else
    {
      options.model = scopedModels[0].model;
      // Use thinking level from first scoped model if explicitly set
      if (!parsed.thinking && scopedModels[0].thinkingLevel) {
        options.thinkingLevel = scopedModels[0].thinkingLevel;
      }
    }
  }
  // Thinking level from CLI (takes precedence over scoped model thinking levels set above)
  if (parsed.thinking) {
    options.thinkingLevel = parsed.thinking;
  }
  // Scoped models for Ctrl+P cycling
  // Keep thinking level undefined when not explicitly set in the model pattern.
  // Undefined means "inherit current session thinking level" during cycling.
  if (scopedModels.length > 0) {
    options.scopedModels = scopedModels.map((sm) => ({
      model: sm.model,
      thinkingLevel: sm.thinkingLevel
    }));
  }
  // API key from CLI - set in authStorage
  // (handled by caller before createAgentSession)
  // Tools
  if (parsed.noTools) {
    options.noTools = "all";
  } else
  if (parsed.noBuiltinTools) {
    options.noTools = "builtin";
  }
  if (parsed.tools) {
    options.tools = [...parsed.tools];
  }
  return { options, cliThinkingFromModel, diagnostics };
}
function resolveCliPaths(cwd, paths) {
  return paths?.map((value) => (0, _paths.isLocalPath)(value) ? (0, _nodePath.resolve)(cwd, value) : value);
}
async function promptForMissingSessionCwd(issue, settingsManager) {
  (0, _theme.initTheme)(settingsManager.getTheme());
  (0, _piTui.setKeybindings)(_keybindings.KeybindingsManager.create());
  return new Promise((resolve) => {
    const ui = new _piTui.TUI(new _piTui.ProcessTerminal(), settingsManager.getShowHardwareCursor());
    ui.setClearOnShrink(settingsManager.getClearOnShrink());
    let settled = false;
    const finish = (result) => {
      if (settled) {
        return;
      }
      settled = true;
      ui.stop();
      resolve(result);
    };
    const selector = new _extensionSelector.ExtensionSelectorComponent((0, _sessionCwd.formatMissingSessionCwdPrompt)(issue), ["Continue", "Cancel"], (option) => finish(option === "Continue" ? issue.fallbackCwd : undefined), () => finish(undefined), { tui: ui });
    ui.addChild(selector);
    ui.setFocus(selector);
    ui.start();
  });
}
async function main(args, options) {
  (0, _timings.resetTimings)();
  const offlineMode = args.includes("--offline") || isTruthyEnvFlag(process.env.PI_OFFLINE);
  if (offlineMode) {
    process.env.PI_OFFLINE = "1";
    process.env.PI_SKIP_VERSION_CHECK = "1";
  }
  if (await (0, _packageManagerCli.handlePackageCommand)(args)) {
    return;
  }
  if (await (0, _packageManagerCli.handleConfigCommand)(args)) {
    return;
  }
  const parsed = (0, _args.parseArgs)(args);
  if (parsed.diagnostics.length > 0) {
    for (const d of parsed.diagnostics) {
      const color = d.type === "error" ? _chalk.default.red : _chalk.default.yellow;
      console.error(color(`${d.type === "error" ? "Error" : "Warning"}: ${d.message}`));
    }
    if (parsed.diagnostics.some((d) => d.type === "error")) {
      process.exit(1);
    }
  }
  (0, _timings.time)("parseArgs");
  let appMode = resolveAppMode(parsed, process.stdin.isTTY);
  const shouldTakeOverStdout = appMode !== "interactive";
  if (shouldTakeOverStdout) {
    (0, _outputGuard.takeOverStdout)();
  }
  if (parsed.version) {
    console.log(_config.VERSION);
    process.exit(0);
  }
  if (parsed.export) {
    let result;
    try {
      const outputPath = parsed.messages.length > 0 ? parsed.messages[0] : undefined;
      result = await (0, _index.exportFromFile)(parsed.export, outputPath);
    }
    catch (error) {
      const message = error instanceof Error ? error.message : "Failed to export session";
      console.error(_chalk.default.red(`Error: ${message}`));
      process.exit(1);
    }
    console.log(`Exported to: ${result}`);
    process.exit(0);
  }
  if (parsed.mode === "rpc" && parsed.fileArgs.length > 0) {
    console.error(_chalk.default.red("Error: @file arguments are not supported in RPC mode"));
    process.exit(1);
  }
  validateForkFlags(parsed);
  // Run migrations (pass cwd for project-local migrations)
  const { migratedAuthProviders: migratedProviders, deprecationWarnings } = (0, _migrations.runMigrations)(process.cwd());
  (0, _timings.time)("runMigrations");
  const cwd = process.cwd();
  const agentDir = (0, _config.getAgentDir)();
  const startupSettingsManager = _settingsManager.SettingsManager.create(cwd, agentDir);
  reportDiagnostics(collectSettingsDiagnostics(startupSettingsManager, "startup session lookup"));
  // Decide the final runtime cwd before creating cwd-bound runtime services.
  // --session and --resume may select a session from another project, so project-local
  // settings, resources, provider registrations, and models must be resolved only after
  // the target session cwd is known. The startup-cwd settings manager is used only for
  // sessionDir lookup during session selection.
  const envSessionDir = process.env[_config.ENV_SESSION_DIR];
  const sessionDir = parsed.sessionDir ?? (
  envSessionDir ? (0, _config.expandTildePath)(envSessionDir) : undefined) ??
  startupSettingsManager.getSessionDir();
  let sessionManager = await createSessionManager(parsed, cwd, sessionDir, startupSettingsManager);
  const missingSessionCwdIssue = (0, _sessionCwd.getMissingSessionCwdIssue)(sessionManager, cwd);
  if (missingSessionCwdIssue) {
    if (appMode === "interactive") {
      const selectedCwd = await promptForMissingSessionCwd(missingSessionCwdIssue, startupSettingsManager);
      if (!selectedCwd) {
        process.exit(0);
      }
      sessionManager = _sessionManager.SessionManager.open(missingSessionCwdIssue.sessionFile, sessionDir, selectedCwd);
    } else
    {
      console.error(_chalk.default.red(new _sessionCwd.MissingSessionCwdError(missingSessionCwdIssue).message));
      process.exit(1);
    }
  }
  (0, _timings.time)("createSessionManager");
  const resolvedExtensionPaths = resolveCliPaths(cwd, parsed.extensions);
  const resolvedSkillPaths = resolveCliPaths(cwd, parsed.skills);
  const resolvedPromptTemplatePaths = resolveCliPaths(cwd, parsed.promptTemplates);
  const resolvedThemePaths = resolveCliPaths(cwd, parsed.themes);
  const authStorage = _authStorage.AuthStorage.create();
  const createRuntime = async ({ cwd, agentDir, sessionManager, sessionStartEvent }) => {
    const services = await (0, _agentSessionServices.createAgentSessionServices)({
      cwd,
      agentDir,
      authStorage,
      extensionFlagValues: parsed.unknownFlags,
      resourceLoaderOptions: {
        additionalExtensionPaths: resolvedExtensionPaths,
        additionalSkillPaths: resolvedSkillPaths,
        additionalPromptTemplatePaths: resolvedPromptTemplatePaths,
        additionalThemePaths: resolvedThemePaths,
        noExtensions: parsed.noExtensions,
        noSkills: parsed.noSkills,
        noPromptTemplates: parsed.noPromptTemplates,
        noThemes: parsed.noThemes,
        noContextFiles: parsed.noContextFiles,
        systemPrompt: parsed.systemPrompt,
        appendSystemPrompt: parsed.appendSystemPrompt,
        extensionFactories: options?.extensionFactories
      }
    });
    const { settingsManager, modelRegistry, resourceLoader } = services;
    const diagnostics = [
    ...services.diagnostics,
    ...collectSettingsDiagnostics(settingsManager, "runtime creation"),
    ...resourceLoader.getExtensions().errors.map(({ path, error }) => ({
      type: "error",
      message: `Failed to load extension "${path}": ${error}`
    }))];

    const modelPatterns = parsed.models ?? settingsManager.getEnabledModels();
    const scopedModels = modelPatterns && modelPatterns.length > 0 ? await (0, _modelResolver.resolveModelScope)(modelPatterns, modelRegistry) : [];
    const { options: sessionOptions, cliThinkingFromModel, diagnostics: sessionOptionDiagnostics } = buildSessionOptions(parsed, scopedModels, sessionManager.buildSessionContext().messages.length > 0, modelRegistry, settingsManager);
    diagnostics.push(...sessionOptionDiagnostics);
    if (parsed.apiKey) {
      if (!sessionOptions.model) {
        diagnostics.push({
          type: "error",
          message: "--api-key requires a model to be specified via --model, --provider/--model, or --models"
        });
      } else
      {
        authStorage.setRuntimeApiKey(sessionOptions.model.provider, parsed.apiKey);
      }
    }
    const created = await (0, _agentSessionServices.createAgentSessionFromServices)({
      services,
      sessionManager,
      sessionStartEvent,
      model: sessionOptions.model,
      thinkingLevel: sessionOptions.thinkingLevel,
      scopedModels: sessionOptions.scopedModels,
      tools: sessionOptions.tools,
      noTools: sessionOptions.noTools,
      customTools: sessionOptions.customTools
    });
    const cliThinkingOverride = parsed.thinking !== undefined || cliThinkingFromModel;
    if (created.session.model && cliThinkingOverride) {
      created.session.setThinkingLevel(created.session.thinkingLevel);
    }
    return {
      ...created,
      services,
      diagnostics
    };
  };
  (0, _timings.time)("createRuntime");
  const runtime = await (0, _agentSessionRuntime.createAgentSessionRuntime)(createRuntime, {
    cwd: sessionManager.getCwd(),
    agentDir,
    sessionManager
  });
  const { services, session, modelFallbackMessage } = runtime;
  const { settingsManager, modelRegistry, resourceLoader } = services;
  if (parsed.help) {
    const extensionFlags = resourceLoader.
    getExtensions().
    extensions.flatMap((extension) => Array.from(extension.flags.values()));
    (0, _args.printHelp)(extensionFlags);
    process.exit(0);
  }
  if (parsed.listModels !== undefined) {
    const searchPattern = typeof parsed.listModels === "string" ? parsed.listModels : undefined;
    await (0, _listModels.listModels)(modelRegistry, searchPattern);
    process.exit(0);
  }
  // Read piped stdin content (if any) - skip for RPC mode which uses stdin for JSON-RPC
  let stdinContent;
  if (appMode !== "rpc") {
    stdinContent = await readPipedStdin();
    if (stdinContent !== undefined && appMode === "interactive") {
      appMode = "print";
    }
  }
  (0, _timings.time)("readPipedStdin");
  const { initialMessage, initialImages } = await prepareInitialMessage(parsed, settingsManager.getImageAutoResize(), stdinContent);
  (0, _timings.time)("prepareInitialMessage");
  (0, _theme.initTheme)(settingsManager.getTheme(), appMode === "interactive");
  (0, _timings.time)("initTheme");
  // Show deprecation warnings in interactive mode
  if (appMode === "interactive" && deprecationWarnings.length > 0) {
    await (0, _migrations.showDeprecationWarnings)(deprecationWarnings);
  }
  const scopedModels = [...session.scopedModels];
  (0, _timings.time)("resolveModelScope");
  reportDiagnostics(runtime.diagnostics);
  if (runtime.diagnostics.some((diagnostic) => diagnostic.type === "error")) {
    process.exit(1);
  }
  (0, _timings.time)("createAgentSession");
  if (appMode !== "interactive" && !session.model) {
    console.error(_chalk.default.red((0, _authGuidance.formatNoModelsAvailableMessage)()));
    process.exit(1);
  }
  const startupBenchmark = isTruthyEnvFlag(process.env.PI_STARTUP_BENCHMARK);
  if (startupBenchmark && appMode !== "interactive") {
    console.error(_chalk.default.red("Error: PI_STARTUP_BENCHMARK only supports interactive mode"));
    process.exit(1);
  }
  if (appMode === "rpc") {
    (0, _timings.printTimings)();
    await (0, _index2.runRpcMode)(runtime);
  } else
  if (appMode === "interactive") {
    if (scopedModels.length > 0 && (parsed.verbose || !settingsManager.getQuietStartup())) {
      const modelList = scopedModels.
      map((sm) => {
        const thinkingStr = sm.thinkingLevel ? `:${sm.thinkingLevel}` : "";
        return `${sm.model.id}${thinkingStr}`;
      }).
      join(", ");
      console.log(_chalk.default.dim(`Model scope: ${modelList} ${_chalk.default.gray("(Ctrl+P to cycle)")}`));
    }
    const interactiveMode = new _index2.InteractiveMode(runtime, {
      migratedProviders,
      modelFallbackMessage,
      initialMessage,
      initialImages,
      initialMessages: parsed.messages,
      verbose: parsed.verbose
    });
    if (startupBenchmark) {
      await interactiveMode.init();
      (0, _timings.time)("interactiveMode.init");
      (0, _timings.printTimings)();
      interactiveMode.stop();
      (0, _theme.stopThemeWatcher)();
      if (process.stdout.writableLength > 0) {
        await new Promise((resolve) => process.stdout.once("drain", resolve));
      }
      if (process.stderr.writableLength > 0) {
        await new Promise((resolve) => process.stderr.once("drain", resolve));
      }
      return;
    }
    (0, _timings.printTimings)();
    await interactiveMode.run();
  } else
  {
    (0, _timings.printTimings)();
    const exitCode = await (0, _index2.runPrintMode)(runtime, {
      mode: toPrintOutputMode(appMode),
      messages: parsed.messages,
      initialMessage,
      initialImages
    });
    (0, _theme.stopThemeWatcher)();
    (0, _outputGuard.restoreStdout)();
    if (exitCode !== 0) {
      process.exitCode = exitCode;
    }
    return;
  }
} /* v9-0edf02ac3d5823d7 */
