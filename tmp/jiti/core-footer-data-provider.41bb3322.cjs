"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FooterDataProvider = void 0;var _child_process = require("child_process");
var _fs = require("fs");
var _path = require("path");
var _fsWatch = require("../utils/fs-watch.js");
/**
 * Find git metadata paths by walking up from cwd.
 * Handles both regular git repos (.git is a directory) and worktrees (.git is a file).
 */
function findGitPaths(cwd) {
  let dir = cwd;
  while (true) {
    const gitPath = (0, _path.join)(dir, ".git");
    if ((0, _fs.existsSync)(gitPath)) {
      try {
        const stat = (0, _fs.statSync)(gitPath);
        if (stat.isFile()) {
          const content = (0, _fs.readFileSync)(gitPath, "utf8").trim();
          if (content.startsWith("gitdir: ")) {
            const gitDir = (0, _path.resolve)(dir, content.slice(8).trim());
            const headPath = (0, _path.join)(gitDir, "HEAD");
            if (!(0, _fs.existsSync)(headPath))
            return null;
            const commonDirPath = (0, _path.join)(gitDir, "commondir");
            const commonGitDir = (0, _fs.existsSync)(commonDirPath) ?
            (0, _path.resolve)(gitDir, (0, _fs.readFileSync)(commonDirPath, "utf8").trim()) :
            gitDir;
            return { repoDir: dir, commonGitDir, headPath };
          }
        } else
        if (stat.isDirectory()) {
          const headPath = (0, _path.join)(gitPath, "HEAD");
          if (!(0, _fs.existsSync)(headPath))
          return null;
          return { repoDir: dir, commonGitDir: gitPath, headPath };
        }
      }
      catch {
        return null;
      }
    }
    const parent = (0, _path.dirname)(dir);
    if (parent === dir)
    return null;
    dir = parent;
  }
}
/** Ask git for the current branch. Returns null on detached HEAD or if git is unavailable. */
function resolveBranchWithGitSync(repoDir) {
  const result = (0, _child_process.spawnSync)("git", ["--no-optional-locks", "symbolic-ref", "--quiet", "--short", "HEAD"], {
    cwd: repoDir,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "ignore"]
  });
  const branch = result.status === 0 ? result.stdout.trim() : "";
  return branch || null;
}
/** Ask git for the current branch asynchronously. Returns null on detached HEAD or if git is unavailable. */
function resolveBranchWithGitAsync(repoDir) {
  return new Promise((resolvePromise) => {
    (0, _child_process.execFile)("git", ["--no-optional-locks", "symbolic-ref", "--quiet", "--short", "HEAD"], {
      cwd: repoDir,
      encoding: "utf8"
    }, (error, stdout) => {
      if (error) {
        resolvePromise(null);
        return;
      }
      const branch = stdout.trim();
      resolvePromise(branch || null);
    });
  });
}
/**
 * Provides git branch and extension statuses - data not otherwise accessible to extensions.
 * Token stats, model info available via ctx.sessionManager and ctx.model.
 */
class FooterDataProvider {
  cwd;
  static WATCH_DEBOUNCE_MS = 500;
  extensionStatuses = new Map();
  cachedBranch = undefined;
  gitPaths = undefined;
  headWatcher = null;
  reftableWatcher = null;
  reftableTablesListWatcher = null;
  reftableTablesListPath = null;
  branchChangeCallbacks = new Set();
  availableProviderCount = 0;
  refreshTimer = null;
  gitWatcherRetryTimer = null;
  refreshInFlight = false;
  refreshPending = false;
  disposed = false;
  constructor(cwd) {
    this.cwd = cwd;
    this.gitPaths = findGitPaths(cwd);
    this.setupGitWatcher();
  }
  /** Current git branch, null if not in repo, "detached" if detached HEAD */
  getGitBranch() {
    if (this.cachedBranch === undefined) {
      this.cachedBranch = this.resolveGitBranchSync();
    }
    return this.cachedBranch;
  }
  /** Extension status texts set via ctx.ui.setStatus() */
  getExtensionStatuses() {
    return this.extensionStatuses;
  }
  /** Subscribe to git branch changes. Returns unsubscribe function. */
  onBranchChange(callback) {
    this.branchChangeCallbacks.add(callback);
    return () => this.branchChangeCallbacks.delete(callback);
  }
  /** Internal: set extension status */
  setExtensionStatus(key, text) {
    if (text === undefined) {
      this.extensionStatuses.delete(key);
    } else
    {
      this.extensionStatuses.set(key, text);
    }
  }
  /** Internal: clear extension statuses */
  clearExtensionStatuses() {
    this.extensionStatuses.clear();
  }
  /** Number of unique providers with available models (for footer display) */
  getAvailableProviderCount() {
    return this.availableProviderCount;
  }
  /** Internal: update available provider count */
  setAvailableProviderCount(count) {
    this.availableProviderCount = count;
  }
  setCwd(cwd) {
    if (this.cwd === cwd) {
      return;
    }
    this.cwd = cwd;
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
    this.clearGitWatchers();
    this.cachedBranch = undefined;
    this.gitPaths = findGitPaths(cwd);
    this.setupGitWatcher();
    this.notifyBranchChange();
  }
  /** Internal: cleanup */
  dispose() {
    this.disposed = true;
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
    this.clearGitWatchers();
    this.branchChangeCallbacks.clear();
  }
  notifyBranchChange() {
    for (const cb of this.branchChangeCallbacks)
    cb();
  }
  scheduleRefresh() {
    if (this.disposed || this.refreshTimer)
    return;
    if (this.refreshInFlight) {
      this.refreshPending = true;
      return;
    }
    this.refreshTimer = setTimeout(() => {
      this.refreshTimer = null;
      void this.refreshGitBranchAsync();
    }, FooterDataProvider.WATCH_DEBOUNCE_MS);
  }
  async refreshGitBranchAsync() {
    if (this.disposed)
    return;
    if (this.refreshInFlight) {
      this.refreshPending = true;
      return;
    }
    this.refreshInFlight = true;
    try {
      const nextBranch = await this.resolveGitBranchAsync();
      if (this.disposed)
      return;
      if (this.cachedBranch !== undefined && this.cachedBranch !== nextBranch) {
        this.cachedBranch = nextBranch;
        this.notifyBranchChange();
        return;
      }
      this.cachedBranch = nextBranch;
    } finally
    {
      this.refreshInFlight = false;
      if (this.refreshPending && !this.disposed) {
        this.refreshPending = false;
        this.scheduleRefresh();
      }
    }
  }
  resolveGitBranchSync() {
    try {
      if (!this.gitPaths)
      return null;
      const content = (0, _fs.readFileSync)(this.gitPaths.headPath, "utf8").trim();
      if (content.startsWith("ref: refs/heads/")) {
        const branch = content.slice(16);
        return branch === ".invalid" ? resolveBranchWithGitSync(this.gitPaths.repoDir) ?? "detached" : branch;
      }
      return "detached";
    }
    catch {
      return null;
    }
  }
  async resolveGitBranchAsync() {
    try {
      if (!this.gitPaths)
      return null;
      const content = (0, _fs.readFileSync)(this.gitPaths.headPath, "utf8").trim();
      if (content.startsWith("ref: refs/heads/")) {
        const branch = content.slice(16);
        return branch === ".invalid" ?
        (await resolveBranchWithGitAsync(this.gitPaths.repoDir)) ?? "detached" :
        branch;
      }
      return "detached";
    }
    catch {
      return null;
    }
  }
  clearGitWatchers() {
    (0, _fsWatch.closeWatcher)(this.headWatcher);
    this.headWatcher = null;
    (0, _fsWatch.closeWatcher)(this.reftableWatcher);
    this.reftableWatcher = null;
    (0, _fsWatch.closeWatcher)(this.reftableTablesListWatcher);
    this.reftableTablesListWatcher = null;
    if (this.reftableTablesListPath) {
      (0, _fs.unwatchFile)(this.reftableTablesListPath);
      this.reftableTablesListPath = null;
    }
    if (this.gitWatcherRetryTimer) {
      clearTimeout(this.gitWatcherRetryTimer);
      this.gitWatcherRetryTimer = null;
    }
  }
  scheduleGitWatcherRetry() {
    if (this.disposed || this.gitWatcherRetryTimer) {
      return;
    }
    this.gitWatcherRetryTimer = setTimeout(() => {
      this.gitWatcherRetryTimer = null;
      this.setupGitWatcher();
    }, _fsWatch.FS_WATCH_RETRY_DELAY_MS);
  }
  handleGitWatcherError() {
    this.clearGitWatchers();
    this.scheduleGitWatcherRetry();
  }
  setupGitWatcher() {
    this.clearGitWatchers();
    if (!this.gitPaths)
    return;
    // Watch the directory containing HEAD, not HEAD itself.
    // Git uses atomic writes (write temp, rename over HEAD), which changes the inode.
    // fs.watch on a file stops working after the inode changes.
    this.headWatcher = (0, _fsWatch.watchWithErrorHandler)((0, _path.dirname)(this.gitPaths.headPath), (_eventType, filename) => {
      if (!filename || filename === "HEAD") {
        this.scheduleRefresh();
      }
    }, () => this.handleGitWatcherError());
    if (!this.headWatcher) {
      return;
    }
    // In reftable repos, branch switches update files in the reftable directory
    // instead of HEAD. Watch it separately so the footer picks up those changes.
    const reftableDir = (0, _path.join)(this.gitPaths.commonGitDir, "reftable");
    if ((0, _fs.existsSync)(reftableDir)) {
      this.reftableWatcher = (0, _fsWatch.watchWithErrorHandler)(reftableDir, () => {
        this.scheduleRefresh();
      }, () => this.handleGitWatcherError());
      if (!this.reftableWatcher) {
        return;
      }
      const tablesListPath = (0, _path.join)(reftableDir, "tables.list");
      if ((0, _fs.existsSync)(tablesListPath)) {
        this.reftableTablesListPath = tablesListPath;
        this.reftableTablesListWatcher = (0, _fsWatch.watchWithErrorHandler)(tablesListPath, () => {
          this.scheduleRefresh();
        }, () => this.handleGitWatcherError());
        if (!this.reftableTablesListWatcher) {
          return;
        }
        (0, _fs.watchFile)(tablesListPath, { interval: 250 }, (current, previous) => {
          if (current.mtimeMs !== previous.mtimeMs ||
          current.ctimeMs !== previous.ctimeMs ||
          current.size !== previous.size) {
            this.scheduleRefresh();
          }
        });
      }
    }
  }
}exports.FooterDataProvider = FooterDataProvider; /* v9-bba16ba31a4c5eec */
