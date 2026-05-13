"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.ThinkingSelectorComponent = void 0;var _piTui = require("@mariozechner/pi-tui");
var _theme = require("../theme/theme.js");
var _dynamicBorder = require("./dynamic-border.js");
const THINKING_SELECT_LIST_LAYOUT = {
  minPrimaryColumnWidth: 12,
  maxPrimaryColumnWidth: 32
};
const LEVEL_DESCRIPTIONS = {
  off: "No reasoning",
  minimal: "Very brief reasoning (~1k tokens)",
  low: "Light reasoning (~2k tokens)",
  medium: "Moderate reasoning (~8k tokens)",
  high: "Deep reasoning (~16k tokens)",
  xhigh: "Maximum reasoning (~32k tokens)"
};
/**
 * Component that renders a thinking level selector with borders
 */
class ThinkingSelectorComponent extends _piTui.Container {
  selectList;
  constructor(currentLevel, availableLevels, onSelect, onCancel) {
    super();
    const thinkingLevels = availableLevels.map((level) => ({
      value: level,
      label: level,
      description: LEVEL_DESCRIPTIONS[level]
    }));
    // Add top border
    this.addChild(new _dynamicBorder.DynamicBorder());
    // Create selector
    this.selectList = new _piTui.SelectList(thinkingLevels, thinkingLevels.length, (0, _theme.getSelectListTheme)(), THINKING_SELECT_LIST_LAYOUT);
    // Preselect current level
    const currentIndex = thinkingLevels.findIndex((item) => item.value === currentLevel);
    if (currentIndex !== -1) {
      this.selectList.setSelectedIndex(currentIndex);
    }
    this.selectList.onSelect = (item) => {
      onSelect(item.value);
    };
    this.selectList.onCancel = () => {
      onCancel();
    };
    this.addChild(this.selectList);
    // Add bottom border
    this.addChild(new _dynamicBorder.DynamicBorder());
  }
  getSelectList() {
    return this.selectList;
  }
}exports.ThinkingSelectorComponent = ThinkingSelectorComponent; /* v9-f46137138fc8b0c5 */
